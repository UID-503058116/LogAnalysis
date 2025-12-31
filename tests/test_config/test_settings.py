"""配置管理模块测试。"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from logginganalysis.config.settings import Settings, get_settings, reset_settings


class TestSettings:
    """Settings 类测试。"""

    def test_settings_with_all_fields(self, mock_settings):
        """测试创建包含所有字段的 Settings。"""
        assert mock_settings.openai_api_key == "test-api-key"
        assert mock_settings.extraction_model == "gpt-4o-mini"
        assert mock_settings.integration_model == "gpt-4o"
        assert mock_settings.chunk_size == 1000
        assert mock_settings.chunk_overlap == 100
        assert mock_settings.max_chunks == 50

    def test_settings_defaults(self):
        """测试 Settings 的默认值。"""
        settings = Settings(
            openai_api_key="test-key",
        )
        assert settings.openai_base_url == "https://api.openai.com/v1"
        assert settings.extraction_model == "gpt-4o-mini"
        assert settings.integration_model == "gpt-4o"
        assert settings.chunk_size == 4000
        assert settings.chunk_overlap == 200
        assert settings.max_chunks == 100
        assert settings.mcp_port == 8000
        assert settings.zai_api_key is None
        assert settings.enable_web_search is False

    def test_settings_validation_error(self):
        """测试 Settings 验证错误。"""
        with pytest.raises(ValidationError):
            Settings()  # 缺少必需的 openai_api_key

    def test_settings_confidence_score_range(self):
        """测试 Settings 字段范围验证。"""
        settings = Settings(openai_api_key="test-key")
        assert 0 <= settings.chunk_size <= 100000
        assert 0 <= settings.chunk_overlap <= settings.chunk_size
        assert settings.max_chunks > 0


class TestGetSettings:
    """get_settings 函数测试。"""

    def test_get_settings_returns_singleton(self):
        """测试 get_settings 返回单例。"""
        reset_settings()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_get_settings_with_env_vars(self, monkeypatch):
        """测试从环境变量加载配置。"""
        reset_settings()
        monkeypatch.setenv("OPENAI_API_KEY", "env-test-key")
        monkeypatch.setenv("EXTRACTION_MODEL", "gpt-3.5-turbo")
        monkeypatch.setenv("CHUNK_SIZE", "2000")

        settings = get_settings()
        assert settings.openai_api_key == "env-test-key"
        assert settings.extraction_model == "gpt-3.5-turbo"
        assert settings.chunk_size == 2000

    def test_get_settings_from_file(self, temp_env_file, monkeypatch):
        """测试从 .env 文件加载配置。"""
        reset_settings()
        # 设置环境变量指向测试文件
        monkeypatch.setenv("OPENAI_API_KEY", "file-test-key")

        settings = get_settings()
        assert settings.openai_api_key == "file-test-key"


class TestResetSettings:
    """reset_settings 函数测试。"""

    def test_reset_settings(self):
        """测试重置配置。"""
        settings1 = get_settings()
        reset_settings()
        settings2 = get_settings()
        # 重置后应该是新的实例
        assert settings1 is not settings2

    def test_reset_settings_allows_new_config(self, monkeypatch):
        """测试重置后可以加载新配置。"""
        # 获取初始配置
        reset_settings()
        monkeypatch.setenv("OPENAI_API_KEY", "first-key")
        settings1 = get_settings()
        assert settings1.openai_api_key == "first-key"

        # 重置并加载新配置
        reset_settings()
        monkeypatch.setenv("OPENAI_API_KEY", "second-key")
        settings2 = get_settings()
        assert settings2.openai_api_key == "second-key"
        assert settings1 is not settings2
