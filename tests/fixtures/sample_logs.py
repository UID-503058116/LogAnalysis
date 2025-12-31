"""示例日志数据用于测试。"""

# 简单的示例日志
SIMPLE_LOG = """2025-12-31 10:00:00 INFO Application starting
2025-12-31 10:00:01 ERROR Database connection failed
2025-12-31 10:00:02 INFO Retrying connection...
2025-12-31 10:00:03 INFO Connection established
"""

# 包含多种日志级别的日志
MULTI_LEVEL_LOG = """2025-12-31 10:00:00 DEBUG Initializing components
2025-12-31 10:00:01 INFO Application starting
2025-12-31 10:00:02 WARNING Deprecated API usage detected
2025-12-31 10:00:03 ERROR Database connection failed
2025-12-31 10:00:04 CRITICAL System shutdown initiated
"""

# 包含堆栈跟踪的日志
LOG_WITH_TRACEBACK = """2025-12-31 10:00:00 INFO Processing request
2025-12-31 10:00:01 ERROR Request processing failed
Traceback (most recent call last):
  File "/app/main.py", line 42, in process_request
    result = database.query(data)
  File "/app/database.py", line 15, in query
    return self.connection.execute(sql)
ConnectionError: Database connection timeout
2025-12-31 10:00:02 INFO Request failed after 2 attempts
"""

# 空日志
EMPTY_LOG = ""

# 只有时间戳的日志
TIMESTAMP_ONLY_LOG = """2025-12-31 10:00:00
2025-12-31 10:00:01
2025-12-31 10:00:02
"""

# 超长日志（用于测试分块）
LONG_LOG = "\n".join(
    f"2025-12-31 10:00:{i:02d} INFO Log message number {i} - " + "x" * 100
    for i in range(500)
)
