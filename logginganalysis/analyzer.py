"""日志分析器主类。

整合所有模块，提供统一的日志分析接口。
"""

import time
from typing import Any

from logginganalysis.chunking import LogChunker
from logginganalysis.config.settings import get_settings
from logginganalysis.extraction import LogExtractor
from logginganalysis.integration import LogIntegrator, WebSearchTool
from logginganalysis.models.report import AnalysisReport
from logginganalysis.reporting import ReportGenerator, get_formatter


class LogAnalyzer:
    """日志分析器。

    整合分块、提取、集成和报告生成功能。
    """

    def __init__(
        self,
        chunker: LogChunker | None = None,
        extractor: LogExtractor | None = None,
        integrator: LogIntegrator | None = None,
        report_generator: ReportGenerator | None = None,
    ) -> None:
        """初始化日志分析器。

        Args:
            chunker: 自定义分块器
            extractor: 自定义提取器
            integrator: 自定义集成器
            report_generator: 自定义报告生成器
        """
        settings = get_settings()

        # 初始化各个组件
        self.chunker = chunker or LogChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        self.extractor = extractor or LogExtractor()
        self.integrator = integrator or LogIntegrator()
        self.report_generator = report_generator or ReportGenerator()

    async def analyze(
        self,
        log_content: str,
        log_source: str | None = None,
        enable_search: bool = False,
        output_format: str = "markdown",
    ) -> AnalysisReport:
        """分析日志内容。

        Args:
            log_content: 日志内容
            log_source: 日志来源（可选）
            enable_search: 是否启用网页搜索
            output_format: 输出格式（markdown/json/text）

        Returns:
            AnalysisReport: 分析报告
        """
        start_time = time.time()

        # 1. 分块
        chunks = self.chunker.chunk_log(log_content, metadata={"source": log_source})

        # 2. 提取
        extractions = await self.extractor.extract_from_chunks(chunks)

        # 3. 集成
        if enable_search:
            analysis, search_results = await self.integrator.integrate_with_search(
                extractions
            )
        else:
            analysis = await self.integrator.integrate(extractions)
            search_results = None

        # 4. 生成报告
        report = self.report_generator.generate(
            analysis=analysis,
            extractions=extractions,
            metadata={
                "log_source": log_source,
                "log_size_bytes": len(log_content.encode("utf-8")),
                "chunk_count": len(chunks.chunks),
                "models_used": {
                    "extraction": get_settings().extraction_model,
                    "integration": get_settings().integration_model,
                },
                "processing_time_seconds": time.time() - start_time,
            },
            search_results=search_results,
        )

        return report

    async def analyze_file(
        self,
        file_path: str,
        enable_search: bool = False,
        output_format: str = "markdown",
    ) -> AnalysisReport:
        """分析日志文件。

        Args:
            file_path: 日志文件路径
            enable_search: 是否启用网页搜索
            output_format: 输出格式

        Returns:
            AnalysisReport: 分析报告
        """
        # 读取文件
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                log_content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, "r", encoding="latin-1") as f:
                log_content = f.read()

        return await self.analyze(
            log_content=log_content,
            log_source=file_path,
            enable_search=enable_search,
            output_format=output_format,
        )

    def format_report(self, report: AnalysisReport, format_type: str = "markdown") -> str:
        """格式化报告为字符串。

        Args:
            report: 分析报告
            format_type: 输出格式

        Returns:
            str: 格式化后的报告
        """
        return self.report_generator.format_report(report, format_type)

    async def analyze_to_string(
        self,
        log_content: str,
        log_source: str | None = None,
        enable_search: bool = False,
        output_format: str = "markdown",
    ) -> str:
        """分析日志并直接返回格式化的报告字符串。

        便捷方法。

        Args:
            log_content: 日志内容
            log_source: 日志来源
            enable_search: 是否启用网页搜索
            output_format: 输出格式

        Returns:
            str: 格式化后的报告字符串
        """
        report = await self.analyze(
            log_content=log_content,
            log_source=log_source,
            enable_search=enable_search,
            output_format=output_format,
        )

        return self.format_report(report, output_format)

    async def analyze_file_to_string(
        self,
        file_path: str,
        enable_search: bool = False,
        output_format: str = "markdown",
    ) -> str:
        """分析日志文件并直接返回格式化的报告字符串。

        便捷方法。

        Args:
            file_path: 日志文件路径
            enable_search: 是否启用网页搜索
            output_format: 输出格式

        Returns:
            str: 格式化后的报告字符串
        """
        report = await self.analyze_file(
            file_path=file_path,
            enable_search=enable_search,
            output_format=output_format,
        )

        return self.format_report(report, output_format)
