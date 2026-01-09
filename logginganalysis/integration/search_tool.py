"""zai-sdk 网页搜索工具包装器。"""

from typing import Any, Protocol

from logginganalysis.utils.exceptions import IntegrationError


class ZaiClientProtocol(Protocol):
    """Protocol for ZaiClient."""

    async def search(self, query: str, limit: int) -> Any: ...


class WebSearchTool:
    """网页搜索工具。

    使用 zai-sdk 进行网页搜索，以获取额外的上下文信息。
    """

    def __init__(self, api_key: str | None = None) -> None:
        """初始化网页搜索工具。

        Args:
            api_key: zai-sdk API 密钥。如果为 None，从配置中读取
        """
        from logginganalysis.config.settings import get_settings

        settings = get_settings()

        self.api_key = api_key or settings.zai_api_key
        self.enabled = settings.enable_web_search and bool(self.api_key)

        self.client: Any = None
        if self.enabled:
            try:
                # 尝试导入 zai-sdk
                from zai import ZaiClient

                self.client = ZaiClient(api_key=self.api_key)
            except ImportError as e:
                raise IntegrationError(f"zai-sdk 未安装，但网页搜索已启用: {e}") from e
            except Exception as e:
                raise IntegrationError(f"初始化 zai-sdk 失败: {e}") from e

    async def search_for_context(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """搜索与问题相关的上下文信息。

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            list[dict]: 搜索结果列表
        """
        if not self.enabled or self.client is None:
            return []

        try:
            # 使用 zai-sdk 进行搜索
            results = await self._search(query, max_results)
            return results

        except Exception as e:
            raise IntegrationError(f"网页搜索失败: {e}") from e

    async def search_error_solutions(
        self,
        error_type: str,
        error_message: str | None = None,
        max_results: int = 3,
    ) -> list[dict[str, Any]]:
        """搜索错误解决方案。

        Args:
            error_type: 错误类型
            error_message: 错误消息（可选）
            max_results: 最大结果数

        Returns:
            list[dict]: 搜索结果列表
        """
        query = f"{error_type} 解决方案"
        if error_message:
            # 从错误消息中提取关键词
            keywords = self._extract_keywords(error_message)
            if keywords:
                query += f" {keywords}"

        return await self.search_for_context(query, max_results)

    async def _search(self, query: str, max_results: int) -> list[dict[str, Any]]:
        """执行搜索的内部方法。

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            list[dict]: 搜索结果列表
        """
        if self.client is None:
            return []

        # 这里假设 zai-sdk 有类似的接口
        # 实际实现需要根据 zai-sdk 的具体 API 调整
        try:
            # 示例调用（需要根据实际 zai-sdk API 调整）
            response = await self.client.search(
                query=query,
                limit=max_results,
            )

            # 格式化结果
            results = []
            if isinstance(response, dict):
                items = response.get("results", response.get("items", []))
            elif isinstance(response, list):
                items = response
            else:
                items = []

            if not items:
                return []

            for item in items[:max_results]:
                if not isinstance(item, dict):
                    continue
                results.append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("url", item.get("link", "")),
                        "snippet": item.get("snippet", item.get("description", "")),
                    }
                )

            return results

        except Exception as e:
            # 搜索失败不应中断整个流程，返回空列表
            return []

    def _extract_keywords(self, error_message: str) -> str:
        """从错误消息中提取关键词。

        Args:
            error_message: 错误消息

        Returns:
            str: 提取的关键词
        """
        # 简单的关键词提取逻辑
        # 实际实现可以使用更复杂的 NLP 技术
        import re

        # 移除常见的无关词汇
        stop_words = {"the", "a", "an", "is", "at", "which", "on", "in", "to"}

        # 提取单词
        words = re.findall(r"\b\w+\b", error_message.lower())

        # 过滤停用词和短词
        keywords = [w for w in words if w not in stop_words and len(w) > 3]

        # 返回前几个关键词
        return " ".join(keywords[:5])

    def is_enabled(self) -> bool:
        """检查网页搜索是否启用。"""
        return self.enabled
