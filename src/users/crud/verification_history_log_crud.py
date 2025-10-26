# backend\src\users\crud\verification_history_log_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# استيراد المودلز من Users (المجموعة 1)
from src.users.models import verification_models as models # UserVerificationHistory, ManualVerificationLog
# استيراد Schemas (إذا لزم الأمر لـ Type Hinting)
from src.users.schemas import verification_lookups_schemas as schemas # UserVerificationHistoryRead, ManualVerificationLogRead


# ==========================================================
# --- CRUD Functions for UserVerificationHistory (سجل تغييرات حالة التحقق للمستخدم) ---
#    هذا الجدول يُنشأ تلقائياً ولا يُعدّل أو يُحذف مباشرةً عبر API.
# ==========================================================

def create_user_verification_history_record(db: Session, record_data: dict) -> models.UserVerificationHistory:
    """
    ينشئ سجلاً جديداً في جدول تاريخ تغييرات حالة التحقق للمستخدم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        record_data (dict): قاموس يحتوي على بيانات السجل
                            (user_id, old/new verification status IDs, changed_by_user_id, notes).

    Returns:
        models.UserVerificationHistory: كائن سجل التاريخ الذي تم إنشاؤه.
    """
    db_record = models.UserVerificationHistory(**record_data)
    db.add(db_record)
    db.commit() # يتم الـ commit هنا لأنها عملية تسجيل مباشر في سجل تاريخي.
    db.refresh(db_record)
    return db_record

def get_user_verification_history_for_user(db: Session, user_id: UUID) -> List[models.UserVerificationHistory]:
    """
    جلب سجل تغييرات حالة التحقق لمستخدم معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم.

    Returns:
        List[models.UserVerificationHistory]: قائمة بسجلات تاريخ حالات التحقق.
    """
    return db.query(models.UserVerificationHistory).options(
        joinedload(models.UserVerificationHistory.old_user_verification_status),
        joinedload(models.UserVerificationHistory.new_user_verification_status),
        joinedload(models.UserVerificationHistory.changed_by_user)
    ).filter(models.UserVerificationHistory.user_id == user_id).order_by(models.UserVerificationHistory.created_at.desc()).all()

# لا يوجد تحديث أو حذف لـ UserVerificationHistory لأنه جدول سجلات تاريخية (immutable).


# ==========================================================
# --- CRUD Functions for ManualVerificationLog (سجل المراجعة اليدوية) ---
#    هذا الجدول يُنشأ تلقائياً ولا يُعدّل أو يُحذف مباشرةً عبر API.
# ==========================================================

def create_manual_verification_log_record(db: Session, log_data: dict) -> models.ManualVerificationLog:
    """
    ينشئ سجلاً جديداً في جدول سجل المراجعة اليدوية.

    Args:
        db (Session): جلسة قاعدة البيانات.
        log_data (dict): قاموس يحتوي على بيانات السجل
                         (reviewer_user_id, entity_type, entity_id, action_taken, notes).

    Returns:
        models.ManualVerificationLog: كائن سجل المراجعة الذي تم إنشاؤه.
    """
    db_record = models.ManualVerificationLog(**log_data)
    db.add(db_record)
    db.commit() # يتم الـ commit هنا لأنها عملية تسجيل مباشر في سجل تاريخي.
    db.refresh(db_record)
    return db_record

def get_manual_verification_log_for_entity(db: Session, entity_type: str, entity_id: int) -> List[models.ManualVerificationLog]:
    """
    جلب سجلات المراجعة اليدوية لكيان معين (مثل ترخيص أو مستخدم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        entity_type (str): نوع الكيان (مثلاً 'LICENSE', 'USER_PROFILE').
        entity_id (int): معرف الكيان.

    Returns:
        List[models.ManualVerificationLog]: قائمة بسجلات المراجعة اليدوية.
    """
    return db.query(models.ManualVerificationLog).options(
        joinedload(models.ManualVerificationLog.reviewer_user)
    ).filter(
        and_(
            models.ManualVerificationLog.entity_type == entity_type,
            models.ManualVerificationLog.entity_id == entity_id
        )
    ).order_by(models.ManualVerificationLog.created_at.desc()).all()

# لا يوجد تحديث أو حذف لـ ManualVerificationLog لأنه جدول سجلات تاريخية (immutable).