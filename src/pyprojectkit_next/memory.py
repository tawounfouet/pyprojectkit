"""Adaptateur InMemory : snapshot isolé, commit atomique et conflit optimiste."""
from __future__ import annotations

from threading import RLock

from .domain import (
    ClosureBlocked, Conflict, Dependency, DependencyViolation, DomainEvent,
    InvalidStateTransition, NotFound, Project, ProjectId, ProjectStatus,
    Task, TaskId, TaskStatus, assert_acyclic,
)


class InMemoryDatabase:
    """Prototype mono-processus. Les événements sont un journal local, pas une outbox."""
    def __init__(self) -> None:
        self._lock = RLock()
        self._revision = 0
        self._projects: dict[ProjectId, Project] = {}
        self._tasks: dict[TaskId, Task] = {}
        self._dependencies: dict[ProjectId, frozenset[Dependency]] = {}
        self._events: tuple[DomainEvent, ...] = ()

    @property
    def events(self) -> tuple[DomainEvent, ...]:
        with self._lock:
            return self._events

    def unit_of_work(self) -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(self)


class InMemoryUnitOfWork:
    def __init__(self, db: InMemoryDatabase) -> None:
        self._db = db
        self._open = False
        self._baseline = -1
        self._projects: dict[ProjectId, Project] = {}
        self._tasks: dict[TaskId, Task] = {}
        self._dependencies: dict[ProjectId, frozenset[Dependency]] = {}
        self._pending: list[DomainEvent] = []
        self._dirty = False

    def __enter__(self) -> InMemoryUnitOfWork:
        if self._open:
            raise Conflict("la transaction est déjà ouverte")
        with self._db._lock:
            self._baseline = self._db._revision
            self._projects = self._db._projects.copy()
            self._tasks = self._db._tasks.copy()
            self._dependencies = self._db._dependencies.copy()
        self._open = True
        self._dirty = False
        self._pending = []
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self._open = False
        self._projects.clear()
        self._tasks.clear()
        self._dependencies.clear()
        self._pending.clear()

    def _require_open(self) -> None:
        if not self._open:
            raise Conflict("transaction inactive")

    def get_project(self, id: ProjectId) -> Project:
        self._require_open()
        try:
            return self._projects[id]
        except KeyError as ex:
            raise NotFound("projet introuvable") from ex

    def list_projects(self) -> tuple[Project, ...]:
        self._require_open()
        return tuple(self._projects.values())

    def get_task(self, id: TaskId) -> Task:
        self._require_open()
        try:
            return self._tasks[id]
        except KeyError as ex:
            raise NotFound("tâche introuvable") from ex

    def list_tasks(self, project_id: ProjectId) -> tuple[Task, ...]:
        self._require_open()
        return tuple(t for t in self._tasks.values() if t.project_id == project_id)

    def list_dependencies(self, project_id: ProjectId) -> tuple[Dependency, ...]:
        self._require_open()
        self.get_project(project_id)
        edges = self._dependencies.get(project_id, frozenset())
        return tuple(sorted(edges, key=lambda e: (e.successor.value, e.predecessor.value)))

    def add_dependency(self, project_id: ProjectId, edge: Dependency) -> None:
        self._require_open()
        project = self.get_project(project_id)
        if project.status in {ProjectStatus.COMPLETED, ProjectStatus.CANCELLED}:
            raise DependencyViolation("projet terminal")
        child = self.get_task(edge.successor)
        predecessor = self.get_task(edge.predecessor)
        if child.project_id != project_id or predecessor.project_id != project_id:
            raise DependencyViolation("dépendance inter-projets interdite")
        current = self._dependencies.get(project_id, frozenset())
        if edge in current:
            raise Conflict("dépendance déjà présente")
        updated = current | {edge}
        assert_acyclic(updated)
        self._dependencies[project_id] = frozenset(updated)
        self._dirty = True

    def add_project(self, project: Project) -> None:
        self._require_open()
        if project.id in self._projects:
            raise Conflict("identifiant de projet déjà utilisé")
        self._projects[project.id] = project
        self._dirty = True

    def save_project(self, project: Project) -> None:
        self._require_open()
        old = self.get_project(project.id)
        if old.version + 1 != project.version:
            raise Conflict("version de projet invalide")
        self._projects[project.id] = project
        self._dirty = True

    def add_task(self, task: Task) -> None:
        self._require_open()
        parent = self.get_project(task.project_id)
        if parent.status in {ProjectStatus.COMPLETED, ProjectStatus.CANCELLED}:
            raise InvalidStateTransition("impossible d'ajouter une tâche à un projet terminal")
        if task.id in self._tasks:
            raise Conflict("identifiant de tâche déjà utilisé")
        self._tasks[task.id] = task
        self._dirty = True

    def save_task(self, task: Task) -> None:
        self._require_open()
        old = self.get_task(task.id)
        if old.project_id != task.project_id or old.version + 1 != task.version:
            raise Conflict("version ou appartenance de tâche invalide")
        self._tasks[task.id] = task
        self._dirty = True

    def record(self, event: DomainEvent) -> None:
        self._require_open()
        self._pending.append(event)

    def commit(self) -> tuple[DomainEvent, ...]:
        self._require_open()
        try:
            if self._pending and not self._dirty:
                raise Conflict("événement sans mutation")
            with self._db._lock:
                if self._db._revision != self._baseline:
                    raise Conflict("état modifié par une transaction concurrente")
                if self._dirty:
                    # Vérifier l'état final du snapshot au point de commit.
                    # Une clôture coordonnée des tâches dans cette UoW est permise.
                    projects_with_open_tasks = {
                        task.project_id for task in self._tasks.values()
                        if task.status not in {TaskStatus.DONE, TaskStatus.CANCELLED}
                    }
                    if any(
                        p.status == ProjectStatus.COMPLETED
                        and p.id in projects_with_open_tasks
                        for p in self._projects.values()
                    ):
                        raise ClosureBlocked("clôture impossible avec tâches ouvertes")
                    self._db._projects = self._projects.copy()
                    self._db._tasks = self._tasks.copy()
                    self._db._dependencies = self._dependencies.copy()
                    self._db._events = self._db._events + tuple(self._pending)
                    self._db._revision += 1
                return tuple(self._pending)
        finally:
            self._open = False
            self._pending.clear()
