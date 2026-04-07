"""Dependency manager for resolving task resource dependencies on workers.

This module defines the DependencyManager interface and a default no-op
implementation. The DependencyManager is responsible for resolving and
fetching resource dependencies to a worker before task execution begins.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from daft.execution.resource_dependency import ResourceDependencies

logger = logging.getLogger(__name__)


class DependencyManager(ABC):
    """Abstract base class for resolving and fetching resource dependencies.

    A DependencyManager is instantiated on each worker and is responsible for
    ensuring that all resource dependencies required by a task are available
    locally before the task begins execution.

    Implementations may cache resolved dependencies to avoid redundant fetches
    across multiple tasks on the same worker.
    """

    @abstractmethod
    def resolve(self, dependencies: ResourceDependencies) -> None:
        """Resolve and fetch all resource dependencies to the local worker.

        This method is called on the worker before task execution begins.
        Implementations should download files, install packages, or perform
        any other necessary setup to make the dependencies available.

        Args:
            dependencies: The resource dependencies to resolve.

        Raises:
            RuntimeError: If any dependency cannot be resolved.
        """


class DefaultDependencyManager(DependencyManager):
    """Default no-op dependency manager.

    This implementation logs dependency information but does not perform
    any actual resolution. It serves as a placeholder until a concrete
    implementation is provided for specific dependency types.
    """

    def resolve(self, dependencies: ResourceDependencies) -> None:
        """Log dependencies but take no action.

        Args:
            dependencies: The resource dependencies (logged but not resolved).
        """
        if not dependencies.is_empty():
            logger.debug(
                "DefaultDependencyManager: received %d dependencies (no-op resolution)",
                len(dependencies),
            )
