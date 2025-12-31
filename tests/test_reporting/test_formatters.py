"""报告格式化器测试。"""

import pytest

from logginganalysis.models.extraction import ChunkExtractionResult
from logginganalysis.models.integration import AnalysisInsight, IntegratedAnalysis
from logginganalysis.models.report import AnalysisReport, ReportMetadata
from logginganalysis.reporting.formatters import (
    JSONFormatter,
    MarkdownFormatter,
    OutputFormat,
    TextFormatter,
    get_formatter,
)


class TestMarkdownFormatter:
    """MarkdownFormatter 测试。"""

    @pytest.fixture
    def sample_report(self):
        """创建示例报告。"""
        metadata = ReportMetadata(
            log_source="test.log",
            log_size_bytes=1024,
            chunk_count=5,
            models_used={"extraction": "gpt-4o-mini", "integration": "gpt-4o"},
            processing_time_seconds=5.5,
        )

        analysis = IntegratedAnalysis(
            overall_summary="Test overall summary",
            key_findings=[
                AnalysisInsight(
                    category="database",
                    description="Database connection issues",
                    evidence=["Connection timeout", "Retry attempts"],
                    recommendations=["Check database", "Increase timeout"],
                )
            ],
            root_cause_analysis="Database service unavailable",
            system_context={"framework": "FastAPI", "database": "PostgreSQL"},
            confidence_score=0.85,
        )

        extractions = [
            ChunkExtractionResult(
                chunk_id="chunk-1",
                summary="First chunk",
                exceptions=[],
                libraries=[],
                problematic_behaviors=[],
            )
        ]

        return AnalysisReport(
            metadata=metadata,
            analysis=analysis,
            raw_extractions=extractions,
        )

    def test_markdown_formatter_basic(self, sample_report):
        """测试 Markdown 基本格式化。"""
        formatter = MarkdownFormatter()
        result = formatter.format(sample_report)

        assert "# 日志分析报告" in result
        assert sample_report.analysis.overall_summary in result
        assert "数据库" in result or "database" in result.lower()

    def test_markdown_formatter_includes_metadata(self, sample_report):
        """测试 Markdown 格式包含元数据。"""
        formatter = MarkdownFormatter()
        result = formatter.format(sample_report)

        assert "test.log" in result
        assert "1024" in result  # log_size_bytes
        assert "5" in result  # chunk_count

    def test_markdown_formatter_confidence_bar(self, sample_report):
        """测试置信度条显示。"""
        formatter = MarkdownFormatter()
        result = formatter.format(sample_report)

        assert "置信度" in result or "confidence" in result.lower()
        # 检查置信度条字符
        assert "█" in result or "░" in result

    def test_markdown_formatter_key_findings(self, sample_report):
        """测试关键发现格式化。"""
        formatter = MarkdownFormatter()
        result = formatter.format(sample_report)

        assert "关键发现" in result or "findings" in result.lower()
        assert "database" in result.lower()

    def test_markdown_formatter_recommendations(self, sample_report):
        """测试建议格式化。"""
        formatter = MarkdownFormatter()
        result = formatter.format(sample_report)

        assert "建议" in result or "recommendation" in result.lower()


class TestJSONFormatter:
    """JSONFormatter 测试。"""

    @pytest.fixture
    def sample_report(self):
        """创建示例报告。"""
        metadata = ReportMetadata(
            log_source=None,
            log_size_bytes=500,
            chunk_count=2,
            models_used={"extraction": "gpt-4o-mini"},
            processing_time_seconds=1.0,
        )

        analysis = IntegratedAnalysis(
            overall_summary="Test summary",
            key_findings=[],
            root_cause_analysis=None,
            system_context={},
            confidence_score=0.75,
        )

        return AnalysisReport(
            metadata=metadata,
            analysis=analysis,
            raw_extractions=[],
        )

    def test_json_formatter_valid(self, sample_report):
        """测试 JSON 格式化器生成有效 JSON。"""
        formatter = JSONFormatter()
        result = formatter.format(sample_report)

        import json

        data = json.loads(result)
        assert data["metadata"]["log_size_bytes"] == 500
        assert data["analysis"]["overall_summary"] == "Test summary"
        assert data["analysis"]["confidence_score"] == 0.75

    def test_json_formatter_structure(self, sample_report):
        """测试 JSON 输出结构。"""
        formatter = JSONFormatter()
        result = formatter.format(sample_report)

        assert '"metadata"' in result
        assert '"analysis"' in result
        assert '"raw_extractions"' in result


class TestTextFormatter:
    """TextFormatter 测试。"""

    @pytest.fixture
    def sample_report(self):
        """创建示例报告。"""
        metadata = ReportMetadata(
            log_source="app.log",
            log_size_bytes=2048,
            chunk_count=3,
            models_used={"extraction": "gpt-4o-mini"},
            processing_time_seconds=2.5,
        )

        analysis = IntegratedAnalysis(
            overall_summary="System running normally",
            key_findings=[],
            root_cause_analysis=None,
            system_context={},
            confidence_score=0.9,
        )

        return AnalysisReport(
            metadata=metadata,
            analysis=analysis,
            raw_extractions=[],
        )

    def test_text_formatter_basic(self, sample_report):
        """测试纯文本格式化。"""
        formatter = TextFormatter()
        result = formatter.format(sample_report)

        assert "日志分析报告" in result
        assert sample_report.analysis.overall_summary in result

    def test_text_formatter_simple_format(self, sample_report):
        """测试纯文本格式简单性。"""
        formatter = TextFormatter()
        result = formatter.format(sample_report)

        # 纯文本不应包含 Markdown 语法
        assert "# " not in result  # Markdown 标题
        assert "```" not in result  # Markdown 代码块
        assert "**" not in result  # Markdown 加粗


class TestGetFormatter:
    """get_formatter 函数测试。"""

    def test_get_markdown_formatter(self):
        """测试获取 Markdown 格式化器。"""
        formatter = get_formatter("markdown")
        assert isinstance(formatter, MarkdownFormatter)

    def test_get_json_formatter(self):
        """测试获取 JSON 格式化器。"""
        formatter = get_formatter("json")
        assert isinstance(formatter, JSONFormatter)

    def test_get_text_formatter(self):
        """测试获取纯文本格式化器。"""
        formatter = get_formatter("text")
        assert isinstance(formatter, TextFormatter)

    def test_get_invalid_formatter(self):
        """测试获取无效格式化器。"""
        with pytest.raises(ValueError):
            get_formatter("invalid_format")
