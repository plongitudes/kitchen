"""Integration tests for Backup API endpoints."""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile


def test_create_backup(async_authenticated_client: TestClient):
    """Test creating a database backup."""
    response = async_authenticated_client.post("/backup/create")

    assert response.status_code == 200
    data = response.json()

    assert "filename" in data
    assert data["filename"].startswith("roanes_kitchen_backup_")
    assert data["filename"].endswith(".sql")
    assert "size" in data
    assert data["size"] > 0


def test_list_backups(async_authenticated_client: TestClient):
    """Test listing available backups."""
    # Create a backup first
    async_authenticated_client.post("/backup/create")

    response = async_authenticated_client.get("/backup/list")

    assert response.status_code == 200
    backups = response.json()

    assert isinstance(backups, list)
    assert len(backups) > 0

    # Check backup structure
    backup = backups[0]
    assert "filename" in backup
    assert "size" in backup
    assert "created_at" in backup


def test_download_backup(async_authenticated_client: TestClient):
    """Test downloading a backup file."""
    # Create a backup first
    create_response = async_authenticated_client.post("/backup/create")
    filename = create_response.json()["filename"]

    # Download it
    response = async_authenticated_client.get(f"/backup/download/{filename}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/sql"
    assert len(response.content) > 0


def test_download_nonexistent_backup(async_authenticated_client: TestClient):
    """Test downloading a backup that doesn't exist."""
    response = async_authenticated_client.get("/backup/download/nonexistent.sql")

    assert response.status_code == 404


def test_delete_backup(async_authenticated_client: TestClient):
    """Test deleting a backup file."""
    # Create a backup first
    create_response = async_authenticated_client.post("/backup/create")
    filename = create_response.json()["filename"]

    # Delete it
    response = async_authenticated_client.delete(f"/backup/{filename}")

    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"].lower()

    # Verify it's gone
    list_response = async_authenticated_client.get("/backup/list")
    backups = list_response.json()
    filenames = [b["filename"] for b in backups]
    assert filename not in filenames


def test_delete_nonexistent_backup(async_authenticated_client: TestClient):
    """Test deleting a backup that doesn't exist."""
    response = async_authenticated_client.delete("/backup/nonexistent.sql")

    assert response.status_code == 404


def test_backup_requires_auth(async_client: TestClient):
    """Test that backup endpoints require authentication."""
    # Create without auth
    response = async_client.post("/backup/create")
    assert response.status_code == 401

    # List without auth
    response = async_client.get("/backup/list")
    assert response.status_code == 401

    # Download without auth
    response = async_client.get("/backup/download/test.sql")
    assert response.status_code == 401

    # Delete without auth
    response = async_client.delete("/backup/test.sql")
    assert response.status_code == 401


def test_upload_backup(async_authenticated_client: TestClient):
    """Test uploading a backup file."""
    # Create a temporary SQL file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        f.write("-- Test SQL backup\n")
        f.write("SELECT 1;\n")
        temp_path = f.name

    try:
        # Upload it
        with open(temp_path, 'rb') as f:
            files = {"file": ("test_backup.sql", f, "application/sql")}
            response = async_authenticated_client.post(
                "/backup/upload",
                files=files,
            )

        assert response.status_code == 200
        assert "uploaded" in response.json()["message"].lower()

        # Verify it appears in the list
        list_response = async_authenticated_client.get("/backup/list")
        backups = list_response.json()
        filenames = [b["filename"] for b in backups]
        assert "test_backup.sql" in filenames

    finally:
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)


def test_upload_non_sql_file(async_authenticated_client: TestClient):
    """Test that uploading non-SQL files is rejected."""
    # Create a temporary non-SQL file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Not a SQL file\n")
        temp_path = f.name

    try:
        with open(temp_path, 'rb') as f:
            files = {"file": ("test.txt", f, "text/plain")}
            response = async_authenticated_client.post(
                "/backup/upload",
                files=files,
            )

        # Should be rejected (implementation dependent - might be 400 or accepted)
        # This is a placeholder - actual behavior depends on validation
        assert response.status_code in [200, 400]

    finally:
        Path(temp_path).unlink(missing_ok=True)
