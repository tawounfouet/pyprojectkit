"""Pilote synthétique, sans stockage externe et sans Pythos réel."""
from pyprojectkit_next import ActorContext, InMemoryDatabase, OwnerScopePolicy, ProjectService, SystemClock, UUIDFactory


def main() -> None:
    database = InMemoryDatabase()
    actor = ActorContext("owner-demo", frozenset({"INTERNAL"}))
    service = ProjectService(database.unit_of_work, clock=SystemClock(),
                             ids=UUIDFactory(), authorization=OwnerScopePolicy())
    project = service.create_project(actor, "Pilote synthétique", "INTERNAL")
    service.plan_project(actor, project.id)
    service.start_project(actor, project.id)
    task = service.create_task(actor, project.id, "Vérifier le noyau")
    service.ready_task(actor, task.id)
    service.start_task(actor, task.id)
    service.complete_task(actor, task.id)
    done = service.complete_project(actor, project.id)
    print(f"VS-REBOOT-01 : {done.status.value} ; événements locaux : {len(database.events)}")


if __name__ == "__main__":
    main()
