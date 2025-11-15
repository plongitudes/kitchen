"""Backup and restore API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
import subprocess
import os
from pathlib import Path

from app.core.deps import get_current_user, get_current_user_no_db
from app.models.user import User

router = APIRouter(prefix="/backup", tags=["backup"])

BACKUP_DIR = Path("/tmp/roanes-kitchen-backups")
BACKUP_DIR.mkdir(exist_ok=True)


@router.post("/create")
async def create_backup(
    current_user: User = Depends(get_current_user),
):
    """Create a database backup and return download link."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"roanes_kitchen_backup_{timestamp}.sql"
    filepath = BACKUP_DIR / filename

    try:
        # Use pg_dump to create backup
        result = subprocess.run(
            [
                "pg_dump",
                "-h",
                "postgres",
                "-U",
                "admin",
                "-d",
                "roanes_kitchen",
                "-f",
                str(filepath),
                "--no-owner",
                "--no-acl",
            ],
            env={**os.environ, "PGPASSWORD": "admin"},
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

    Runs restore commands directly in the postgres container to avoid
    backend connection conflicts.
    """
    filepath = BACKUP_DIR / filename

    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found"
        )

    try:
        # Copy backup file to postgres container
        copy_result = subprocess.run(
            ["docker", "cp", str(filepath), "roanes-kitchen-postgres:/tmp/restore.sql"],
            capture_output=True,
            text=True,
        )

        if copy_result.returncode != 0:
            raise Exception(
                f"Failed to copy backup to postgres container: {copy_result.stderr}"
            )

        # Run restore commands in postgres container to avoid backend connection issues
        restore_cmd = """
        export PGPASSWORD=admin

        echo 'Step 1: Terminating connections...'
        psql -U admin -d postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'roanes_kitchen' AND pid <> pg_backend_pid();" 2>/dev/null || true

        echo 'Step 2: Dropping database...'
        psql -U admin -d postgres -c "DROP DATABASE IF EXISTS roanes_kitchen;"

        echo 'Step 3: Creating database...'
        psql -U admin -d postgres -c "CREATE DATABASE roanes_kitchen;"

        echo 'Step 4: Restoring from backup...'
        psql -U admin -d roanes_kitchen -f /tmp/restore.sql

        rm -f /tmp/restore.sql
        echo 'Restore completed!'
        """

        result = subprocess.run(
            ["docker", "exec", "roanes-kitchen-postgres", "bash", "-c", restore_cmd],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode != 0:
            error_msg = (
                f"Restore failed.\nStdout: {result.stdout}\nStderr: {result.stderr}"
            )
            raise Exception(error_msg)

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
