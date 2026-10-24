from sqlalchemy import text

from app.deps import get_db


def test_get_db_connects_to_the_test_database() -> None:
    gen = get_db()
    session = next(gen)

    assert session.execute(text("select current_database()")).scalar_one() == "thyma_test"

    # Finishing the generator runs the cleanup that closes the session.
    gen.close()
