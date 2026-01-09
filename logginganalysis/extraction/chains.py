"""提取模块的 LangChain 链。"""

from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from logginganalysis.config.settings import get_settings
from logginganalysis.extraction.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    STRUCTURED_OUTPUT_INSTRUCTIONS,
    extraction_prompt,
    simple_extraction_prompt,
)
from logginganalysis.models.extraction import ChunkExtractionResult


def create_extraction_chain(
    llm: ChatOpenAI | None = None,
    use_simple_prompt: bool = False,
) -> Runnable[dict[str, str], ChunkExtractionResult]:
    """创建提取链。

    使用 LCEL (LangChain Expression Language) 构建提取链。

    Args:
        llm: 使用的语言模型。如果为 None，使用配置中的提取模型
        use_simple_prompt: 是否使用简化版提示词

    Returns:
        Chain: 可调用的提取链
    """
    settings = get_settings()

    if llm is None:
        llm = ChatOpenAI(
            model=settings.extraction_model,
            api_key=SecretStr(settings.openai_api_key),
            base_url=settings.openai_base_url,
            temperature=0,  # 使用较低温度以获得更一致的结果
        )

    # 选择提示词模板
    prompt = simple_extraction_prompt if use_simple_prompt else extraction_prompt

    # 创建输出解析器
    parser = PydanticOutputParser(pydantic_object=ChunkExtractionResult)

    # 构建链：prompt | llm | parser
    chain: Runnable[Any, ChunkExtractionResult] = (  # type: ignore[assignment]
        {
            "log_chunk": lambda x: x["log_chunk"],
            "format_instructions": lambda _: parser.get_format_instructions(),
        }
        | prompt.partial(format_instructions=STRUCTURED_OUTPUT_INSTRUCTIONS)
        | llm
        | parser
    )

    return chain


def create_structured_extraction_chain(
    llm: ChatOpenAI | None = None,
) -> Runnable[dict[str, str], ChunkExtractionResult]:
    """创建使用结构化输出的提取链。

    使用 OpenAI 的原生结构化输出功能（仅适用于支持该功能的模型）。

    Args:
        llm: 使用的语言模型。如果为 None，使用配置中的提取模型

    Returns:
        配置了结构化输出的 LLM
    """
    settings = get_settings()

    if llm is None:
        llm = ChatOpenAI(
            model=settings.extraction_model,
            api_key=SecretStr(settings.openai_api_key),
            base_url=settings.openai_base_url,
            temperature=0,
        )

    # 使用 with_structured_output 方法（OpenAI 原生支持）
    structured_llm = llm.with_structured_output(ChunkExtractionResult)

    # 创建不需要 format_instructions 的提示词
    structured_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", EXTRACTION_SYSTEM_PROMPT),
            ("human", "请分析以下日志块并提取关键信息：\n\n```\n{log_chunk}\n```"),
        ]
    )

    # 构建完整的链
    chain = structured_prompt | structured_llm  # type: ignore[return-value]

    return chain  # type: ignore[return-value]
