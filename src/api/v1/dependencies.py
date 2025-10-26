# backend\src\api\v1\dependencies.py
# ----------------------------------------------------------------------------------------------------
# هذا الملف يحتوي على التوابع التي تُستخدم لحماية نقاط النهاية (Endpoints) في تطبيق FastAPI.
# هو يستخدم نظام "حقن التوابع" (Dependency Injection) الخاص بـ FastAPI لضمان:
# 1. المصادقة (Authentication): التحقق من هوية المستخدم.
# 2. التفويض (Authorization): التحقق مما إذا كان المستخدم يملك الصلاحيات اللازمة للقيام بإجراء معين.
# ----------------------------------------------------------------------------------------------------

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # لجلب التوكن من ترويسة Authorization
from sqlalchemy.orm import Session # لإدارة جلسات قاعدة البيانات
from uuid import UUID # لمعرفات المستخدمين (UUIDs)
from typing import Callable, Optional, Union, List # لأنواع البيانات المعقدة

from jose import jwt, JWTError
from pydantic import ValidationError

from src.core import security # لوحدة الأمان الخاصة بنا (فك تشفير JWTs، خوارزميات التشفير)
from src.core.config import settings # لإعدادات التطبيق (مثل المفتاح السري لـ JWT)
from src.db.session import get_db # للحصول على جلسة قاعدة البيانات للوصول إلى DB
from src.users.crud import core_crud # للوصول إلى دوال CRUD للمستخدمين (مثل get_user_by_id)

# استيراد مودل User مباشرة
from src.users.models.core_models import User # <-- تم التعديل هنا: استيراد User مباشرة
# ... (بقية الاستيرادات مثل TokenData) ...
# from src.users.schemas.security_schemas import TokenData # تأكد من أن هذا موجود لديك أو قم بإنشائه
from src.users.schemas.security_schemas import TokenPayload # <-- تأكد من هذا الاستيراد: TokenPayload وليس TokenData القديم

# ----------------------------------------------------------------------------------------------------
# إعداد OAuth2PasswordBearer
# ----------------------------------------------------------------------------------------------------
# يخبر FastAPI بالبحث عن توكن OAuth2 (Bearer token) في ترويسة Authorization.
# tokenUrl تحدد نقطة نهاية تسجيل الدخول حيث يمكن للعميل الحصول على التوكن.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login") # للتوكنات المطلوبة (إلزامية)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False) # للتوكنات الاختيارية (يمكن أن تكون None)


# ----------------------------------------------------------------------------------------------------
# التابع الأول: get_current_user
# الغرض: جلب كائن المستخدم من قاعدة البيانات بناءً على Access Token.
# ----------------------------------------------------------------------------------------------------
async def get_current_user(
    db: Session = Depends(get_db), # حقن جلسة قاعدة البيانات
    token: str = Depends(oauth2_scheme) # حقن Access Token من ترويسة Authorization
) -> User:
    """
    يعتمد على Access Token (JWT) ويسترد كائن المستخدم من قاعدة البيانات.
    يتحقق من صحة التوكن، ويستخلص معرف المستخدم، ويجلب المستخدم من DB.
    """
    credentials_exception = HTTPException( # استثناء يرمى إذا كانت بيانات الاعتماد غير صالحة
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="تعذر التحقق من بيانات الاعتماد",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. فك تشفير التوكن (JWT) والتحقق من توقيعه
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # 2. استخلاص معرف المستخدم (sub) من حمولة التوكن
        user_id_from_token: Optional[str] = payload.get("sub")

        if user_id_from_token is None:
            raise credentials_exception
        
    except (JWTError, ValidationError): # نلتقط أي أخطاء متعلقة بـ JWT أو Pydantic ValidationError
        raise credentials_exception # يتم رمي استثناء بيانات الاعتماد غير الصالحة

    # 4. جلب كائن المستخدم من قاعدة البيانات باستخدام معرف المستخدم من التوكن
    user = core_crud.get_user_by_id(db, user_id=UUID(user_id_from_token)) # تحويل sub إلى UUID
    if user is None:
        # إذا تم حذف المستخدم من قاعدة البيانات بعد إصدار التوكن، يعتبر التوكن غير صالح
        raise credentials_exception 
    
    # TODO: هنا يمكن إضافة تحقق إضافي لـ JTI (معرف الجلسة) لضمان أن الجلسة لم يتم إبطالها يدوياً.
    # if token_data.sid:
    #    db_session = security_crud.get_user_session_by_id(db, session_id=UUID(token_data.sid))
    #    if not db_session or not db_session.is_active:
    #        raise credentials_exception # الجلسة غير نشطة أو ملغاة

    return user


# ----------------------------------------------------------------------------------------------------
# التابع الثاني: get_current_active_user
# الغرض: جلب كائن المستخدم الحالي والتحقق من أن حسابه نشط.
# ----------------------------------------------------------------------------------------------------
async def get_current_active_user(
    current_user: User = Depends(get_current_user) # يعتمد على التابع السابق لجلب المستخدم
) -> User:
    """
    يجلب المستخدم الحالي النشط. يمنع الوصول إذا كان الحساب غير نشط أو محذوف.
    """
    if current_user.account_status.status_name_key != "ACTIVE": # يعتمد على تحميل حالة الحساب في مودل User
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, # Forbidden (ممنوع) هو الأنسب لحساب غير نشط
            detail="الحساب غير نشط. يرجى التواصل مع فريق الدعم."
        )
    if current_user.is_deleted: # حقل الحذف الناعم في مودل User
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="الحساب محذوف ولا يمكن الوصول إليه."
        )
    return current_user


