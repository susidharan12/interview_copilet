# Coding Sandbox — Architecture

## Overview

Isolated Docker-based execution environment for generated code. Provides safe, resource-limited execution of candidate solutions with automatic test validation.

## Architecture

```
CodingEngine
    │
    ▼
┌─────────────────┐
│  SandboxManager  │
│  (Python async)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Docker Client   │ ← docker-py / httpx Docker API
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Isolated Container                      │
│  ┌───────────────────────────────────┐  │
│  │ /tmp/sandbox/                     │  │
│  │   solution.py                     │  │
│  │   test_solution.py                │  │
│  │   input.txt (stdin)              │  │
│  │   output.txt (stdout)            │  │
│  │   error.txt (stderr)             │  │
│  └───────────────────────────────────┘  │
│  Resources: --cpus=0.5 --memory=256m    │
│  Network: --network=none                │
│  Timeout: 30s (configurable)            │
│  Auto-remove: true                      │
└─────────────────────────────────────────┘
```

## Supported Languages

| Language | Runtime Image | Default Timeout | Notes |
|----------|--------------|-----------------|-------|
| Python | python:3.12-slim | 10s | pytest available |
| JavaScript | node:20-slim | 10s | Jest available |
| TypeScript | node:20-slim + tsx | 10s | tsx runner |
| Java | eclipse-temurin:21-jre | 15s | javac + java |
| Kotlin | kotlin:1.9-jre | 15s | kotlinc available |
| C++ | gcc:13 | 10s | g++ available |
| SQL | sqlite:3 | 5s | SQLite for testing |

## Security Constraints

```yaml
resources:
  cpus: 0.5
  memory: 256MB
  pids_limit: 64
  read_only_rootfs: true

network: none

security:
  no_new_privileges: true
  drop_capabilities: [ALL]
  seccomp_profile: restricted

filesystem:
  tmpfs: /tmp:size=100M
  volumes: []  # no host mounts

cleanup:
  auto_remove: true
  max_containers_per_session: 50
```

## Execution Flow

1. Generate code solution + test cases
2. Create temp directory with source files
3. Pull/create language-specific container
4. Copy source files into container
5. Execute with timeout
6. Capture stdout, stderr, exit code
7. Parse test results
8. Cleanup (auto-remove container)
9. Return structured result

## Result Schema

```json
{
  "success": true,
  "language": "python",
  "exit_code": 0,
  "stdout": "All tests passed\n...",
  "stderr": "",
  "execution_time_ms": 1523,
  "test_results": {
    "total": 5,
    "passed": 5,
    "failed": 0,
    "details": [...]
  },
  "resource_usage": {
    "cpu_time_ms": 892,
    "peak_memory_mb": 45.2
  }
}
```

## Fallback

If Docker is unavailable (development mode):
- Execute in a subprocess with resource limits via `resource` module
- Apply timeout via `signal.alarm` (Unix) or `threading.Timer`
- Log warning about reduced isolation
- Same interface, weaker guarantees
