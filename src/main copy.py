
from fastapi import FastAPI, APIRouter, status #,Request , Depends
from fastapi.middleware.cors import CORSMiddleware
from src.db import base # هذا الاستيراد الواحد يقوم بتحميل كل نماذج قاعدة البيانات
#from src.api.v1 import dependencies
from src.api.v1.routers import (
    # users:
    users_router, auth_router, password_reset_router, user_admin_router, address_admin_router,phone_change_router,  #, admin_router
    # products
    future_offerings_router, inventory_router, products_router, orders_router,pricing_router, product_admin_router
     )

# إضافة استيراد معالج الاستثناءات العام
from src.api.exception_handlers import http_exception_handler 
from fastapi.exceptions import HTTPException # <--  (للتصريح بنوع الاستثناء الذي سيعالجه المعالج)


app = FastAPI(
    title="Mothmerah API",
    description="The backend service for the Mothmerah digital marketplace.",
    version="1.0.0",
)

# ... (باقي الملف CORS و Routers يبقى كما هو)
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]

# تسجيل معالج الاستثناءات العام
app.add_exception_handler(HTTPException, http_exception_handler) 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok", "message": "Welcome to the Mothmerah API! The journey begins."}

# --- تنظيم وتسجيل الراوترات ---
api_v1_router = APIRouter(prefix="/api/v1")

# وحدة المستخدمين
api_v1_router.include_router(users_router.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(auth_router.router, prefix="/auth", tags=["Authentication"])

# وحدة المستخدمين
api_v1_router.include_router(users_router.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(auth_router.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(password_reset_router.router, prefix="/password-reset", tags=["Password Reset"])
api_v1_router.include_router(phone_change_router.router, prefix="/users", tags=["Users - Phone Management"]) 

# ... (باقي راوترات المستخدمين)

# وحدة المنتجات
api_v1_router.include_router(products_router.router, prefix="/products", tags=["Products"])
# ... (باقي راوترات المنتجات)

# وحدة السوق والطلبات
api_v1_router.include_router(orders_router.router, prefix="/orders", tags=["Orders"])

# وحدة التسعير
api_v1_router.include_router(pricing_router.router, prefix="/pricing-rules", tags=["Pricing"])
# وحدة الالمخزون
api_v1_router.include_router(inventory_router.router, prefix="/inventory", tags=["Inventory"])
# وحدة العروض
api_v1_router.include_router(future_offerings_router.router, prefix="/expected-crops", tags=["Expected Crops"])

# --- تجميع كل راوترات الإدارة تحت مسار /admin ---
admin_base_router = APIRouter(prefix="/admin", tags=["Administration"])
admin_base_router.include_router(user_admin_router.router)
admin_base_router.include_router(product_admin_router.router)
admin_base_router.include_router(address_admin_router.router) 

# إضافة راوتر الإدارة المجمع إلى الـ API الرئيسي
api_v1_router.include_router(admin_base_router)

# تسجيل الراوتر الرئيسي V1 في التطبيق
app.include_router(api_v1_router)



