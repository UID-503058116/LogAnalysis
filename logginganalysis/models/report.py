"""报告数据模型。"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from logginganalysis.models.integration import IntegratedAnalysis
from logginganalysis.models.extraction import ChunkExtractionResult


class ReportMetadata(BaseModel):
    """报告元数据模型。

    包含报告生成过程中的元信息。
    """

    log_source: str | None = Field(default=None, description="日志来源（文件路径或标识）")
    log_size_bytes: int = Field(..., description="原始日志大小（字节）")
    chunk_count: int = Field(..., description="日志分块数量")
    models_used: dict[str, str] = Field(..., description="使用的AI模型")
    processing_time_seconds: float = Field(..., description="处理耗时（秒）")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "log_source": "/var/log/application.log",
                "log_size_bytes": 102400,
                "chunk_count": 25,
                "models_used": {
                    "extraction": "gpt-4o-mini",
                    "integration": "gpt-4o",
                },
                "processing_time_seconds": 12.5,
            }
        }
    )


class AnalysisReport(BaseModel):
    """分析报告模型。

    包含完整的日志分析结果。
    """

    metadata: ReportMetadata = Field(..., description="报告元数据")
    analysis: IntegratedAnalysis = Field(..., description="集成分析结果")
    raw_extractions: list[ChunkExtractionResult] = Field(
        default_factory=list, description="各块的原始提取结果"
    )
    search_results: list[dict[str, Any]] | None = Field(
        default=None, description="网页搜索结果（如果有）"
    )
    generated_at: datetime = Field(default_factory=datetime.now, description="报告生成时间")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metadata": {
                    "log_source": "/var/log/application.log",
                    "log_size_bytes": 102400,
                    "chunk_count": 25,
                    "models_used": {
                        "extraction": "gpt-4o-mini",
                        "integration": "gpt-4o",
                    },
                    "processing_time_seconds": 12.5,
                },
                "analysis": {
                    "overall_summary": "Database connectivity issues detected",
                    "key_findings": [],
                    "root_cause_analysis": None,
                    "system_context": {},
                    "confidence_score": 0.85,
                },
                "raw_extractions": [],
                "search_results": None,
                "generated_at": "2025-12-31T10:00:00Z",
            }
        }
    )
