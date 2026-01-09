"""集成模块的 LangChain 链。"""

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from logginganalysis.config.settings import get_settings
from logginganalysis.integration.prompts import (
    format_extractions_for_integration,
    integration_prompt,
    simple_integration_prompt,
)
from logginganalysis.models.extraction import ChunkExtractionResult
from logginganalysis.models.integration import IntegratedAnalysis


def create_integration_chain(
    llm: ChatOpenAI | None = None,
    use_simple_prompt: bool = False,
) -> Runnable:
    """创建集成链。

    使用 LCEL (LangChain Expression Language) 构建集成链。

    Args:
        llm: 使用的语言模型。如果为 None，使用配置中的集成模型
        use_simple_prompt: 是否使用简化版提示词

    Returns:
        Runnable: 可调用的集成链
    """
    settings = get_settings()

    if llm is None:
        llm = ChatOpenAI(
            model=settings.integration_model,
            api_key=SecretStr(settings.openai_api_key),
            base_url=settings.openai_base_url,
            temperature=0.3,  # 略高的温度以允许更多综合分析
        )

    # 选择提示词模板
    prompt = simple_integration_prompt if use_simple_prompt else integration_prompt

    # 创建输出解析器
    parser = PydanticOutputParser(pydantic_object=IntegratedAnalysis)

    # 构建链
    def prepare_input(inputs: dict) -> dict:
        """准备集成链的输入。"""
        extractions = inputs["extractions"]

        # 格式化提取结果
        extractions_summary = format_extractions_for_integration(
            [e.model_dump() for e in extractions]
        )

        # 统计信息
        total_exceptions = sum(len(e.exceptions) for e in extractions)
        total_behaviors = sum(len(e.problematic_behaviors) for e in extractions)
        all_libraries: set[str] = set()
        for e in extractions:
            all_libraries.update(lib.name for lib in e.libraries)

        return {
            "extractions_summary": extractions_summary,
            "chunk_count": len(extractions),
            "total_exceptions": total_exceptions,
            "total_behaviors": total_behaviors,
            "library_count": len(all_libraries),
            "format_instructions": parser.get_format_instructions(),
        }

    # 完整的链
    chain = prepare_input | prompt | llm | parser

    return chain


def create_structured_integration_chain(
    llm: ChatOpenAI | None = None,
) -> Runnable:
    """创建使用结构化输出的集成链。

    使用 OpenAI 的原生结构化输出功能。

    Args:
        llm: 使用的语言模型。如果为 None，使用配置中的集成模型

    Returns:
        Runnable: 配置了结构化输出的集成链
    """
    settings = get_settings()

    if llm is None:
        llm = ChatOpenAI(
            model=settings.integration_model,
            api_key=SecretStr(settings.openai_api_key),
            base_url=settings.openai_base_url,
            temperature=0.3,
        )

    # 使用结构化输出
    structured_llm = llm.with_structured_output(IntegratedAnalysis)

    # 构建链
    def prepare_input(inputs: dict) -> dict:
        """准备集成链的输入。"""
        extractions = inputs["extractions"]

        # 格式化提取结果
        extractions_summary = format_extractions_for_integration(
            [e.model_dump() for e in extractions]
        )

        # 统计信息
        total_exceptions = sum(len(e.exceptions) for e in extractions)
        total_behaviors = sum(len(e.problematic_behaviors) for e in extractions)
        all_libraries: set[str] = set()
        for e in extractions:
            all_libraries.update(lib.name for lib in e.libraries)

        return {
            "extractions_summary": extractions_summary,
            "chunk_count": len(extractions),
            "total_exceptions": total_exceptions,
            "total_behaviors": total_behaviors,
            "library_count": len(all_libraries),
        }

    chain = prepare_input | integration_prompt | structured_llm

    return chain
