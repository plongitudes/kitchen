"""Backup and restore API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
import subprocess
import os
from pathlib import Path
from urllib.parse import urlparse

from app.core.deps import get_current_user, get_current_user_no_db
from app.models.user import User
from app.core.config import get_settings

router = APIRouter(prefix="/backup", tags=["backup"])

BACKUP_DIR = Path("/tmp/roanes-kitchen-backups")
BACKUP_DIR.mkdir(exist_ok=True)

settings = get_settings()

# Parse database credentials from DATABASE_URL
def get_db_credentials():
    """Extract database credentials from DATABASE_URL."""
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    parsed = urlparse(db_url)
    return {
        "host": parsed.hostname or "postgres",
        "port": parsed.port or 5432,
        "user": parsed.username or "admin",
        "password": parsed.password or "admin",
        "database": parsed.path.lstrip("/") or "roanes_kitchen",
    }


@router.post("/create")
async def create_backup(
    current_user: User = Depends(get_current_user),
):
    """Create a database backup and return download link."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"roanes_kitchen_backup_{timestamp}.sql"
    filepath = BACKUP_DIR / filename

    db_creds = get_db_credentials()

    try:
        # Use pg_dump to create backup
        result = subprocess.run(
            [
                "pg_dump",
                "-h",
                db_creds["host"],
                "-U",
                db_creds["user"],
                "-d",
                db_creds["database"],
                "-f",
                str(filepath),
                "--no-owner",
                "--no-acl",
            ],
            env={**os.environ, "PGPASSWORD": db_creds["password"]},
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise Exception(f"pg_dump failed: {result.stderr}")

        return {
            "filename": filename,
            "filepath": str(filepath),
            "size": filepath.stat().st_size,
            "created_at": timestamp,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup failed: {str(e)}",
        )


@router.get("/download/{filename}")
async def download_backup(
    filename: str,
    current_user: User = Depends(get_current_user),
):
    """Download a backup file."""
    filepath = BACKUP_DIR / filename

    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found"
        )

    return FileResponse(
        path=str(filepath), filename=filename, media_type="application/sql"
    )


@router.post("/restore/{filename}")
async def restore_backup(
    filename: str,
    current_user: dict = Depends(get_current_user_no_db),
):
    """Restore database from a backup file.

    WARNING: This will drop and recreate the entire database,
    disconnecting all active connections. Users should reload the page after restore.

    Uses direct psql commands to postgres over the Docker network.
    """
    filepath = BACKUP_DIR / filename

    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found"
        )

    db_creds = get_db_credentials()

    # Environment for PostgreSQL commands
    pg_env = {**os.environ, "PGPASSWORD": db_creds["password"]}

    try:
        # Step 1: Terminate active connections
        terminate_result = subprocess.run(
            [
                "psql",
                "-h", db_creds["host"],
                "-U", db_creds["user"],
                "-d", "postgres",
                "-c",
                f"SELECT pg_terminate_backend(pg_stat_activity.pid) "
                f"FROM pg_stat_activity "
                f"WHERE pg_stat_activity.datname = '{db_creds['database']}' "
                f"AND pid <> pg_backend_pid();"
            ],
            env=pg_env,
            capture_output=True,
            text=True,
        )
        # Ignore errors here - might have no connections to terminate

        # Step 2: Drop database
        drop_result = subprocess.run(
            [
                "psql",
                "-h", db_creds["host"],
                "-U", db_creds["user"],
                "-d", "postgres",
                "-c", f"DROP DATABASE IF EXISTS {db_creds['database']};"
            ],
            env=pg_env,
            capture_output=True,
            text=True,
        )

        if drop_result.returncode != 0:
            raise Exception(f"Failed to drop database: {drop_result.stderr}")

        # Step 3: Create database
        create_result = subprocess.run(
            [
                "psql",
                "-h", db_creds["host"],
                "-U", db_creds["user"],
                "-d", "postgres",
                "-c", f"CREATE DATABASE {db_creds['database']};"
            ],
            env=pg_env,
            capture_output=True,
            text=True,
        )

        if create_result.returncode != 0:
            raise Exception(f"Failed to create database: {create_result.stderr}")

        # Step 4: Restore from backup file
        restore_result = subprocess.run(
            [
                "psql",
                "-h", db_creds["host"],
                "-U", db_creds["user"],
                "-d", db_creds["database"],
                "-f", str(filepath)
            ],
            env=pg_env,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if restore_result.returncode != 0:
            raise Exception(f"Failed to restore from backup: {restore_result.stderr}")

        # Step 5: Run migrations to bring schema up to date
        migration_result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if migration_result.returncode != 0:
            raise Exception(f"Failed to run migrations: {migration_result.stderr}")

        return {
            "message": "Database restored successfully. Please reload the page to reconnect.",
            "filename": filename,
            "reload_required": True,
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Restore operation timed out after 5 minutes",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restore failed: {str(e)}",
        )


@router.post("/upload")
async def upload_backup(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a backup file."""
    if not file.filename.endswith(".sql"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .sql files are allowed",
        )

    try:
        filepath = BACKUP_DIR / file.filename

        # Write uploaded file
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)

        return {
            "filename": file.filename,
            "size": len(content),
            "message": "Backup uploaded successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )


@router.get("/list")
async def list_backups(
    current_user: User = Depends(get_current_user),
):
    """List all available backup files."""
    backups = []

    for filepath in BACKUP_DIR.glob("*.sql"):
        stat = filepath.stat()
        backups.append(
            {
                "filename": filepath.name,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        )

    # Sort by creation time, newest first
    backups.sort(key=lambda x: x["created_at"], reverse=True)

    return backups


@router.delete("/{filename}")
async def delete_backup(
    filename: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a backup file."""
    filepath = BACKUP_DIR / filename

    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found"
        )

    try:
        filepath.unlink()
        return {"message": f"Backup {filename} deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete failed: {str(e)}",
        )
