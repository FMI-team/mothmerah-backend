# backend\src\users\models\__init__.py

# استيراد جميع ملفات المودلز الفرعية لجعلها متاحة عند استخدام 'from src.users.models import *'
# هذا يضمن أن جميع تعريفات المودلز يتم تحميلها بواسطة SQLAlchemy.

from .core_models import *
from .addresses_models import *
from .roles_models import *
from .security_models import *
from .verification_models import *

# ملاحظات:
# - يجب أن تكون هذه الاستيرادات موجودة لكي يتمكن SQLAlchemy من اكتشاف جميع الجداول.
# - تم تجنب الاستيرادات التي قد تسبب مشاكل مثل 'Table already defined'
#   (كما ناقشنا سابقًا).

# استيراد مودلات من Community (المجموعة 6)
from src.community.models import reviews_models 

# استيراد مودلات من Auditing (المجموعة 13) إذا كان هناك أي علاقات عكسية
from src.auditing.models import logs_models 
