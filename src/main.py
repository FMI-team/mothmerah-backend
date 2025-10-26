# backend\src\main.py

from fastapi import FastAPI, Depends, HTTPException, status,APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

# هذا الاستيراد يقوم بتحميل جميع نماذج قاعدة البيانات (المودلز)
# وهو أمر حيوي لـ SQLAlchemy لتكتشف الجداول
from src.db import base 

# استيراد الراوترات (يجب أن يتم بعد استيراد المودلز لتجنب مشاكل التحميل)
# راوترات المستخدمين (المجموعة 1)
from src.api.v1.routers import auth_router
from src.api.v1.routers import users_router
from src.api.v1.routers import phone_change_router
# TODO: إذا كان هناك راوتر password_reset_router.py منفصل

# راوترات المنتجات (المجموعة 2)
from src.api.v1.routers import products_router

# راوترات التسعير (المجموعة 3)
from src.api.v1.routers import pricing_router

# راوترات عمليات السوق (المجموعة 4)
from src.api.v1.routers import orders_router
from src.api.v1.routers import rfqs_router
from src.api.v1.routers import quotes_router
from src.api.v1.routers import shipments_router

# راوترات المزادات (المجموعة 5)
from src.api.v1.routers import auctions_router

# راوترات المراجعات والتقييمات (المجموعة 6)
# from src.api.v1.routers import community_router # <-- فيه مشاكل لم لسه ما اشتغلت عليه بسبب انشغالي باللطلب الاستدعاء الدائري


# الراوتر الإداري الشامل (يضم الراوترات الإدارية المتخصصة)
# هذا هو user_admin_router.py (أو product_admin_router.py) الذي تم تحديثه لديك             # لم اقم باكماله باقي ابني له schemas و crud لجداول العامة لجداول الحالة ودمجها مع باقي النماذج
from src.api.v1.routers import user_admin_router


# استيراد معالج الاستثناءات
from src.core.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from pydantic import ValidationError # <-- استورد ValidationError لتسجيل معالجها


# -----------------------------------------------------------------------------
# خطوة حاسمة: إعادة بناء Schemas لضمان حل المراجع الأمامية بعد تحميل جميع الوحدات
# -----------------------------------------------------------------------------
from src.core.schemas_bootstrap import rebuild_all_schemas # <-- تأكد من أن هذا الاستيراد موجود
rebuild_all_schemas() # <-- استدعاء دالة إعادة بناء Schemas هنا


app = FastAPI(
    title="Mothmerah API",
    description="The backend service for the Mothmerah digital marketplace. Provides core functionalities for user management, product catalog, dynamic pricing, market operations, and auction management.",
    version="1.0.0",
    openapi_tags=[ # تعريف ترتيب ووصف للوسوم الرئيسية في Swagger UI
        {"name": "Health Check", "description": "نقطة وصول للتحقق من حالة عمل API."},
        {"name": "Authentication", "description": "إدارة عمليات تسجيل الدخول، إنشاء الحسابات، وإدارة التوكنات."},
        {"name": "Users - Profile & Management", "description": "إدارة الملفات الشخصية للمستخدمين وعناوينهم، وتفضيلاتهم."},
        {"name": "Products & Catalog - User Facing", "description": "عرض المنتجات، الأصناف، خيارات التعبئة، والصور للمستخدمين."},
        {"name": "Pricing - Dynamic Rules Management", "description": "تطبيق قواعد التسعير الديناميكي على المنتجات."},
        {"name": "Market - Orders Management", "description": "إدارة الطلبات المباشرة، بنودها، وحالاتها للمشترين والبائعين."},
        {"name": "Market - RFQs Management", "description": "إدارة طلبات عروض الأسعار (RFQs) للمشترين والبائعين."},
        {"name": "Market - Quotes Management", "description": "إدارة عروض الأسعار (Quotes) المقدمة من البائعين للمشترين."},
        {"name": "Market - Shipments Management", "description": "إدارة وتتبع الشحنات المرتبطة بالطلبات."},
        {"name": "Auction Management - User Facing", "description": "إنشاء المزادات، المزايدة، إدارة قوائم المراقبة، والإعدادات الآلية."},
        {"name": "Admin - Core User Management", "description": "إدارة المستخدمين الأساسية (جلب، تعديل حالة، حذف)."},
        {"name": "Admin - RBAC Management", "description": "إدارة الأدوار والصلاحيات من جانب المسؤول."},
        {"name": "Admin - Address Lookups Management", "description": "إدارة الجداول المرجعية للعناوين والمواقع الجغرافية."},
        {"name": "Admin - Verification & Licenses", "description": "إدارة التراخيص وحالات التحقق من جانب المسؤول."},
        {"name": "Admin - Auction Management", "description": "إدارة المزادات، المزايدات، والتسويات من جانب المسؤول."},
        {"name": "Admin - Product Attributes", "description": "إدارة سمات المنتجات وقيمها."},
        {"name": "Admin - Product Categories", "description": "إدارة فئات المنتجات."},
        {"name": "Admin - Product Management", "description": "إدارة المنتجات وأصنافها للمسؤولين."},
        {"name": "Admin - Inventory Management", "description": "إدارة بنود المخزون وحركاته للمسؤولين."},
        {"name": "Admin - Inventory Lookups", "description": "إدارة جداول المخزون المرجعية (حالات المخزون، أنواع الحركات)."},
        {"name": "Admin - Unit of Measure Management", "description": "إدارة وحدات القياس."},
        {"name": "Admin - Future Offerings Management", "description": "إدارة العروض المستقبلية والمحاصيل المتوقعة."},
        {"name": "Admin - Market Operations General", "description": "مراجعة عامة لعمليات السوق من جانب المسؤول."},
        {"name": "Admin - General Lookup Tables", "description": "إدارة الجداول المرجعية العامة (عملات، لغات، تواريخ، أنشطة، أحداث أمان، أنواع كيانات)."},
        {"name": "Admin - Audit & Activity Logs", "description": "إدارة سجلات التدقيق والأنشطة العامة للنظام."},
        {"name": "Admin - System Settings & Configuration", "description": "إدارة إعدادات وتكوينات النظام من جانب المسؤول."},
        {"name": "Community - Reviews", "description": "إدارة المراجعات والتقييمات من جانب المستخدمين."}, 
    ]
)

