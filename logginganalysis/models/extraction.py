"""提取结果数据模型。"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ExceptionInfo(BaseModel):
    """异常信息模型。

    表示从日志中提取的异常信息。
    """

    type: str = Field(..., description="异常类型")
    message: str = Field(..., description="异常消息")
    stack_trace: str | list[str] | None = Field(default=None, description="堆栈跟踪信息")
    occurrence_count: int = Field(default=1, description="出现次数")
    severity: Literal["low", "medium", "high", "critical"] | None = Field(
        default=None, description="严重程度"
    )

    @field_validator("stack_trace", mode="before")
    @classmethod
    def convert_stack_trace_to_string(cls, v: str | list[str] | None) -> str | None:
        """将堆栈跟踪列表转换为字符串。"""
        if isinstance(v, list):
            return "\n".join(v)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "type": "ConnectionError",
                "message": "Database connection timeout",
                "stack_trace": "Traceback (most recent call last)...",
                "occurrence_count": 3,
            }
        }


class LibraryReference(BaseModel):
    """库引用模型。

    表示从日志中提取的库或框架引用信息。
    """

    name: str = Field(..., description="库名称")
    version: str | None = Field(default=None, description="库版本")
    context: str | None = Field(default=None, description="引用上下文信息")
    path: str | None = Field(default=None, description="库路径")
    type: str | None = Field(default=None, description="库类型 (如 mod, framework, library 等)")
    source: str | None = Field(default=None, description="来源信息")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "FastAPI",
                "version": "0.104.1",
                "context": "INFO: Started server process [1234] using Uvicorn",
            }
        }


class ProblematicBehavior(BaseModel):
    """问题行为模型。

    表示从日志中识别的潜在问题行为。
    """

    category: str | None = Field(
        default=None, description="问题类别（如：database、network、memory、performance、native_library、security、launch_tweaking）"
    )
    description: str = Field(..., description="问题描述")
    severity: Literal["low", "medium", "high", "critical", "warning", "info"] = Field(
        default="medium", description="严重程度"
    )
    details: str | None = Field(default=None, description="详细信息")
    context: str | None = Field(default=None, description="上下文信息")
    occurrences: list[str] = Field(default_factory=list, description="相关的日志行")

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, v: str) -> str:
        """标准化严重程度值。"""
        if v == "warning":
            return "low"
        if v == "info":
            return "low"
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "category": "database",
                "description": "Multiple database connection failures detected",
                "severity": "high",
                "occurrences": [
                    "2025-12-31 10:00:01 ERROR Database connection failed: timeout",
                    "2025-12-31 10:00:05 ERROR Database connection failed: timeout",
                ],
            }
        }


class ChunkExtractionResult(BaseModel):
    """日志块提取结果模型。

    表示从单个日志块中提取的所有信息。
    """

    chunk_id: str | None = Field(default=None, description="对应的日志块ID（AI提取时可为空，由调用方填充）")
    exceptions: list[ExceptionInfo] = Field(default_factory=list, description="提取的异常信息")
    libraries: list[LibraryReference] = Field(
        default_factory=list, description="提取的库引用信息"
    )
    problematic_behaviors: list[ProblematicBehavior] = Field(
        default_factory=list, description="提取的问题行为"
    )
    summary: str = Field(..., description="该块的简要总结")

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
                "exceptions": [
                    {
                        "type": "ConnectionError",
                        "message": "Database connection timeout",
                        "stack_trace": None,
                        "occurrence_count": 3,
                    }
                ],
                "libraries": [
                    {
                        "name": "FastAPI",
                        "version": "0.104.1",
                        "context": "INFO: Started server process",
                    }
                ],
                "problematic_behaviors": [
                    {
                        "category": "database",
                        "description": "Multiple database connection failures",
                        "severity": "high",
                        "occurrences": ["ERROR: Database connection failed"],
                    }
                ],
                "summary": "Chunk contains database connection issues and FastAPI startup logs.",
            }
        }
