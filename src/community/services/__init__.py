# backend\src\community\services\__init__.py

# استيراد جميع دوال الخدمات من الملفات المتخصصة في هذا المجلد.
# هذا يضمن أن جميع تعريفات الخدمات يتم تحميلها.

from .reviews_service import *
from .review_responses_service import *
from .review_reports_service import *
from .review_criteria_service import *
from .review_ratings_by_criteria_service import *
from .review_statuses_service import *
from .review_report_reasons_service import *