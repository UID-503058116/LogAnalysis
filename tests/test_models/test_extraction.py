"""提取结果模型测试。"""

import pytest

from logginganalysis.models.extraction import (
    ChunkExtractionResult,
    ExceptionInfo,
    LibraryReference,
    ProblematicBehavior,
)


class TestExceptionInfo:
    """ExceptionInfo 模型测试。"""

    def test_create_exception_info(self):
        """测试创建异常信息。"""
        exc = ExceptionInfo(
            type="ConnectionError",
            message="Database timeout",
            stack_trace="Traceback...",
            occurrence_count=3,
        )
        assert exc.type == "ConnectionError"
        assert exc.message == "Database timeout"
        assert exc.stack_trace == "Traceback..."
        assert exc.occurrence_count == 3

    def test_exception_info_defaults(self):
        """测试异常信息默认值。"""
        exc = ExceptionInfo(
            type="ValueError",
            message="Invalid input",
        )
        assert exc.stack_trace is None
        assert exc.occurrence_count == 1


class TestLibraryReference:
    """LibraryReference 模型测试。"""

    def test_create_library_reference(self):
        """测试创建库引用。"""
        lib = LibraryReference(
            name="FastAPI",
            version="0.104.1",
            context="FastAPI version 0.104.1 starting up",
        )
        assert lib.name == "FastAPI"
        assert lib.version == "0.104.1"
        assert lib.context == "FastAPI version 0.104.1 starting up"

    def test_library_reference_without_version(self):
        """测试没有版本的库引用。"""
        lib = LibraryReference(
            name="SQLAlchemy",
            version=None,
            context="SQLAlchemy initialized",
        )
        assert lib.name == "SQLAlchemy"
        assert lib.version is None


class TestProblematicBehavior:
    """ProblematicBehavior 模型测试。"""

    def test_create_problematic_behavior(self):
        """测试创建问题行为。"""
        behavior = ProblematicBehavior(
            category="database",
            description="Multiple connection failures",
            severity="high",
            occurrences=["ERROR: timeout", "ERROR: failed"],
        )
        assert behavior.category == "database"
        assert behavior.description == "Multiple connection failures"
        assert behavior.severity == "high"
        assert len(behavior.occurrences) == 2

    def test_problematic_behavior_severity_validation(self):
        """测试问题行为严重程度验证。"""
        valid_severities = ["low", "medium", "high", "critical"]
        for severity in valid_severities:
            behavior = ProblematicBehavior(
                category="test",
                description="Test",
                severity=severity,
                occurrences=[],
            )
            assert behavior.severity == severity

    def test_problematic_behavior_defaults(self):
        """测试问题行为默认值。"""
        behavior = ProblematicBehavior(
            category="performance",
            description="Slow response",
            occurrences=["WARNING: slow"],
        )
        assert behavior.severity == "medium"  # 默认值
        assert behavior.occurrences == ["WARNING: slow"]


class TestChunkExtractionResult:
    """ChunkExtractionResult 模型测试。"""

    def test_create_extraction_result(self):
        """测试创建提取结果。"""
        result = ChunkExtractionResult(
            chunk_id="chunk-123",
            exceptions=[
                ExceptionInfo(
                    type="ConnectionError",
                    message="Timeout",
                )
            ],
            libraries=[
                LibraryReference(
                    name="FastAPI",
                    version="0.104.1",
                    context="Starting",
                )
            ],
            problematic_behaviors=[
                ProblematicBehavior(
                    category="database",
                    description="Connection failed",
                    severity="high",
                    occurrences=["ERROR: timeout"],
                )
            ],
            summary="Database connectivity issues detected",
        )
        assert result.chunk_id == "chunk-123"
        assert len(result.exceptions) == 1
        assert len(result.libraries) == 1
        assert len(result.problematic_behaviors) == 1
        assert result.summary == "Database connectivity issues detected"

    def test_extraction_result_defaults(self):
        """测试提取结果默认值。"""
        result = ChunkExtractionResult(
            chunk_id="chunk-456",
            summary="No issues found",
        )
        assert result.exceptions == []
        assert result.libraries == []
        assert result.problematic_behaviors == []

    def test_extraction_result_serialization(self):
        """测试提取结果序列化。"""
        result = ChunkExtractionResult(
            chunk_id="chunk-789",
            summary="Test",
        )
        data = result.model_dump()
        assert data["chunk_id"] == "chunk-789"
        assert data["summary"] == "Test"

        json_str = result.model_dump_json()
        assert "chunk-789" in json_str
