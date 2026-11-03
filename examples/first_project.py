"""Exemple sans réseau ni base de données."""
from datetime import datetime, timezone
from functools import partial

from pyprojectkit import (
    ActorContext, ExplicitPolicy, FixedClock, InMemoryDatabase,
    InMemoryUnitOfWork, ProjectService, ProjectStatus, TaskStatus,
)

db = InMemoryDatabase()
actor = ActorContext("demo", "demo-scope")
permissions = {"PROJECT_CREATE", "PROJECT_VIEW", "PROJECT_PLAN", "PROJECT_START", "TASK_CREATE", "TASK_VIEW", "TASK_EDIT", "TASK_START", "TASK_COMPLETE"}
service = ProjectService(partial(InMemoryUnitOfWork, db), ExplicitPolicy({"demo": permissions}), FixedClock(datetime(2026, 11, 3, tzinfo=timezone.utc)))
project = service.create_project(actor, "Projet de démonstration", "demo")
service.transition_project(actor, project, ProjectStatus.PLANNED)
service.transition_project(actor, project, ProjectStatus.ACTIVE)
a = service.create_task(actor, project, "Écrire le contrat")
b = service.create_task(actor, project, "Vérifier le contrat")
service.add_dependency(actor, b, a)
service.transition_task(actor, a, TaskStatus.READY)
service.transition_task(actor, a, TaskStatus.IN_PROGRESS)
service.transition_task(actor, a, TaskStatus.DONE)
service.transition_task(actor, b, TaskStatus.READY)
service.transition_task(actor, b, TaskStatus.IN_PROGRESS)
print(f"Projet {project.value} : {len(service.list_tasks(actor, project))} tâches, {len(db.events)} événements confirmés")