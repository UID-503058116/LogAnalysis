"""日志信息集成器。"""

import logging
from typing import Any

from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from logginganalysis.config.settings import get_settings
from logginganalysis.integration.chains import (
    create_integration_chain,
    create_structured_integration_chain,
)
from logginganalysis.integration.search_tool import WebSearchTool
from logginganalysis.models.extraction import ChunkExtractionResult
from logginganalysis.models.integration import IntegratedAnalysis
from logginganalysis.utils.exceptions import IntegrationError
from logginganalysis.utils.rate_limiter import RateLimiter, RateLimitConfig

logger = logging.getLogger(__name__)


class LogIntegrator:
    """日志信息集成器。

    使用 AI 模型整合所有提取结果，生成综合分析。
    """

    def __init__(
        self,
        chain: Runnable | None = None,
        llm: ChatOpenAI | None = None,
        use_structured_output: bool = False,
        search_tool: WebSearchTool | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        """初始化日志集成器。

        Args:
            chain: 自定义集成链。如果为 None，将创建默认链
            llm: 使用的语言模型。如果为 None，使用配置中的集成模型
            use_structured_output: 是否使用 OpenAI 的原生结构化输出
            search_tool: 网页搜索工具。如果为 None，根据配置创建
            rate_limiter: 流控器。如果为 None，根据配置创建
        """
        settings = get_settings()

        if chain is None:
            if use_structured_output:
                self.chain = create_structured_integration_chain(llm)
            else:
                self.chain = create_integration_chain(llm)
        else:
            self.chain = chain

        self.search_tool = search_tool or WebSearchTool()

        # 初始化流控器
        if rate_limiter is None and settings.enable_rate_limit:
            rate_limiter = RateLimiter(
                RateLimitConfig(
                    tpm_limit=settings.tpm_limit,
                    rpm_limit=settings.rpm_limit,
                    burst_size=settings.rate_limit_burst,
                    enabled=settings.enable_rate_limit,
                )
            )
        self.rate_limiter = rate_limiter

    async def integrate(
        self,
        extractions: list[ChunkExtractionResult],
        enable_search: bool = False,
    ) -> IntegratedAnalysis:
        """整合提取结果，生成综合分析。

        Args:
            extractions: 提取结果列表
            enable_search: 是否启用网页搜索获取额外上下文

        Returns:
            IntegratedAnalysis: 综合分析结果

        Raises:
            IntegrationError: 集成失败时抛出
        """
        if not extractions:
            logger.warning("没有可分析的日志提取结果")
            return IntegratedAnalysis(
                overall_summary="没有可分析的日志提取结果",
                key_findings=[],
                root_cause_analysis=None,
                system_context={},
                confidence_score=0.0,
            )

        logger.info(
            f"开始集成分析 {len(extractions)} 个提取结果，"
            f"发现 {sum(len(e.exceptions) for e in extractions)} 个异常"
        )

        # 等待流控许可（集成调用通常消耗更多资源）
        if self.rate_limiter:
            await self.rate_limiter.wait_for_permission(tokens=2)

        try:
            # 可选：执行网页搜索获取额外上下文
            search_results: list[dict[str, Any]] = []
            if enable_search and self.search_tool.is_enabled():
                logger.info("启用网页搜索获取额外上下文")
                search_results = await self._perform_context_search(extractions)

            # 执行集成分析
            analysis: IntegratedAnalysis = await self.chain.ainvoke({"extractions": extractions})

            logger.info(
                f"集成分析完成，生成了 {len(analysis.key_findings)} 个关键发现，"
                f"置信度: {analysis.confidence_score:.2f}"
            )

            return analysis

        except Exception as e:
            logger.error(f"集成分析失败: {e}", exc_info=True)
            raise IntegrationError(f"集成分析失败: {e}") from e

    async def _perform_context_search(
        self,
        extractions: list[ChunkExtractionResult],
    ) -> list[dict[str, Any]]:
        """为提取结果执行上下文搜索。

        Args:
            extractions: 提取结果列表

        Returns:
            list[dict]: 搜索结果列表
        """
        import asyncio

        # 收集需要搜索的错误类型
        error_types = set()
        for extraction in extractions:
            for exc in extraction.exceptions:
                error_types.add(exc.type)

        # 并发搜索每个错误的解决方案
        search_tasks = []
        for error_type in list(error_types)[:3]:  # 限制搜索数量
            task = self.search_tool.search_error_solutions(error_type)
            search_tasks.append(task)

        results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # 合并结果
        all_results: list[dict[str, Any]] = []
        for result in results:
            if isinstance(result, list):
                all_results.extend(result)

        return all_results[:10]  # 限制总结果数

    async def integrate_with_search(
        self,
        extractions: list[ChunkExtractionResult],
    ) -> tuple[IntegratedAnalysis, list[dict[str, Any]]]:
        """整合提取结果，包含网页搜索结果。

        Args:
            extractions: 提取结果列表

        Returns:
            tuple: (综合分析结果, 搜索结果列表)
        """
        search_results = await self._perform_context_search(extractions)

        analysis = await self.integrate(extractions, enable_search=False)

        return analysis, search_results
