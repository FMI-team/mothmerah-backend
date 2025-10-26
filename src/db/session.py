from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# قراءة رابط قاعدة البيانات من متغيرات البيئة
load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# دالة لتوفير جلسة قاعدة البيانات للـ Endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()