"""ARCH-06 : contrat d'intention idempotente et simulateur d'accusé de commit perdu.

Ce module est un *simulateur*, pas un adapter durable, un outbox ni un host IAM.
Il n'est pas branché sur UnitOfWork.commit() et ne constitue pas G3.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from threading import RLock

from .domain import Conflict, DomainError, InvalidValue

_MAX_PAYLOAD_BYTES = 1024 * 1024
_MAX_TOPICS = 64


class CommitOutcomeUnknown(DomainError):
    """Le client ne sait pas si le backend a réellement validé le commit."""

    code = "COMMIT_OUTCOME_UNKNOWN"


class IdempotencyConflict(Conflict):
    """Même identité d'intention avec empreinte de commande différente."""

    code = "IDEMPOTENCY_CONFLICT"


class RecoveryState(str, Enum):
    """Ne jamais interpréter l'absence de reçu comme un rollback prouvé."""

    COMMITTED = "COMMITTED"
    INDETERMINATE = "INDETERMINATE"


class FailurePoint(str, Enum):
    NONE = "NONE"
    BEFORE_COMMIT = "BEFORE_COMMIT"
    AFTER_COMMIT_BEFORE_ACK = "AFTER_COMMIT_BEFORE_ACK"


def _identifier(value: str, field: str) -> None:
    if (not isinstance(value, str) or not value or len(value) > 128
            or value.strip() != value or any(ord(c) < 33 or ord(c) > 126 for c in value)):
        raise InvalidValue(f"{field} doit être un identifiant ASCII visible sans espaces")


def _validate_payload(payload: bytes, topics: tuple[str, ...]) -> None:
    if not isinstance(payload, bytes) or not payload or len(payload) > _MAX_PAYLOAD_BYTES:
        raise InvalidValue("payload binaire non vide requis (1 MiB maximum)")
    if (not isinstance(topics, tuple) or not topics or len(topics) > _MAX_TOPICS):
        raise InvalidValue("liste d'événements non vide requise (64 maximum)")
    for name in topics:
        _identifier(name, "nom d'événement")


def _fingerprint(payload: bytes, topics: tuple[str, ...]) -> str:
    _validate_payload(payload, topics)
    digest = sha256(b"pyprojectkit.arch06.simulator.v1\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    digest.update(len(topics).to_bytes(4, "big"))
    for topic in topics:
        encoded = topic.encode("ascii")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class CommitIntent:
    """Identité de commande liée à une empreinte du payload et des événements.

    L'acteur et le scope doivent être attestés en amont par un host de confiance.
    Aucun contenu de commande n'est conservé dans cet objet.
    """

    operation_id: str
    actor_id: str
    scope: str
    fingerprint: str

    def __post_init__(self) -> None:
        _identifier(self.operation_id, "operation_id")
        _identifier(self.actor_id, "actor_id")
        _identifier(self.scope, "scope")
        if (not isinstance(self.fingerprint, str) or len(self.fingerprint) != 64
                or any(c not in "0123456789abcdef" for c in self.fingerprint)):
            raise InvalidValue("fingerprint SHA-256 canonique requis")

    @classmethod
    def bind(cls, operation_id: str, actor_id: str, scope: str,
             payload: bytes, event_names: tuple[str, ...]) -> CommitIntent:
        return cls(operation_id, actor_id, scope, _fingerprint(payload, event_names))


@dataclass(frozen=True, slots=True)
class CommitReceipt:
    """Référence d'un commit simulé (non persistée et sans garantie interprocessus)."""

    operation_id: str
    actor_id: str
    scope: str
    fingerprint: str
    sequence: int
    event_count: int

    def __post_init__(self) -> None:
        _identifier(self.operation_id, "operation_id")
        _identifier(self.actor_id, "actor_id")
        _identifier(self.scope, "scope")
        if (not isinstance(self.fingerprint, str) or len(self.fingerprint) != 64
                or any(c not in "0123456789abcdef" for c in self.fingerprint)):
            raise InvalidValue("reçu non conforme")
        if (type(self.sequence) is not int or self.sequence < 1
                or type(self.event_count) is not int or self.event_count < 1):
            raise InvalidValue("numéros de reçu invalides")


@dataclass(frozen=True, slots=True)
class RecoveryResolution:
    state: RecoveryState
    receipt: CommitReceipt | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.state, RecoveryState):
            raise InvalidValue("état de réconciliation invalide")
        if (self.state is RecoveryState.COMMITTED) != (self.receipt is not None):
            raise InvalidValue("un commit confirmé exige son reçu, et lui seul")

    @property
    def safe_to_retry(self) -> bool:
        """Aucun retry automatique sans une preuve durable d'abandon, absente ici."""
        return False


