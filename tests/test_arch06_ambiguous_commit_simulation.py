"""Oracles C06-09 : reprise fail closed dans un simulateur purement mémoire."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from pyprojectkit_next.domain import Conflict, DomainError, InvalidValue
from pyprojectkit_next.recovery import (
    CommitIntent, CommitOutcomeUnknown, FailurePoint, IdempotencyConflict,
    RecoveryResolution,
    RecoveryState, SimulatedCommitLedger,
)

PAYLOAD = b'{"cmd":"create_project","name":"synthetic"}'
EVENTS = ("ProjectCreated",)


def intent(*, op: str = "request-1", actor: str = "alice", scope: str = "alpha",
           payload: bytes = PAYLOAD, events: tuple[str, ...] = EVENTS) -> CommitIntent:
    return CommitIntent.bind(op, actor, scope, payload, events)


def test_commit_returns_receipt_and_reconcile_committed() -> None:
    sim = SimulatedCommitLedger()
    req = intent()
    receipt = sim.submit(req, PAYLOAD, EVENTS)
    resolution = sim.reconcile(req)
    assert resolution == RecoveryResolution(RecoveryState.COMMITTED, receipt)
    assert not resolution.safe_to_retry
    assert receipt.sequence == 1 and receipt.event_count == 1
    assert len(sim.event_log) == 1


def test_pre_commit_communication_failure_remains_indeterminate() -> None:
    sim = SimulatedCommitLedger()
    req = intent()
    with pytest.raises(CommitOutcomeUnknown):
        sim.submit(req, PAYLOAD, EVENTS, fail_at=FailurePoint.BEFORE_COMMIT)
    resolution = sim.reconcile(req)
    assert resolution.state is RecoveryState.INDETERMINATE
    assert resolution.receipt is None and not resolution.safe_to_retry
    assert sim.event_log == ()


def test_indeterminate_operation_cannot_be_retried_blindly() -> None:
    sim = SimulatedCommitLedger()
    req = intent()
    with pytest.raises(CommitOutcomeUnknown):
        sim.submit(req, PAYLOAD, EVENTS, fail_at=FailurePoint.BEFORE_COMMIT)
    with pytest.raises(CommitOutcomeUnknown):
        sim.submit(req, PAYLOAD, EVENTS)
    assert sim.event_log == ()


def test_post_commit_lost_ack_reconciles_positive_receipt() -> None:
    sim = SimulatedCommitLedger()
    req = intent()
    with pytest.raises(CommitOutcomeUnknown):
        sim.submit(req, PAYLOAD, EVENTS, fail_at=FailurePoint.AFTER_COMMIT_BEFORE_ACK)
    resolution = sim.reconcile(req)
    assert resolution.state is RecoveryState.COMMITTED
    assert resolution.receipt is not None
    assert resolution.receipt.sequence == 1
    assert len(sim.event_log) == 1


def test_identical_replay_returns_same_receipt_without_double_events() -> None:
    sim = SimulatedCommitLedger()
    req = intent()
    with pytest.raises(CommitOutcomeUnknown):
        sim.submit(req, PAYLOAD, EVENTS, fail_at=FailurePoint.AFTER_COMMIT_BEFORE_ACK)
    original = sim.reconcile(req).receipt
    retry = sim.submit(req, PAYLOAD, EVENTS)
    assert original == retry
    assert len(sim.event_log) == 1


def test_same_operation_with_changed_payload_is_a_conflict() -> None:
    sim = SimulatedCommitLedger()
    req = intent()
    sim.submit(req, PAYLOAD, EVENTS)
    altered_payload = b"different command"
    with pytest.raises(Conflict):
        sim.submit(intent(payload=altered_payload), altered_payload, EVENTS)
    assert len(sim.event_log) == 1


def test_same_operation_with_changed_event_plan_is_a_conflict() -> None:
    sim = SimulatedCommitLedger()
    req = intent()
    sim.submit(req, PAYLOAD, EVENTS)
    with pytest.raises(Conflict):
        sim.submit(intent(events=("ProjectCancelled",)), PAYLOAD, ("ProjectCancelled",))
    assert len(sim.event_log) == 1


def test_mismatched_intent_payload_does_not_modify_journal() -> None:
    sim = SimulatedCommitLedger()
    with pytest.raises(Conflict):
        sim.submit(intent(), b"different bytes", EVENTS)
    assert sim.event_log == ()


def test_intention_is_namespaced_by_actor_and_scope() -> None:
    sim = SimulatedCommitLedger()
    a = sim.submit(intent(actor="alice", scope="alpha"), PAYLOAD, EVENTS)
    b = sim.submit(intent(actor="bob", scope="alpha"), PAYLOAD, EVENTS)
    c = sim.submit(intent(actor="alice", scope="beta"), PAYLOAD, EVENTS)
    assert (a.sequence, b.sequence, c.sequence) == (1, 2, 3)
    assert len(sim.event_log) == 3
    assert sim.reconcile(intent(actor="bob", scope="alpha")).receipt == b


def test_no_receipt_does_not_prove_absence_even_without_prior_attempt() -> None:
    sim = SimulatedCommitLedger()
    state = sim.reconcile(intent(op="unknown"))
    assert state.state is RecoveryState.INDETERMINATE
    assert not state.safe_to_retry


def test_validation_rejects_invalid_identity_and_fingerprint() -> None:
    with pytest.raises(InvalidValue):
        intent(op="a b")
    with pytest.raises(InvalidValue):
        CommitIntent("id", "alice", "alpha", "not-a-hash")
    with pytest.raises(InvalidValue):
        intent(payload=b"")
    with pytest.raises(InvalidValue):
        intent(events=())
    with pytest.raises(InvalidValue):
        intent(events=("a\nsecret",))


def test_failure_is_not_a_normal_conflict() -> None:
    assert not issubclass(CommitOutcomeUnknown, Conflict)
    assert issubclass(CommitOutcomeUnknown, DomainError)
    assert CommitOutcomeUnknown.code == "COMMIT_OUTCOME_UNKNOWN"


def test_recovery_resolution_refuses_false_positive_receipt() -> None:
    with pytest.raises(InvalidValue):
        RecoveryResolution(RecoveryState.COMMITTED)
    receipt = SimulatedCommitLedger().submit(intent(), PAYLOAD, EVENTS)
    with pytest.raises(InvalidValue):
        RecoveryResolution(RecoveryState.INDETERMINATE, receipt)


def test_two_parallel_submits_for_same_operation_are_idempotent() -> None:
    sim = SimulatedCommitLedger()
    req = intent()
    with ThreadPoolExecutor(max_workers=8) as executor:
        receipts = list(executor.map(lambda _: sim.submit(req, PAYLOAD, EVENTS), range(24)))
    assert all(receipt == receipts[0] for receipt in receipts)
    assert len(sim.event_log) == 1


def test_two_distinct_operations_are_recorded_in_order() -> None:
    sim = SimulatedCommitLedger()
    first = sim.submit(intent(op="one"), PAYLOAD, EVENTS)
    second = sim.submit(intent(op="two"), PAYLOAD, ("ProjectCreated",))
    assert first.sequence == 1 and second.sequence == 2
    assert [row[2] for row in sim.event_log] == ["one", "two"]


def test_no_accidental_persistence_across_fresh_simulator() -> None:
    req = intent()
    sim = SimulatedCommitLedger()
    sim.submit(req, PAYLOAD, EVENTS)
    assert SimulatedCommitLedger().reconcile(req).state is RecoveryState.INDETERMINATE


def test_indeterminate_key_cannot_be_reused_with_another_fingerprint() -> None:
    sim = SimulatedCommitLedger()
    with pytest.raises(CommitOutcomeUnknown):
        sim.submit(intent(), PAYLOAD, EVENTS, fail_at=FailurePoint.BEFORE_COMMIT)
    different_payload = b"changed"
    with pytest.raises(Conflict):
        sim.reconcile(intent(payload=different_payload))
    with pytest.raises(Conflict):
        sim.submit(intent(payload=different_payload), different_payload, EVENTS)
    assert sim.event_log == ()


def test_invalid_failure_point_is_rejected_before_any_commit() -> None:
    sim = SimulatedCommitLedger()
    with pytest.raises(InvalidValue):
        sim.submit(intent(), PAYLOAD, EVENTS, fail_at="AFTER_COMMIT_BEFORE_ACK")  # type: ignore[arg-type]
    assert sim.event_log == ()


def test_invalid_recovery_state_is_not_accepted() -> None:
    with pytest.raises(InvalidValue):
        RecoveryResolution("COMMITTED")  # type: ignore[arg-type]


def test_idempotency_conflict_has_specific_stable_error_code() -> None:
    assert issubclass(IdempotencyConflict, Conflict)
    assert IdempotencyConflict.code == "IDEMPOTENCY_CONFLICT"
    sim = SimulatedCommitLedger()
    sim.submit(intent(), PAYLOAD, EVENTS)
    with pytest.raises(IdempotencyConflict):
        sim.submit(intent(payload=b"changed"), b"changed", EVENTS)
