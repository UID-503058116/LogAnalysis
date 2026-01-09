"""测试编号顺序和进度计算的修复。"""

import pytest
from unittest.mock import AsyncMock, Mock

from logginganalysis.extraction.extractor import LogExtractor
from logginganalysis.models.chunk import LogChunk, LogChunks
from logginganalysis.models.extraction import ChunkExtractionResult


@pytest.mark.asyncio
async def test_extract_from_chunks_preserves_order():
    """测试 extract_from_chunks 方法保持结果的原始顺序。"""
    chunks = LogChunks(
        chunks=[
            LogChunk(
                id="chunk-1",
                content="First chunk",
                start_index=0,
                end_index=10,
            ),
            LogChunk(
                id="chunk-2",
                content="Second chunk",
                start_index=10,
                end_index=20,
            ),
            LogChunk(
                id="chunk-3",
                content="Third chunk",
                start_index=20,
                end_index=30,
            ),
        ],
        total_size=30,
        original_log_size=30,
    )

    mock_chain = Mock()
    mock_chain.ainvoke = AsyncMock()

    async def mock_invoke(inputs):
        result = ChunkExtractionResult(
            chunk_id="",
            exceptions=[],
            libraries=[],
            problematic_behaviors=[],
            summary=f"Summary for {inputs.get('log_chunk', '')}",
        )
        return result

    mock_chain.ainvoke.side_effect = mock_invoke

    extractor = LogExtractor(chain=mock_chain)
    results = await extractor.extract_from_chunks(chunks, max_concurrency=3)

    assert len(results) == 3
    assert results[0].chunk_id == "chunk-1"
    assert results[1].chunk_id == "chunk-2"
    assert results[2].chunk_id == "chunk-3"


@pytest.mark.asyncio
async def test_progress_callback_with_correct_percentage():
    """测试进度回调函数接收正确的完成进度。"""
    chunks = LogChunks(
        chunks=[
            LogChunk(
                id="chunk-1",
                content="First chunk",
                start_index=0,
                end_index=10,
            ),
            LogChunk(
                id="chunk-2",
                content="Second chunk",
                start_index=10,
                end_index=20,
            ),
        ],
        total_size=20,
        original_log_size=20,
    )

    mock_chain = Mock()
    mock_chain.ainvoke = AsyncMock()

    async def mock_invoke(inputs):
        result = ChunkExtractionResult(
            chunk_id="",
            exceptions=[],
            libraries=[],
            problematic_behaviors=[],
            summary="Summary",
        )
        return result

    mock_chain.ainvoke.side_effect = mock_invoke

    progress_updates = []

    def progress_callback(update):
        progress_updates.append(update)

    extractor = LogExtractor(chain=mock_chain, progress_callback=progress_callback)
    await extractor.extract_from_chunks(chunks, max_concurrency=2)

    completed_updates = [u for u in progress_updates if u["status"] == "completed"]
    assert len(completed_updates) == 2

    # 验证完成时的进度计算正确：使用 (index + 1) / total * 100
    first_progress = completed_updates[0]["progress_percentage"]
    second_progress = completed_updates[1]["progress_percentage"]

    assert first_progress == 50.0  # (1 / 2) * 100
    assert second_progress == 100.0  # (2 / 2) * 100
