import pytest

from app.config import DEFAULT_DATABASE_URL, get_settings


def test_defaults_when_env_is_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ["DATABASE_URL", "UPLOAD_DIR", "LLM_PROVIDER", "READ_ONLY_DEMO"]:
        monkeypatch.delenv(name, raising=False)

    settings = get_settings()

    assert settings.database_url == DEFAULT_DATABASE_URL
    assert settings.upload_dir == "uploads"
    assert settings.llm_provider == "fake"
    assert settings.read_only_demo is False


def test_env_overrides_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://x:y@db:5432/other")
    monkeypatch.setenv("LLM_PROVIDER", "claude")

    settings = get_settings()

    assert settings.database_url == "postgresql+psycopg://x:y@db:5432/other"
    assert settings.llm_provider == "claude"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("true", True), ("TRUE", True), ("1", True), ("yes", True), ("false", False), ("0", False)],
)
def test_read_only_demo_parsing(monkeypatch: pytest.MonkeyPatch, raw: str, expected: bool) -> None:
    monkeypatch.setenv("READ_ONLY_DEMO", raw)

    assert get_settings().read_only_demo is expected
