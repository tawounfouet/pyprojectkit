"""M2-12 - Q-M2 evidence report ne produit jamais un verdict humain."""
from __future__ import annotations

from dataclasses import replace

import pytest

from pyprojectkit import InvalidValue
from pyprojectkit.m2.qualification import (
    AcceptanceEvidence, CRITERIA, CRITERION_REQUIREMENTS,
    build_qualification_dossier,
)

SHA = "a" * 40
CI_URL = "https://github.com/tawounfouet/pyprojectkit/actions/runs/41911590621"


def evidence(criteria=CRITERIA, status="PASS"):
    return tuple(
        AcceptanceEvidence(
            criterion_id=ac, status=status, code_sha=SHA,
            test_node_ids=("tests/test_m2c_pilots.py::test_p1_audit_001_local_git_sha_and_tree_unchanged",),
            ci_run_url=CI_URL, environment="synthetic Python 3.12/3.13",
            observed_result="Fixture deterministic CI, non independent external verification",
            limitations=("Contract or tool not available for full audit",) if status != "PASS" else (),
            residual_risks=("Fake Pythos only",),
        )
        for ac in criteria
    )


def test_qm2_01_requires_exact_eleven_distinct_criteria():
    assert len(CRITERIA) == 11
    assert len(CRITERION_REQUIREMENTS) == 11
    with pytest.raises(InvalidValue):
        build_qualification_dossier(evidence(CRITERIA[:-1]))
    with pytest.raises(InvalidValue):
        build_qualification_dossier(evidence(CRITERIA[:-1]+(CRITERIA[0],)))


def test_qm2_02_pass_eleven_is_not_human_go():
    dossier = build_qualification_dossier(evidence())
    assert dossier.assessed_count == 11
    assert dossier.passed_count == 11
    assert dossier.unassessed_count == 0
    assert dossier.technical_status == "TECHNICAL_PASS_REPORTED"
    assert dossier.human_gate == "PENDING"
    assert dossier.adoption_decision == "NOT_GRANTED"
    assert "GO_LOCAL" not in dossier.to_json()


def test_qm2_03_cross_owner_fail_causes_no_go_recommendation():
    rows = list(evidence())
    idx = CRITERIA.index("AC-035")
    rows[idx] = replace(rows[idx], status="FAIL", limitations=("Cross-scope leak detected",))
    dossier = build_qualification_dossier(tuple(rows))
    assert dossier.failed_count == 1
    assert dossier.technical_status == "BLOCKED"
    assert dossier.recommendation == "NO_GO_RECOMMENDED"
    assert dossier.adoption_decision == "NOT_GRANTED"


def test_qm2_04_partial_security_criterion_blocks_automatic_go():
    rows = list(evidence())
    idx = CRITERIA.index("AC-031")
    rows[idx] = replace(rows[idx], status="PARTIAL",
                        limitations=("No actual merge/publish command surface exposed",))
    dossier = build_qualification_dossier(tuple(rows))
    assert dossier.partial_count == 1
    assert dossier.technical_status == "BLOCKED"
    assert dossier.human_gate == "PENDING"


def test_qm2_05_not_executed_requires_limitation_and_stays_unassessed():
    rows = list(evidence())
    rows[0] = replace(rows[0], status="NOT_EXECUTED",
                      limitations=("CI pending",), test_node_ids=())
    dossier = build_qualification_dossier(tuple(rows))
    assert dossier.unassessed_count == 1 and dossier.assessed_count == 10
    assert dossier.adoption_decision == "NOT_GRANTED"
    with pytest.raises(InvalidValue):
        replace(rows[0], limitations=())


def test_qm2_06_different_sha_is_invalid():
    rows = list(evidence())
    rows[-1] = replace(rows[-1], code_sha="b"*40)
    with pytest.raises(InvalidValue):
        build_qualification_dossier(tuple(rows))


def test_qm2_07_invalid_evidence_fields_rejected():
    row = evidence()[0]
    with pytest.raises(InvalidValue):
        replace(row, ci_run_url="http://unverified.invalid")
    with pytest.raises(InvalidValue):
        replace(row, status="PASS", test_node_ids=())
    with pytest.raises(InvalidValue):
        replace(row, code_sha="main")


def test_qm2_08_json_does_not_expose_authority_capabilities():
    dossier = build_qualification_dossier(evidence())
    raw = dossier.to_json()
    assert '"human_gate": "PENDING"' in raw
    assert '"adoption_decision": "NOT_GRANTED"' in raw
    assert "AUTO_APPROVE" not in raw


def test_qm2_09_realistic_partial_manifest_requires_review():
    rows = list(evidence())
    for ac in ("AC-031", "AC-034"):
        index = CRITERIA.index(ac)
        rows[index] = replace(rows[index], status="PARTIAL",
                              limitations=("Human review or external command not exercised",))
    dossier = build_qualification_dossier(tuple(rows))
    assert (dossier.assessed_count, dossier.passed_count,
            dossier.partial_count, dossier.failed_count) == (11, 9, 2, 0)
    assert dossier.recommendation == "NO_GO_RECOMMENDED"
    assert dossier.adoption_decision == "NOT_GRANTED"
