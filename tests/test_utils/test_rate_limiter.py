"""流控器测试。"""

import asyncio
import time

import pytest

from logginganalysis.utils.rate_limiter import (
    RateLimitConfig,
    RateLimitError,
    RateLimiter,
    SlidingWindow,
    TokenBucket,
    with_rate_limit,
)


class TestTokenBucket:
    """TokenBucket 测试。"""

    @pytest.mark.asyncio
    async def test_token_bucket_initialization(self):
        """测试令牌桶初始化。"""
        bucket = TokenBucket(rate=60, burst=10)
        assert bucket.rate == 60
        assert bucket.burst == 10
        assert bucket.tokens == 10

    @pytest.mark.asyncio
    async def test_token_bucket_acquire_success(self):
        """测试成功获取令牌。"""
        bucket = TokenBucket(rate=60, burst=10)
        success = await bucket.acquire(1)
        assert success is True
        assert bucket.tokens == 9

    @pytest.mark.asyncio
    async def test_token_bucket_acquire_multiple(self):
        """测试获取多个令牌。"""
        bucket = TokenBucket(rate=60, burst=10)
        success = await bucket.acquire(5)
        assert success is True
        assert bucket.tokens == 5

    @pytest.mark.asyncio
    async def test_token_bucket_exhausted(self):
        """测试令牌耗尽。"""
        bucket = TokenBucket(rate=60, burst=5)

        # 获取所有令牌
        assert await bucket.acquire(5) is True
        # 尝试获取更多
        assert await bucket.acquire(1) is False

    @pytest.mark.asyncio
    async def test_token_bucket_refill(self):
        """测试令牌补充。"""
        bucket = TokenBucket(rate=60, burst=10)  # 60 tokens/min = 1 token/sec

        # 耗尽所有令牌
        await bucket.acquire(10)
        assert bucket.tokens == 0

        # 等待 2 秒，应该补充约 2 个令牌
        await asyncio.sleep(2)

        # 再次调用 acquire 会触发令牌补充
        success = await bucket.acquire(1)
        # 应该有足够的令牌了
        assert success is True

    @pytest.mark.asyncio
    async def test_token_bucket_wait_for_token(self):
        """测试等待令牌。"""
        bucket = TokenBucket(rate=60, burst=2)

        # 耗尽令牌
        await bucket.acquire(2)
        start = time.time()

        # 等待令牌
        await bucket.wait_for_token(1)
        elapsed = time.time() - start

        # 应该等待约 1 秒（1 token/sec）
        assert elapsed >= 0.9


class TestSlidingWindow:
    """SlidingWindow 测试。"""

    @pytest.mark.asyncio
    async def test_sliding_window_initialization(self):
        """测试滑动窗口初始化。"""
        window = SlidingWindow(limit=10, window=60)
        assert window.limit == 10
        assert window.window == 60
        assert len(window.requests) == 0

    @pytest.mark.asyncio
    async def test_sliding_window_acquire_success(self):
        """测试成功获取许可。"""
        window = SlidingWindow(limit=10, window=60)
        success = await window.acquire()
        assert success is True
        assert len(window.requests) == 1

    @pytest.mark.asyncio
    async def test_sliding_window_fill_up(self):
        """测试窗口填满。"""
        window = SlidingWindow(limit=5, window=60)

        # 填满窗口
        for _ in range(5):
            assert await window.acquire() is True

        # 第 6 个应该失败
        assert await window.acquire() is False

    @pytest.mark.asyncio
    async def test_sliding_window_expire_old(self):
        """测试旧请求过期。"""
        # 使用 2 秒窗口以便测试
        window = SlidingWindow(limit=2, window=2)

        # 填满窗口
        assert await window.acquire() is True
        assert await window.acquire() is True
        assert await window.acquire() is False

        # 等待窗口过期
        await asyncio.sleep(2.1)

        # 现在应该可以获取新的许可
        assert await window.acquire() is True

    @pytest.mark.asyncio
    async def test_sliding_window_wait_for_slot(self):
        """测试等待插槽。"""
        window = SlidingWindow(limit=1, window=1)

        # 填满窗口
        await window.acquire()

        # 等待插槽
        start = time.time()
        await window.wait_for_slot()
        elapsed = time.time() - start

        # 应该等待约 1 秒
        assert elapsed >= 0.9


