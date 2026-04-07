"""Tests for resource dependency types and dependency manager."""

from __future__ import annotations

import pickle

from daft.execution.dependency_manager import DefaultDependencyManager
from daft.execution.resource_dependency import (
    FileDependency,
    PythonPackageDependency,
    ResourceDependencies,
)


class TestFileDependency:
    def test_creation(self):
        dep = FileDependency(uri="s3://bucket/path/file.jar")
        assert dep.dependency_type == "file"
        assert dep.uri == "s3://bucket/path/file.jar"
        assert dep.local_path is None

    def test_creation_with_local_path(self):
        dep = FileDependency(uri="s3://bucket/file.jar", local_path="/tmp/file.jar")
        assert dep.uri == "s3://bucket/file.jar"
        assert dep.local_path == "/tmp/file.jar"

    def test_equality(self):
        dep1 = FileDependency(uri="s3://bucket/file.jar")
        dep2 = FileDependency(uri="s3://bucket/file.jar")
        dep3 = FileDependency(uri="s3://bucket/other.jar")
        assert dep1 == dep2
        assert dep1 != dep3

    def test_hash(self):
        dep1 = FileDependency(uri="s3://bucket/file.jar")
        dep2 = FileDependency(uri="s3://bucket/file.jar")
        assert hash(dep1) == hash(dep2)

    def test_repr(self):
        dep = FileDependency(uri="s3://bucket/file.jar")
        assert "s3://bucket/file.jar" in repr(dep)

    def test_pickle_roundtrip(self):
        dep = FileDependency(uri="s3://bucket/file.jar", local_path="/tmp/file.jar")
        restored = pickle.loads(pickle.dumps(dep))
        assert restored == dep
        assert restored.uri == dep.uri
        assert restored.local_path == dep.local_path


class TestPythonPackageDependency:
    def test_creation(self):
        dep = PythonPackageDependency(package_name="numpy")
        assert dep.dependency_type == "python_package"
        assert dep.package_name == "numpy"
        assert dep.version is None

    def test_creation_with_version(self):
        dep = PythonPackageDependency(package_name="numpy", version=">=1.24.0")
        assert dep.package_name == "numpy"
        assert dep.version == ">=1.24.0"

    def test_equality(self):
        dep1 = PythonPackageDependency(package_name="numpy", version=">=1.24.0")
        dep2 = PythonPackageDependency(package_name="numpy", version=">=1.24.0")
        dep3 = PythonPackageDependency(package_name="pandas")
        assert dep1 == dep2
        assert dep1 != dep3

    def test_hash(self):
        dep1 = PythonPackageDependency(package_name="numpy")
        dep2 = PythonPackageDependency(package_name="numpy")
        assert hash(dep1) == hash(dep2)

    def test_repr(self):
        dep = PythonPackageDependency(package_name="numpy", version=">=1.24.0")
        assert "numpy" in repr(dep)

    def test_pickle_roundtrip(self):
        dep = PythonPackageDependency(package_name="numpy", version=">=1.24.0")
        restored = pickle.loads(pickle.dumps(dep))
        assert restored == dep


class TestResourceDependencies:
    def test_empty(self):
        deps = ResourceDependencies()
        assert deps.is_empty()
        assert len(deps) == 0
        assert deps.dependencies == []

    def test_init_with_list(self):
        dep1 = FileDependency(uri="s3://bucket/file1.jar")
        dep2 = PythonPackageDependency(package_name="numpy")
        deps = ResourceDependencies([dep1, dep2])
        assert not deps.is_empty()
        assert len(deps) == 2

    def test_add(self):
        deps = ResourceDependencies()
        deps.add(FileDependency(uri="s3://bucket/file.jar"))
        assert len(deps) == 1
        assert not deps.is_empty()

    def test_merge_deduplicates(self):
        dep1 = FileDependency(uri="s3://bucket/file1.jar")
        dep2 = FileDependency(uri="s3://bucket/file2.jar")
        dep3 = PythonPackageDependency(package_name="numpy")

        deps_a = ResourceDependencies([dep1, dep2])
        deps_b = ResourceDependencies([dep2, dep3])  # dep2 is duplicate

        merged = deps_a.merge(deps_b)
        assert len(merged) == 3
        assert dep1 in list(merged)
        assert dep2 in list(merged)
        assert dep3 in list(merged)

    def test_merge_empty(self):
        deps = ResourceDependencies([FileDependency(uri="s3://bucket/file.jar")])
        merged = deps.merge(ResourceDependencies())
        assert len(merged) == 1

    def test_iter(self):
        dep1 = FileDependency(uri="s3://bucket/file1.jar")
        dep2 = PythonPackageDependency(package_name="numpy")
        deps = ResourceDependencies([dep1, dep2])
        items = list(deps)
        assert items == [dep1, dep2]

    def test_equality(self):
        dep1 = FileDependency(uri="s3://bucket/file.jar")
        deps_a = ResourceDependencies([dep1])
        deps_b = ResourceDependencies([dep1])
        assert deps_a == deps_b

    def test_pickle_roundtrip(self):
        deps = ResourceDependencies([
            FileDependency(uri="s3://bucket/file.jar", local_path="/tmp/file.jar"),
            PythonPackageDependency(package_name="numpy", version=">=1.24.0"),
        ])
        restored = pickle.loads(pickle.dumps(deps))
        assert restored == deps
        assert len(restored) == 2

    def test_repr(self):
        deps = ResourceDependencies([FileDependency(uri="s3://bucket/file.jar")])
        assert "ResourceDependencies" in repr(deps)


class TestDefaultDependencyManager:
    def test_resolve_empty(self):
        manager = DefaultDependencyManager()
        deps = ResourceDependencies()
        # Should not raise
        manager.resolve(deps)

    def test_resolve_non_empty(self):
        manager = DefaultDependencyManager()
        deps = ResourceDependencies([
            FileDependency(uri="s3://bucket/file.jar"),
            PythonPackageDependency(package_name="numpy"),
        ])
        # DefaultDependencyManager is no-op, should not raise
        manager.resolve(deps)

    def test_is_subclass_of_abc(self):
        from daft.execution.dependency_manager import DependencyManager
        assert issubclass(DefaultDependencyManager, DependencyManager)
