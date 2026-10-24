import os

# Point the app at the test database before any app module is imported,
# so tests can never read or write the real dev database.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://thyma:thyma@localhost:5432/thyma_test"
)
