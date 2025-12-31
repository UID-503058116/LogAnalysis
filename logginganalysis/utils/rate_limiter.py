"""流控器模块。

实现 TPM (每分钟事务数) 和 RPM (每分钟请求数) 流控。
"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RateLimitConfig:
    """流控配置。"""

    tpm_limit: int | None = None  # TPM (每分钟事务数) 限制
    rpm_limit: int | None = None  # RPM (每分钟请求数) 限制
    burst_size: int = 10  # 突发容量
    enabled: bool = True  # 是否启用流控


class TokenBucket:
    """令牌桶算法实现流控。

    适用于 RPM (每分钟请求数) 流控。
    """

    def __init__(self, rate: int, burst: int = 10) -> None:
        """初始化令牌桶。

        Args:
            rate: 每分钟补充的令牌数 (RPM)
            burst: 桶的最大容量（突发容量）
        """
        self.rate = rate  # 令牌/分钟
        self.burst = burst  # 最大桶容量
        self.tokens = burst  # 当前令牌数
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """获取令牌。

        Args:
            tokens: 需要的令牌数量

        Returns:
            bool: 是否成功获取令牌
        """
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update

            # 补充令牌
            refill_amount = (elapsed / 60) * self.rate
            self.tokens = min(self.burst, self.tokens + refill_amount)
            self.last_update = now

            # 检查是否有足够令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    async def wait_for_token(self, tokens: int = 1) -> None:
        """等待直到可以获取令牌。

        Args:
            tokens: 需要的令牌数量
        """
        while not await self.acquire(tokens):
            # 计算需要等待的时间
            wait_time = (tokens - self.tokens) * 60 / self.rate
            await asyncio.sleep(max(0.1, min(wait_time, 1)))


class SlidingWindow:
    """滑动窗口算法实现流控。

    适用于 TPM (每分钟事务数) 流控。
    """

    def __init__(self, limit: int, window: int = 60) -> None:
        """初始化滑动窗口。

        Args:
            limit: 时间窗口内的最大请求数
            window: 时间窗口大小（秒），默认 60 秒
        """
        self.limit = limit
        self.window = window
        self.requests: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """检查是否允许请求。

        Returns:
            bool: 是否允许请求
        """
        async with self._lock:
            now = time.time()

            # 移除窗口外的请求
            while self.requests and self.requests[0] <= now - self.window:
                self.requests.popleft()

            # 检查是否超过限制
            if len(self.requests) < self.limit:
                self.requests.append(now)
                return True

            return False

    async def wait_for_slot(self) -> None:
        """等待直到可以发送请求。"""
        while not await self.acquire():
            # 计算需要等待的时间（最旧请求过期时间）
            if self.requests:
                wait_time = self.requests[0] + self.window - time.time()
                await asyncio.sleep(max(0.1, min(wait_time, 1)))
            else:
                await asyncio.sleep(0.1)


class RateLimiter:
    """流控器。

    同时支持 TPM 和 RPM 流控。
    """

    def __init__(
        self,
        config: RateLimitConfig | None = None,
    ) -> None:
        """初始化流控器。

        Args:
            config: 流控配置
        """
        self.config = config or RateLimitConfig()

        # 初始化流控器
        self._rpm_limiter: TokenBucket | None = None
        self._tpm_limiter: SlidingWindow | None = None

        if self.config.enabled:
            if self.config.rpm_limit:
                self._rpm_limiter = TokenBucket(
                    rate=self.config.rpm_limit,
                    burst=self.config.burst_size,
                )

            if self.config.tpm_limit:
                self._tpm_limiter = SlidingWindow(
                    limit=self.config.tpm_limit,
                    window=60,
                )

    async def acquire(self, tokens: int = 1) -> bool:
        """尝试获取流控许可。

        Args:
            tokens: 需要的令牌数（用于 RPM）

        Returns:
            bool: 是否获得许可
        """
        if not self.config.enabled:
            return True

        # 检查 RPM 限制
        if self._rpm_limiter:
            if not await self._rpm_limiter.acquire(tokens):
                return False

        # 检查 TPM 限制
        if self._tpm_limiter:
            if not await self._tpm_limiter.acquire():
                return False

        return True

    async def wait_for_permission(self, tokens: int = 1) -> None:
        """等待直到获得流控许可。

        Args:
            tokens: 需要的令牌数
        """
        if not self.config.enabled:
            return

        # 同时等待两个限制
        tasks = []

        if self._rpm_limiter:
            tasks.append(self._rpm_limiter.wait_for_token(tokens))

        if self._tpm_limiter:
            tasks.append(self._tpm_limiter.wait_for_slot())

        if tasks:
            await asyncio.gather(*tasks)

    def get_stats(self) -> dict[str, Any]:
        """获取流控统计信息。

        Returns:
            dict: 流控统计信息
        """
        stats = {
            "enabled": self.config.enabled,
            "tpm_limit": self.config.tpm_limit,
            "rpm_limit": self.config.rpm_limit,
            "burst_size": self.config.burst_size,
        }

        if self._rpm_limiter:
            stats["rpm_available_tokens"] = round(self._rpm_limiter.tokens, 2)
            stats["rpm_bucket_size"] = self._rpm_limiter.burst

        if self._tpm_limiter:
            stats["tpm_current_requests"] = len(self._tpm_limiter.requests)
            stats["tpm_limit"] = self._tpm_limiter.limit

        return stats


class RateLimitError(Exception):
    """流控错误异常。"""

    def __init__(self, message: str, stats: dict[str, Any] | None = None) -> None:
        self.message = message
        self.stats = stats or {}
        super().__init__(self.message)


async def with_rate_limit(
    rate_limiter: RateLimiter,
    tokens: int = 1,
    raise_on_limit: bool = False,
) -> None:
    """流控上下文管理器。

    Args:
        rate_limiter: 流控器实例
        tokens: 需要的令牌数
        raise_on_limit: 超限时是否抛出异常

    Raises:
        RateLimitError: 超限时且 raise_on_limit=True
    """
    if raise_on_limit:
        if not await rate_limiter.acquire(tokens):
            raise RateLimitError(
                "Rate limit exceeded",
                stats=rate_limiter.get_stats(),
            )
    else:
        await rate_limiter.wait_for_permission(tokens)
