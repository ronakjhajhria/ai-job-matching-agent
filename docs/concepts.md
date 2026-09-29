# Concepts

## Phase 1: Project foundation

- **FastAPI** exposes the health check as an HTTP API and generates its OpenAPI
  description from the route and response model. It is the requested API
  framework; a smaller framework such as Flask would also work, but would not
  match the planned stack.
- **Pydantic Settings** loads typed configuration from `JOBMIND_*` environment
  variables and an optional local `.env` file. Invalid values fail validation
  instead of silently becoming application state. Plain `os.environ` would
  avoid a dependency, but would require us to implement parsing and validation.
- **`create_app(settings)`** keeps application construction testable and allows
  settings to be injected without mutating process-wide environment state.
- **Standard-library logging** avoids adding a logging dependency. The current
  setup configures readable level-and-time output; centralized JSON logging is
  deferred until there is a concrete deployment need.
- **`pyproject.toml`** is the single dependency and tool-configuration source.
  A separate `requirements.txt` would duplicate that information at this stage.
- **HTTPX and FastAPI `TestClient`** exercise the route through the ASGI
  interface. This verifies response serialization and status, not deployment
  networking.

### Limitations

The health route confirms only that the application process can serve a request.
There are no external services yet, so it does not perform dependency checks.
There is no authentication, persistence, LLM integration, or production
container configuration in this phase.