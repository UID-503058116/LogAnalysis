"""测试日志和进度记录功能。"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from logginganalysis.chunking import LogChunker
from logginganalysis.extraction import LogExtractor
from logginganalysis.models.extraction import ChunkExtractionResult
from logginganalysis.models.integration import AnalysisInsight
from tests.fixtures.mock_responses import MOCK_EXTRACTION_RESPONSE


@pytest.mark.asyncio
async def test_extract_from_chunk_with_logging(caplog):
    """测试chunk提取时记录日志。"""
    caplog.set_level(logging.INFO)

    chunker = LogChunker(chunk_size=4000, chunk_overlap=0)
    log_content = "2025-12-31 10:00:00 INFO Test log entry\n"
    chunks = chunker.chunk_log(log_content)

    with patch("logginganalysis.extraction.extractor.create_extraction_chain") as mock_chain:
        mock_result = ChunkExtractionResult(**MOCK_EXTRACTION_RESPONSE)
        mock_chain.return_value = MagicMock(ainvoke=AsyncMock(return_value=mock_result))

        extractor = LogExtractor()
        result = await extractor.extract_from_chunk(chunks.chunks[0], chunk_index=0, total_chunks=1)

        assert result is not None

        log_messages = [record.message for record in caplog.records]
        assert any("开始提取chunk" in msg for msg in log_messages)
        assert any("成功提取chunk" in msg for msg in log_messages)


@pytest.mark.asyncio
async def test_extract_from_chunks_with_progress_tracking(caplog):
    """测试批量提取时记录进度。"""
    caplog.set_level(logging.INFO)

    chunker = LogChunker(chunk_size=4000, chunk_overlap=0)
    log_content = "2025-12-31 10:00:00 INFO Test log entry\n"
    chunks = chunker.chunk_log(log_content)

    progress_updates = []

    def progress_callback(update):
        progress_updates.append(update)

    with patch("logginganalysis.extraction.extractor.create_extraction_chain") as mock_chain:
        mock_result = ChunkExtractionResult(**MOCK_EXTRACTION_RESPONSE)
        mock_chain.return_value = MagicMock(ainvoke=AsyncMock(return_value=mock_result))

        extractor = LogExtractor(progress_callback=progress_callback)
        results = await extractor.extract_from_chunks(chunks)

        assert len(results) == 1
        assert len(progress_updates) > 0

        log_messages = [record.message for record in caplog.records]
        assert any("开始批量提取" in msg for msg in log_messages)


@pytest.mark.asyncio
async def test_analyzer_with_progress_tracking(caplog):
    """测试分析器进度跟踪。"""
    caplog.set_level(logging.INFO)

    from logginganalysis.analyzer import LogAnalyzer

    progress_updates = []

    def progress_callback(update):
        progress_updates.append(update)

    with (
        patch("logginganalysis.extraction.extractor.create_extraction_chain") as mock_chain,
        patch("logginganalysis.integration.chains.create_integration_chain") as mock_integration,
    ):
        mock_result = ChunkExtractionResult(**MOCK_EXTRACTION_RESPONSE)
        mock_chain.return_value = MagicMock(ainvoke=AsyncMock(return_value=mock_result))

        from logginganalysis.models.integration import IntegratedAnalysis

        mock_insight = AnalysisInsight(
            category="test",
            description="测试发现",
            evidence=[],
            recommendations=[],
        )
        mock_analysis = IntegratedAnalysis(
            overall_summary="测试摘要",
            key_findings=[mock_insight],
            root_cause_analysis="测试原因",
            system_context={"test": "context"},
            confidence_score=0.8,
        )
        mock_integration.return_value = MagicMock(ainvoke=AsyncMock(return_value=mock_analysis))

        analyzer = LogAnalyzer(progress_callback=progress_callback)
        report = await analyzer.analyze("Test log content")

        assert report is not None
        assert len(progress_updates) > 0

        log_messages = [record.message for record in caplog.records]
        assert any("开始分析日志" in msg for msg in log_messages)
        assert any("分析完成" in msg for msg in log_messages)

        steps = [update["step"] for update in progress_updates]
        assert "chunking" in steps
        assert "extraction" in steps
        assert "integration" in steps
        assert "reporting" in steps
