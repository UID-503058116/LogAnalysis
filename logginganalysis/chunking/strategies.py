"""分块策略模块。

提供不同的日志分块策略。
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

from logginganalysis.models.chunk import LogChunk, LogChunks


class BaseChunkingStrategy(ABC):
    """分块策略基类。"""

    @abstractmethod
    def chunk(self, log_content: str, **kwargs: Any) -> LogChunks:
        """执行分块。

        Args:
            log_content: 日志内容
            **kwargs: 额外参数

        Returns:
            LogChunks: 分块结果
        """
        pass


class TimestampBasedChunking(BaseChunkingStrategy):
    """基于时间戳的分块策略。

    按照时间间隔将日志分组，适用于按时间分析的日志。
    """

    def __init__(self, interval_minutes: int = 5) -> None:
        """初始化基于时间戳的分块策略。

        Args:
            interval_minutes: 每个块的时间间隔（分钟）
        """
        self.interval_minutes = interval_minutes

    def chunk(self, log_content: str, **kwargs: Any) -> LogChunks:
        """按时间戳分块。

        Args:
            log_content: 日志内容
            **kwargs: 额外参数

        Returns:
            LogChunks: 分块结果
        """
        import re

        # 常见的时间戳正则模式
        timestamp_patterns = [
            r"\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}",  # ISO 格式
            r"\d{2}/\d{2}/\d{4}\s\d{2}:\d{2}:\d{2}",  # MM/DD/YYYY
            r"\d{4}/\d{2}/\d{2}\s\d{2}:\d{2}:\d{2}",  # YYYY/MM/DD
        ]

        lines = log_content.split("\n")
        chunks: list[LogChunk] = []

        current_chunk_lines: list[str] = []
        current_timestamp: datetime | None = None
        current_start_index = 0
        chunk_number = 0

        for line in lines:
            timestamp = self._extract_timestamp(line, timestamp_patterns)

            if timestamp:
                if current_timestamp is None:
                    current_timestamp = timestamp
                    current_start_index = 0
                elif timestamp - current_timestamp >= timedelta(minutes=self.interval_minutes):
                    # 时间间隔超过阈值，创建新块
                    if current_chunk_lines:
                        content = "\n".join(current_chunk_lines)
                        chunks.append(
                            LogChunk(
                                content=content,
                                start_index=current_start_index,
                                end_index=current_start_index + len(content),
                                metadata={
                                    "chunk_number": chunk_number,
                                    "time_interval_minutes": self.interval_minutes,
                                    "start_time": current_timestamp.isoformat(),
                                },
                            )
                        )
                        chunk_number += 1
                        current_chunk_lines = []
                    current_timestamp = timestamp
                    current_start_index = sum(len(c.content) for c in chunks)

            current_chunk_lines.append(line)

        # 添加最后一个块
        if current_chunk_lines:
            content = "\n".join(current_chunk_lines)
            chunks.append(
                LogChunk(
                    content=content,
                    start_index=current_start_index,
                    end_index=current_start_index + len(content),
                    metadata={
                        "chunk_number": chunk_number,
                        "time_interval_minutes": self.interval_minutes,
                        "start_time": current_timestamp.isoformat() if current_timestamp else None,
                    },
                )
            )

        return LogChunks(
            chunks=chunks,
            total_size=sum(len(c.content) for c in chunks),
            original_log_size=len(log_content),
        )

    def _extract_timestamp(self, line: str, patterns: list[str]) -> datetime | None:
        """从日志行中提取时间戳。

        Args:
            line: 日志行
            patterns: 时间戳正则模式列表

        Returns:
            datetime | None: 提取的时间戳
        """
        import re

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                timestamp_str = match.group()
                try:
                    # 尝试解析时间戳
                    if "T" in timestamp_str:
                        return datetime.fromisoformat(timestamp_str.replace("T", " "))
                    return datetime.strptime(timestamp_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
        return None


class ErrorBoundaryChunking(BaseChunkingStrategy):
    """基于错误边界的分块策略。

    在错误/异常处进行分块，便于错误分析。
    """

    def __init__(
        self,
        error_keywords: list[str] | None = None,
    ) -> None:
        """初始化基于错误边界的分块策略。

        Args:
            error_keywords: 错误关键字列表，默认为常见错误级别
        """
        self.error_keywords = error_keywords or [
            "ERROR",
            "CRITICAL",
            "FATAL",
            "Exception",
            "Traceback",
        ]

    def chunk(self, log_content: str, **kwargs: Any) -> LogChunks:
        """按错误边界分块。

        Args:
            log_content: 日志内容
            **kwargs: 额外参数

        Returns:
            LogChunks: 分块结果
        """
        lines = log_content.split("\n")
        chunks: list[LogChunk] = []

        current_chunk_lines: list[str] = []
        current_start_index = 0
        chunk_number = 0
        contains_error = False

        for i, line in enumerate(lines):
            # 检查是否包含错误关键字
            is_error_boundary = any(
                keyword in line for keyword in self.error_keywords
            )

            if is_error_boundary and current_chunk_lines and contains_error:
                # 遇到新错误且当前块已包含错误，创建新块
                content = "\n".join(current_chunk_lines)
                chunks.append(
                    LogChunk(
                        content=content,
                        start_index=current_start_index,
                        end_index=current_start_index + len(content),
                        metadata={
                            "chunk_number": chunk_number,
                            "contains_error": True,
                            "error_boundary": True,
                        },
                    )
                )
                chunk_number += 1
                current_chunk_lines = []
                current_start_index = sum(len(c.content) for c in chunks)
                contains_error = False

            current_chunk_lines.append(line)
            if is_error_boundary:
                contains_error = True

        # 添加最后一个块
        if current_chunk_lines:
            content = "\n".join(current_chunk_lines)
            chunks.append(
                LogChunk(
                    content=content,
                    start_index=current_start_index,
                    end_index=current_start_index + len(content),
                    metadata={
                        "chunk_number": chunk_number,
                        "contains_error": contains_error,
                        "error_boundary": contains_error,
                    },
                )
            )

        return LogChunks(
            chunks=chunks,
            total_size=sum(len(c.content) for c in chunks),
            original_log_size=len(log_content),
        )
