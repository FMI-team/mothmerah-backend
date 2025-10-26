# backend/src/users/tasks.py

from src.core.celery_app import celery
from src.db.session import SessionLocal
from src.users.crud import security_crud
from src.core.config import settings
from datetime import datetime, timedelta, timezone

# هذه هي الدالة التي سيتم تنفيذها كل ساعة.
@celery.task
def cleanup_inactive_sessions():
    """
    مهمة Celery دورية لتنظيف الجلسات غير النشطة.
    """
    db = SessionLocal()
    try:
        inactive_threshold = datetime.now(timezone.utc) - timedelta(minutes=settings.INACTIVE_SESSION_MINUTES)

        num_revoked = security_crud.revoke_inactive_sessions(
            db=db,
            inactive_before=inactive_threshold
)

        print(f"[{datetime.now(timezone.utc)}] Inactive session cleanup: Revoked {num_revoked} sessions.")
        return f"Revoked {num_revoked} sessions."
    finally:
        db.close()

