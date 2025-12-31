"""日志块模型测试。"""

import pytest
from pydantic import ValidationError

from logginganalysis.models.chunk import LogChunk, LogChunks


class TestLogChunk:
    """LogChunk 模型测试。"""

    def test_create_log_chunk(self):
        """测试创建日志块。"""
        chunk = LogChunk(
            content="2025-12-31 10:00:00 INFO Test log",
            start_index=0,
            end_index=25,
        )
        assert chunk.content == "2025-12-31 10:00:00 INFO Test log"
        assert chunk.start_index == 0
        assert chunk.end_index == 25
        assert chunk.id is not None  # 自动生成的 UUID
        assert chunk.metadata == {}

    def test_create_log_chunk_with_metadata(self):
        """测试创建带元数据的日志块。"""
        chunk = LogChunk(
            content="Test log",
            start_index=0,
            end_index=8,
            metadata={"chunk_number": 1, "source": "test.log"},
        )
        assert chunk.metadata == {"chunk_number": 1, "source": "test.log"}

    def test_log_chunk_validation_error(self):
        """测试日志块验证错误。"""
        with pytest.raises(ValidationError):
            LogChunk(
                content="Test",
                # 缺少 start_index
                end_index=4,
            )


class TestLogChunks:
    """LogChunks 模型测试。"""

    def test_create_empty_log_chunks(self):
        """测试创建空的日志块集合。"""
        chunks = LogChunks(chunks=[], total_size=0, original_log_size=0)
        assert chunks.chunks == []
        assert chunks.total_size == 0
        assert chunks.original_log_size == 0

    def test_create_log_chunks_with_data(self):
        """测试创建包含数据的日志块集合。"""
        chunk1 = LogChunk(content="First chunk", start_index=0, end_index=11)
        chunk2 = LogChunk(content="Second chunk", start_index=11, end_index=23)

        chunks = LogChunks(
            chunks=[chunk1, chunk2],
            total_size=23,
            original_log_size=23,
        )
        assert len(chunks.chunks) == 2
        assert chunks.total_size == 23
        assert chunks.original_log_size == 23
        assert chunks.chunks[0].content == "First chunk"
        assert chunks.chunks[1].content == "Second chunk"

    def test_log_chunks_default_empty_list(self):
        """测试日志块集合的默认空列表。"""
        chunks = LogChunks(chunks=[], total_size=0, original_log_size=100)
        assert chunks.chunks == []

    def test_log_chunks_with_overlap(self):
        """测试有重叠的日志块集合。"""
        chunk1 = LogChunk(content="AAAAABBBBB", start_index=0, end_index=10)
        chunk2 = LogChunk(content="BBBBBCCCCC", start_index=5, end_index=15)  # 5字符重叠

        chunks = LogChunks(
            chunks=[chunk1, chunk2],
            total_size=20,  # 包含重叠
            original_log_size=15,
        )
        assert chunks.total_size == 20
        assert chunks.original_log_size == 15
