# # backend/src/products/models/__init__.py
# الخطوة 1: استيراد النماذج المرجعية التي لا تعتمد على غيرها
from .categories_models import *
from .units_models import *
from .attributes_models import *
# from .statuses_models import * # الخطوة 2: استيراد النماذج الرئيسية التي قد تعتمد على النماذج أعلاه
from .products_models import *
from .inventory_models import *

# الخطوة 3: استيراد النماذج التي لها اعتماديات واضحة على ما سبق
from .offerings_models import * 

# استيراد مودلات من Community (المجموعة 6)
from src.community.models import reviews_models 

# استيراد مودلات من Auditing (المجموعة 13) إذا كان هناك أي علاقات عكسية
from src.auditing.models import logs_models 
