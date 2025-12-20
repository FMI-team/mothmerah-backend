# backend\src\users\crud\core_crud.py

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import exists, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# استيراد المودلز من Users (المجموعة 1)
from src.users.models import core_models as models # User, UserPreference, AccountStatusHistory
from src.users.models.roles_models import Role, RolePermission, Permission
# استيراد Schemas
from src.users.schemas import core_schemas as schemas # User, UserPreference, AccountStatusHistory

# ==========================================================
# --- CRUD Functions for User (المستخدمون) ---
# ==========================================================

def get_user_by_phone_number(db: Session, phone_number: str) -> Optional[models.User]:
    """
    يبحث عن مستخدم عن طريق رقم الجوال.
    """
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """
    يبحث عن مستخدم عن طريق البريد الإلكتروني.
    """
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: UUID) -> Optional[models.User]:
    """
    يبحث عن مستخدم عن طريق الـ ID الخاص به.
    يتم تحميل بعض العلاقات الأساسية بشكل فوري لتحسين الأداء.
    """
    # Convert UUID to string for SQLite compatibility if needed
    # SQLAlchemy will handle the conversion automatically, but we ensure it's a proper UUID object
    if not isinstance(user_id, UUID):
        user_id = UUID(str(user_id))
    
    user = db.query(models.User).options(
        joinedload(models.User.account_status), # حالة الحساب
        joinedload(models.User.user_type),     # نوع المستخدم
        joinedload(models.User.default_role),  # الدور الأساسي
        joinedload(models.User.user_verification_status), # حالة التحقق
        joinedload(models.User.preferred_language) # اللغة المفضلة
        # TODO: يمكن إضافة المزيد من التحميلات الفورية حسب الحاجة (مثل Addresses, UserPreferences)
    ).filter(models.User.user_id == user_id).first()
    
    # Load permissions separately if role exists (to avoid SQLAlchemy string path issues)
    if user and user.default_role:
        # Query the role with permissions
        role_with_perms = db.query(Role).options(
            selectinload(Role.permission_associations).joinedload(RolePermission.permission)
        ).filter(Role.role_id == user.default_role.role_id).first()
        
        if role_with_perms:
            # Replace the role in user object with the one that has permissions loaded
            user.default_role = role_with_perms
    
    return user

def get_all_users(db: Session, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[models.User]:
    """
    جلب قائمة بجميع المستخدمين مع تحميل العلاقات الأساسية.
    
    Args:
        db (Session): جلسة قاعدة البيانات.
        skip (int): عدد السجلات لتخطيها (للترقيم).
        limit (int): الحد الأقصى لعدد السجلات المراد جلبها.
        include_deleted (bool): إذا كان True، يتم تضمين المستخدمين المحذوفين ناعمًا.
    
    Returns:
        List[models.User]: قائمة بجميع المستخدمين.
    """
    query = db.query(models.User).options(
        joinedload(models.User.account_status), # حالة الحساب
        joinedload(models.User.user_type),     # نوع المستخدم
        joinedload(models.User.default_role),  # الدور الأساسي
        joinedload(models.User.user_verification_status), # حالة التحقق
        joinedload(models.User.preferred_language) # اللغة المفضلة
    )
    
    if not include_deleted:
        query = query.filter(models.User.is_deleted == False)
    
    return query.offset(skip).limit(limit).all()

def create_user(db: Session, user_data: dict) -> models.User:
    """
    ينشئ سجل مستخدم جديد في قاعدة البيانات.
    يستقبل قاموسًا (dict) بالبيانات الجاهزة للحفظ.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_data (dict): قاموس يحتوي على بيانات المستخدم (بعد تجزئة كلمة المرور وتعيين IDs للحالات والأدوار).

    Returns:
        models.User: كائن المستخدم الذي تم إنشاؤه.
    """
    db_user = models.User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, db_user: models.User, user_in: schemas.UserUpdate) -> models.User:
    """
    يحدث بيانات مستخدم موجود.

    Args:
        db (Session): جلسة قاعدة البيانات.
        db_user (models.User): كائن المستخدم من قاعدة البيانات المراد تحديثه.
        user_in (schemas.UserUpdate): البيانات المراد تحديثها (الـ Schema).

    Returns:
        models.User: كائن المستخدم المحدث.
    """
    # تحويل الـ schema إلى قاموس، مع استبعاد الحقول التي لم يتم إرسالها (None أو غير محددة)
    update_data = user_in.model_dump(exclude_unset=True)
    
    # تحديث حقول كائن المستخدم بالبيانات الجديدة
    for key, value in update_data.items():
        setattr(db_user, key, value)
        
    db.add(db_user) # إضافة الكائن إلى الجلسة لتتبع التغييرات
    db.commit() # حفظ التغييرات في قاعدة البيانات
    db.refresh(db_user) # تحديث الكائن ليعكس البيانات من قاعدة البيانات
    return db_user