class TestRateLimiter:
    """RateLimiter 测试。"""

    def test_rate_limiter_initialization(self):
        """测试流控器初始化。"""
        config = RateLimitConfig(
            tpm_limit=100,
            rpm_limit=60,
            burst_size=10,
            enabled=True,
        )
        limiter = RateLimiter(config)

        assert limiter.config.tpm_limit == 100
        assert limiter.config.rpm_limit == 60
        assert limiter._rpm_limiter is not None
        assert limiter._tpm_limiter is not None

    def test_rate_limiter_disabled(self):
        """测试禁用流控。"""
        config = RateLimitConfig(
            tpm_limit=100,
            rpm_limit=60,
            enabled=False,
        )
        limiter = RateLimiter(config)

        assert limiter._rpm_limiter is None
        assert limiter._tpm_limiter is None

    def test_rate_limiter_no_limits(self):
        """测试无限制流控。"""
        config = RateLimitConfig(
            tpm_limit=None,
            rpm_limit=None,
            enabled=True,
        )
        limiter = RateLimiter(config)

        assert limiter._rpm_limiter is None
        assert limiter._tpm_limiter is None

    @pytest.mark.asyncio
    async def test_rate_limiter_acquire_success(self):
        """测试流控器成功获取许可。"""
        config = RateLimitConfig(
            rpm_limit=60,
            burst_size=5,
            enabled=True,
        )
        limiter = RateLimiter(config)

        success = await limiter.acquire()
        assert success is True

    @pytest.mark.asyncio
    async def test_rate_limiter_acquire_disabled(self):
        """测试禁用流控时总是成功。"""
        config = RateLimitConfig(enabled=False)
        limiter = RateLimiter(config)

        # 禁用状态下应该总是返回 True
        for _ in range(100):
            assert await limiter.acquire() is True

    @pytest.mark.asyncio
    async def test_rate_limiter_wait_for_permission(self):
        """测试等待许可。"""
        config = RateLimitConfig(
            rpm_limit=60,
            burst_size=2,
            enabled=True,
        )
        limiter = RateLimiter(config)

        # 耗尽突发容量
        await limiter.acquire(tokens=2)
        start = time.time()

        # 等待新许可
        await limiter.wait_for_permission(tokens=1)
        elapsed = time.time() - start

        # 应该等待约 1 秒
        assert elapsed >= 0.8

    def test_rate_limiter_get_stats(self):
        """测试获取统计信息。"""
        config = RateLimitConfig(
            tpm_limit=100,
            rpm_limit=60,
            burst_size=10,
            enabled=True,
        )
        limiter = RateLimiter(config)

        stats = limiter.get_stats()

        assert stats["enabled"] is True
        assert stats["tpm_limit"] == 100
        assert stats["rpm_limit"] == 60
        assert stats["burst_size"] == 10
        assert "rpm_available_tokens" in stats
        assert "tpm_current_requests" in stats


class TestRateLimitContextManager:
    """流控上下文管理器测试。"""

    @pytest.mark.asyncio
    async def test_with_rate_limit_success(self):
        """测试流控上下文管理器成功。"""
        config = RateLimitConfig(
            rpm_limit=60,
            burst_size=5,
            enabled=True,
        )
        limiter = RateLimiter(config)

        # 不抛出异常
        await with_rate_limit(limiter, tokens=1, raise_on_limit=False)

    @pytest.mark.asyncio
    async def test_with_rate_limit_raises(self):
        """测试流控超限抛出异常。"""
        config = RateLimitConfig(
            rpm_limit=60,
            burst_size=1,
            enabled=True,
        )
        limiter = RateLimiter(config)

        # 耗尽容量
        await limiter.acquire(tokens=1)

        # 下一个应该抛出异常
        with pytest.raises(RateLimitError):
            await with_rate_limit(limiter, tokens=1, raise_on_limit=True)

    @pytest.mark.asyncio
    async def test_with_rate_limit_disabled(self):
        """测试禁用流控时不抛异常。"""
        config = RateLimitConfig(enabled=False)
        limiter = RateLimiter(config)

        # 禁用状态下不抛异常
        for _ in range(100):
            await with_rate_limit(limiter, raise_on_limit=True)


class TestRateLimitConfig:
    """RateLimitConfig 测试。"""

    def test_config_defaults(self):
        """测试配置默认值。"""
        config = RateLimitConfig()
        assert config.tpm_limit is None
        assert config.rpm_limit is None
        assert config.burst_size == 10
        assert config.enabled is True

    def test_config_custom_values(self):
        """测试自定义配置值。"""
        config = RateLimitConfig(
            tpm_limit=100,
            rpm_limit=60,
            burst_size=20,
            enabled=False,
        )
        assert config.tpm_limit == 100
        assert config.rpm_limit == 60
        assert config.burst_size == 20
        assert config.enabled is False
