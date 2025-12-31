"""信息集成模块。"""

from logginganalysis.integration.chains import (
    create_integration_chain,
    create_structured_integration_chain,
)
from logginganalysis.integration.integrator import LogIntegrator
from logginganalysis.integration.prompts import (
    INTEGRATION_SYSTEM_PROMPT,
    SIMPLE_INTEGRATION_SYSTEM_PROMPT,
    format_extractions_for_integration,
    integration_prompt,
    simple_integration_prompt,
)
from logginganalysis.integration.search_tool import WebSearchTool

__all__ = [
    "LogIntegrator",
    "WebSearchTool",
    "create_integration_chain",
    "create_structured_integration_chain",
    "INTEGRATION_SYSTEM_PROMPT",
    "SIMPLE_INTEGRATION_SYSTEM_PROMPT",
    "integration_prompt",
    "simple_integration_prompt",
    "format_extractions_for_integration",
]
