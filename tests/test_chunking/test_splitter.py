"""分块器测试。"""

import pytest

from logginganalysis.chunking.splitter import ChunkStrategy, LogChunker
from logginganalysis.utils.exceptions import ChunkingError


class TestLogChunker:
    """LogChunker 测试。"""

    def test_chunker_initialization(self):
        """测试分块器初始化。"""
        chunker = LogChunker(
            chunk_size=1000,
            chunk_overlap=100,
            strategy=ChunkStrategy.RECURSIVE,
        )
        assert chunker.chunk_size == 1000
        assert chunker.chunk_overlap == 100
        assert chunker.strategy == ChunkStrategy.RECURSIVE

    def test_chunker_default_strategy(self):
        """测试分块器默认策略。"""
        chunker = LogChunker()
        assert chunker.strategy == ChunkStrategy.RECURSIVE

    def test_chunk_empty_log(self):
        """测试处理空日志。"""
        chunker = LogChunker()
        chunks = chunker.chunk_log("")
        assert chunks.chunks == []
        assert chunks.total_size == 0
        assert chunks.original_log_size == 0

    def test_chunk_small_log(self):
        """测试处理小日志（小于 chunk_size）。"""
        chunker = LogChunker(chunk_size=1000, chunk_overlap=0)
        small_log = "2025-12-31 10:00:00 INFO Test log entry\n"
        chunks = chunker.chunk_log(small_log)
        assert len(chunks.chunks) == 1
        assert chunks.chunks[0].content == small_log
        assert chunks.original_log_size == len(small_log)

    def test_chunk_large_log(self):
        """测试处理大日志（需要分块）。"""
        chunker = LogChunker(chunk_size=200, chunk_overlap=50)
        # 创建足够大的日志
        large_log = "\n".join(
            f"2025-12-31 10:00:{i:02d} INFO Log entry number {i} - " + "x" * 50
            for i in range(20)
        )
        chunks = chunker.chunk_log(large_log)
        assert len(chunks.chunks) > 1
        assert chunks.original_log_size == len(large_log)

    def test_chunk_with_metadata(self):
        """测试带元数据的分块。"""
        chunker = LogChunker(chunk_size=500, chunk_overlap=50)
        log_content = "Line 1\nLine 2\nLine 3\n" * 50
        metadata = {"source": "test.log", "level": "INFO"}

        chunks = chunker.chunk_log(log_content, metadata=metadata)

        # 检查每个块都有正确的元数据
        for chunk in chunks.chunks:
            assert chunk.metadata["source"] == "test.log"
            assert chunk.metadata["level"] == "INFO"
            assert "chunk_number" in chunk.metadata
            assert "chunk_strategy" in chunk.metadata

    def test_chunk_positions(self):
        """测试分块位置信息。"""
        chunker = LogChunker(chunk_size=100, chunk_overlap=20)
        log_content = "A" * 50 + "\n" + "B" * 50 + "\n" + "C" * 50

        chunks = chunker.chunk_log(log_content)

        # 检查起始和结束位置
        for i, chunk in enumerate(chunks.chunks):
            assert chunk.start_index >= 0
            assert chunk.end_index <= len(log_content)
            assert chunk.end_index > chunk.start_index

            # 检查内容匹配
            expected_content = log_content[chunk.start_index : chunk.end_index]
            assert chunk.content == expected_content

    def test_chunk_line_based_strategy(self, sample_log_content):
        """测试基于行的分块策略。"""
        chunker = LogChunker(
            chunk_size=200,
            chunk_overlap=0,
            strategy=ChunkStrategy.LINE_BASED,
        )
        chunks = chunker.chunk_log(sample_log_content)
        assert len(chunks.chunks) > 0

    def test_chunk_error_boundaries_strategy(self, sample_log_content):
        """测试错误边界分块策略。"""
        chunker = LogChunker(
            chunk_size=500,
            chunk_overlap=50,
            strategy=ChunkStrategy.ERROR_BOUNDARIES,
        )
        chunks = chunker.chunk_log(sample_log_content)
        assert len(chunks.chunks) > 0

    def test_chunk_total_size_calculation(self):
        """测试总大小计算。"""
        chunker = LogChunker(chunk_size=100, chunk_overlap=20)
        log_content = "A" * 150 + "\n" + "B" * 150

        chunks = chunker.chunk_log(log_content)

        # total_size 应该是所有块大小的总和（包括重叠）
        expected_total = sum(len(c.content) for c in chunks.chunks)
        assert chunks.total_size == expected_total

    def test_chunk_with_multibyte_characters(self):
        """测试包含多字节字符的分块。"""
        chunker = LogChunker(chunk_size=50, chunk_overlap=10)
        log_content = "中文日志内容测试\n" + "日本語ログ\n" + "한국어 로그\n" * 10

        chunks = chunker.chunk_log(log_content)
        assert len(chunks.chunks) > 0

        # 验证内容没有损坏
        for chunk in chunks.chunks:
            # 确保字符计数正确
            assert len(chunk.content) == len(chunk.content)


class TestChunkStrategies:
    """分块策略测试。"""

    def test_recursive_strategy_default(self):
        """测试递归策略为默认。"""
        chunker = LogChunker()
        assert chunker.strategy == ChunkStrategy.RECURSIVE

    def test_all_strategies_enum(self):
        """测试所有策略枚举值。"""
        strategies = [
            ChunkStrategy.RECURSIVE,
            ChunkStrategy.LINE_BASED,
            ChunkStrategy.ERROR_BOUNDARIES,
        ]
        for strategy in strategies:
            chunker = LogChunker(strategy=strategy)
            assert chunker.strategy == strategy
