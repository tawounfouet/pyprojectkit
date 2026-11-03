"""Adapter InMemory transactionnel, versions optimistes et buffer d'événements."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from threading import RLock
from typing import Callable, Generic, TypeVar

from .domain import Conflict, Dependency, DomainEvent, Project, ProjectId, Task, TaskId, assert_acyclic

T = TypeVar("T", Project, Task)
I = TypeVar("I", ProjectId, TaskId)


class InMemoryDatabase:
    def __init__(self) -> None:
        self._lock = RLock()
        self.projects: dict[ProjectId, Project] = {}
        self.tasks: dict[TaskId, Task] = {}
        self.graphs: dict[ProjectId, tuple[int, set[Dependency]]] = {}
        self.events: list[DomainEvent] = []


class Repository(Generic[I, T]):
    def __init__(self, original: dict[I, T], identity: Callable[[T], I]):
        self._identity = identity
        self.original: dict[I, T] = deepcopy(original)
        self.staged: dict[I, T] = {}
        self.read_versions: dict[I, int | None] = {}

    def get(self, identifier: I) -> T | None:
        obj = self.staged.get(identifier, self.original.get(identifier))
        original = self.original.get(identifier)
        self.read_versions.setdefault(identifier, original.version if original else None)
        return deepcopy(obj) if obj is not None else None

    def list_all(self) -> list[T]:
        keys = self.original.keys() | self.staged.keys()
        result: list[T] = []
        for key in keys:
            obj = self.get(key)
            if obj is not None:
                result.append(obj)
        return result

    def add(self, obj: T) -> None:
        identifier = self._identity(obj)
        if identifier in self.staged or identifier in self.original:
            raise Conflict("Identité déjà utilisée")
        self.staged[identifier] = deepcopy(obj)

    def save(self, obj: T, *, expected_version: int) -> None:
        identifier = self._identity(obj)
        known = self.staged.get(identifier, self.original.get(identifier))
        if known is None or known.version != expected_version:
            raise Conflict("Version obsolète ou entité absente")
        self.staged[identifier] = deepcopy(obj)


class DependencyGraphPort:
    def __init__(self, original: dict[ProjectId, tuple[int, set[Dependency]]]) -> None:
        self.original = deepcopy(original)
        self.staged: dict[ProjectId, tuple[int, set[Dependency]]] = {}

    def snapshot(self, project_id: ProjectId) -> tuple[int, set[Dependency]]:
        return deepcopy(self.staged.get(project_id, self.original.get(project_id, (0, set()))))

    def replace_if_version(
        self, project_id: ProjectId, *, expected_version: int, edges: set[Dependency]
    ) -> None:
        current_version, _ = self.snapshot(project_id)
        if current_version != expected_version:
            raise Conflict("Version de graphe obsolète")
        assert_acyclic(edges)
        self.staged[project_id] = (expected_version + 1, deepcopy(edges))


def _verify_repo(repo: Repository[I, T], global_store: dict[I, T]) -> None:
    for key in repo.staged.keys() | repo.read_versions.keys():
        before = repo.original.get(key)
        current = global_store.get(key)
        if before is None and current is not None:
            raise Conflict("Création concurrente")
        if before is not None and (current is None or current.version != before.version):
            raise Conflict("Modification concurrente")


class InMemoryUnitOfWork:
    """Commit atomique par verrou et validation de versions des writes.

    Les copies sauvegardées n'exposent jamais les objets du store global.
    """
    def __init__(self, db: InMemoryDatabase):
        self.db = db
        self._active = False
        self._committed = False
        self._events: list[DomainEvent] = []
        self.projects: Repository[ProjectId, Project]
        self.tasks: Repository[TaskId, Task]
        self.dependencies: DependencyGraphPort

    def __enter__(self) -> "InMemoryUnitOfWork":
        if self._active:
            raise RuntimeError("UnitOfWork déjà ouverte")
        with self.db._lock:
            self.projects = Repository[ProjectId, Project](self.db.projects, lambda p: p.id)
            self.tasks = Repository[TaskId, Task](self.db.tasks, lambda t: t.id)
            self.dependencies = DependencyGraphPort(self.db.graphs)
        self._active = True
        return self

    def record(self, event: DomainEvent) -> None:
        if not self._active or self._committed:
            raise RuntimeError("UnitOfWork inactive")
        self._events.append(event)

    def commit(self) -> None:
        if not self._active or self._committed:
            raise RuntimeError("Commit impossible")
        with self.db._lock:
            _verify_repo(self.projects, self.db.projects)
            _verify_repo(self.tasks, self.db.tasks)
            for key in self.dependencies.staged:
                before_version = self.dependencies.original.get(key, (0, set()))[0]
                current_version = self.db.graphs.get(key, (0, set()))[0]
                if current_version != before_version:
                    raise Conflict("Conflit concurrent sur le graphe")
            # Prepare replacement objects before the first global mutation.
            prepared_projects = {
                key: replace(deepcopy(obj), version=(self.projects.original[key].version + 1 if key in self.projects.original else 1))
                for key, obj in self.projects.staged.items()
            }
            prepared_tasks = {
                key: replace(deepcopy(obj), version=(self.tasks.original[key].version + 1 if key in self.tasks.original else 1))
                for key, obj in self.tasks.staged.items()
            }
            prepared_graphs = deepcopy(self.dependencies.staged)
            prepared_events = deepcopy(self._events)
            # Applying prepared state under one lock is atomic for InMemory observers.
            self.db.projects.update(prepared_projects)
            self.db.tasks.update(prepared_tasks)
            self.db.graphs.update(prepared_graphs)
            self.db.events.extend(prepared_events)
        self._committed = True

    def rollback(self) -> None:
        self._events.clear()
        self._active = False

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: object) -> None:
        if not self._committed:
            self.rollback()
        self._active = False
