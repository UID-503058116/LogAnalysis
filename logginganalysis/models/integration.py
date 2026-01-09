"""集成分析数据模型。"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorChain(BaseModel):
    """错误链模型。

    表示错误之间的因果关系链，展示错误是如何从一个初始问题逐步引发其他问题的。
    """

    root_cause: str = Field(..., description="根本原因描述")
    chain: list[dict[str, Any]] = Field(
        default_factory=list,
        description="错误链步骤，每步包含 event（事件）和 impact（影响）",
    )
    final_outcome: str = Field(..., description="最终结果")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "root_cause": "LWJGL 原生库版本冲突",
                "chain": [
                    {
                        "step": 1,
                        "event": "LWJGL 2.9.4 与 3.x 混用",
                        "impact": "导致 getPointer 方法找不到",
                    },
                    {
                        "step": 2,
                        "event": "NoSuchMethodError: getPointer",
                        "impact": "原生库加载失败",
                    },
                    {
                        "step": 3,
                        "event": "UnsatisfiedLinkError",
                        "impact": "游戏客户端崩溃",
                    },
                ],
                "final_outcome": "客户端完全无法启动",
            }
        }
    )


class AnalysisInsight(BaseModel):
    """分析洞察模型。

    表示从集成分析中得出的关键洞察。
    """

    category: str = Field(..., description="洞察类别")
    description: str = Field(..., description="洞察描述")
    evidence: list[str] = Field(default_factory=list, description="支持该洞察的证据")
    recommendations: list[str] = Field(default_factory=list, description="基于该洞察的建议")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "database",
                "description": "Database connection pool exhaustion detected",
                "evidence": [
                    "Multiple connection timeout errors",
                    "Connection pool stats show 0 available connections",
                ],
                "recommendations": [
                    "Increase connection pool size",
                    "Review connection leak in application code",
                ],
            }
        }
    )


class IntegratedAnalysis(BaseModel):
    """集成分析结果模型。

    表示对所有日志块提取结果进行综合分析后的结果。
    """

    overall_summary: str = Field(..., description="整体分析摘要")
    key_findings: list[AnalysisInsight] = Field(default_factory=list, description="关键发现列表")
    error_chain: ErrorChain | None = Field(
        default=None, description="错误链，展示错误之间的因果关系"
    )
    root_cause_analysis: str | None = Field(default=None, description="根因分析")
    system_context: dict[str, Any] = Field(
        default_factory=dict,
        description="推断的系统环境信息（如操作系统、框架、数据库等）",
    )
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="分析的置信度分数（0.0-1.0）")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall_summary": "The system is experiencing database connectivity issues "
                "likely due to connection pool exhaustion.",
                "key_findings": [
                    {
                        "category": "database",
                        "description": "Database connection pool exhaustion",
                        "evidence": ["Connection timeout errors", "Zero available connections"],
                        "recommendations": ["Increase pool size", "Fix connection leaks"],
                    }
                ],
                "root_cause_analysis": "The root cause appears to be unclosed database "
                "connections leading to pool exhaustion.",
                "system_context": {
                    "framework": "FastAPI",
                    "database": "PostgreSQL",
                    "language": "Python",
                },
                "confidence_score": 0.85,
            }
        }
    )
