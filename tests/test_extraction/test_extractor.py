"""提取器测试。"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from logginganalysis.extraction.extractor import LogExtractor
from logginganalysis.models.chunk import LogChunk, LogChunks
from logginganalysis.models.extraction import ChunkExtractionResult
from logginganalysis.utils.exceptions import ExtractionError


class TestLogExtractor:
    """LogExtractor 测试。"""

    @pytest.fixture
    def mock_chain(self):
        """创建 mock chain。"""
        chain = Mock()
        chain.ainvoke = AsyncMock()
        return chain

    @pytest.fixture
    def sample_chunks(self):
        """创建示例日志块。"""
        return LogChunks(
            chunks=[
                LogChunk(
                    id="chunk-1",
                    content="2025-12-31 ERROR Database timeout",
                    start_index=0,
                    end_index=30,
                ),
                LogChunk(
                    id="chunk-2",
                    content="2025-12-31 INFO Application started",
                    start_index=30,
                    end_index=60,
                ),
            ],
            total_size=60,
            original_log_size=60,
        )

    @pytest.fixture
    def mock_extraction_result(self):
        """创建模拟提取结果。"""
        return ChunkExtractionResult(
            chunk_id="",
            exceptions=[],
            libraries=[],
            problematic_behaviors=[],
            summary="Test summary",
        )

    def test_extractor_initialization(self, mock_chain):
        """测试提取器初始化。"""
        extractor = LogExtractor(chain=mock_chain)
        assert extractor.chain == mock_chain

    def test_extractor_default_initialization(self):
        """测试提取器默认初始化。"""
        with patch("logginganalysis.extraction.extractor.create_extraction_chain"):
            extractor = LogExtractor()
            assert extractor is not None

    @pytest.mark.asyncio
    async def test_extract_from_chunk_success(
        self, mock_chain, mock_extraction_result
    ):
        """测试成功从单个块提取。"""
        chunk = LogChunk(
            id="test-chunk", content="Test log", start_index=0, end_index=8
        )

        mock_chain.ainvoke.return_value = mock_extraction_result

        extractor = LogExtractor(chain=mock_chain)
        result = await extractor.extract_from_chunk(chunk)

        assert result.chunk_id == "test-chunk"
        assert result.summary == "Test summary"
        mock_chain.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_from_chunk_failure(self, mock_chain):
        """测试从块提取失败。"""
        chunk = LogChunk(id="test-chunk", content="Test", start_index=0, end_index=4)

        mock_chain.ainvoke.side_effect = Exception("LLM error")

        extractor = LogExtractor(chain=mock_chain)

        with pytest.raises(ExtractionError):
            await extractor.extract_from_chunk(chunk)

    @pytest.mark.asyncio
    async def test_extract_from_chunks_empty(self, mock_chain):
        """测试从空块列表提取。"""
        chunks = LogChunks(chunks=[], total_size=0, original_log_size=0)

        extractor = LogExtractor(chain=mock_chain)
        results = await extractor.extract_from_chunks(chunks)

        assert results == []
        mock_chain.ainvoke.assert_not_called()

    @pytest.mark.asyncio
    async def test_extract_from_chunks_success(
        self, mock_chain, sample_chunks, mock_extraction_result
    ):
        """测试成功从多个块提取。"""
        # 设置 mock 返回值
        async def mock_invoke(inputs):
            result = mock_extraction_result.model_copy()
            result.chunk_id = inputs.get("log_chunk", "")[:10]  # 模拟返回 chunk_id
            return result

        mock_chain.ainvoke.side_effect = mock_invoke

        extractor = LogExtractor(chain=mock_chain)
        results = await extractor.extract_from_chunks(sample_chunks, max_concurrency=2)

        assert len(results) == 2
        assert mock_chain.ainvoke.call_count == 2

    @pytest.mark.asyncio
    async def test_extract_from_chunks_with_error(self, mock_chain, sample_chunks):
        """测试从多个块提取时部分失败。"""
        # 第一次调用成功，第二次失败
        mock_chain.ainvoke.side_effect = [
            ChunkExtractionResult(
                chunk_id="chunk-1",
                exceptions=[],
                libraries=[],
                problematic_behaviors=[],
                summary="OK",
            ),
            Exception("Network error"),
        ]

        extractor = LogExtractor(chain=mock_chain)

        with pytest.raises(ExtractionError):
            await extractor.extract_from_chunks(sample_chunks)

    @pytest.mark.asyncio
    async def test_extract_from_log_directly(self, mock_chain, mock_extraction_result):
        """测试直接从日志内容提取。"""
        mock_chain.ainvoke.return_value = mock_extraction_result

        with patch("logginganalysis.extraction.extractor.LogChunker") as MockChunker:
            mock_chunker = Mock()
            mock_chunks = LogChunks(
                chunks=[
                    LogChunk(
                        id="chunk-1", content="Test", start_index=0, end_index=4
                    )
                ],
                total_size=4,
                original_log_size=4,
            )
            mock_chunker.return_value.chunk_log.return_value = mock_chunks
            MockChunker.return_value = mock_chunker

            extractor = LogExtractor(chain=mock_chain)
            results = await extractor.extract_from_log("Test log content")

            assert isinstance(results, list)
            mock_chunker.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrency_limit(self, mock_chain, sample_chunks):
        """测试并发限制。"""
        mock_chain.ainvoke = AsyncMock(
            return_value=ChunkExtractionResult(
                chunk_id="test",
                exceptions=[],
                libraries=[],
                problematic_behaviors=[],
                summary="Test",
            )
        )

        extractor = LogExtractor(chain=mock_chain)
        # 设置 max_concurrency=1，应该串行执行
        results = await extractor.extract_from_chunks(sample_chunks, max_concurrency=1)

        assert len(results) == 2
