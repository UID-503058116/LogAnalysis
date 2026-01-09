"""日志信息提取器。"""

import asyncio
import logging
from typing import Any

from pydantic import SecretStr

from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from logginganalysis.config.settings import get_settings
from logginganalysis.extraction.chains import create_extraction_chain
from logginganalysis.models.chunk import LogChunk, LogChunks
from logginganalysis.models.extraction import ChunkExtractionResult
from logginganalysis.utils.exceptions import ExtractionError
from logginganalysis.utils.rate_limiter import RateLimiter, RateLimitConfig

logger = logging.getLogger(__name__)


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
        progress_callback: Any | None = None,
    ) -> None:
        """初始化日志提取器。

        Args:
            chain: 自定义提取链。如果为 None，将创建默认链
            llm: 使用的语言模型。如果为 None，使用配置中的提取模型
            use_structured_output: 是否使用 OpenAI 的原生结构化输出
            rate_limiter: 流控器。如果为 None，根据配置创建
            progress_callback: 进度回调函数
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
            api_key=SecretStr(settings.openai_api_key),
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
        self.progress_callback = progress_callback

    async def extract_from_chunk(
        self,
        chunk: LogChunk,
        chunk_index: int = 0,
        total_chunks: int = 1,
    ) -> ChunkExtractionResult:
        """从单个日志块中提取信息。

        Args:
            chunk: 日志块
            chunk_index: chunk索引
            total_chunks: 总chunk数

        Returns:
            ChunkExtractionResult: 提取结果

        Raises:
            ExtractionError: 提取失败时抛出
        """
        logger.info(
            f"[{chunk_index + 1}/{total_chunks}] "
            f"开始提取chunk {chunk.id} (大小: {len(chunk.content)} 字符)"
        )

        if self.progress_callback:
            progress_percentage = (chunk_index / total_chunks * 100) if total_chunks > 0 else 0
            self.progress_callback(
                {
                    "step": "extraction",
                    "chunk_id": chunk.id,
                    "chunk_index": chunk_index + 1,
                    "total_chunks": total_chunks,
                    "progress_percentage": progress_percentage,
                    "status": "processing",
                }
            )

        # 等待流控许可
        if self.rate_limiter:
            await self.rate_limiter.wait_for_permission(tokens=1)

        try:
            from logginganalysis.models.extraction import ChunkExtractionResult

            chain_result = await self.chain.ainvoke({"log_chunk": chunk.content})

            # 检查是否返回了 None
            if chain_result is None:
                logger.warning(f"[{chunk_index + 1}/{total_chunks}] AI 返回了 None，使用空结果")
                result = ChunkExtractionResult(
                    chunk_id=chunk.id,
                    exceptions=[],
                    libraries=[],
                    problematic_behaviors=[],
                    summary="AI 返回空结果，无法提取信息",
                )
            else:
                result = chain_result

            # 确保结果包含正确的 chunk_id
            result.chunk_id = chunk.id

            logger.info(
                f"[{chunk_index + 1}/{total_chunks}] 成功提取chunk {chunk.id}，"
                f"发现 {len(result.exceptions)} 个异常，"
                f"{len(result.problematic_behaviors)} 个问题行为，{len(result.libraries)} 个库引用"
            )

            if self.progress_callback:
                progress_percentage = (
                    ((chunk_index + 1) / total_chunks * 100) if total_chunks > 0 else 0
                )
                self.progress_callback(
                    {
                        "step": "extraction",
                        "chunk_id": chunk.id,
                        "chunk_index": chunk_index + 1,
                        "total_chunks": total_chunks,
                        "progress_percentage": progress_percentage,
                        "status": "completed",
                        "exceptions_found": len(result.exceptions),
                        "behaviors_found": len(result.problematic_behaviors),
                        "libraries_found": len(result.libraries),
                    }
                )

            return result

        except Exception as e:
            logger.error(
                f"[{chunk_index + 1}/{total_chunks}] 从chunk {chunk.id} 提取失败: {e}",
                extra={"chunk_id": chunk.id, "chunk_size": len(chunk.content)},
            )

            if self.progress_callback:
                progress_percentage = (
                    ((chunk_index + 1) / total_chunks * 100) if total_chunks > 0 else 0
                )
                self.progress_callback(
                    {
                        "step": "extraction",
                        "chunk_id": chunk.id,
                        "chunk_index": chunk_index + 1,
                        "total_chunks": total_chunks,
                        "progress_percentage": progress_percentage,
                        "status": "failed",
                        "error": str(e),
                    }
                )

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
            list[ChunkExtractionResult]: 提取结果列表（按原始chunk顺序）

        Raises:
            ExtractionError: 提取失败时抛出
        """
        if not chunks.chunks:
            logger.info("没有需要提取的chunk")
            return []

        logger.info(f"开始批量提取 {len(chunks.chunks)} 个chunk，最大并发数: {max_concurrency}")

        try:
            # 使用信号量限制并发数
            semaphore = asyncio.Semaphore(max_concurrency)

            async def extract_with_semaphore(
                chunk: LogChunk, index: int
            ) -> tuple[int, ChunkExtractionResult | Exception]:
                async with semaphore:
                    try:
                        result = await self.extract_from_chunk(chunk, index, len(chunks.chunks))
                        return (index, result)
                    except Exception as e:
                        return (index, e)

            # 并发提取所有块
            indexed_results = await asyncio.gather(
                *[extract_with_semaphore(chunk, i) for i, chunk in enumerate(chunks.chunks)],
            )

            # 按索引排序，确保结果顺序与原始chunk顺序一致
            indexed_results.sort(key=lambda x: x[0])

            # 检查是否有异常
            extractions: list[ChunkExtractionResult] = []
            errors: list[tuple[int, str, Exception]] = []

            for index, result in indexed_results:
                if isinstance(result, Exception):
                    errors.append((index, chunks.chunks[index].id, result))
                elif isinstance(result, ChunkExtractionResult):
                    extractions.append(result)

            if errors:
                error_msg = f"提取过程中发生 {len(errors)} 个错误"
                logger.error(
                    f"{error_msg}: {[cid for _, cid, _ in errors]}",
                    extra={
                        "error_count": len(errors),
                        "errors": [(index, cid, str(e)) for index, cid, e in errors],
                    },
                )
                raise ExtractionError(
                    error_msg,
                    details={"errors": [(index, cid, str(e)) for index, cid, e in errors]},
                )

            logger.info(f"批量提取完成，成功: {len(extractions)}/{len(chunks.chunks)} 个chunk")

            return extractions

        except ExtractionError:
            raise
        except Exception as e:
            logger.error(f"批量提取失败: {e}", exc_info=True)
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
