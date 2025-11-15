"""Integration tests for database connectivity and basic operations."""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.user import User
from app.core.security import get_password_hash


@pytest.mark.integration
def test_database_connection(db_session: Session):
    """Test that database connection works."""
    # Simple query to verify connection
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.integration
def test_create_user_in_database(db_session: Session):
    """Test creating a user record in the database."""
    user = User(
        username="dbtest",
        password_hash=get_password_hash("testpass"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.username == "dbtest"
    assert user.created_at is not None


@pytest.mark.integration
def test_query_user_from_database(db_session: Session, test_user: User):
    """Test querying a user from the database."""
    queried_user = db_session.query(User).filter(User.id == test_user.id).first()

    assert queried_user is not None
    assert queried_user.id == test_user.id
    assert queried_user.username == test_user.username


@pytest.mark.integration
def test_update_user_in_database(db_session: Session, test_user: User):
    """Test updating a user record in the database."""
    new_discord_id = "987654321"
    test_user.discord_user_id = new_discord_id
    db_session.commit()
    db_session.refresh(test_user)

    assert test_user.discord_user_id == new_discord_id


@pytest.mark.integration
def test_delete_user_from_database(db_session: Session):
    """Test deleting a user from the database."""
    user = User(
        username="todelete",
        password_hash=get_password_hash("pass"),
    )
    db_session.add(user)
    db_session.commit()
    user_id = user.id

    db_session.delete(user)
    db_session.commit()

    deleted_user = db_session.query(User).filter(User.id == user_id).first()
    assert deleted_user is None


@pytest.mark.integration
def test_multiple_users(db_session: Session, test_user: User, second_test_user: User):
    """Test that multiple users can coexist in the database."""
    users = db_session.query(User).all()

    assert len(users) >= 2
    usernames = {u.username for u in users}
    assert test_user.username in usernames
    assert second_test_user.username in usernames
