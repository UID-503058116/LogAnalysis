"""Mock LLM 响应数据。"""

# 提取阶段的模拟响应
MOCK_EXTRACTION_RESPONSE = {
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
        {"name": "FastAPI", "version": "0.104.1", "context": "FastAPI starting up"},
        {"name": "SQLAlchemy", "version": None, "context": "SQLAlchemy initialized"},
    ],
    "problematic_behaviors": [
        {
            "category": "database",
            "description": "Multiple database connection failures",
            "severity": "high",
            "occurrences": ["ERROR Database connection failed"],
        }
    ],
    "summary": "Application startup with database connectivity issues",
}

# 集成阶段的模拟响应
MOCK_INTEGRATION_RESPONSE = {
    "overall_summary": "Database connectivity issues detected during application startup. "
    "The system is experiencing connection timeouts to the PostgreSQL database.",
    "key_findings": [
        {
            "category": "database",
            "description": "Database connection failures",
            "evidence": ["Connection timeout errors", "ConnectionError exceptions"],
            "recommendations": ["Check database availability", "Increase timeout"],
        }
    ],
    "root_cause_analysis": "Database service appears to be unavailable or network connectivity is blocked.",
    "system_context": {
        "framework": "FastAPI",
        "database": "PostgreSQL",
        "language": "Python",
    },
    "confidence_score": 0.85,
}

# 无异常的提取响应
MOCK_EXTRACTION_NO_ERRORS = {
    "chunk_id": "test-chunk-2",
    "exceptions": [],
    "libraries": [
        {"name": "FastAPI", "version": "0.104.1", "context": "Server started"}
    ],
    "problematic_behaviors": [],
    "summary": "Application started successfully on port 8000",
}

# 多个异常的提取响应
MOCK_EXTRACTION_MULTIPLE_ERRORS = {
    "chunk_id": "test-chunk-3",
    "exceptions": [
        {
            "type": "ConnectionError",
            "message": "Database timeout",
            "stack_trace": None,
            "occurrence_count": 3,
        },
        {
            "type": "ValueError",
            "message": "Invalid input parameter",
            "stack_trace": "Traceback...",
            "occurrence_count": 1,
        },
    ],
    "libraries": [],
    "problematic_behaviors": [
        {
            "category": "database",
            "description": "Connection pool exhausted",
            "severity": "critical",
            "occurrences": ["ERROR: Timeout"],
        },
        {
            "category": "performance",
            "description": "Slow query execution",
            "severity": "medium",
            "occurrences": ["WARNING: Query took 5s"],
        },
    ],
    "summary": "Multiple critical issues detected including database and performance problems",
}
