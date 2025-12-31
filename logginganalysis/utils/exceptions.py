"""自定义异常类。"""

from typing import Any


class LoggingAnalysisError(Exception):
    """日志分析基础异常类。"""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - 详情: {self.details}"
        return self.message


class ConfigurationError(LoggingAnalysisError):
    """配置错误异常。"""

    pass


class ChunkingError(LoggingAnalysisError):
    """日志分块错误异常。"""

    pass


class ExtractionError(LoggingAnalysisError):
    """信息提取错误异常。"""

    pass


class IntegrationError(LoggingAnalysisError):
    """信息集成错误异常。"""

    pass


class ReportGenerationError(LoggingAnalysisError):
    """报告生成错误异常。"""

    pass


class MCPServerError(LoggingAnalysisError):
    """MCP 服务器错误异常。"""

    pass
