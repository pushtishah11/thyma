from alembic import command
from alembic.config import Config


def test_models_and_migrations_match(alembic_config: Config) -> None:
    """Fails if a model changed without a matching migration.

    alembic check runs autogenerate against the migrated test database and
    raises if it would produce any new operations.
    """
    command.check(alembic_config)
