"""报告生成器。"""

import time
from typing import Any

from logginganalysis.config.settings import get_settings
from logginganalysis.models.extraction import ChunkExtractionResult
from logginganalysis.models.integration import IntegratedAnalysis
from logginganalysis.models.report import AnalysisReport, ReportMetadata
from logginganalysis.reporting.formatters import ReportFormatter, get_formatter
from logginganalysis.utils.exceptions import ReportGenerationError


class ReportGenerator:
    """报告生成器。

    将集成分析结果转换为可读的报告。
    """

    def __init__(
        self,
        formatter: ReportFormatter | None = None,
        default_format: str = "markdown",
    ) -> None:
        """初始化报告生成器。

        Args:
            formatter: 自定义格式化器。如果为 None，使用默认格式化器
            default_format: 默认输出格式
        """
        self.formatter = formatter or get_formatter(default_format)
        self.default_format = default_format

    def generate(
        self,
        analysis: IntegratedAnalysis,
        extractions: list[ChunkExtractionResult],
        metadata: ReportMetadata | None = None,
        search_results: list[dict[str, Any]] | None = None,
    ) -> AnalysisReport:
        """生成分析报告。

        Args:
            analysis: 集成分析结果
            extractions: 原始提取结果
            metadata: 报告元数据
            search_results: 网页搜索结果（可选）

        Returns:
            AnalysisReport: 完整的分析报告
        """
        if metadata is None:
            # 创建默认元数据
            settings = get_settings()
            metadata = ReportMetadata(
                log_source=None,
                log_size_bytes=0,
                chunk_count=len(extractions),
                models_used={
                    "extraction": settings.extraction_model,
                    "integration": settings.integration_model,
                },
                processing_time_seconds=0.0,
            )

        return AnalysisReport(
            metadata=metadata,
            analysis=analysis,
            raw_extractions=extractions,
            search_results=search_results,
        )

    def format_report(self, report: AnalysisReport, format_type: str | None = None) -> str:
        """格式化报告为字符串。

        Args:
            report: 分析报告
            format_type: 输出格式。如果为 None，使用默认格式

        Returns:
            str: 格式化后的报告字符串

        Raises:
            ReportGenerationError: 格式化失败时抛出
        """
        try:
            if format_type and format_type != self.default_format:
                formatter = get_formatter(format_type)
                return formatter.format(report)

            return self.formatter.format(report)

        except Exception as e:
            raise ReportGenerationError(f"报告格式化失败: {e}") from e

    def generate_and_format(
        self,
        analysis: IntegratedAnalysis,
        extractions: list[ChunkExtractionResult],
        log_source: str | None = None,
        log_size_bytes: int = 0,
        processing_start_time: float | None = None,
        format_type: str | None = None,
        search_results: list[dict[str, Any]] | None = None,
    ) -> str:
        """生成并格式化报告。

        这是一个便捷方法，合并了 generate 和 format_report。

        Args:
            analysis: 集成分析结果
            extractions: 原始提取结果
            log_source: 日志来源
            log_size_bytes: 日志大小
            processing_start_time: 处理开始时间（用于计算处理时间）
            format_type: 输出格式
            search_results: 网页搜索结果

        Returns:
            str: 格式化后的报告字符串
        """
        # 计算处理时间
        processing_time = 0.0
        if processing_start_time is not None:
            processing_time = time.time() - processing_start_time

        # 创建元数据
        settings = get_settings()
        metadata = ReportMetadata(
            log_source=log_source,
            log_size_bytes=log_size_bytes,
            chunk_count=len(extractions),
            models_used={
                "extraction": settings.extraction_model,
                "integration": settings.integration_model,
            },
            processing_time_seconds=processing_time,
        )

        # 生成报告
        report = self.generate(
            analysis=analysis,
            extractions=extractions,
            metadata=metadata,
            search_results=search_results,
        )

        # 格式化报告
        return self.format_report(report, format_type)


def generate_markdown_report(
    analysis: IntegratedAnalysis,
    extractions: list[ChunkExtractionResult],
    **kwargs: Any,
) -> str:
    """生成 Markdown 格式的报告。

    便捷函数。

    Args:
        analysis: 集成分析结果
        extractions: 原始提取结果
        **kwargs: 其他参数传递给 ReportGenerator

    Returns:
        str: Markdown 格式的报告
    """
    generator = ReportGenerator(default_format="markdown")
    return generator.generate_and_format(
        analysis=analysis,
        extractions=extractions,
        format_type="markdown",
        **kwargs,
    )


def generate_json_report(
    analysis: IntegratedAnalysis,
    extractions: list[ChunkExtractionResult],
    **kwargs: Any,
) -> str:
    """生成 JSON 格式的报告。

    便捷函数。

    Args:
        analysis: 集成分析结果
        extractions: 原始提取结果
        **kwargs: 其他参数传递给 ReportGenerator

    Returns:
        str: JSON 格式的报告
    """
    generator = ReportGenerator(default_format="json")
    return generator.generate_and_format(
        analysis=analysis,
        extractions=extractions,
        format_type="json",
        **kwargs,
    )
