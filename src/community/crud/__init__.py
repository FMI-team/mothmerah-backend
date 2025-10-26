# backend\src\community\crud\__init__.py

# استيراد جميع دوال CRUD من الملفات المتخصصة في هذا المجلد.
# هذا يضمن أن جميع تعريفات CRUD يتم تحميلها.

from .reviews_crud import *
from .review_ratings_by_criteria_crud import *
from .review_responses_crud import *
from .review_reports_crud import *