# ----------------------------------------------------------------------------------------------------
# التابع الثالث: has_permission
# الغرض: إنشاء تابع (Dependency) يمكن استخدامه في نقاط النهاية للتحقق من صلاحيات محددة.
# ----------------------------------------------------------------------------------------------------
def has_permission(permission_key: str) -> Callable:
    """
    دالة مصنع (Dependency Factory): تنشئ تابعاً لـ FastAPI يتحقق مما إذا كان المستخدم الحالي
    يمتلك الصلاحية المطلوبة (عبر RBAC)، مع إمكانية تجاوز للمسؤولين الفائقين.
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user) # يعتمد على المستخدم النشط الحالي
    ) -> User:
        # 1. التحقق من أن المستخدم لديه دور أساسي وصلاحيات محملة
        if not current_user.default_role or not current_user.default_role.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="المستخدم ليس لديه دور أساسي أو صلاحيات محددة."
            )

        # 2. البحث مباشرة في قائمة الصلاحيات الممنوحة للدور الأساسي للمستخدم
        # TODO: يمكن تحسين هذا للتحقق من جميع أدوار المستخدم (default_role + user_roles)
        has_perm = any(
            p.permission_name_key == permission_key # مقارنة مفتاح الصلاحية المطلوب
            for p in current_user.default_role.permissions # قائمة الصلاحيات للدور الافتراضي
        )

        # 3. تجاوز الصلاحية للمسؤولين الفائقين (SUPER_ADMIN)
        # TODO: يجب أن يكون مفتاح الدور "SUPER_ADMIN" معرفاً كقيمة ثابتة في مكان مركزي (مثل settings).
        #       يفترض أن SUPER_ADMIN له صلاحية عامة.
        is_super_admin = False
        if current_user.default_role.role_name_key == "SUPER_ADMIN":
            is_super_admin = True
            
        if not has_perm and not is_super_admin: # إذا لم يمتلك الصلاحية المطلوبة وليس سوبر أدمن
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"ليس لديك الصلاحية المطلوبة: '{permission_key}'"
            )

        return current_user # إعادة كائن المستخدم إذا كان يملك الصلاحية

    return permission_checker


# ----------------------------------------------------------------------------------------------------
# التابع الرابع: get_current_user_or_none
# الغرض: جلب كائن المستخدم الحالي إذا كان التوكن موجودًا وصحيحًا، وإلا إرجاع None.
# ----------------------------------------------------------------------------------------------------
async def get_current_user_or_none(
    db: Session = Depends(get_db), # حقن جلسة قاعدة البيانات
    token: Optional[str] = Depends(oauth2_scheme_optional) # توكن اختياري
) -> Optional[User]:
    """
    اعتمادية لجلب المستخدم الحالي إذا كان التوكن موجودًا وصحيحًا،
    أو إرجاع None إذا لم يكن هناك توكن.
    تُستخدم لنقاط النهاية التي يمكن الوصول إليها بمستخدم مصادق عليه أو بدون (اختياري).
    """
    if token is None: # إذا لم يتم تقديم أي توكن (أو auto_error=False)
        return None
    try:
        # هنا نستفيد من التحسينات في دالة security.decode_access_token
        payload = security.decode_access_token(token)
        user = core_crud.get_user_by_id(db, user_id=UUID(payload.get("sub"))) # user_id هو payload.sub
        if user is None: # إذا لم يتم العثور على المستخدم
            return None
        return user
    except HTTPException: # نلتقط الاستثناءات التي ترفعها دالة decode_access_token (توكن غير صالح/منتهي)
        # إذا كان التوكن موجودًا ولكنه غير صالح، نعيد None بدلاً من إيقاف الطلب
        return None
