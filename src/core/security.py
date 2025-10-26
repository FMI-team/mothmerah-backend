# backend/src/core/security.py
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import  jwt ,JWTError
from src.core.config import settings
from typing import Optional
import uuid  # استيراد مكتبة UUID للتعامل مع معرفات المستخدمين
from fastapi import HTTPException, status
from pydantic import BaseModel, Field, ValidationError
from passlib.context import CryptContext

# --- القسم الأول: نماذج البيانات (Schemas) للمصادقة ---

class TokenPayload(BaseModel):
    """
    نموذج Pydantic لتمثيل والتحقق من صحة البيانات (الحمولة) داخل توكن JWT.
    
    يضمن هذا النموذج أن الحمولة التي تم فك تشفيرها تحتوي على حقل 'sub'
    وأن قيمته يمكن تحويلها بشكل صحيح إلى معرف مستخدم من نوع UUID.
    """
    # نستخدم Field مع alias='sub' للربط مع الحقل القياسي في JWT
    user_id: uuid.UUID = Field(..., alias="sub")
    sid: Optional[uuid.UUID] = None # مُعرف الجلسة، اختياري ليكون متوافقًا مع كلا النوعين من التوكن

# --- القسم الثاني: إعدادات ووظائف كلمة المرور ---

# --- 1. إعداد سياق تجزئة كلمة المرور ---
# نحدد هنا أننا سنستخدم خوارزمية "bcrypt" وهي من أقوى الخوارزميات الموصى بها حاليًا.
# مكتبة passlib ستقوم تلقائيًا بإنشاء "ملح" (salt) فريد لكل كلمة مرور قبل تجزئتها،
# وهذا إجراء أمني حيوي لمنع هجمات القواميس وقوس قزح (Rainbow Table Attacks).
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- 2. وظائف تجزئة والتحقق من كلمة المرور (محسّنة) ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    تتحقق مما إذا كانت كلمة المرور النصية تتطابق مع النسخة المجزأة المخزنة.
    
    :param plain_password: كلمة المرور النصية الصريحة التي أدخلها المستخدم.
    :param hashed_password: النسخة المجزأة المخزنة في قاعدة البيانات.
    :return: True إذا تطابقت كلمات المرور، و False خلاف ذلك.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    [الاسم الأصلي محفوظ]
    تقوم بتجزئة وتمليح كلمة مرور نصية باستخدام bcrypt.

    :param password: كلمة المرور النصية الصريحة المراد تجزئتها.
    :return: سلسلة نصية تحتوي على النسخة المجزأة والمملحة لكلمة المرور.
    """
    return pwd_context.hash(password)

# --- القسم الثالث: وظائف إنشاء والتحقق من توكن JWT ---

def create_access_token(user_id: uuid.UUID, expires_delta: Optional[timedelta] = None) -> str:
    """
    إنشاء توكن وصول JWT جديد للمستخدم بشكل آمن ومحدد.

    وفقًا لمعيار RFC 7519، يتم استخدام حقل 'sub' (subject) لتعريف هوية المستخدم.

    :param user_id: المعرف الفريد للمستخدم (UUID) الذي سيتم تضمينه في التوكن.
    :param expires_delta: مدة صلاحية مخصصة للتوكن (اختياري).
    :return: توكن JWT مشفر كسلسلة نصية.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # استخدام مدة الصلاحية الافتراضية من ملف الإعدادات
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # بناء حمولة التوكن بشكل صريح باستخدام 'sub'
    to_encode = {"exp": expire, "sub": str(user_id)}
    
    # تشفير الحمولة باستخدام المفتاح السري والخوارزمية المحددة
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token (token: str) -> TokenPayload: #decode_and_validate_token(token: str) -> TokenPayload:
    """
    يفك تشفير توكن JWT المستلم، ويتحقق من صلاحيته وتوقيعه،
    ثم يتحقق من صحة هيكل حمولته باستخدام نموذج TokenPayload.

    :param token: توكن JWT كسلسلة نصية مستلمة من العميل.
    :raises HTTPException: يطلق استثناء (401 Unauthorized) في أي من الحالات التالية:
                            - التوكن تالف أو تم التلاعب به (JWTError).
                            - انتهت صلاحية التوكن.
                            - حمولة التوكن لا تتوافق مع نموذج TokenPayload (ValidationError).
    :return: حمولة التوكن التي تم التحقق من صحتها ككائن TokenPayload.
    """
    # إعداد استثناء موحد يتم إطلاقه في حالة فشل المصادقة لأي سبب
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="لا يمكن التحقق من بيانات الاعتماد، التوكن غير صالح أو منتهي الصلاحية",
        headers={"WWW-Authenticate": "Bearer"},
    )  
    try:
        # 1. محاولة فك تشفير التوكن باستخدام نفس المفتاح السري والخوارزمية
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        # 2. التحقق من صحة هيكل الحمولة باستخدام نموذج Pydantic
        # إذا كانت الحمولة لا تحتوي على حقل 'sub' أو قيمته خاطئة، سيتم إطلاق ValidationError
        token_data = TokenPayload(**payload)
        
    except (JWTError, ValidationError):
        # 3. إذا حدث أي خطأ أثناء فك التشفير أو التحقق من الهيكل، أطلق الاستثناء الموحد
        raise credentials_exception

    # 4. في حالة النجاح، أرجع البيانات التي تم التحقق منها
    return token_data

def create_refresh_token(user_id: uuid.UUID, session_id: uuid.UUID) -> str:
    """
    إنشاء Refresh Token جديد للمستخدم مرتبط بجلسة معينة.
    هذا التوكن له مدة صلاحية أطول بكثير من الـ Access Token.

    :param user_id: المعرف الفريد للمستخدم.
    :param session_id: المعرف الفريد للجلسة (من جدول user_sessions).
    :return: Refresh Token مشفر.
    """
    # مدة صلاحية طويلة للـ Refresh Token (مثلاً 7 أيام)
    # يمكن جعل هذه القيمة في ملف الإعدادات .env
    REFRESH_TOKEN_EXPIRE_DAYS = 7 
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # حمولة الـ Refresh Token تحتوي على هوية المستخدم وهوية الجلسة
    to_encode = {"exp": expire, "sub": str(user_id), "sid": str(session_id)}
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
