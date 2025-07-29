# Refactoring Log: From Claude to Multi-Agent Architecture

This document outlines the key changes made to transition the Tmux Orchestrator from a Claude-centric system to a flexible, multi-agent architecture supporting Gemini and the Rovodev brand.

## 1. Project Re-branding

The primary branding was updated from "Tmux Orchestrator" and "Claude" to "Rovodev" and "Gemini".

- **`README.md`**: The main documentation was overhauled to replace all instances of "Claude" with "Gemini" and the orchestrator concept with "Rovodev". The quick start guides and examples were updated to reflect the new `gemini` command.

## 2. Core Script Refactoring

The core scripts were updated to remove hardcoded dependencies on a single AI provider.

- **`send-claude-message.sh` -> `send-gemini-message.sh`**: The primary message-sending script was renamed. Its internal logic was modified to call the `ai_provider.py` script, passing `"gemini"` as the desired provider. This abstracts the communication logic.

- **`schedule_with_note.sh`**: This script was significantly improved:
    - **Removed Hardcoded Paths**: The script no longer uses absolute paths, making it portable across different environments.
    - **Generic Status Check**: The hardcoded call to a non-existent `claude_control.py` was replaced with a call to `python3 tmux_utils.py`, which provides a generic and robust status overview of all tmux sessions and windows.

## 3. Knowledge Base Migration

The agent-specific knowledge base and instructions were migrated.

- **`CLAUDE.md` -> `GEMINI.md`**: The file containing agent behavior instructions and operational guidelines was renamed to align with the new default agent.

## 4. Architectural Shift: AI Provider Abstraction

The most significant change was the introduction of an abstraction layer for AI providers, enabling the system to support multiple agents.

- **`ai_provider.py`**: This new file acts as a central router. It receives requests from scripts like `send-gemini-message.sh` and, based on the provider name passed as an argument (e.g., "gemini"), it loads the appropriate configuration and interacts with the correct AI model.

- **`ai_config.yml`**: This configuration file stores the specific settings for each AI, such as API endpoints, model names, and keys. This allows for easy management of different AI providers without changing the core application logic.

## 5. Introduction of Unit Tests

To improve code quality and ensure the stability of the core utilities, a testing framework was introduced.

- **`tests/` directory**: A new directory was created to house all unit tests.
- **`tests/test_tmux_utils.py`**: A comprehensive test suite was created for the `TmuxOrchestrator` class in `tmux_utils.py`. This includes mocked tests for all public methods, ensuring that session and window management functions work as expected. This provides a safety net for future refactoring and development.
