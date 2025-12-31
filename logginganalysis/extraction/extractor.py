"""日志信息提取器。"""

import asyncio
from typing import Any

from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from logginganalysis.config.settings import get_settings
from logginganalysis.extraction.chains import create_extraction_chain
from logginganalysis.models.chunk import LogChunk, LogChunks
from logginganalysis.models.extraction import ChunkExtractionResult
from logginganalysis.utils.exceptions import ExtractionError
from logginganalysis.utils.rate_limiter import RateLimiter, RateLimitConfig


class LogExtractor:
    """日志信息提取器。

    使用 AI 模型从日志块中提取关键信息。
    """

    def __init__(
        self,
        chain: Runnable | None = None,
        llm: ChatOpenAI | None = None,
        use_structured_output: bool = False,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        """初始化日志提取器。

        Args:
            chain: 自定义提取链。如果为 None，将创建默认链
            llm: 使用的语言模型。如果为 None，使用配置中的提取模型
            use_structured_output: 是否使用 OpenAI 的原生结构化输出
            rate_limiter: 流控器。如果为 None，根据配置创建
        """
        settings = get_settings()

        if chain is None:
            if use_structured_output:
                from logginganalysis.extraction.chains import (
                    create_structured_extraction_chain,
                )

                self.chain = create_structured_extraction_chain(llm)
            else:
                self.chain = create_extraction_chain(llm)
        else:
            self.chain = chain

        self.llm = llm or ChatOpenAI(
            model=settings.extraction_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0,
        )

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

    async def extract_from_chunk(
        self,
        chunk: LogChunk,
    ) -> ChunkExtractionResult:
        """从单个日志块中提取信息。

        Args:
            chunk: 日志块

        Returns:
            ChunkExtractionResult: 提取结果

        Raises:
            ExtractionError: 提取失败时抛出
        """
        # 等待流控许可
        if self.rate_limiter:
            await self.rate_limiter.wait_for_permission(tokens=1)

        try:
            result: ChunkExtractionResult = await self.chain.ainvoke(
                {"log_chunk": chunk.content}
            )

            # 确保结果包含正确的 chunk_id
            result.chunk_id = chunk.id

            return result

        except Exception as e:
            raise ExtractionError(
                f"从块 {chunk.id} 提取信息失败: {e}",
                details={"chunk_id": chunk.id, "chunk_size": len(chunk.content)},
            ) from e

    async def extract_from_chunks(
        self,
        chunks: LogChunks,
        max_concurrency: int = 5,
    ) -> list[ChunkExtractionResult]:
        """从多个日志块中提取信息。

        Args:
            chunks: 日志块集合
            max_concurrency: 最大并发数

        Returns:
            list[ChunkExtractionResult]: 提取结果列表

        Raises:
            ExtractionError: 提取失败时抛出
        """
        if not chunks.chunks:
            return []

        try:
            # 使用信号量限制并发数
            semaphore = asyncio.Semaphore(max_concurrency)

            async def extract_with_semaphore(chunk: LogChunk) -> ChunkExtractionResult:
                async with semaphore:
                    return await self.extract_from_chunk(chunk)

            # 并发提取所有块
            results = await asyncio.gather(
                *[extract_with_semaphore(chunk) for chunk in chunks.chunks],
                return_exceptions=True,
            )

            # 检查是否有异常
            extractions: list[ChunkExtractionResult] = []
            errors: list[tuple[str, Exception]] = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    errors.append((chunks.chunks[i].id, result))
                elif isinstance(result, ChunkExtractionResult):
                    extractions.append(result)

            if errors:
                error_msg = f"提取过程中发生 {len(errors)} 个错误"
                raise ExtractionError(
                    error_msg,
                    details={"errors": [(cid, str(e)) for cid, e in errors]},
                )

            return extractions

        except ExtractionError:
            raise
        except Exception as e:
            raise ExtractionError(f"批量提取失败: {e}") from e

    async def extract_from_log(
        self,
        log_content: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[ChunkExtractionResult]:
        """直接从日志内容中提取信息。

        此方法会先对日志进行分块，然后提取信息。

        Args:
            log_content: 日志内容
            metadata: 可选的元数据

        Returns:
            list[ChunkExtractionResult]: 提取结果列表
        """
        from logginganalysis.chunking import LogChunker

        # 首先对日志进行分块
        chunker = LogChunker(
            chunk_size=get_settings().chunk_size,
            chunk_overlap=get_settings().chunk_overlap,
        )
        chunks = chunker.chunk_log(log_content, metadata)

        # 然后提取信息
        return await self.extract_from_chunks(chunks)