# تسجيل معالجات الاستثناءات
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# إعدادات CORS (تبقى كما هي)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8080", "http://localhost:3000"], # TODO: تحديث هذا لبيئة الإنتاج
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok", "message": "Welcome to the Mothmerah API! The journey begins."}

# --- تنظيم وتسجيل الراوترات ---
# يتم تعريف api_v1_router لجميع نقاط الوصول تحت /api/v1
api_v1_router = APIRouter(prefix="/api/v1")


# ================================================================
# المجموعات الرئيسية (ترتيب هذه الاستدعاءات يؤثر على ترتيب ظهورها في Swagger UI)
# ================================================================

# --- 1. إدارة المستخدمين والهوية والوصول (المجموعة 1) ---
api_v1_router.include_router(auth_router.router)
api_v1_router.include_router(users_router.router)
api_v1_router.include_router(phone_change_router.router)
# TODO: إذا كان هناك راوتر password_reset_router.py منفصل

# --- 2. إدارة كتالوج المنتجات والمخزون الأساسي (المجموعة 2) ---
api_v1_router.include_router(products_router.router) # User-facing products

# --- 3. إدارة الأسعار الديناميكية (المجموعة 3) ---
api_v1_router.include_router(pricing_router.router) # User-facing pricing

# --- 4. إدارة عمليات السوق (المجموعة 4) ---
api_v1_router.include_router(orders_router.router)
api_v1_router.include_router(rfqs_router.router)
api_v1_router.include_router(quotes_router.router)
api_v1_router.include_router(shipments_router.router)

# --- 5. إدارة المزادات (المجموعة 5) ---
# api_v1_router.include_router(auctions_router.router) # لم اقم باكماله باقي ابني له schemas و crud لجداول العامة لجداول الحالة ودمجها مع باقي النماذج

# --- 6. إدارة المراجعات والتقييمات (المجموعة 6) ---
# api_v1_router.include_router(community_router.router)  # لم اقم باكماله باقي ابني له schemas و crud لجداول العامة لجداول الحالة ودمجها مع باقي النماذج


# ================================================================
# راوترات لوحة التحكم الإدارية (تُجمع تحت مسار /admin)
# ================================================================
admin_base_router = APIRouter(prefix="/admin")

# الراوتر الإداري الشامل الذي يضم جميع الراوترات الإدارية المتخصصة
# هذا هو user_admin_router.py (أو product_admin_router.py) الذي قمنا بتنظيفه
admin_base_router.include_router(user_admin_router.router) # يتضمن الآن جميع الراوترات الإدارية المتخصصة


# تسجيل الراوتر الرئيسي V1 في التطبيق
app.include_router(api_v1_router) # يضم كل الراوترات العادية
app.include_router(admin_base_router) # يضم كل الراوترات الإدارية (تحت /api/v1/admin)
