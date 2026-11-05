"""API expérimentale VS-REBOOT-01. Ne remplace PAS ``pyprojectkit``."""
from .application import OwnerScopePolicy, ProjectService, SystemClock, UUIDFactory
from .domain import (
    AccessDenied, ClosureBlocked, Conflict, Dependency, DependencyViolation, DomainError, DomainEvent,
    Milestone, MilestoneId, assert_acyclic, InvalidStateTransition,
    InvalidValue, NotFound, Project, ProjectId, ProjectStatus, Task, TaskId, TaskStatus,
)
from .memory import InMemoryDatabase, InMemoryUnitOfWork
from .ports import ActorContext, AuthorizationPolicy, Clock, IdFactory, UnitOfWork, UnitOfWorkFactory

__all__ = [
    "AccessDenied", "ActorContext", "AuthorizationPolicy", "Clock", "ClosureBlocked", "Conflict",
    "Dependency", "DependencyViolation", "Milestone", "MilestoneId", "assert_acyclic",
    "DomainError", "DomainEvent", "IdFactory", "InMemoryDatabase", "InMemoryUnitOfWork",
    "InvalidStateTransition", "InvalidValue", "NotFound", "OwnerScopePolicy", "Project",
    "ProjectId", "ProjectService", "ProjectStatus", "SystemClock", "Task", "TaskId", "TaskStatus",
    "UnitOfWork", "UnitOfWorkFactory", "UUIDFactory",
]
