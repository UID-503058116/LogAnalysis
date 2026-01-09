"""日志块数据模型。"""

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class LogChunk(BaseModel):
    """日志块模型。

    表示日志内容的一个分块。
    """

    id: str = Field(default_factory=lambda: str(uuid4()), description="日志块唯一标识")
    content: str = Field(..., description="日志块内容")
    start_index: int = Field(..., description="在原始日志中的起始位置")
    end_index: int = Field(..., description="在原始日志中的结束位置")
    metadata: dict[str, Any] = Field(default_factory=dict, description="额外的元数据")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "content": "2025-12-31 10:00:00 INFO Starting application...",
                "start_index": 0,
                "end_index": 50,
                "metadata": {"timestamp": "2025-12-31T10:00:00"},
            }
        }
    )


class LogChunks(BaseModel):
    """日志块集合模型。

    表示日志内容被分割后的所有块的集合。
    """

    chunks: list[LogChunk] = Field(default_factory=list, description="日志块列表")
    total_size: int = Field(default=0, description="所有块的总字符数")
    original_log_size: int = Field(..., description="原始日志的字符数")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chunks": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "content": "2025-12-31 10:00:00 INFO Starting application...",
                        "start_index": 0,
                        "end_index": 50,
                        "metadata": {},
                    }
                ],
                "total_size": 50,
                "original_log_size": 50,
            }
        }
    )
