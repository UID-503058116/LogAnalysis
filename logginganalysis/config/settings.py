"""配置管理模块。

使用 pydantic-settings 从环境变量或 .env 文件加载配置。
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用程序配置。

    从环境变量或 .env 文件加载配置。
    """

    # OpenAI 配置
    openai_api_key: str = Field(..., description="OpenAI API 密钥")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API 基础 URL",
    )

    # 模型配置
    extraction_model: str = Field(
        default="gpt-4o-mini",
        description="用于提取日志信息的模型（经济型）",
    )
    integration_model: str = Field(
        default="gpt-4o",
        description="用于集成分析结果的模型（强大）",
    )

    # 分块配置
    chunk_size: int = Field(default=4000, description="每个日志块的最大字符数")
    chunk_overlap: int = Field(default=200, description="相邻块之间的重叠字符数")
    max_chunks: int = Field(default=100, description="最大分块数量限制")

    # MCP 服务器配置
    mcp_port: int = Field(default=8000, description="MCP 服务器监听端口")

    # zai-sdk 可选配置
    zai_api_key: str | None = Field(default=None, description="zai-sdk API 密钥（可选）")
    enable_web_search: bool = Field(default=False, description="是否启用网页搜索功能")

    # ========== 流控配置 ==========
    # TPM (每分钟事务数) 流控
    tpm_limit: int | None = Field(
        default=None,
        description="TPM (每分钟事务数) 限制，None 表示不限制",
    )

    # RPM (每分钟请求数) 流控
    rpm_limit: int | None = Field(
        default=None,
        description="RPM (每分钟请求数) 限制，None 表示不限制",
    )

    # 流控突发容量
    rate_limit_burst: int = Field(
        default=10,
        description="流控突发容量（令牌桶最大容量）",
    )

    # 是否启用流控
    enable_rate_limit: bool = Field(
        default=True,
        description="是否启用 TPM/RPM 流控",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# 全局配置实例
_settings: Settings | None = None


def get_settings() -> Settings:
    """获取配置实例。

    使用单例模式，确保只加载一次配置。
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """重置配置实例（主要用于测试）。"""
    global _settings
    _settings = None
