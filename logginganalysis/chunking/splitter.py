"""日志分块器。

使用 LangChain 的文本分割器将大型日志分割成可管理的块。
"""

from enum import Enum

from langchain_text_splitters import RecursiveCharacterTextSplitter

from logginganalysis.models.chunk import LogChunk, LogChunks
from logginganalysis.utils.exceptions import ChunkingError


class ChunkStrategy(str, Enum):
    """分块策略枚举。"""

    RECURSIVE = "recursive"
    LINE_BASED = "line_based"
    ERROR_BOUNDARIES = "error_boundaries"


class LogChunker:
    """日志分块器。

    使用 LangChain 的 RecursiveCharacterTextSplitter 进行智能分块。
    """

    def __init__(
        self,
        chunk_size: int = 4000,
        chunk_overlap: int = 200,
        strategy: ChunkStrategy = ChunkStrategy.RECURSIVE,
    ) -> None:
        """初始化日志分块器。

        Args:
            chunk_size: 每个块的最大字符数
            chunk_overlap: 相邻块之间的重叠字符数
            strategy: 分块策略
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy

        # 根据策略选择分隔符
        if strategy == ChunkStrategy.RECURSIVE:
            separators = ["\n\n", "\n", " ", ""]
        elif strategy == ChunkStrategy.LINE_BASED:
            separators = ["\n"]
        else:  # ERROR_BOUNDARIES
            # 首先按错误级别分隔，然后回退到标准分隔符
            separators = ["\nERROR", "\nCRITICAL", "\nFATAL", "\n\n", "\n", " ", ""]

        self.splitter = RecursiveCharacterTextSplitter(
            separators=separators,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            keep_separator=False,
        )

    def chunk_log(self, log_content: str, metadata: dict | None = None) -> LogChunks:
        """将日志内容分割成块。

        Args:
            log_content: 日志内容
            metadata: 可选的元数据，将添加到每个块

        Returns:
            LogChunks: 日志块集合

        Raises:
            ChunkingError: 分块失败时抛出
        """
        if not log_content:
            return LogChunks(chunks=[], total_size=0, original_log_size=0)

        try:
            # 使用 LangChain 分割器进行分块
            texts = self.splitter.split_text(log_content)

            # 计算每个块的起始和结束位置
            chunks: list[LogChunk] = []
            current_position = 0
            base_metadata = metadata or {}

            for i, text in enumerate(texts):
                # 在原始日志中查找文本位置
                start_index = log_content.find(text, current_position)
                if start_index == -1:
                    # 如果找不到（由于重叠等），使用当前位置
                    start_index = current_position
                end_index = start_index + len(text)

                # 创建日志块
                chunk = LogChunk(
                    content=text,
                    start_index=start_index,
                    end_index=end_index,
                    metadata={
                        **base_metadata,
                        "chunk_number": i + 1,
                        "chunk_strategy": self.strategy.value,
                    },
                )
                chunks.append(chunk)

                # 更新当前位置（考虑重叠）
                current_position = end_index - self.chunk_overlap if i > 0 else end_index

            # 计算总大小
            total_size = sum(len(chunk.content) for chunk in chunks)

            return LogChunks(
                chunks=chunks,
                total_size=total_size,
                original_log_size=len(log_content),
            )

        except Exception as e:
            raise ChunkingError(f"日志分块失败: {e}") from e
