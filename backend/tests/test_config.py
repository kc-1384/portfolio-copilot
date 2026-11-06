"""Tests for application settings."""

from app.core.config import Settings


def make_settings(password: str = "secret") -> Settings:
    # _env_file=None: ignore the real .env so the test only uses the values given here.
    return Settings(
        _env_file=None,
        postgres_user="copilot",
        postgres_password=password,
        postgres_db="copilot",
    )


def test_database_url_is_built_from_parts() -> None:
    url = make_settings().database_url.render_as_string(hide_password=False)

    assert url == "postgresql+psycopg://copilot:secret@127.0.0.1:5432/copilot"


def test_special_characters_in_password_are_escaped() -> None:
    url = make_settings(password="p@ss/word").database_url.render_as_string(hide_password=False)

    # "@" becomes %40 and "/" becomes %2F, so the URL is still valid.
    assert url == "postgresql+psycopg://copilot:p%40ss%2Fword@127.0.0.1:5432/copilot"


def test_password_is_hidden_when_printed() -> None:
    settings = make_settings(password="topsecret")

    assert "topsecret" not in repr(settings)
    assert "topsecret" not in str(settings.database_url)
