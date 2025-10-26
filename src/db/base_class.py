# backend/src/db/base_class.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """الفئة الأساسية التي ترث منها جميع نماذج قاعدة البيانات."""
    pass