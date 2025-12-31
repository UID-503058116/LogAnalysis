"""Pytest 配置和共享 fixtures。"""

import os
from typing import Generator
from unittest.mock import AsyncMock, Mock

import pytest
from langchain_openai import ChatOpenAI

from logginganalysis.config.settings import Settings, reset_settings


@pytest.fixture
def mock_settings() -> Settings:
    """Mock settings for testing."""
    return Settings(
        openai_api_key="test-api-key",
        openai_base_url="https://api.openai.com/v1",
        extraction_model="gpt-4o-mini",
        integration_model="gpt-4o",
        chunk_size=1000,
        chunk_overlap=100,
        max_chunks=50,
        mcp_port=8000,
        zai_api_key=None,
        enable_web_search=False,
    )


@pytest.fixture
def sample_log_content() -> str:
    """Sample log content for testing."""
    return """2025-12-31 10:00:00 INFO Starting application...
2025-12-31 10:00:01 INFO Initializing database connection...
2025-12-31 10:00:02 ERROR Database connection failed: timeout after 30s
2025-12-31 10:00:03 ERROR Exception: ConnectionError - Unable to connect to postgresql://localhost:5432/db
2025-12-31 10:00:04 INFO Retrying connection...
2025-12-31 10:00:05 ERROR Database connection failed: timeout after 30s
2025-12-31 10:00:10 INFO Application started on port 8000
2025-12-31 10:00:15 WARNING High memory usage detected: 85%
2025-12-31 10:00:20 INFO Request processed: GET /api/users - 200 OK
2025-12-31 10:00:25 INFO Request processed: POST /api/users - 201 Created
"""


@pytest.fixture
def sample_log_with_libraries() -> str:
    """Sample log with library references."""
    return """2025-12-31 10:00:00 INFO FastAPI version 0.104.1 starting up
2025-12-31 10:00:01 INFO Uvicorn running on http://0.0.0.0:8000
2025-12-31 10:00:02 INFO SQLAlchemy engine initialized
2025-12-31 10:00:03 INFO Redis cache connection established
2025-12-31 10:00:04 ERROR Pydantic validation error in request body
"""


@pytest.fixture
def sample_large_log() -> str:
    """Large sample log for testing chunking."""
    base_log = """2025-12-31 10:00:{i:02d} INFO Log entry number {i} - Testing application performance
2025-12-31 10:00:{i:02d} DEBUG Processing request with ID: req-{i:04d}
2025-12-31 10:00:{i:02d} DEBUG Database query executed in {i}ms
"""
    return "".join(base_log.format(i=i) for i in range(100))


@pytest.fixture
def mock_llm() -> Mock:
    """Mock LLM for testing."""
    llm = Mock(spec=ChatOpenAI)
    llm.ainvoke = AsyncMock()
    return llm


@pytest.fixture
def mock_extraction_response() -> dict:
    """Mock extraction response from LLM."""
    return {
        "chunk_id": "test-chunk-1",
        "exceptions": [
            {
                "type": "ConnectionError",
                "message": "Database connection timeout",
                "stack_trace": None,
                "occurrence_count": 2,
            }
        ],
        "libraries": [
            {
                "name": "FastAPI",
                "version": "0.104.1",
                "context": "FastAPI version 0.104.1 starting up",
            },
            {
                "name": "SQLAlchemy",
                "version": None,
                "context": "SQLAlchemy engine initialized",
            },
        ],
        "problematic_behaviors": [
            {
                "category": "database",
                "description": "Multiple database connection failures",
                "severity": "high",
                "occurrences": [
                    "ERROR Database connection failed: timeout after 30s",
                    "ERROR Exception: ConnectionError",
                ],
            }
        ],
        "summary": "Application startup with database connection issues",
    }


@pytest.fixture
def mock_integration_response() -> dict:
    """Mock integration response from LLM."""
    return {
        "overall_summary": "The system is experiencing database connectivity issues during startup. "
        "Multiple connection timeout errors indicate a potential database service problem.",
        "key_findings": [
            {
                "category": "database",
                "description": "Database connection pool exhaustion detected",
                "evidence": [
                    "Multiple connection timeout errors",
                    "ConnectionError exceptions in logs",
                ],
                "recommendations": [
                    "Check database service availability",
                    "Increase connection timeout",
                    "Review connection pool configuration",
                ],
            }
        ],
        "root_cause_analysis": "The root cause appears to be database service unavailability or network connectivity issues. "
        "The application is correctly retrying connections but ultimately failing.",
        "system_context": {
            "framework": "FastAPI",
            "language": "Python",
            "database": "PostgreSQL",
            "cache": "Redis",
        },
        "confidence_score": 0.85,
    }


@pytest.fixture(autouse=True)
def reset_settings_fixture() -> Generator[None, None, None]:
    """Reset settings before each test."""
    reset_settings()
    yield
    reset_settings()


@pytest.fixture
def temp_env_file(tmp_path) -> Generator[str, None, None]:
    """Create a temporary .env file for testing."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        """OPENAI_API_KEY=test-key-for-testing
EXTRACTION_MODEL=gpt-4o-mini
INTEGRATION_MODEL=gpt-4o
CHUNK_SIZE=2000
CHUNK_OVERLAP=200
"""
    )
    return str(env_file)


@pytest.fixture
def set_test_env(temp_env_file: str, monkeypatch) -> None:
    """Set environment variables for testing."""
    monkeypatch.setenv("ENV_FILE", temp_env_file)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-for-testing")