# لا يوجد delete_user مباشر، يتم إدارة الحالة عبر is_deleted و account_status_id في طبقة الخدمة.


# ==========================================================
# --- CRUD Functions for User Preferences (تفضيلات المستخدمين) ---
# ==========================================================

def get_user_preferences(db: Session, user_id: UUID) -> List[models.UserPreference]:
    """
    جلب كل تفضيلات مستخدم معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم.

    Returns:
        List[models.UserPreference]: قائمة بتفضيلات المستخدم.
    """
    return db.query(models.UserPreference).filter(models.UserPreference.user_id == user_id).all()

def get_user_preference_by_key(db: Session, user_id: UUID, preference_key: str) -> Optional[models.UserPreference]:
    """
    جلب تفضيل مستخدم واحد عن طريق مفتاحه.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم.
        preference_key (str): مفتاح التفضيل.

    Returns:
        Optional[models.UserPreference]: كائن التفضيل أو None.
    """
    return db.query(models.UserPreference).filter(
        and_(
            models.UserPreference.user_id == user_id,
            models.UserPreference.preference_key == preference_key
        )
    ).first()

def create_or_update_user_preference(db: Session, user_id: UUID, pref_in: schemas.UserPreferenceCreate) -> models.UserPreference:
    """
    ينشئ تفضيل جديد لمستخدم، أو يحدثه إذا كان موجودًا بالفعل.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم.
        pref_in (schemas.UserPreferenceCreate): بيانات التفضيل.

    Returns:
        models.UserPreference: كائن التفضيل الذي تم إنشاؤه/تحديثه.
    """
    # ابحث عن التفضيل أولاً
    db_pref = get_user_preference_by_key(db, user_id=user_id, preference_key=pref_in.preference_key)

    if db_pref:
        # تحديث القيمة إذا كان موجودًا
        db_pref.preference_value = pref_in.preference_value
    else:
        # إنشاء سجل جديد إذا لم يكن موجودًا
        db_pref = models.UserPreference(**pref_in.model_dump(), user_id=user_id)

    db.add(db_pref)
    db.commit()
    db.refresh(db_pref)
    return db_pref

def delete_user_preference_by_key(db: Session, user_id: UUID, preference_key: str) -> bool:
    """
    يحذف سجل تفضيل معين لمستخدم معين بناءً على المفتاح.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم.
        preference_key (str): مفتاح التفضيل.

    Returns:
        bool: True إذا تم الحذف بنجاح، و False إذا لم يتم العثور على التفضيل.
    """
    db_pref = get_user_preference_by_key(db, user_id=user_id, preference_key=preference_key)

    if db_pref:
        db.delete(db_pref)
        db.commit()
        return True
    return False


# ==========================================================
# --- CRUD Functions for Account Status History (سجل تغييرات حالة الحساب) ---
# ==========================================================

def create_account_status_history_record(db: Session, record_data: dict) -> models.AccountStatusHistory:
    """
    ينشئ سجل جديد في جدول تاريخ حالات الحساب.
    تُستخدم لتوثيق كل تغيير في حالة حساب المستخدم.

    Args:
        db (Session): جلسة قاعدة البيانات.
        record_data (dict): قاموس يحتوي على بيانات السجل (user_id, old/new status IDs, changed_by_user_id, reason).

    Returns:
        models.AccountStatusHistory: كائن سجل التاريخ الذي تم إنشاؤه.
    """
    # توليد ID يدوياً لـ SQLite (لأن SQLite لا يدعم autoincrement مع BIGINT بشكل صحيح)
    from sqlalchemy import func
    db_dialect = db.get_bind().dialect.name
    if db_dialect == 'sqlite':
        # جلب أكبر ID موجود وإضافة 1
        max_id = db.query(func.max(models.AccountStatusHistory.account_status_history_id)).scalar()
        record_data['account_status_history_id'] = (max_id or 0) + 1
    
    db_record = models.AccountStatusHistory(**record_data)
    db.add(db_record)
    db.commit() # يتم الـ commit هنا لأنها عملية تسجيل مباشر
    db.refresh(db_record)
    return db_record

def get_account_status_history_for_user(db: Session, user_id: UUID) -> List[models.AccountStatusHistory]:
    """
    جلب سجل تغييرات الحالة لمستخدم معين.

    Args:
        db (Session): جلسة قاعدة البيانات.
        user_id (UUID): معرف المستخدم.

    Returns:
        List[models.AccountStatusHistory]: قائمة بسجلات تاريخ حالات الحساب.
    """
    return db.query(models.AccountStatusHistory).filter(models.AccountStatusHistory.user_id == user_id).order_by(models.AccountStatusHistory.change_timestamp.desc()).all()

# لا يوجد تحديث أو حذف لـ AccountStatusHistory لأنه جدول سجلات تاريخية (immutable).