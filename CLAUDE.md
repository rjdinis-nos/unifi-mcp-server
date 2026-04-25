# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all unit tests
pytest tests/unit/

# Run a single test file
pytest tests/unit/tools/test_backups_tools.py

# Run a single test by name
pytest tests/unit/tools/test_backups_tools.py::test_trigger_backup_success

# Run with coverage report
pytest tests/unit/ --cov=src --cov-report=term-missing

# Format code
black src/ tests/ && isort src/ tests/

# Lint
ruff check src/ tests/ --fix

# Type check
mypy src/

# Run all pre-commit checks
pre-commit run --all-files
```

## Architecture

### Tool Registration (`src/tool_registry.py`)

Tools are plain `async` functions with `settings: Settings` as their last parameter. `register_module_tools()` in `tool_registry.py` auto-discovers public async functions in a module, binds `settings` via `functools.partial`, strips it from the MCP schema, and registers each as an `@mcp.tool()`. This means adding a new tool is just writing a new `async def` in the right module — no explicit registration needed.

`src/main.py` splits tool loading based on `settings.api_type`:

- **Cloud API** (cloud-v1, cloud-ea): loads only `sites` and `site_manager` tool modules
- **Local API**: loads all ~35 tool modules

### API Client (`src/api/client.py`)

`UniFiClient` handles authentication, rate limiting, retries, and **endpoint translation**. All tools use Cloud EA endpoint format (e.g., `/ea/sites/{site_id}/devices`); the client transparently translates these to Local API paths (e.g., `/proxy/network/api/s/{site_name}/stat/device`) when `api_type=local`. The rate limiter uses a token bucket algorithm. Always use the client as an async context manager:

```python
async with UniFiClient(settings) as client:
    await client.authenticate()
    response = await client.get("/ea/sites")
```

### Models (`src/models/`)

All Pydantic models use `extra="allow"` for forward API compatibility and `populate_by_name=True`. Many fields use `AliasChoices` to handle Cloud vs. Local API field name differences. Export everything through `src/models/__init__.py`.

### Tools (`src/tools/`)

Standard tool function structure:

1. Validate inputs using helpers from `src/utils/validators.py` (e.g., `validate_site_id`, `validate_mac_address`)
2. Create client, authenticate, call API
3. Parse response into Pydantic models
4. Return `model.model_dump()`

All mutating operations must accept a `confirm: bool = False` parameter and raise `ConfirmationRequiredError` when `confirm=False`. Mutating ops should also call `log_audit()` from `src/utils/audit.py`.

### Resources (`src/resources/`)

Resource handlers (registered as `sites://`, `site-manager://health`, etc.) are class-based aggregators that batch multiple API calls. They differ from tools in that they're designed for read-only MCP resource URIs, not tool invocations.

### Exception Hierarchy (`src/utils/exceptions.py`)

```
UniFiMCPException
├── ConfigurationError
├── AuthenticationError
├── APIError (has status_code, response_data)
├── RateLimitError
├── ResourceNotFoundError
├── ValidationError
└── ConfirmationRequiredError
```

### Configuration (`src/config/config.py`)

`Settings` is a Pydantic `BaseSettings` class loaded from `.env` + environment variables. Key vars: `UNIFI_API_TYPE` (local/cloud-v1/cloud-ea), `UNIFI_API_KEY`, `UNIFI_LOCAL_HOST`. See `.env.example` for all options.

## API Modes

| Mode | `UNIFI_API_TYPE` | Scope |
|------|-----------------|-------|
| Local Gateway (recommended) | `local` | Full feature set, requires `UNIFI_LOCAL_HOST` |
| Cloud V1 | `cloud-v1` | Aggregate stats only |
| Cloud EA | `cloud-ea` | Early Access, aggregate stats only |

Integration tests require real UniFi hardware and a configured `.env` file.

## Adding a New Tool

Use the `unifi-mcp-tool-builder` skill (`/unifi-mcp-tool-builder`) for guided scaffolding. Otherwise:

1. Add an `async def your_tool(param: str, settings: Settings) -> dict` to the appropriate module in `src/tools/`
2. Add the module to `_LOCAL_TOOL_MODULES` (or `_CLOUD_TOOL_MODULES`) in `src/main.py` if it's a new file
3. Add a Pydantic model in `src/models/` if needed
4. Write unit tests with mocked `UniFiClient` in `tests/unit/tools/`
5. Update `API.md` with the new tool's docstring
