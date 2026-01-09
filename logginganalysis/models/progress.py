"""进度跟踪模型。"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ProcessingStep(BaseModel):
    """处理步骤。"""

    step_name: str = Field(..., description="步骤名称")
    status: str = Field(..., description="状态: pending, in_progress, completed, failed")
    start_time: datetime | None = Field(default=None, description="开始时间")
    end_time: datetime | None = Field(default=None, description="结束时间")
    error_message: str | None = Field(default=None, description="错误信息")
    metadata: dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "step_name": "chunk_extraction",
                "status": "completed",
                "start_time": "2024-01-01T00:00:00",
                "end_time": "2024-01-01T00:00:01",
            }
        }
    )


class ChunkProgress(BaseModel):
    """单个chunk的处理进度。"""

    chunk_id: str = Field(..., description="Chunk ID")
    chunk_index: int = Field(..., description="Chunk索引")
    total_chunks: int = Field(..., description="总chunk数")
    step: ProcessingStep = Field(..., description="当前处理步骤")
    tokens_processed: int = Field(default=0, description="已处理的token数")
    duration_seconds: float = Field(default=0.0, description="处理时长（秒）")

    @property
    def progress_percentage(self) -> float:
        """计算进度百分比。"""
        return (self.chunk_index / self.total_chunks) * 100 if self.total_chunks > 0 else 0

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chunk_id": "chunk-001",
                "chunk_index": 1,
                "total_chunks": 10,
                "step": {
                    "step_name": "extraction",
                    "status": "completed",
                    "start_time": "2024-01-01T00:00:00",
                    "end_time": "2024-01-01T00:00:01",
                },
                "tokens_processed": 500,
                "duration_seconds": 1.23,
            }
        }
    )


class AnalysisProgress(BaseModel):
    """整体分析进度。"""

    analysis_id: str = Field(default_factory=lambda: str(uuid4()), description="分析唯一ID")
    start_time: datetime = Field(default_factory=datetime.now, description="开始时间")
    end_time: datetime | None = Field(default=None, description="结束时间")
    status: str = Field(default="pending", description="状态")
    total_chunks: int = Field(default=0, description="总chunk数")
    completed_chunks: int = Field(default=0, description="已完成的chunk数")
    failed_chunks: int = Field(default=0, description="失败的chunk数")
    current_step: str = Field(default="pending", description="当前步骤")
    chunk_progress: list[ChunkProgress] = Field(default_factory=list, description="各chunk的进度")
    errors: list[str] = Field(default_factory=list, description="错误列表")
    metadata: dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    @property
    def total_duration_seconds(self) -> float:
        """计算总时长。"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    @property
    def progress_percentage(self) -> float:
        """计算总体进度百分比。"""
        return (self.completed_chunks / self.total_chunks) * 100 if self.total_chunks > 0 else 0

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "analysis_id": "analysis-001",
                "start_time": "2024-01-01T00:00:00",
                "end_time": "2024-01-01T00:00:10",
                "status": "completed",
                "total_chunks": 10,
                "completed_chunks": 10,
                "failed_chunks": 0,
                "current_step": "reporting",
            }
        }
    )
