# backend\migrations\env.py
import os
import sys
from logging.config import fileConfig

# استيراد مكتبة python-dotenv لقراءة ملف .env
from dotenv import load_dotenv

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- الجزء الأهم: ربط Alembic ببيئة التطبيق ---

# إضافة المسار الجذر للمشروع (مجلد /app داخل الحاوية) إلى مسارات بايثون
# هذا هو الحل لمشكلة ModuleNotFoundError، حيث يسمح لـ Alembic بالعثور على مجلد 'src'
# واستيراد النماذج منه.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# تحديد المسار إلى ملف .env الرئيسي وتحميله
# المسار يُبنى نسبةً إلى موقع هذا الملف (env.py)
# '..' تعني الرجوع خطوة للخلف (من migrations إلى backend) ثم العثور على .env
DOTENV_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(DOTENV_PATH)

# استيراد الفئة الأساسية Base التي سترث منها جميع نماذجنا
# هذا يسمح لـ Alembic باكتشاف نماذجنا
from src.db.base_class import Base

# TODO: هنا سنقوم باستيراد جميع ملفات النماذج (models) في المستقبل
# استيراد Base من مكانه الصحيح
from src.db.base_class import Base
# استيراد الملف المركزي الذي يقوم بدوره باستيراد جميع النماذج
# هذا السطر يضمن أن Alembic يرى كل شيء
from src.db import base 
# # --- التعديل هنا: إزالة استيراد src.db.base واستيراد حزم المودلز مباشرة ---
# # استيراد الملفات الرئيسية التي تحتوي على تعريفات المودلز، لتضمن أن Alembic يراها
# # هذا يحل مشكلة التعريف المزدوج لـ Base.metadata
import src.lookups.models
import src.users.models
import src.products.models
import src.market.models
import src.finance.models
import src.agreements.models
import src.guarantees.models
import src.auditing.models
import src.configuration.models
import src.communications.models
import src.reselling.models
import src.auctions.models
import src.pricing.models
import src.users.models 
import src.community.models 


# --- نهاية الجزء الهام ---


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None
# إضافة نموذج التعريف (MetaData) الخاص بنماذجنا هنا
# من أجل دعم الترحيل التلقائي "autogenerate".
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # url = config.get_main_option("sqlalchemy.url")
    url = os.getenv('DATABASE_URL')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # نقوم بتعيين رابط قاعدة البيانات من متغيرات البيئة التي تم تحميلها
    # هذا يتجاوز القيمة الموجودة في alembic.ini ويضمن استخدام الإعدادات الصحيحة
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = os.getenv('DATABASE_URL')
    connectable = engine_from_config(
        # config.get_section(config.config_ini_section, {}),
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