class SimulatedCommitLedger:
    """Simulateur mono-processus des trois fenêtres de commit.

    Ne partage pas la transaction InMemoryDatabase : ne JAMAIS brancher dans une
    production ni présenter ce journal comme un outbox atomique/durable.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._sequence = 0
        self._receipts: dict[tuple[str, str, str], CommitReceipt] = {}
        self._unknown: dict[tuple[str, str, str], CommitIntent] = {}
        self._event_log: tuple[tuple[str, str, str, str], ...] = ()

    @staticmethod
    def _key(intent: CommitIntent) -> tuple[str, str, str]:
        return (intent.actor_id, intent.scope, intent.operation_id)

    @property
    def event_log(self) -> tuple[tuple[str, str, str, str], ...]:
        with self._lock:
            return self._event_log

    def reconcile(self, intent: CommitIntent) -> RecoveryResolution:
        """Le reçu constitue une preuve positive ; son absence n'en est jamais une."""
        if not isinstance(intent, CommitIntent):
            raise InvalidValue("CommitIntent requis")
        with self._lock:
            key = self._key(intent)
            existing = self._receipts.get(key)
            unknown = self._unknown.get(key)
            if ((existing is not None and existing.fingerprint != intent.fingerprint)
                    or (unknown is not None and unknown.fingerprint != intent.fingerprint)):
                raise IdempotencyConflict("réutilisation de clé avec requête différente")
            if existing is None:
                return RecoveryResolution(RecoveryState.INDETERMINATE)
            return RecoveryResolution(RecoveryState.COMMITTED, existing)

    def submit(self, intent: CommitIntent, payload: bytes,
               event_names: tuple[str, ...], *,
               fail_at: FailurePoint = FailurePoint.NONE) -> CommitReceipt:
        """Simule commit + perte d'ack. Ne réessaie jamais un état indéterminé."""
        if not isinstance(intent, CommitIntent):
            raise InvalidValue("CommitIntent requis")
        if not isinstance(fail_at, FailurePoint):
            raise InvalidValue("point de défaillance inconnu")
        if _fingerprint(payload, event_names) != intent.fingerprint:
            raise IdempotencyConflict("intention et commande incompatibles")
        key = self._key(intent)
        with self._lock:
            existing = self._receipts.get(key)
            if existing is not None:
                if existing.fingerprint != intent.fingerprint:
                    raise IdempotencyConflict("réutilisation de clé avec requête différente")
                return existing
            unknown = self._unknown.get(key)
            if unknown is not None:
                if unknown.fingerprint != intent.fingerprint:
                    raise IdempotencyConflict("réutilisation de clé avec requête différente")
                raise CommitOutcomeUnknown("issue du commit indéterminée, réconciliation requise")
            if fail_at is FailurePoint.BEFORE_COMMIT:
                self._unknown[key] = intent
                raise CommitOutcomeUnknown("issue du commit indéterminée, réconciliation requise")
            self._sequence += 1
            receipt = CommitReceipt(intent.operation_id, intent.actor_id,
                                    intent.scope, intent.fingerprint,
                                    self._sequence, len(event_names))
            # Mutation de l'état et enregistrement du reçu dans une section critique
            # seulement pour ce simulateur, pas une transaction durable.
            self._event_log += tuple((intent.actor_id, intent.scope,
                                      intent.operation_id, event) for event in event_names)
            self._receipts[key] = receipt
            if fail_at is FailurePoint.AFTER_COMMIT_BEFORE_ACK:
                raise CommitOutcomeUnknown("ack perdu après commit, réconciliation requise")
            return receipt
