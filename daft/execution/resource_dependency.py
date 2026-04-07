"""Resource dependency definitions for Daft task execution.

This module defines the base types for resource dependencies that tasks may require.
Resource dependencies represent external resources (files, packages, etc.) that must
be resolved and fetched to a worker before a task can execute.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ResourceDependency(ABC):
    """Base class for a resource dependency that a task requires.

    Subclasses represent specific types of dependencies (files, packages, etc.).
    All ResourceDependency instances must be serializable via cloudpickle for
    distribution to workers.
    """

    @property
    @abstractmethod
    def dependency_type(self) -> str:
        """Returns the type identifier for this dependency."""

    @abstractmethod
    def __repr__(self) -> str: ...

    @abstractmethod
    def __eq__(self, other: object) -> bool: ...

    @abstractmethod
    def __hash__(self) -> int: ...


class FileDependency(ResourceDependency):
    """A file or artifact that needs to be available on the worker.

    Attributes:
        uri: The URI of the file resource (e.g., s3://bucket/path, http://...).
        local_path: Optional local path where the file should be placed on the worker.
    """

    def __init__(self, uri: str, local_path: str | None = None):
        self._uri = uri
        self._local_path = local_path

    @property
    def dependency_type(self) -> str:
        return "file"

    @property
    def uri(self) -> str:
        return self._uri

    @property
    def local_path(self) -> str | None:
        return self._local_path

    def __repr__(self) -> str:
        if self._local_path:
            return f"FileDependency(uri={self._uri!r}, local_path={self._local_path!r})"
        return f"FileDependency(uri={self._uri!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FileDependency):
            return NotImplemented
        return self._uri == other._uri and self._local_path == other._local_path

    def __hash__(self) -> int:
        return hash(("file", self._uri, self._local_path))


class PythonPackageDependency(ResourceDependency):
    """A Python package that needs to be installed on the worker.

    Attributes:
        package_name: The name of the Python package.
        version: Optional version constraint (e.g., ">=1.0.0").
    """

    def __init__(self, package_name: str, version: str | None = None):
        self._package_name = package_name
        self._version = version

    @property
    def dependency_type(self) -> str:
        return "python_package"

    @property
    def package_name(self) -> str:
        return self._package_name

    @property
    def version(self) -> str | None:
        return self._version

    def __repr__(self) -> str:
        if self._version:
            return f"PythonPackageDependency(package_name={self._package_name!r}, version={self._version!r})"
        return f"PythonPackageDependency(package_name={self._package_name!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PythonPackageDependency):
            return NotImplemented
        return self._package_name == other._package_name and self._version == other._version

    def __hash__(self) -> int:
        return hash(("python_package", self._package_name, self._version))


class ResourceDependencies:
    """A collection of resource dependencies for a task.

    This class aggregates multiple ResourceDependency instances and provides
    methods for adding, merging, and querying dependencies. It is designed
    to be serializable via cloudpickle for distribution to workers.
    """

    def __init__(self, dependencies: list[ResourceDependency] | None = None):
        self._dependencies: list[ResourceDependency] = list(dependencies) if dependencies else []

    @property
    def dependencies(self) -> list[ResourceDependency]:
        """Returns a copy of the dependencies list."""
        return list(self._dependencies)

    def add(self, dep: ResourceDependency) -> None:
        """Add a single dependency to the collection."""
        self._dependencies.append(dep)

    def merge(self, other: ResourceDependencies) -> ResourceDependencies:
        """Merge two ResourceDependencies collections, deduplicating entries.

        Args:
            other: Another ResourceDependencies to merge with.

        Returns:
            A new ResourceDependencies containing the union of both collections.
        """
        seen: set[ResourceDependency] = set(self._dependencies)
        merged = list(self._dependencies)
        for dep in other._dependencies:
            if dep not in seen:
                seen.add(dep)
                merged.append(dep)
        return ResourceDependencies(merged)

    def is_empty(self) -> bool:
        """Returns True if there are no dependencies."""
        return len(self._dependencies) == 0

    def __len__(self) -> int:
        return len(self._dependencies)

    def __repr__(self) -> str:
        return f"ResourceDependencies({self._dependencies!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ResourceDependencies):
            return NotImplemented
        return self._dependencies == other._dependencies

    def __iter__(self):
        return iter(self._dependencies)
