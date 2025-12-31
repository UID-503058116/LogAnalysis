"""日志分块模块。"""

from logginganalysis.chunking.splitter import ChunkStrategy, LogChunker
from logginganalysis.chunking.strategies import (
    BaseChunkingStrategy,
    ErrorBoundaryChunking,
    TimestampBasedChunking,
)

__all__ = [
    "ChunkStrategy",
    "LogChunker",
    "BaseChunkingStrategy",
    "TimestampBasedChunking",
    "ErrorBoundaryChunking",
]
