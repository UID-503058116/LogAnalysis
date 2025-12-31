"""日志分析器主类。

整合所有模块，提供统一的日志分析接口。
"""

import logging
import time
from typing import Any

from logginganalysis.chunking import LogChunker
from logginganalysis.config.settings import get_settings
from logginganalysis.extraction import LogExtractor
from logginganalysis.integration import LogIntegrator, WebSearchTool
from logginganalysis.models.report import AnalysisReport
from logginganalysis.reporting import ReportGenerator, get_formatter

logger = logging.getLogger(__name__)


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
        progress_callback: Any | None = None,
    ) -> None:
        """初始化日志分析器。

        Args:
            chunker: 自定义分块器
            extractor: 自定义提取器
            integrator: 自定义集成器
            report_generator: 自定义报告生成器
            progress_callback: 进度回调函数
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
        self.progress_callback = progress_callback

    def _update_progress(
        self,
        step: str,
        message: str,
        current: int | None = None,
        total: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """更新进度。

        Args:
            step: 当前步骤
            message: 进度消息
            current: 当前进度
            total: 总数
            extra: 额外信息
        """
        progress_info: dict[str, Any] = {
            "step": step,
            "progress_message": message,
        }
        if current is not None and total is not None:
            progress_info["progress"] = f"{current}/{total} ({current / total * 100:.1f}%)"
        if extra:
            progress_info.update(extra)

        logger.info(f"[{step}] {message}", extra=progress_info)

        if self.progress_callback:
            callback_info: dict[str, Any] = {"step": step, "message": message}
            if current is not None and total is not None:
                callback_info["progress"] = f"{current}/{total} ({current / total * 100:.1f}%)"
            if extra:
                callback_info.update(extra)
            self.progress_callback(callback_info)

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
        log_size = len(log_content.encode("utf-8"))

        self._update_progress(
            "start",
            f"开始分析日志，来源: {log_source or '内存'}，大小: {log_size} 字节",
            extra={"log_size": log_size, "enable_search": enable_search},
        )

        # 1. 分块
        self._update_progress("chunking", "开始分块日志")
        chunks = self.chunker.chunk_log(log_content, metadata={"source": log_source})
        self._update_progress("chunking", f"日志分块完成，生成 {len(chunks.chunks)} 个chunk")

        # 2. 提取
        self._update_progress(
            "extraction",
            "开始提取日志信息",
            current=0,
            total=len(chunks.chunks),
        )
        extractions = await self.extractor.extract_from_chunks(chunks)

        # 3. 集成
        self._update_progress("integration", "开始集成分析")
        if enable_search:
            analysis, search_results = await self.integrator.integrate_with_search(extractions)
        else:
            analysis = await self.integrator.integrate(extractions)
            search_results = None

        # 4. 生成报告
        self._update_progress("reporting", "生成分析报告")
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

        self._update_progress(
            "complete",
            f"分析完成，总耗时: {time.time() - start_time:.2f} 秒，"
            f"发现 {sum(len(e.exceptions) for e in extractions)} 个异常",
            extra={
                "total_duration": time.time() - start_time,
                "exception_count": sum(len(e.exceptions) for e in extractions),
            },
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
        logger.info(f"准备读取日志文件: {file_path}")

        # 读取文件
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                log_content = f.read()
        except UnicodeDecodeError:
            logger.info("UTF-8解码失败，尝试使用latin-1编码")
            # 尝试其他编码
            with open(file_path, "r", encoding="latin-1") as f:
                log_content = f.read()
        except FileNotFoundError:
            logger.error(f"文件不存在: {file_path}")
            raise
        except Exception as e:
            logger.error(f"读取文件失败: {e}", exc_info=True)
            raise

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
