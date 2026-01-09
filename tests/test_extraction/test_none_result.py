"""测试 AI 返回 None 的处理。"""

import pytest
from unittest.mock import AsyncMock, Mock

from logginganalysis.extraction.extractor import LogExtractor
from logginganalysis.models.chunk import LogChunk, LogChunks
from logginganalysis.models.extraction import ChunkExtractionResult


@pytest.mark.asyncio
async def test_extract_from_chunk_handles_none_result():
    """测试 extract_from_chunk 处理 AI 返回 None 的情况。"""
    chunk = LogChunk(
        id="test-chunk",
        content="Test log content",
        start_index=0,
        end_index=20,
    )

    mock_chain = Mock()
    mock_chain.ainvoke = AsyncMock(return_value=None)

    extractor = LogExtractor(chain=mock_chain)
    result = await extractor.extract_from_chunk(chunk, chunk_index=0, total_chunks=1)

    assert result.chunk_id == "test-chunk"
    assert len(result.exceptions) == 0
    assert len(result.libraries) == 0
    assert len(result.problematic_behaviors) == 0
    assert "AI 返回空结果" in result.summary


@pytest.mark.asyncio
async def test_extract_from_chunks_handles_one_none_result():
    """测试 extract_from_chunks 处理单个 chunk 返回 None 的情况。"""
    chunks = LogChunks(
        chunks=[
            LogChunk(id="chunk-1", content="First chunk", start_index=0, end_index=10),
            LogChunk(id="chunk-2", content="Second chunk", start_index=10, end_index=20),
            LogChunk(id="chunk-3", content="Third chunk", start_index=20, end_index=30),
        ],
        total_size=30,
        original_log_size=30,
    )

    mock_chain = Mock()
    mock_chain.ainvoke = AsyncMock(
        side_effect=[
            ChunkExtractionResult(
                chunk_id="",
                exceptions=[],
                libraries=[],
                problematic_behaviors=[],
                summary="First",
            ),
            None,  # 第二个 chunk 返回 None
            ChunkExtractionResult(
                chunk_id="",
                exceptions=[],
                libraries=[],
                problematic_behaviors=[],
                summary="Third",
            ),
        ]
    )

    extractor = LogExtractor(chain=mock_chain)
    results = await extractor.extract_from_chunks(chunks)

    assert len(results) == 3
    assert results[0].chunk_id == "chunk-1"
    assert results[1].chunk_id == "chunk-2"
    assert results[2].chunk_id == "chunk-3"
    assert results[1].summary == "AI 返回空结果，无法提取信息"
