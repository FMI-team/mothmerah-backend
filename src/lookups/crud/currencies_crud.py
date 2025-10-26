# backend\src\lookups\crud\currencies_crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from typing import List, Optional
from datetime import datetime, timezone

# استيراد المودلز
from src.lookups.models import lookups_models as models # Currency, CurrencyTranslation
# استيراد Schemas
from src.lookups.schemas import lookups_schemas as schemas # Currency, CurrencyTranslation


# ==========================================================
# --- CRUD Functions for Currency (العملات) ---
# ==========================================================

def create_currency(db: Session, currency_in: schemas.CurrencyCreate) -> models.Currency:
    """
    ينشئ عملة جديدة في قاعدة البيانات، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        currency_in (schemas.CurrencyCreate): بيانات العملة للإنشاء.

    Returns:
        models.Currency: كائن العملة الذي تم إنشاؤه.
    """
    db_currency = models.Currency(
        currency_code=currency_in.currency_code,
        currency_name_key=currency_in.currency_name_key,
        symbol=currency_in.symbol,
        decimal_places=currency_in.decimal_places,
        is_active=currency_in.is_active
    )
    db.add(db_currency)
    db.flush() # للحصول على currency_code قبل إضافة الترجمات

    if currency_in.translations:
        for trans_in in currency_in.translations:
            db_translation = models.CurrencyTranslation(
                currency_code=db_currency.currency_code,
                language_code=trans_in.language_code,
                translated_currency_name=trans_in.translated_currency_name
            )
            db.add(db_translation)
    db.commit()
    db.refresh(db_currency)
    return db_currency

def get_currency(db: Session, currency_code: str) -> Optional[models.Currency]:
    """
    يجلب عملة واحدة بالرمز الخاص بها، مع ترجماتها.

    Args:
        db (Session): جلسة قاعدة البيانات.
        currency_code (str): رمز العملة المطلوب.

    Returns:
        Optional[models.Currency]: كائن العملة أو None.
    """
    return db.query(models.Currency).options(
        joinedload(models.Currency.translations)
    ).filter(models.Currency.currency_code == currency_code).first()

def get_currency_by_key(db: Session, key: str) -> Optional[models.Currency]:
    """جلب عملة عن طريق المفتاح النصي."""
    return db.query(models.Currency).filter(models.Currency.currency_name_key == key).first()


def get_all_currencies(db: Session, include_inactive: bool = False) -> List[models.Currency]:
    """
    يجلب قائمة بجميع العملات.

    Args:
        db (Session): جلسة قاعدة البيانات.
        include_inactive (bool): هل يجب تضمين العملات غير النشطة؟

    Returns:
        List[models.Currency]: قائمة بكائنات العملات.
    """
    query = db.query(models.Currency).options(
        joinedload(models.Currency.translations)
    )
    if not include_inactive:
        query = query.filter(models.Currency.is_active == True)
    return query.all()

def update_currency(db: Session, db_currency: models.Currency, currency_in: schemas.CurrencyUpdate) -> models.Currency:
    """
    يحدث بيانات عملة موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_currency (models.Currency): كائن العملة من قاعدة البيانات.
        currency_in (schemas.CurrencyUpdate): البيانات المراد تحديثها.

    Returns:
        models.Currency: كائن العملة المحدث.
    """
    update_data = currency_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_currency, key, value)
    db_currency.updated_at = datetime.now(timezone.utc)
    db.add(db_currency)
    db.commit()
    db.refresh(db_currency)
    return db_currency

# لا يوجد delete_currency مباشر، بل يتم إدارة الحالة عبر is_active.


# ==========================================================
# --- CRUD Functions for CurrencyTranslation (ترجمات العملات) ---
# ==========================================================

def create_currency_translation(db: Session, currency_code: str, trans_in: schemas.CurrencyTranslationCreate) -> models.CurrencyTranslation:
    """
    ينشئ ترجمة جديدة لعملة معينة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        currency_code (str): رمز العملة الأم.
        trans_in (schemas.CurrencyTranslationCreate): بيانات الترجمة للإنشاء.

    Returns:
        models.CurrencyTranslation: كائن الترجمة الذي تم إنشاؤه.
    """
    db_translation = models.CurrencyTranslation(
        currency_code=currency_code,
        language_code=trans_in.language_code,
        translated_currency_name=trans_in.translated_currency_name
    )
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def get_currency_translation(db: Session, currency_code: str, language_code: str) -> Optional[models.CurrencyTranslation]:
    """
    يجلب ترجمة عملة محددة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        currency_code (str): رمز العملة.
        language_code (str): رمز اللغة.

    Returns:
        Optional[models.CurrencyTranslation]: كائن الترجمة أو None.
    """
    return db.query(models.CurrencyTranslation).filter(
        and_(
            models.CurrencyTranslation.currency_code == currency_code,
            models.CurrencyTranslation.language_code == language_code
        )
    ).first()

def update_currency_translation(db: Session, db_translation: models.CurrencyTranslation, trans_in: schemas.CurrencyTranslationUpdate) -> models.CurrencyTranslation:
    """
    يحدث ترجمة عملة موجودة.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.CurrencyTranslation): كائن الترجمة من قاعدة البيانات.
        trans_in (schemas.CurrencyTranslationUpdate): البيانات المراد تحديثها.

    Returns:
        models.CurrencyTranslation: كائن الترجمة المحدث.
    """
    update_data = trans_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_translation, key, value)
    db_translation.updated_at = datetime.now(timezone.utc)
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    return db_translation

def delete_currency_translation(db: Session, db_translation: models.CurrencyTranslation):
    """
    يحذف ترجمة عملة معينة (حذف صارم).

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_translation (models.CurrencyTranslation): كائن الترجمة من قاعدة البيانات.
    """
    db.delete(db_translation)
    db.commit()
    return