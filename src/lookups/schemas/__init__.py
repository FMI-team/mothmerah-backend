# backend\src\lookups\schemas\__init__.py

# استيراد جميع Schemas من هذا المجلد لجعلها متاحة عند استخدام 'from src.lookups.schemas import *'
# هذا يضمن أن جميع تعريفات Schemas يتم تحميلها بواسطة Pydantic و FastAPI.

from .lookups_schemas import * # هذا يستورد Schemas من ملف lookups_schemas.py (الذي يحتوي على جميع تعريفات Schemas)

# TODO: تأكد أنك تستخدم هذا الملف لتعريف Schemas Lookups العامة بدلاً من ملف آخر إذا كان لديك.
#       الاسم الافتراضي للملف الذي يحمل Schemas في هذا المجلد هو lookups_schemas.py.
#       إذا كان اسم ملف Schemas الرئيسي لديك هو lookups_schemas.py، فتأكد من أن السطر أعلاه صحيح.
#       (بناءً على الخطوة 29، قمنا بإنشاء ملف باسم lookups_schemas.py).

# استيراد Schemas من Community (المجموعة 6)
from src.community.schemas import reviews_schemas 

