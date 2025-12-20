import logging
from sqlalchemy.orm import Session
from src.db.session import SessionLocal
from src.db import base  # نستورد هذا الملف المركزي لضمان رؤية كل النماذج

# # استيراد الخدمات والـ Schemas
from src.users.schemas import core_schemas
from src.users.crud import core_crud
from src.users.services import core_service
from src.lookups.models.lookups_models import *
from src.auctions.models import AuctionSettlementStatus, AuctionSettlementStatusTranslation
from src.users.models import *
from src.communications.models import *
from src.products.models import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_main_table(db: Session, model, pk_name: str, data_list: list[dict]):
    """دالة مساعدة لبذر الجداول المرجعية الرئيسية."""
    model_name = model.__tablename__
    count = 0
    for data in data_list:
        if not db.query(model).filter(getattr(model, pk_name) == data[pk_name]).first():
            db.add(model(**data))
            count += 1
    if count > 0:
        logger.info(f"Seeded {count} new records into {model_name}")

def seed_translation_table(db: Session, model, fk_name: str, data_list: list[dict]):
    """دالة مساعدة لبذر جداول الترجمة."""
    model_name = model.__tablename__
    count = 0
    for data in data_list:
        if not db.query(model).filter_by(language_code=data['language_code'], **{fk_name: data[fk_name]}).first():
            db.add(model(**data))
            count += 1
    if count > 0:
        logger.info(f"Seeded {count} new records into {model_name}")

def seed_all(db: Session):
    logger.info("--- Starting Comprehensive Database Seeding ---")

    # ================================================================
    # --- الفئة 0: البيانات الأساسية جداً
    # ================================================================

    LANGUAGES = [
        {"language_code": "ar", "language_name_native": "العربية", "language_name_en": "Arabic", "text_direction": "RTL", "is_active_for_interface": True, "sort_order": 1},
        {"language_code": "en", "language_name_native": "English", "language_name_en": "English", "text_direction": "LTR", "is_active_for_interface": True, "sort_order": 2},
        {"language_code": "bn", "language_name_native": "বাংলা", "language_name_en": "Bengali", "text_direction": "LTR", "is_active_for_interface": True, "sort_order": 3},
        {"language_code": "hi", "language_name_native": "हिन्दी", "language_name_en": "Hindi", "text_direction": "LTR", "is_active_for_interface": True, "sort_order": 4},
        {"language_code": "ur", "language_name_native": "اردو", "language_name_en": "Urdu", "text_direction": "RTL", "is_active_for_interface": True, "sort_order": 5},
        {"language_code": "fr", "language_name_native": "Français", "language_name_en": "French", "text_direction": "LTR", "is_active_for_interface": True, "sort_order": 6},
    ]
    seed_main_table(db, Language, "language_code", LANGUAGES)

    ROLES = [
        {"role_id": 1, "role_name_key": "BASE_USER"}, 
        {"role_id": 2, "role_name_key": "ADMIN"}, 
        {"role_id": 3, "role_name_key": "WHOLESALER"},
        {"role_id": 4, "role_name_key": "PRODUCING_FAMILY"},
        {"role_id": 5, "role_name_key": "COMMERCIAL_BUYER"},
        {"role_id": 6, "role_name_key": "RESELLER"},
        {"role_id": 7, "role_name_key": "FARMER"},
        ]
    seed_main_table(db, Role, "role_id", ROLES)


    db.commit()

    # ================================================================
    # --- الفئة 1: جداول الحالات (Status Tables) وترجماتها
    # ================================================================
    logger.info("Seeding Status Tables...")

    USER_TYPES = [   # لا بد ان تكون مثل roles
        {"user_type_id": 1, "user_type_name_key": "BASE_USER"},
        {"user_type_id": 2, "user_type_name_key": "ADMIN"},
        {"user_type_id": 3, "user_type_name_key": "WHOLESALER"},
        {"user_type_id": 4, "user_type_name_key": "PRODUCING_FAMILY"},
        {"user_type_id": 5, "user_type_name_key": "COMMERCIAL_BUYER"},
        {"user_type_id": 6, "user_type_name_key": "RESELLER"},
        {"user_type_id": 7, "user_type_name_key": "FARMER"},
    ]
    seed_main_table(db, UserType, "user_type_id",USER_TYPES)
    seed_translation_table(db, UserTypeTranslation, "user_type_id", [
        # BASE_USER (ID: 1)
        {"user_type_id": 1, "language_code": "ar", "translated_user_type_name": "مستخدم أساسي", "translated_description": "مستخدم عادي بصلاحيات أساسية."},
        {"user_type_id": 1, "language_code": "en", "translated_user_type_name": "Base User", "translated_description": "A standard user with basic permissions."},
        {"user_type_id": 1, "language_code": "fr", "translated_user_type_name": "Utilisateur de base", "translated_description": "Un utilisateur standard avec des autorisations de base."},
        {"user_type_id": 1, "language_code": "ur", "translated_user_type_name": "بنیادی صارف", "translated_description": "بنیادی اجازتوں کے ساتھ ایک معیاری صارف۔"},
        {"user_type_id": 1, "language_code": "hi", "translated_user_type_name": "मूल उपयोगकर्ता", "translated_description": "बुनियादी अनुमतियों वाला एक मानक उपयोगकर्ता।"},
        {"user_type_id": 1, "language_code": "bn", "translated_user_type_name": "বেস ব্যবহারকারী", "translated_description": "মৌলিক অনুমতি সহ একজন সাধারণ ব্যবহারকারী।"},
        # ADMIN (ID: 2)
        {"user_type_id": 2,"language_code": "ar", "translated_user_type_name":"مسؤول","translated_description": "مستخدم يمتلك صلاحيات وصول وتحكم كاملة في النظام." },
        {"user_type_id": 2,"language_code": "en", "translated_user_type_name":"Administrator","translated_description": "A user with full access and control privileges over the system."},
        {"user_type_id": 2,"language_code": "fr","translated_user_type_name": "Administrateur","translated_description": "Un utilisateur avec des privilèges d'accès et de contrôle complets sur le système."    },
        {"user_type_id": 2,"language_code": "ur","translated_user_type_name": "منتظم","translated_description": "ایک صارف جسے سسٹم پر مکمل رسائی اور کنٹرول کے اختیارات حاصل ہیں۔"},
        {"user_type_id": 2,"language_code": "hi","translated_user_type_name": "प्रशासक","translated_description": "एक उपयोगकर्ता जिसके पास सिस्टम पर पूर्ण पहुंच और नियंत्रण के विशेषाधिकार हैं।"},
        {"user_type_id": 2,"language_code": "bn","translated_user_type_name": "প্রশাসক","translated_description": "একজন ব্যবহারকারী যার সিস্টেমের উপর সম্পূর্ণ অ্যাক্সেস এবং নিয়ন্ত্রণের বিশেষাধিকার রয়েছে।"},
        # WHOLESALER (ID: 3)
        {"user_type_id": 3, "language_code": "ar", "translated_user_type_name": "تاجر جملة", "translated_description": "مستخدم يشتري المنتجات بكميات كبيرة لإعادة بيعها."},
        {"user_type_id": 3, "language_code": "en", "translated_user_type_name": "Wholesaler", "translated_description": "A user who buys products in bulk for resale."},
        {"user_type_id": 3, "language_code": "fr", "translated_user_type_name": "Grossiste", "translated_description": "Un utilisateur qui achète des produits en gros pour les revendre."},
        {"user_type_id": 3, "language_code": "ur", "translated_user_type_name": "تھوک فروش", "translated_description": "ایک صارف جو دوبارہ فروخت کے لیے بڑی تعداد میں مصنوعات خریدتا ہے۔"},
        {"user_type_id": 3, "language_code": "hi", "translated_user_type_name": "थोक विक्रेता", "translated_description": "एक उपयोगकर्ता जो पुनर्विक्रय के लिए थोक में उत्पाद खरीदता है।"},
        {"user_type_id": 3, "language_code": "bn", "translated_user_type_name": "পাইকার", "translated_description": "একজন ব্যবহারকারী যিনি পুনঃবিক্রয়ের জন্য প্রচুর পরিমাণে পণ্য ক্রয় করেন।"},
        # PRODUCING_FAMILY (ID: 4)
        {"user_type_id": 4, "language_code": "ar", "translated_user_type_name": "أسرة منتجة", "translated_description": "أسرة تقوم بإنتاج سلع أو حرف يدوية من المنزل."},
        {"user_type_id": 4, "language_code": "en", "translated_user_type_name": "Producing Family", "translated_description": "A family that produces goods or crafts from home."},
        {"user_type_id": 4, "language_code": "fr", "translated_user_type_name": "Famille productrice", "translated_description": "Une famille qui produit des biens ou de l'artisanat à domicile."},
        {"user_type_id": 4, "language_code": "ur", "translated_user_type_name": "پیداواری خاندان", "translated_description": "ایک خاندان جو گھر سے سامان یا دستکاری تیار کرتا ہے۔"},
        {"user_type_id": 4, "language_code": "hi", "translated_user_type_name": "उत्पादक परिवार", "translated_description": "एक परिवार जो घर से सामान या शिल्प का उत्पादन करता है।"},
        {"user_type_id": 4, "language_code": "bn", "translated_user_type_name": "উৎপাদক পরিবার", "translated_description": "একটি পরিবার যারা বাড়ি থেকে পণ্য বা কারুশিল্প তৈরি করে।"},
        # COMMERCIAL_BUYER (ID: 5)
        {"user_type_id": 5, "language_code": "ar", "translated_user_type_name": "مشترٍ تجاري", "translated_description": "شركة أو مؤسسة تجارية تقوم بشراء السلع."},
        {"user_type_id": 5, "language_code": "en", "translated_user_type_name": "Commercial Buyer", "translated_description": "A business or company that purchases goods."},
        {"user_type_id": 5, "language_code": "fr", "translated_user_type_name": "Acheteur commercial", "translated_description": "Une entreprise ou une société qui achète des marchandises."},
        {"user_type_id": 5, "language_code": "ur", "translated_user_type_name": "تجارتی خریدار", "translated_description": "ایک کاروبار یا کمپنی جو سامان خریدتی ہے۔"},
        {"user_type_id": 5, "language_code": "hi", "translated_user_type_name": "वाणिज्यिक खरीदार", "translated_description": "एक व्यवसाय या कंपनी जो सामान खरीदती है।"},
        {"user_type_id": 5, "language_code": "bn", "translated_user_type_name": "বাণিজ্যিক ক্রেতা", "translated_description": "একটি ব্যবসা বা কোম্পানি যা পণ্য ক্রয় করে।"},
        # RESELLER (ID: 6)
        {"user_type_id": 6, "language_code": "ar", "translated_user_type_name": "موزع", "translated_description": "مستخدم يشتري المنتجات لبيعها لعملاء آخرين."},
        {"user_type_id": 6, "language_code": "en", "translated_user_type_name": "Reseller", "translated_description": "A user who buys products to sell them to other customers."},
        {"user_type_id": 6, "language_code": "fr", "translated_user_type_name": "Revendeur", "translated_description": "Un utilisateur qui achète des produits pour les vendre à d'autres clients."},
        {"user_type_id": 6, "language_code": "ur", "translated_user_type_name": "دوبارہ فروخت کنندہ", "translated_description": "ایک صارف جو دوسرے صارفین کو فروخت کرنے کے لیے مصنوعات خریدتا ہے۔"},
        {"user_type_id": 6, "language_code": "hi", "translated_user_type_name": "पुनर्विक्रेता", "translated_description": "एक उपयोगकर्ता जो अन्य ग्राहकों को बेचने के लिए उत्पाद खरीदता है।"},
        {"user_type_id": 6, "language_code": "bn", "translated_user_type_name": "পুনঃবিক্রেতা", "translated_description": "একজন ব্যবহারকারী যিনি অন্য গ্রাহকদের কাছে বিক্রি করার জন্য পণ্য ক্রয় করেন।"}
    ])

     # 1. حالات الطلبات
    order_statuses = [{"order_status_id": i + 1, "status_name_key": k} for i, k in enumerate(["PENDING", "CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED", "REFUNDED"])]
    seed_main_table(db, OrderStatus,"order_status_id", order_statuses)
    seed_translation_table(db, OrderStatusTranslation,"order_status_id", [
        # PENDING
        {"order_status_id": 1, "language_code": "ar", "translated_status_name": "قيد الانتظار"}, 
        {"order_status_id": 1, "language_code": "en", "translated_status_name": "Pending"},
        {"order_status_id": 1, "language_code": "fr", "translated_status_name": "En attente"},
        {"order_status_id": 1, "language_code": "ur", "translated_status_name": "زیر التواء"},
        {"order_status_id": 1, "language_code": "hi", "translated_status_name": "लंबित"},
        {"order_status_id": 1, "language_code": "bn", "translated_status_name": "অপেক্ষমাণ"},
        # CONFIRMED
        {"order_status_id": 2, "language_code": "ar", "translated_status_name": "مؤكد"}, 
        {"order_status_id": 2, "language_code": "en", "translated_status_name": "Confirmed"},
        {"order_status_id": 2, "language_code": "fr", "translated_status_name": "Confirmé"},
        {"order_status_id": 2, "language_code": "ur", "translated_status_name": "تصدیق شدہ"},
        {"order_status_id": 2, "language_code": "hi", "translated_status_name": "पुष्टि की गई"},
        {"order_status_id": 2, "language_code": "bn", "translated_status_name": "নিশ্চিত"},
        # PROCESSING
        {"order_status_id": 3, "language_code": "ar", "translated_status_name": "قيد التجهيز"}, 
        {"order_status_id": 3, "language_code": "en", "translated_status_name": "Processing"},
        {"order_status_id": 3, "language_code": "fr", "translated_status_name": "En cours de traitement"},
        {"order_status_id": 3, "language_code": "ur", "translated_status_name": "زیر عمل"},
        {"order_status_id": 3, "language_code": "hi", "translated_status_name": "प्रसंस्करण"},
        {"order_status_id": 3, "language_code": "bn", "translated_status_name": "প্রসেসিং"},
        # SHIPPED
        {"order_status_id": 4, "language_code": "ar", "translated_status_name": "تم الشحن"}, 
        {"order_status_id": 4, "language_code": "en", "translated_status_name": "Shipped"},
        {"order_status_id": 4, "language_code": "fr", "translated_status_name": "Expédié"},
        {"order_status_id": 4, "language_code": "ur", "translated_status_name": "بھیج دیا گیا"},
        {"order_status_id": 4, "language_code": "hi", "translated_status_name": "भेज दिया गया"},
        {"order_status_id": 4, "language_code": "bn", "translated_status_name": "পাঠানো হয়েছে"},
        # DELIVERED
        {"order_status_id": 5, "language_code": "ar", "translated_status_name": "تم التوصيل"}, 
        {"order_status_id": 5, "language_code": "en", "translated_status_name": "Delivered"},
        {"order_status_id": 5, "language_code": "fr", "translated_status_name": "Livré"},
        {"order_status_id": 5, "language_code": "ur", "translated_status_name": "پہنچا دیا گیا"},
        {"order_status_id": 5, "language_code": "hi", "translated_status_name": "पहुंचा दिया गया"},
        {"order_status_id": 5, "language_code": "bn", "translated_status_name": "ডেলিভারি হয়েছে"},
        # CANCELLED
        {"order_status_id": 6, "language_code": "ar", "translated_status_name": "ملغى"}, 
        {"order_status_id": 6, "language_code": "en", "translated_status_name": "Cancelled"},
        {"order_status_id": 6, "language_code": "fr", "translated_status_name": "Annulé"},
        {"order_status_id": 6, "language_code": "ur", "translated_status_name": "منسوخ"},
        {"order_status_id": 6, "language_code": "hi", "translated_status_name": "रद्द"},
        {"order_status_id": 6, "language_code": "bn", "translated_status_name": "বাতিল"},
        # REFUNDED
        {"order_status_id": 7, "language_code": "ar", "translated_status_name": "مسترد"}, 
        {"order_status_id": 7, "language_code": "en", "translated_status_name": "Refunded"},
        {"order_status_id": 7, "language_code": "fr", "translated_status_name": "Remboursé"},
        {"order_status_id": 7, "language_code": "ur", "translated_status_name": "رقم واپس"},
        {"order_status_id": 7, "language_code": "hi", "translated_status_name": "धनवापसी"},
        {"order_status_id": 7, "language_code": "bn", "translated_status_name": "ফেরত দেওয়া হয়েছে"},
    ])

    # 2. حالات RFQ
    rfq_statuses = [{"rfq_status_id": i + 1, "status_name_key": k} for i, k in enumerate(["OPEN", "CLOSED", "CANCELLED"])]
    seed_main_table(db, RfqStatus, "rfq_status_id", rfq_statuses)
    seed_translation_table(db, RfqStatusTranslation, "rfq_status_id", [
        {"rfq_status_id": 1, "language_code": "ar", "translated_status_name": "مفتوح"},
        {"rfq_status_id": 1, "language_code": "en", "translated_status_name": "Open"},
        {"rfq_status_id": 1, "language_code": "fr", "translated_status_name": "Ouvert"},
        {"rfq_status_id": 1, "language_code": "ur", "translated_status_name": "کھلا"},
        {"rfq_status_id": 1, "language_code": "hi", "translated_status_name": "खुला"},
        {"rfq_status_id": 1, "language_code": "bn", "translated_status_name": "খোলা"},
        
        {"rfq_status_id": 2, "language_code": "ar", "translated_status_name": "مغلق"},
        {"rfq_status_id": 2, "language_code": "en", "translated_status_name": "Closed"},
        {"rfq_status_id": 2, "language_code": "fr", "translated_status_name": "Fermé"},
        {"rfq_status_id": 2, "language_code": "ur", "translated_status_name": "بند"},
        {"rfq_status_id": 2, "language_code": "hi", "translated_status_name": "बंद"},
        {"rfq_status_id": 2, "language_code": "bn", "translated_status_name": "বন্ধ"},

        {"rfq_status_id": 3, "language_code": "ar", "translated_status_name": "ملغى"},
        {"rfq_status_id": 3, "language_code": "en", "translated_status_name": "Cancelled"},
        {"rfq_status_id": 3, "language_code": "fr", "translated_status_name": "Annulé"},
        {"rfq_status_id": 3, "language_code": "ur", "translated_status_name": "منسوخ"},
        {"rfq_status_id": 3, "language_code": "hi", "translated_status_name": "रद्द"},
        {"rfq_status_id": 3, "language_code": "bn", "translated_status_name": "বাতিল"},
    ])

    # 3. حالات عروض الأسعار
    quote_statuses = [{"quote_status_id": i + 1, "status_name_key": k} for i, k in enumerate(["SUBMITTED", "ACCEPTED", "REJECTED", "EXPIRED"])]
    seed_main_table(db, QuoteStatus, "quote_status_id", quote_statuses)
    seed_translation_table(db, QuoteStatusTranslation, "quote_status_id", [
        {"quote_status_id": 1, "language_code": "ar", "translated_status_name": "تم التقديم"},
        {"quote_status_id": 1, "language_code": "en", "translated_status_name": "Submitted"},
        {"quote_status_id": 1, "language_code": "fr", "translated_status_name": "Soumis"},
        {"quote_status_id": 1, "language_code": "ur", "translated_status_name": "جمع کرایا گیا"},
        {"quote_status_id": 1, "language_code": "hi", "translated_status_name": "प्रस्तुत"},
        {"quote_status_id": 1, "language_code": "bn", "translated_status_name": "জমা দেওয়া হয়েছে"},

        {"quote_status_id": 2, "language_code": "ar", "translated_status_name": "مقبول"},
        {"quote_status_id": 2, "language_code": "en", "translated_status_name": "Accepted"},
        {"quote_status_id": 2, "language_code": "fr", "translated_status_name": "Accepté"},
        {"quote_status_id": 2, "language_code": "ur", "translated_status_name": "قبول کر لیا"},
        {"quote_status_id": 2, "language_code": "hi", "translated_status_name": "स्वीकृत"},
        {"quote_status_id": 2, "language_code": "bn", "translated_status_name": "গৃহীত"},

        {"quote_status_id": 3, "language_code": "ar", "translated_status_name": "مرفوض"},
        {"quote_status_id": 3, "language_code": "en", "translated_status_name": "Rejected"},
        {"quote_status_id": 3, "language_code": "fr", "translated_status_name": "Rejeté"},
        {"quote_status_id": 3, "language_code": "ur", "translated_status_name": "مسترد"},
        {"quote_status_id": 3, "language_code": "hi", "translated_status_name": "अस्वीकृत"},
        {"quote_status_id": 3, "language_code": "bn", "translated_status_name": "প্রত্যাখ্যাত"},

        {"quote_status_id": 4, "language_code": "ar", "translated_status_name": "منتهي الصلاحية"},
        {"quote_status_id": 4, "language_code": "en", "translated_status_name": "Expired"},
        {"quote_status_id": 4, "language_code": "fr", "translated_status_name": "Expiré"},
        {"quote_status_id": 4, "language_code": "ur", "translated_status_name": "میعاد ختم"},
        {"quote_status_id": 4, "language_code": "hi", "translated_status_name": "समय सीमा समाप्त"},
        {"quote_status_id": 4, "language_code": "bn", "translated_status_name": "মেয়াদোত্তীর্ণ"},
    ])
    
    # 4. حالات الشحنات
    shipment_statuses = [{"shipment_status_id": i + 1, "status_name_key": k} for i, k in enumerate(["PENDING", "IN_TRANSIT", "DELIVERED", "FAILED"])]
    seed_main_table(db, ShipmentStatus, "shipment_status_id", shipment_statuses)
    seed_translation_table(db, ShipmentStatusTranslation, "shipment_status_id",[
        {"shipment_status_id": 1, "language_code": "ar", "translated_status_name": "قيد التجهيز"}, 
        {"shipment_status_id": 1, "language_code": "en", "translated_status_name": "Pending"},
        {"shipment_status_id": 1, "language_code": "fr", "translated_status_name": "En attente"},
        {"shipment_status_id": 1, "language_code": "ur", "translated_status_name": "زیر التواء"},
        {"shipment_status_id": 1, "language_code": "hi", "translated_status_name": "लंबित"},
        {"shipment_status_id": 1, "language_code": "bn", "translated_status_name": "অপেক্ষমাণ"},

        {"shipment_status_id": 2, "language_code": "ar", "translated_status_name": "في الطريق"}, 
        {"shipment_status_id": 2, "language_code": "en", "translated_status_name": "In Transit"},
        {"shipment_status_id": 2, "language_code": "fr", "translated_status_name": "En transit"},
        {"shipment_status_id": 2, "language_code": "ur", "translated_status_name": "راستے میں"},
        {"shipment_status_id": 2, "language_code": "hi", "translated_status_name": "पारगमन में"},
        {"shipment_status_id": 2, "language_code": "bn", "translated_status_name": "ট্রানজিটে"},

        {"shipment_status_id": 3, "language_code": "ar", "translated_status_name": "تم التوصيل"}, 
        {"shipment_status_id": 3, "language_code": "en", "translated_status_name": "Delivered"},
        {"shipment_status_id": 3, "language_code": "fr", "translated_status_name": "Livré"},
        {"shipment_status_id": 3, "language_code": "ur", "translated_status_name": "پہنچا دیا گیا"},
        {"shipment_status_id": 3, "language_code": "hi", "translated_status_name": "पहुंचा दिया गया"},
        {"shipment_status_id": 3, "language_code": "bn", "translated_status_name": "ডেলিভারি হয়েছে"},

        {"shipment_status_id": 4, "language_code": "ar", "translated_status_name": "فشل التوصيل"}, 
        {"shipment_status_id": 4, "language_code": "en", "translated_status_name": "Failed"},
        {"shipment_status_id": 4, "language_code": "fr", "translated_status_name": "Échec de la livraison"},
        {"shipment_status_id": 4, "language_code": "ur", "translated_status_name": "ڈیلیوری ناکام"},
        {"shipment_status_id": 4, "language_code": "hi", "translated_status_name": "वितरण विफल"},
        {"shipment_status_id": 4, "language_code": "bn", "translated_status_name": "ডেলিভারি ব্যর্থ হয়েছে"},
    ])

    # 5. حالات المزادات
    auction_statuses = [{"auction_status_id": i + 1, "status_name_key": k} for i, k in enumerate(["UPCOMING", "ACTIVE", "CLOSED", "CANCELLED"])]
    seed_main_table(db, AuctionStatus, "auction_status_id", auction_statuses)
    seed_translation_table(db, AuctionStatusTranslation, "auction_status_id",  [
        # UPCOMING
        {"auction_status_id": 1, "language_code": "ar", "translated_status_name": "قادم", "translated_description": "المزاد مجدول ولم يبدأ بعد."},
        {"auction_status_id": 1, "language_code": "en", "translated_status_name": "Upcoming", "translated_description": "The auction is scheduled and has not started yet."},
        {"auction_status_id": 1, "language_code": "fr", "translated_status_name": "À venir", "translated_description": "L'enchère est programmée et n'a pas encore commencé."},
        {"auction_status_id": 1, "language_code": "ur", "translated_status_name": "آنے والا", "translated_description": "نیلامی طے شدہ ہے اور ابھی شروع نہیں ہوئی ہے۔"},
        {"auction_status_id": 1, "language_code": "hi", "translated_status_name": "आगामी", "translated_description": "नीलामी निर्धारित है और अभी शुरू नहीं हुई है।"},
        {"auction_status_id": 1, "language_code": "bn", "translated_status_name": "আসন্ন", "translated_description": "নিলামটি নির্ধারিত এবং এখনও শুরু হয়নি।"},
        # ACTIVE
        {"auction_status_id": 2, "language_code": "ar", "translated_status_name": "نشط", "translated_description": "المزاد مفتوح حاليًا ويقبل المزايدات."},
        {"auction_status_id": 2, "language_code": "en", "translated_status_name": "Active", "translated_description": "The auction is currently open and accepting bids."},
        {"auction_status_id": 2, "language_code": "fr", "translated_status_name": "Actif", "translated_description": "L'enchère est actuellement ouverte et accepte les offres."},
        {"auction_status_id": 2, "language_code": "ur", "translated_status_name": "فعال", "translated_description": "نیلامی فی الحال کھلی ہے اور بولیاں قبول کر رہی ہے۔"},
        {"auction_status_id": 2, "language_code": "hi", "translated_status_name": "सक्रिय", "translated_description": "नीलामी वर्तमान में खुली है और बोलियाँ स्वीकार कर रही है।"},
        {"auction_status_id": 2, "language_code": "bn", "translated_status_name": "সক্রিয়", "translated_description": "নিলামটি বর্তমানে খোলা এবং বিড গ্রহণ করছে।"},
        # CLOSED
        {"auction_status_id": 3, "language_code": "ar", "translated_status_name": "مغلق", "translated_description": "انتهى وقت المزاد ولم يعد يقبل مزايدات جديدة."},
        {"auction_status_id": 3, "language_code": "en", "translated_status_name": "Closed", "translated_description": "The auction time has ended and is no longer accepting new bids."},
        {"auction_status_id": 3, "language_code": "fr", "translated_status_name": "Fermé", "translated_description": "Le temps de l'enchère est terminé et n'accepte plus de nouvelles offres."},
        {"auction_status_id": 3, "language_code": "ur", "translated_status_name": "بند", "translated_description": "نیلامی کا وقت ختم ہو گیا ہے اور اب نئی بولیاں قبول نہیں کی جا رہی ہیں۔"},
        {"auction_status_id": 3, "language_code": "hi", "translated_status_name": "बंद", "translated_description": "नीलामी का समय समाप्त हो गया है और अब नई बोलियाँ स्वीकार नहीं की जा रही हैं।"},
        {"auction_status_id": 3, "language_code": "bn", "translated_status_name": "বন্ধ", "translated_description": "নিলামের সময় শেষ হয়ে গেছে এবং নতুন বিড আর গ্রহণ করা হচ্ছে না।"},
        # CANCELLED
        {"auction_status_id": 4, "language_code": "ar", "translated_status_name": "ملغى", "translated_description": "تم إلغاء المزاد من قبل البائع أو المسؤول."},
        {"auction_status_id": 4, "language_code": "en", "translated_status_name": "Cancelled", "translated_description": "The auction was cancelled by the seller or an admin."},
        {"auction_status_id": 4, "language_code": "fr", "translated_status_name": "Annulé", "translated_description": "L'enchère a été annulée par le vendeur ou un administrateur."},
        {"auction_status_id": 4, "language_code": "ur", "translated_status_name": "منسوخ", "translated_description": "نیلامی بیچنے والے یا منتظم کی طرف سے منسوخ کر دی گئی تھی۔"},
        {"auction_status_id": 4, "language_code": "hi", "translated_status_name": "रद्द", "translated_description": "नीलामी विक्रेता या व्यवस्थापक द्वारा रद्द कर दी गई थी।"},
        {"auction_status_id": 4, "language_code": "bn", "translated_status_name": "বাতিল", "translated_description": "নিলামটি বিক্রেতা বা প্রশাসক দ্বারা বাতিল করা হয়েছে।"},
    ]
    )

    # 6. حالات تسوية المزادات
    auction_settlement_statuses = [{"settlement_status_id": i + 1, "status_name_key": k} for i, k in enumerate(["PENDING_PAYMENT", "PAID", "SETTLED"])]
    seed_main_table(db, AuctionSettlementStatus, "settlement_status_id", auction_settlement_statuses)
    seed_translation_table(db, AuctionSettlementStatusTranslation,"settlement_status_id",  [
        {"settlement_status_id": 1, "language_code": "ar", "translated_status_name": "بانتظار الدفع"}, 
        {"settlement_status_id": 1, "language_code": "en", "translated_status_name": "Pending Payment"},
        {"settlement_status_id": 1, "language_code": "fr", "translated_status_name": "En attente de paiement"},
        {"settlement_status_id": 1, "language_code": "ur", "translated_status_name": "ادائیگی کا منتظر"},
        {"settlement_status_id": 1, "language_code": "hi", "translated_status_name": "भुगतान लंबित है"},
        {"settlement_status_id": 1, "language_code": "bn", "translated_status_name": "অর্থপ্রদান বাকি"},

        {"settlement_status_id": 2, "language_code": "ar", "translated_status_name": "مدفوع"}, 
        {"settlement_status_id": 2, "language_code": "en", "translated_status_name": "Paid"},
        {"settlement_status_id": 2, "language_code": "fr", "translated_status_name": "Payé"},
        {"settlement_status_id": 2, "language_code": "ur", "translated_status_name": "ادا کیا"},
        {"settlement_status_id": 2, "language_code": "hi", "translated_status_name": "भुगतान किया गया"},
        {"settlement_status_id": 2, "language_code": "bn", "translated_status_name": "পরিশোধিত"},

        {"settlement_status_id": 3, "language_code": "ar", "translated_status_name": "تمت التسوية"}, 
        {"settlement_status_id": 3, "language_code": "en", "translated_status_name": "Settled"},
        {"settlement_status_id": 3, "language_code": "fr", "translated_status_name": "Réglé"},
        {"settlement_status_id": 3, "language_code": "ur", "translated_status_name": "تصفیہ شدہ"},
        {"settlement_status_id": 3, "language_code": "hi", "translated_status_name": "निपटारा किया गया"},
        {"settlement_status_id": 3, "language_code": "bn", "translated_status_name": "নিষ্পত্তি"},
    ])

    # 7. حالات المراجعات
    review_statuses = [{"status_id": i + 1, "status_name_key": k} for i, k in enumerate(["PENDING_APPROVAL", "PUBLISHED", "REJECTED"])]
    seed_main_table(db, ReviewStatus, "status_id", review_statuses)
    seed_translation_table(db, ReviewStatusTranslation,"status_id",  [
        {"status_id": 1, "language_code": "ar", "translated_status_name": "بانتظار الموافقة"}, 
        {"status_id": 1, "language_code": "en", "translated_status_name": "Pending Approval"},
        {"status_id": 1, "language_code": "fr", "translated_status_name": "En attente d'approbation"},
        {"status_id": 1, "language_code": "ur", "translated_status_name": "منظوری کا منتظر"},
        {"status_id": 1, "language_code": "hi", "translated_status_name": "अनुमोदन लंबित है"},
        {"status_id": 1, "language_code": "bn", "translated_status_name": "অনুমোদনের জন্য অপেক্ষারত"},

        {"status_id": 2, "language_code": "ar", "translated_status_name": "منشورة"}, 
        {"status_id": 2, "language_code": "en", "translated_status_name": "Published"},
        {"status_id": 2, "language_code": "fr", "translated_status_name": "Publié"},
        {"status_id": 2, "language_code": "ur", "translated_status_name": "شائع شدہ"},
        {"status_id": 2, "language_code": "hi", "translated_status_name": "प्रकाशित"},
        {"status_id": 2, "language_code": "bn", "translated_status_name": "প্রকাশিত"},

        {"status_id": 3, "language_code": "ar", "translated_status_name": "مرفوضة"}, 
        {"status_id": 3, "language_code": "en", "translated_status_name": "Rejected"},
        {"status_id": 3, "language_code": "fr", "translated_status_name": "Rejeté"},
        {"status_id": 3, "language_code": "ur", "translated_status_name": "مسترد"},
        {"status_id": 3, "language_code": "hi", "translated_status_name": "अस्वीकृत"},
        {"status_id": 3, "language_code": "bn", "translated_status_name": "প্রত্যাখ্যাত"},
    ])

    # 8. حالات طلبات السحب
    withdrawal_statuses = [{"withdrawal_request_status_id": i + 1, "status_name_key": k} for i, k in enumerate(["PENDING_REVIEW", "APPROVED", "COMPLETED", "REJECTED"])]
    seed_main_table(db, WithdrawalRequestStatus, "withdrawal_request_status_id", withdrawal_statuses)
    seed_translation_table(db, WithdrawalRequestStatusTranslation,"withdrawal_request_status_id", [
        {"withdrawal_request_status_id": 1, "language_code": "ar", "translated_status_name": "قيد المراجعة"}, 
        {"withdrawal_request_status_id": 1, "language_code": "en", "translated_status_name": "Pending Review"},
        {"withdrawal_request_status_id": 1, "language_code": "fr", "translated_status_name": "En cours d'examen"},
        {"withdrawal_request_status_id": 1, "language_code": "ur", "translated_status_name": "زیر جائزہ"},
        {"withdrawal_request_status_id": 1, "language_code": "hi", "translated_status_name": "समीक्षाधीन"},
        {"withdrawal_request_status_id": 1, "language_code": "bn", "translated_status_name": "পর্যালোচনার অধীনে"},

        {"withdrawal_request_status_id": 2, "language_code": "ar", "translated_status_name": "تمت الموافقة"}, 
        {"withdrawal_request_status_id": 2, "language_code": "en", "translated_status_name": "Approved"},
        {"withdrawal_request_status_id": 2, "language_code": "fr", "translated_status_name": "Approuvé"},
        {"withdrawal_request_status_id": 2, "language_code": "ur", "translated_status_name": "منظور شدہ"},
        {"withdrawal_request_status_id": 2, "language_code": "hi", "translated_status_name": "स्वीकृत"},
        {"withdrawal_request_status_id": 2, "language_code": "bn", "translated_status_name": "অনুমোদিত"},

        {"withdrawal_request_status_id": 3, "language_code": "ar", "translated_status_name": "مكتمل"}, 
        {"withdrawal_request_status_id": 3, "language_code": "en", "translated_status_name": "Completed"},
        {"withdrawal_request_status_id": 3, "language_code": "fr", "translated_status_name": "Terminé"},
        {"withdrawal_request_status_id": 3, "language_code": "ur", "translated_status_name": "مکمل"},
        {"withdrawal_request_status_id": 3, "language_code": "hi", "translated_status_name": "पूर्ण"},
        {"withdrawal_request_status_id": 3, "language_code": "bn", "translated_status_name": "সম্পন্ন"},

        {"withdrawal_request_status_id": 4, "language_code": "ar", "translated_status_name": "مرفوض"}, 
        {"withdrawal_request_status_id": 4, "language_code": "en", "translated_status_name": "Rejected"},
        {"withdrawal_request_status_id": 4, "language_code": "fr", "translated_status_name": "Rejeté"},
        {"withdrawal_request_status_id": 4, "language_code": "ur", "translated_status_name": "مسترد"},
        {"withdrawal_request_status_id": 4, "language_code": "hi", "translated_status_name": "अस्वीकृत"},
        {"withdrawal_request_status_id": 4, "language_code": "bn", "translated_status_name": "প্রত্যাখ্যাত"},
    ])

    # 9. حالات اتفاقيات الدفع الآجل
    agreement_statuses = [{"deferred_payment_agreement_status_id": i + 1, "status_name_key": k} for i, k in enumerate(["ACTIVE", "COMPLETED", "DEFAULTED"])]
    seed_main_table(db, DeferredPaymentAgreementStatus, "deferred_payment_agreement_status_id", agreement_statuses)
    seed_translation_table(db, DeferredPaymentAgreementStatusTranslation,"deferred_payment_agreement_status_id",  [
        {"deferred_payment_agreement_status_id": 1, "language_code": "ar", "translated_status_name": "نشطة"}, 
        {"deferred_payment_agreement_status_id": 1, "language_code": "en", "translated_status_name": "Active"},
        {"deferred_payment_agreement_status_id": 1, "language_code": "fr", "translated_status_name": "Actif"},
        {"deferred_payment_agreement_status_id": 1, "language_code": "ur", "translated_status_name": "فعال"},
        {"deferred_payment_agreement_status_id": 1, "language_code": "hi", "translated_status_name": "सक्रिय"},
        {"deferred_payment_agreement_status_id": 1, "language_code": "bn", "translated_status_name": "সক্রিয়"},

        {"deferred_payment_agreement_status_id": 2, "language_code": "ar", "translated_status_name": "مكتملة"}, 
        {"deferred_payment_agreement_status_id": 2, "language_code": "en", "translated_status_name": "Completed"},
        {"deferred_payment_agreement_status_id": 2, "language_code": "fr", "translated_status_name": "Terminé"},
        {"deferred_payment_agreement_status_id": 2, "language_code": "ur", "translated_status_name": "مکمل"},
        {"deferred_payment_agreement_status_id": 2, "language_code": "hi", "translated_status_name": "पूर्ण"},
        {"deferred_payment_agreement_status_id": 2, "language_code": "bn", "translated_status_name": "সম্পন্ন"},

        {"deferred_payment_agreement_status_id": 3, "language_code": "ar", "translated_status_name": "متعثرة"}, 
        {"deferred_payment_agreement_status_id": 3, "language_code": "en", "translated_status_name": "Defaulted"},
        {"deferred_payment_agreement_status_id": 3, "language_code": "fr", "translated_status_name": "En défaut"},
        {"deferred_payment_agreement_status_id": 3, "language_code": "ur", "translated_status_name": "نا دہندہ"},
        {"deferred_payment_agreement_status_id": 3, "language_code": "hi", "translated_status_name": "चूक"},
        {"deferred_payment_agreement_status_id": 3, "language_code": "bn", "translated_status_name": "খেলাপী"},
    ])

    # 10. حالات الأقساط
    installment_statuses = [{"installment_status_id": i + 1, "status_name_key": k} for i, k in enumerate(["DUE", "PAID", "OVERDUE"])]
    seed_main_table(db, InstallmentStatus, "installment_status_id", installment_statuses)
    seed_translation_table(db, InstallmentStatusTranslation,"installment_status_id",  [
        {"installment_status_id": 1, "language_code": "ar", "translated_status_name": "مستحق"}, 
        {"installment_status_id": 1, "language_code": "en", "translated_status_name": "Due"},
        {"installment_status_id": 1, "language_code": "fr", "translated_status_name": "Dû"},
        {"installment_status_id": 1, "language_code": "ur", "translated_status_name": "واجب الادا"},
        {"installment_status_id": 1, "language_code": "hi", "translated_status_name": "देय"},
        {"installment_status_id": 1, "language_code": "bn", "translated_status_name": "বকেয়া"},

        {"installment_status_id": 2, "language_code": "ar", "translated_status_name": "مدفوع"}, 
        {"installment_status_id": 2, "language_code": "en", "translated_status_name": "Paid"},
        {"installment_status_id": 2, "language_code": "fr", "translated_status_name": "Payé"},
        {"installment_status_id": 2, "language_code": "ur", "translated_status_name": "ادا کیا"},
        {"installment_status_id": 2, "language_code": "hi", "translated_status_name": "भुगतान किया गया"},
        {"installment_status_id": 2, "language_code": "bn", "translated_status_name": "পরিশোধিত"},

        {"installment_status_id": 3, "language_code": "ar", "translated_status_name": "متأخر"},
        {"installment_status_id": 3, "language_code": "en", "translated_status_name": "Overdue"},
        {"installment_status_id": 3, "language_code": "fr", "translated_status_name": "En retard"},
        {"installment_status_id": 3, "language_code": "ur", "translated_status_name": "زائد الميعاد"},
        {"installment_status_id": 3, "language_code": "hi", "translated_status_name": "अतिदेय"},
        {"installment_status_id": 3, "language_code": "bn", "translated_status_name": "মেয়াদোত্তীর্ণ"},
    ])

    # 11. حالات مطالبات الضمان الذهبي
    claim_statuses = [{"gg_claim_status_id": i + 1, "status_name_key": k} for i, k in enumerate(["SUBMITTED", "UNDER_REVIEW", "RESOLVED", "CLOSED"])]
    seed_main_table(db, GGClaimStatus, "gg_claim_status_id", claim_statuses)
    seed_translation_table(db, GGClaimStatusTranslation, "gg_claim_status_id",[
        # SUBMITTED
        {"gg_claim_status_id": 1, "language_code": "ar", "translated_status_name": "تم التقديم"}, 
        {"gg_claim_status_id": 1, "language_code": "en", "translated_status_name": "Submitted"},
        {"gg_claim_status_id": 1, "language_code": "fr", "translated_status_name": "Soumis"},
        {"gg_claim_status_id": 1, "language_code": "ur", "translated_status_name": "جمع کرایا گیا"},
        {"gg_claim_status_id": 1, "language_code": "hi", "translated_status_name": "प्रस्तुत"},
        {"gg_claim_status_id": 1, "language_code": "bn", "translated_status_name": "জমা দেওয়া হয়েছে"},
        # UNDER_REVIEW
        {"gg_claim_status_id": 2, "language_code": "ar", "translated_status_name": "قيد المراجعة"}, 
        {"gg_claim_status_id": 2, "language_code": "en", "translated_status_name": "Under Review"},
        {"gg_claim_status_id": 2, "language_code": "fr", "translated_status_name": "En cours d'examen"},
        {"gg_claim_status_id": 2, "language_code": "ur", "translated_status_name": "زیر جائزہ"},
        {"gg_claim_status_id": 2, "language_code": "hi", "translated_status_name": "समीक्षाधीन"},
        {"gg_claim_status_id": 2, "language_code": "bn", "translated_status_name": "পর্যালোচনার অধীনে"},
        # RESOLVED
        {"gg_claim_status_id": 3, "language_code": "ar", "translated_status_name": "تم الحل"}, 
        {"gg_claim_status_id": 3, "language_code": "en", "translated_status_name": "Resolved"},
        {"gg_claim_status_id": 3, "language_code": "fr", "translated_status_name": "Résolu"},
        {"gg_claim_status_id": 3, "language_code": "ur", "translated_status_name": "حل"},
        {"gg_claim_status_id": 3, "language_code": "hi", "translated_status_name": "हल"},
        {"gg_claim_status_id": 3, "language_code": "bn", "translated_status_name": "সমাধান করা হয়েছে"},
        # CLOSED
        {"gg_claim_status_id": 4, "language_code": "ar", "translated_status_name": "مغلقة"},
        {"gg_claim_status_id": 4, "language_code": "en", "translated_status_name": "Closed"},
        {"gg_claim_status_id": 4, "language_code": "fr", "translated_status_name": "Fermé"},
        {"gg_claim_status_id": 4, "language_code": "ur", "translated_status_name": "بند"},
        {"gg_claim_status_id": 4, "language_code": "hi", "translated_status_name": "बंद"},
        {"gg_claim_status_id": 4, "language_code": "bn", "translated_status_name": "বন্ধ"},
    ])
    
    # 12. حالات الحساب (من مجموعة المستخدمين)
    account_statuses = [
        {"account_status_id": 1, "status_name_key": "PENDING_ACTIVATION", "is_terminal": False},
        {"account_status_id": 2, "status_name_key": "ACTIVE", "is_terminal": False},
        {"account_status_id": 3, "status_name_key": "SUSPENDED", "is_terminal": False},
        {"account_status_id": 4, "status_name_key": "DELETED", "is_terminal": True},
    ]
    seed_main_table(db, AccountStatus, "account_status_id", account_statuses)
    seed_translation_table(db, AccountStatusTranslation, "account_status_id", [
        # PENDING_ACTIVATION
        {"account_status_id": 1, "language_code": "ar", "translated_status_name": "بانتظار التفعيل"}, 
        {"account_status_id": 1, "language_code": "en", "translated_status_name": "Pending Activation"},
        {"account_status_id": 1, "language_code": "fr", "translated_status_name": "En attente d'activation"}, 
        {"account_status_id": 1, "language_code": "ur", "translated_status_name": "فعال سازی کا منتظر"},
        {"account_status_id": 1, "language_code": "hi", "translated_status_name": "सक्रियण लंबित है"},
        {"account_status_id": 1, "language_code": "bn", "translated_status_name": "সক্রিয়করণের জন্য অপেক্ষমান"},
        # ACTIVE
        {"account_status_id": 2, "language_code": "ar", "translated_status_name": "نشط"}, 
        {"account_status_id": 2, "language_code": "en", "translated_status_name": "Active"},
        {"account_status_id": 2, "language_code": "fr", "translated_status_name": "Actif"}, 
        {"account_status_id": 2, "language_code": "ur", "translated_status_name": "فعال"},
        {"account_status_id": 2, "language_code": "hi", "translated_status_name": "सक्रिय"},
        {"account_status_id": 2, "language_code": "bn", "translated_status_name": "সক্রিয়"},
        # SUSPENDED
        {"account_status_id": 3, "language_code": "ar", "translated_status_name": "موقوف"}, 
        {"account_status_id": 3, "language_code": "en", "translated_status_name": "Suspended"},
        {"account_status_id": 3, "language_code": "fr", "translated_status_name": "Suspendu"}, 
        {"account_status_id": 3, "language_code": "ur", "translated_status_name": "معطل"},
        {"account_status_id": 3, "language_code": "hi", "translated_status_name": "निलंबित"},
        {"account_status_id": 3, "language_code": "bn", "translated_status_name": "স্থগিত"},
        # DELETED
        {"account_status_id": 4, "language_code": "ar", "translated_status_name": "محذوف"}, 
        {"account_status_id": 4, "language_code": "en", "translated_status_name": "Deleted"},
        {"account_status_id": 4, "language_code": "fr", "translated_status_name": "Supprimé"}, 
        {"account_status_id": 4, "language_code": "ur", "translated_status_name": "حذف شدہ"},
        {"account_status_id": 4, "language_code": "bn", "translated_status_name": "মুছে ফেলা হয়েছে"},
    ])
    
    # 13. حالات التحقق من المستخدم
    user_verification_statuses = [
        {"user_verification_status_id": 1, "status_name_key": "NOT_VERIFIED", "description_key": "User has not submitted any documents for verification."},
        {"user_verification_status_id": 2, "status_name_key": "PENDING_REVIEW", "description_key": "User has submitted documents and is awaiting admin review."},
        {"user_verification_status_id": 3, "status_name_key": "VERIFIED", "description_key": "User has been successfully verified."},
        {"user_verification_status_id": 4, "status_name_key": "REJECTED", "description_key": "User's verification request was rejected."},
        {"user_verification_status_id": 5, "status_name_key": "ACTIVE", "description_key": "User account is active and ready to use."},
    ]
    seed_main_table(db, UserVerificationStatus, "user_verification_status_id", user_verification_statuses)
    seed_translation_table(db, UserVerificationStatusTranslation, "user_verification_status_id",  [
        # NOT_VERIFIED
        {"user_verification_status_id": 1, "language_code": "ar", "translated_status_name": "لم يتم التحقق", "translated_description": "لم يقم المستخدم بتقديم أي وثائق للتحقق."},
        {"user_verification_status_id": 1, "language_code": "en", "translated_status_name": "Not Verified", "translated_description": "User has not submitted any documents for verification."},
        {"user_verification_status_id": 1, "language_code": "fr", "translated_status_name": "Non vérifié", "translated_description": "L'utilisateur n'a soumis aucun document pour vérification."},
        {"user_verification_status_id": 1, "language_code": "ur", "translated_status_name": "غیر تصدیق شدہ", "translated_description": "صارف نے تصدیق کے لیے کوئی دستاویزات جمع نہیں کرائی ہیں۔"},
        {"user_verification_status_id": 1, "language_code": "hi", "translated_status_name": "सत्यापित नहीं है", "translated_description": "उपयोगकर्ता ने सत्यापन के लिए कोई दस्तावेज़ प्रस्तुत नहीं किया है।"},
        {"user_verification_status_id": 1, "language_code": "bn", "translated_status_name": "যাচাই করা হয়নি", "translated_description": "ব্যবহারকারী যাচাইয়ের জন্য কোনো নথি জমা দেননি।"},
        # PENDING_REVIEW
        {"user_verification_status_id": 2, "language_code": "ar", "translated_status_name": "قيد المراجعة", "translated_description": "قدم المستخدم وثائق وهو في انتظار مراجعة المسؤول."},
        {"user_verification_status_id": 2, "language_code": "en", "translated_status_name": "Pending Review", "translated_description": "User has submitted documents and is awaiting admin review."},
        {"user_verification_status_id": 2, "language_code": "fr", "translated_status_name": "En cours d'examen", "translated_description": "L'utilisateur a soumis des documents et attend l'examen par l'administrateur."},
        {"user_verification_status_id": 2, "language_code": "ur", "translated_status_name": "زیر جائزہ", "translated_description": "صارف نے دستاویزات جمع کرادی ہیں اور منتظم کے جائزے کا منتظر ہے۔"},
        {"user_verification_status_id": 2, "language_code": "hi", "translated_status_name": "समीक्षाधीन", "translated_description": "उपयोगकर्ता ने दस्तावेज़ जमा कर दिए हैं और व्यवस्थापक समीक्षा की प्रतीक्षा कर रहे हैं।"},
        {"user_verification_status_id": 2, "language_code": "bn", "translated_status_name": "পর্যালোচনা অধীন", "translated_description": "ব্যবহারকারী নথি জমা দিয়েছেন এবং অ্যাডমিনের পর্যালোচনার জন্য অপেক্ষা করছেন।"},
        # VERIFIED
        {"user_verification_status_id": 3, "language_code": "ar", "translated_status_name": "تم التحقق", "translated_description": "تم التحقق من حساب المستخدم بنجاح."},
        {"user_verification_status_id": 3, "language_code": "en", "translated_status_name": "Verified", "translated_description": "The user's account has been successfully verified."},
        {"user_verification_status_id": 3, "language_code": "fr", "translated_status_name": "Vérifié", "translated_description": "Le compte de l'utilisateur a été vérifié avec succès."},
        {"user_verification_status_id": 3, "language_code": "ur", "translated_status_name": "تصدیق شدہ", "translated_description": "صارف کا اکاؤنٹ کامیابی سے تصدیق ہو گیا ہے۔"},
        {"user_verification_status_id": 3, "language_code": "hi", "translated_status_name": "सत्यापित", "translated_description": "उपयोगकर्ता का खाता सफलतापूर्वक सत्यापित हो गया है।"},
        {"user_verification_status_id": 3, "language_code": "bn", "translated_status_name": "যাচাইকৃত", "translated_description": "ব্যবহারকারীর অ্যাকাউন্ট সফলভাবে যাচাই করা হয়েছে।"},
        # REJECTED
        {"user_verification_status_id": 4, "language_code": "ar", "translated_status_name": "مرفوض", "translated_description": "تم رفض طلب التحقق الخاص بالمستخدم."},
        {"user_verification_status_id": 4, "language_code": "en", "translated_status_name": "Rejected", "translated_description": "The user's verification request was rejected."},
        {"user_verification_status_id": 4, "language_code": "fr", "translated_status_name": "Rejeté", "translated_description": "La demande de vérification de l'utilisateur a été rejetée."},
        {"user_verification_status_id": 4, "language_code": "ur", "translated_status_name": "مسترد", "translated_description": "صارف کی تصدیقی درخواست مسترد کر دی گئی۔"},
        {"user_verification_status_id": 4, "language_code": "hi", "translated_status_name": "अस्वीकृत", "translated_description": "उपयोगकर्ता का सत्यापन अनुरोध अस्वीकार कर दिया गया था।"},
        {"user_verification_status_id": 4, "language_code": "bn", "translated_status_name": "প্রত্যাখ্যাত", "translated_description": "ব্যবহারকারীর যাচাইকরণ অনুরোধ প্রত্যাখ্যান করা হয়েছে।"},
        # ACTIVE
        {"user_verification_status_id": 5, "language_code": "ar", "translated_status_name": "نشط", "translated_description": "حساب المستخدم نشط وجاهز للاستخدام."},
        {"user_verification_status_id": 5, "language_code": "en", "translated_status_name": "Active", "translated_description": "User account is active and ready to use."},
        {"user_verification_status_id": 5, "language_code": "fr", "translated_status_name": "Actif", "translated_description": "Le compte utilisateur est actif et prêt à être utilisé."},
        {"user_verification_status_id": 5, "language_code": "ur", "translated_status_name": "فعال", "translated_description": "صارف کا اکاؤنٹ فعال ہے اور استعمال کے لیے تیار ہے۔"},
        {"user_verification_status_id": 5, "language_code": "hi", "translated_status_name": "सक्रिय", "translated_description": "उपयोगकर्ता का खाता सक्रिय है और उपयोग के लिए तैयार है।"},
        {"user_verification_status_id": 5, "language_code": "bn", "translated_status_name": "সক্রিয়", "translated_description": "ব্যবহারকারীর অ্যাকাউন্ট সক্রিয় এবং ব্যবহারের জন্য প্রস্তুত।"},
    ])

    db.commit()
    # logger.info("All status tables have been seeded successfully.")

    logger.info("--- Seeding Type & Classification Tables ---")

    ########################################################
    #  قيم أولية (Initial Values) أو بيانات مرجعية،
    #  جداول الأنواع والتصنيفات (Type & Classification Tables)
    ########################################################

    # 1. أنواع المزادات
    auction_types = [
        {"auction_type_id": 1, "type_name_key": "STANDARD_ENGLISH_AUCTION", "description_key": "Standard ascending price auction."},
    ]
    seed_main_table(db, AuctionType, "auction_type_id", auction_types)
    seed_translation_table(db, AuctionTypeTranslation, "auction_type_id", [
        {"auction_type_id": 1, "language_code": "ar", "translated_type_name": "مزاد إنجليزي قياسي"},
        {"auction_type_id": 1, "language_code": "en", "translated_type_name": "Standard English Auction"},
        {"auction_type_id": 1, "language_code": "fr", "translated_type_name": "Enchère anglaise standard"},
        {"auction_type_id": 1, "language_code": "ur", "translated_type_name": "معیاری انگریزی نیلامی"},
        {"auction_type_id": 1, "language_code": "hi", "translated_type_name": "मानक अंग्रेजी नीलामी"},
        {"auction_type_id": 1, "language_code": "bn", "translated_type_name": "স্ট্যান্ডার্ড ইংলিশ নিলাম"},
    ])

    # 2. أنواع المعاملات المالية
    transaction_types = [
        {"transaction_type_id": 1, "transaction_type_name_key": "DEPOSIT", "is_credit": True},
        {"transaction_type_id": 2, "transaction_type_name_key": "WITHDRAWAL", "is_credit": False},
        {"transaction_type_id": 3, "transaction_type_name_key": "ORDER_PAYMENT", "is_credit": False},
        {"transaction_type_id": 4, "transaction_type_name_key": "ORDER_REFUND", "is_credit": True},
        {"transaction_type_id": 5, "transaction_type_name_key": "AUCTION_SETTLEMENT_PAYOUT", "is_credit": True},
    ]
    seed_main_table(db, TransactionType, "transaction_type_id", transaction_types)
    seed_translation_table(db, TransactionTypeTranslation, "transaction_type_id", [
        # DEPOSIT
        {"transaction_type_id": 1, "language_code": "ar", "translated_transaction_type_name": "إيداع"},
        {"transaction_type_id": 1, "language_code": "en", "translated_transaction_type_name": "Deposit"},
        {"transaction_type_id": 1, "language_code": "fr", "translated_transaction_type_name": "Dépôt"},
        {"transaction_type_id": 1, "language_code": "ur", "translated_transaction_type_name": "جمع"},
        {"transaction_type_id": 1, "language_code": "hi", "translated_transaction_type_name": "जमा"},
        {"transaction_type_id": 1, "language_code": "bn", "translated_transaction_type_name": "জমা"},
        # WITHDRAWAL
        {"transaction_type_id": 2, "language_code": "ar", "translated_transaction_type_name": "سحب"},
        {"transaction_type_id": 2, "language_code": "en", "translated_transaction_type_name": "Withdrawal"},
        {"transaction_type_id": 2, "language_code": "fr", "translated_transaction_type_name": "Retrait"},
        {"transaction_type_id": 2, "language_code": "ur", "translated_transaction_type_name": "واپسی"},
        {"transaction_type_id": 2, "language_code": "hi", "translated_transaction_type_name": "निकासी"},
        {"transaction_type_id": 2, "language_code": "bn", "translated_transaction_type_name": "উত্তোলন"},
        # ORDER_PAYMENT
        {"transaction_type_id": 3, "language_code": "ar", "translated_transaction_type_name": "دفع طلب"},
        {"transaction_type_id": 3, "language_code": "en", "translated_transaction_type_name": "Order Payment"},
        {"transaction_type_id": 3, "language_code": "fr", "translated_transaction_type_name": "Paiement de commande"},
        {"transaction_type_id": 3, "language_code": "ur", "translated_transaction_type_name": "آرڈر کی ادائیگی"},
        {"transaction_type_id": 3, "language_code": "hi", "translated_transaction_type_name": "आर्डर भुगतान"},
        {"transaction_type_id": 3, "language_code": "bn", "translated_transaction_type_name": "অর্ডার পেমেন্ট"},
        # ORDER_REFUND
        {"transaction_type_id": 4, "language_code": "ar", "translated_transaction_type_name": "استرداد مبلغ طلب"},
        {"transaction_type_id": 4, "language_code": "en", "translated_transaction_type_name": "Order Refund"},
        {"transaction_type_id": 4, "language_code": "fr", "translated_transaction_type_name": "Remboursement de commande"},
        {"transaction_type_id": 4, "language_code": "ur", "translated_transaction_type_name": "آرڈر کی واپسی"},
        {"transaction_type_id": 4, "language_code": "hi", "translated_transaction_type_name": "आर्डर वापसी"},
        {"transaction_type_id": 4, "language_code": "bn", "translated_transaction_type_name": "অর্ডার রিফান্ড"},
        # AUCTION_SETTLEMENT_PAYOUT
        {"transaction_type_id": 5, "language_code": "ar", "translated_transaction_type_name": "تسوية مزاد"},
        {"transaction_type_id": 5, "language_code": "en", "translated_transaction_type_name": "Auction Payout"},
        {"transaction_type_id": 5, "language_code": "fr", "translated_transaction_type_name": "Paiement d'enchère"},
        {"transaction_type_id": 5, "language_code": "ur", "translated_transaction_type_name": "نیلامی کی ادائیگی"},
        {"transaction_type_id": 5, "language_code": "hi", "translated_transaction_type_name": "नीलामी भुगतान"},
        {"transaction_type_id": 5, "language_code": "bn", "translated_transaction_type_name": "নিলামের অর্থ প্রদান"},
    ])

    # 3. أدوار المستخدمين (تم بذرها سابقًا، ولكن نضعها هنا للتنظيم)
    # تم حذف البذر المكرر للأدوار - تم بذرها مسبقاً في السطر 67
    seed_translation_table(db, RoleTranslation, "role_id", [
        # BASE_USER
        {"role_id": 1, "language_code": "ar", "translated_role_name": "مستخدم أساسي"},
        {"role_id": 1, "language_code": "en", "translated_role_name": "Base User"},
        {"role_id": 1, "language_code": "fr", "translated_role_name": "Utilisateur de base"},
        {"role_id": 1, "language_code": "ur", "translated_role_name": "بنیادی صارف"},
        {"role_id": 1, "language_code": "hi", "translated_role_name": "मूल उपयोगकर्ता"},
        {"role_id": 1, "language_code": "bn", "translated_role_name": "বেস ব্যবহারকারী"},
        # ADMIN
        {"role_id": 2, "language_code": "ar", "translated_role_name": "مسؤول"}, 
        {"role_id": 2, "language_code": "en", "translated_role_name": "Admin"},
        {"role_id": 2, "language_code": "fr", "translated_role_name": "Administrateur"},
        {"role_id": 2, "language_code": "ur", "translated_role_name": "منتظم"},
        {"role_id": 2, "language_code": "hi", "translated_role_name": "प्रशासक"},
        {"role_id": 2, "language_code": "bn", "translated_role_name": "প্রশাসক"},
        # WHOLESALER
        {"role_id": 3, "language_code": "ar", "translated_role_name": "تاجر جملة"},
        {"role_id": 3, "language_code": "en", "translated_role_name": "Wholesaler"},
        {"role_id": 3, "language_code": "fr", "translated_role_name": "Grossiste"},
        {"role_id": 3, "language_code": "ur", "translated_role_name": "تھوک فروش"},
        {"role_id": 3, "language_code": "hi", "translated_role_name": "थोक विक्रेता"},
        {"role_id": 3, "language_code": "bn", "translated_role_name": "পাইকার"},
        # PRODUCING_FAMILY
        {"role_id": 4, "language_code": "ar", "translated_role_name": "أسرة منتجة"},
        {"role_id": 4, "language_code": "en", "translated_role_name": "Producing Family"},
        {"role_id": 4, "language_code": "fr", "translated_role_name": "Famille productrice"},
        {"role_id": 4, "language_code": "ur", "translated_role_name": "پیداواری خاندان"},
        {"role_id": 4, "language_code": "hi", "translated_role_name": "उत्पादक परिवार"},
        {"role_id": 4, "language_code": "bn", "translated_role_name": "উৎপাদনকারী পরিবার"},
        # COMMERCIAL_BUYER
        {"role_id": 5, "language_code": "ar", "translated_role_name": "مشترٍ تجاري"},
        {"role_id": 5, "language_code": "en", "translated_role_name": "Commercial Buyer"},
        {"role_id": 5, "language_code": "fr", "translated_role_name": "Acheteur commercial"},
        {"role_id": 5, "language_code": "ur", "translated_role_name": "تجارتی خریدار"},
        {"role_id": 5, "language_code": "hi", "translated_role_name": "वाणिज्यिक खरीदार"},
        {"role_id": 5, "language_code": "bn", "translated_role_name": "বাণিজ্যিক ক্রেতা"},
        # RESELLER
        {"role_id": 6, "language_code": "ar", "translated_role_name": "مندوب بيع"},
        {"role_id": 6, "language_code": "en", "translated_role_name": "Reseller"},
        {"role_id": 6, "language_code": "fr", "translated_role_name": "Revendeur"},
        {"role_id": 6, "language_code": "ur", "translated_role_name": "ری سیلر"},
        {"role_id": 6, "language_code": "hi", "translated_role_name": "पुनर्विक्रेता"},
        {"role_id": 6, "language_code": "bn", "translated_role_name": "পুনরায় বিক্রেতা"},
        # FARMER
        {"role_id": 7, "language_code": "ar", "translated_role_name": "مزارع"},
        {"role_id": 7, "language_code": "en", "translated_role_name": "Farmer"},
        {"role_id": 7, "language_code": "fr", "translated_role_name": "Agriculteur"},
        {"role_id": 7, "language_code": "ur", "translated_role_name": "کسان"},
        {"role_id": 7, "language_code": "hi", "translated_role_name": "किसान"},
        {"role_id": 7, "language_code": "bn", "translated_role_name": "কৃষক"},
    ])
    
    # 4. أنواع التراخيص
    license_types = [
        {"license_type_id": 1, "license_type_name_key": "COMMERCIAL_REGISTER", "is_mandatory_for_role": True},
        {"license_type_id": 2, "license_type_name_key": "FREELANCE_DOCUMENT", "is_mandatory_for_role": True},
    ]
    seed_main_table(db, LicenseType, "license_type_id", license_types)
    seed_translation_table(db, LicenseTypeTranslation, "license_type_id", [
        # COMMERCIAL_REGISTER
        {"license_type_id": 1, "language_code": "ar", "translated_license_type_name": "سجل تجاري"},
        {"license_type_id": 1, "language_code": "en", "translated_license_type_name": "Commercial Register"},
        {"license_type_id": 1, "language_code": "fr", "translated_license_type_name": "Registre de commerce"},
        {"license_type_id": 1, "language_code": "ur", "translated_license_type_name": "تجارتی رجسٹر"},
        {"license_type_id": 1, "language_code": "hi", "translated_license_type_name": "वाणिज्यिक रजिस्टर"},
        {"license_type_id": 1, "language_code": "bn", "translated_license_type_name": "বাণিজ্যিক নিবন্ধন"},
        # FREELANCE_DOCUMENT
        {"license_type_id": 2, "language_code": "ar", "translated_license_type_name": "وثيقة عمل حر"},
        {"license_type_id": 2, "language_code": "en", "translated_license_type_name": "Freelance Document"},
        {"license_type_id": 2, "language_code": "fr", "translated_license_type_name": "Document de freelance"},
        {"license_type_id": 2, "language_code": "ur", "translated_license_type_name": "فری لانس دستاویز"},
        {"license_type_id": 2, "language_code": "hi", "translated_license_type_name": "फ्रीलांस दस्तावेज़"},
        {"license_type_id": 2, "language_code": "bn", "translated_license_type_name": "ফ্রিল্যান্স নথি"},
    ])

    # 5. قنوات الإشعارات
    notification_channels = [
        {"channel_id": 1, "channel_name_key": "IN_APP"},
        {"channel_id": 2, "channel_name_key": "EMAIL"},
        {"channel_id": 3, "channel_name_key": "SMS"},
    ]
    seed_main_table(db, NotificationChannel, "channel_id", notification_channels)
    seed_translation_table(db, NotificationChannelTranslation, "channel_translation_id", [
        # IN_APP
        {"channel_translation_id": 1, "channel_id": 1, "language_code": "ar", "translated_channel_name": "داخل التطبيق"},
        # EMAIL
        {"channel_translation_id": 2, "channel_id": 2, "language_code": "ar", "translated_channel_name": "بريد إلكتروني"},
        # SMS
        {"channel_translation_id": 3, "channel_id": 3, "language_code": "ar", "translated_channel_name": "رسالة نصية"},
    ])
    
    # 6. أنواع حلول مطالبات الضمان
    gg_resolution_types = [
        {"gg_resolution_type_id": 1, "resolution_type_name_key": "FULL_REFUND"},
        {"gg_resolution_type_id": 2, "resolution_type_name_key": "PARTIAL_REFUND"},
        {"gg_resolution_type_id": 3, "resolution_type_name_key": "REPLACEMENT"},
    ]
    seed_main_table(db, GGResolutionType, "gg_resolution_type_id", gg_resolution_types)
    seed_translation_table(db, GGResolutionTypeTranslation, "gg_resolution_type_id", [
        # FULL_REFUND
        {"gg_resolution_type_id": 1, "language_code": "ar", "translated_resolution_type_name": "استرداد كامل"},
        {"gg_resolution_type_id": 1, "language_code": "en", "translated_resolution_type_name": "Full Refund"},
        {"gg_resolution_type_id": 1, "language_code": "fr", "translated_resolution_type_name": "Remboursement complet"},
        {"gg_resolution_type_id": 1, "language_code": "ur", "translated_resolution_type_name": "مکمل رقم کی واپسی"},
        {"gg_resolution_type_id": 1, "language_code": "hi", "translated_resolution_type_name": "पूरी धनवापसी"},
        {"gg_resolution_type_id": 1, "language_code": "bn", "translated_resolution_type_name": "সম্পূর্ণ ফেরত"},
        # PARTIAL_REFUND
        {"gg_resolution_type_id": 2, "language_code": "ar", "translated_resolution_type_name": "استرداد جزئي"},
        {"gg_resolution_type_id": 2, "language_code": "en", "translated_resolution_type_name": "Partial Refund"},
        {"gg_resolution_type_id": 2, "language_code": "fr", "translated_resolution_type_name": "Remboursement partiel"},
        {"gg_resolution_type_id": 2, "language_code": "ur", "translated_resolution_type_name": "جزوی رقم کی واپسی"},
        {"gg_resolution_type_id": 2, "language_code": "hi", "translated_resolution_type_name": "आंशिक धनवापसि"},
        {"gg_resolution_type_id": 2, "language_code": "bn", "translated_resolution_type_name": "আংশিক ফেরত"},
        # REPLACEMENT
        {"gg_resolution_type_id": 3, "language_code": "ar", "translated_resolution_type_name": "استبدال"},
        {"gg_resolution_type_id": 3, "language_code": "en", "translated_resolution_type_name": "Replacement"},
        {"gg_resolution_type_id": 3, "language_code": "fr", "translated_resolution_type_name": "Remplacement"},
        {"gg_resolution_type_id": 3, "language_code": "ur", "translated_resolution_type_name": "تبدیلی"},
        {"gg_resolution_type_id": 3, "language_code": "hi", "translated_resolution_type_name": "प्रतिस्थापन"},
        {"gg_resolution_type_id": 3, "language_code": "bn", "translated_resolution_type_name": "প্রতিস্থাপন"},
    ])
    
    # 7. أنواع الكيانات للمراجعات والصور
    entity_types = [
        {"entity_type_code": "PRODUCT", "entity_type_name_key": "product_entity", "description_key": "Refers to a product in the catalog"},
        {"entity_type_code": "SELLER", "entity_type_name_key": "seller_entity", "description_key": "Refers to a seller user"},
        {"entity_type_code": "BUYER", "entity_type_name_key": "buyer_entity", "description_key": "Refers to a buyer user"},
        {"entity_type_code": "AUCTION_LOT", "entity_type_name_key": "auction_lot_entity", "description_key": "Refers to a specific lot within an auction"},
    ]
    seed_main_table(db, EntityTypeForReviewOrImage, "entity_type_code", entity_types)
    seed_translation_table(db, EntityTypeTranslation, "entity_type_code", [
        # PRODUCT
        {"entity_type_code": "PRODUCT", "language_code": "ar", "translated_entity_type_name": "منتج", "translated_entity_description": "يشير إلى منتج في الكتالوج الرئيسي"},
        {"entity_type_code": "PRODUCT", "language_code": "en", "translated_entity_type_name": "Product", "translated_entity_description": "Refers to a product in the main catalog"},
        {"entity_type_code": "PRODUCT", "language_code": "fr", "translated_entity_type_name": "Produit", "translated_entity_description": "Fait référence à un produit dans le catalogue principal"},
        {"entity_type_code": "PRODUCT", "language_code": "ur", "translated_entity_type_name": "مصنوع", "translated_entity_description": "مرکزی کیٹلاگ میں ایک مصنوعات کا حوالہ دیتا ہے۔"},
        {"entity_type_code": "PRODUCT", "language_code": "hi", "translated_entity_type_name": "उत्पाद", "translated_entity_description": "मुख्य कैटलॉग में एक उत्पाद को संदर्भित करता है"},
        {"entity_type_code": "PRODUCT", "language_code": "bn", "translated_entity_type_name": "পণ্য", "translated_entity_description": "মূল ক্যাটালগের একটি পণ্য বোঝায়"},
        # SELLER
        {"entity_type_code": "SELLER", "language_code": "ar", "translated_entity_type_name": "بائع", "translated_entity_description": "يشير إلى حساب مستخدم من نوع بائع"},
        {"entity_type_code": "SELLER", "language_code": "en", "translated_entity_type_name": "Seller", "translated_entity_description": "Refers to a seller user account"},
        {"entity_type_code": "SELLER", "language_code": "fr", "translated_entity_type_name": "Vendeur", "translated_entity_description": "Fait référence à un compte d'utilisateur vendeur"},
        {"entity_type_code": "SELLER", "language_code": "ur", "translated_entity_type_name": "بیچنے والا", "translated_entity_description": "ایک بیچنے والے صارف اکاؤنٹ کا حوالہ دیتا ہے۔"},
        {"entity_type_code": "SELLER", "language_code": "hi", "translated_entity_type_name": "विक्रेता", "translated_entity_description": "एक विक्रेता उपयोगकर्ता खाते को संदर्भित करता है"},
        {"entity_type_code": "SELLER", "language_code": "bn", "translated_entity_type_name": "বিক্রেতা", "translated_entity_description": "একজন বিক্রেতার ব্যবহারকারী অ্যাকাউন্ট বোঝায়"},
        # BUYER
        {"entity_type_code": "BUYER", "language_code": "ar", "translated_entity_type_name": "مشتري", "translated_entity_description": "يشير إلى حساب مستخدم من نوع مشتري"},
        {"entity_type_code": "BUYER", "language_code": "en", "translated_entity_type_name": "Buyer", "translated_entity_description": "Refers to a buyer user account"},
        {"entity_type_code": "BUYER", "language_code": "fr", "translated_entity_type_name": "Acheteur", "translated_entity_description": "Fait référence à un compte d'utilisateur acheteur"},
        {"entity_type_code": "BUYER", "language_code": "ur", "translated_entity_type_name": "خریدار", "translated_entity_description": "ایک خریدار صارف اکاؤنٹ کا حوالہ دیتا ہے۔"},
        {"entity_type_code": "BUYER", "language_code": "hi", "translated_entity_type_name": "क्रेता", "translated_entity_description": "एक खरीदार उपयोगकर्ता खाते को संदर्भित करता है"},
        {"entity_type_code": "BUYER", "language_code": "bn", "translated_entity_type_name": "ক্রেতা", "translated_entity_description": "একজন ক্রেতার ব্যবহারকারী অ্যাকাউন্ট বোঝায়"},
        # AUCTION_LOT
        {"entity_type_code": "AUCTION_LOT", "language_code": "ar", "translated_entity_type_name": "لوت مزاد", "translated_entity_description": "يشير إلى دفعة محددة داخل مزاد"},
        {"entity_type_code": "AUCTION_LOT", "language_code": "en", "translated_entity_type_name": "Auction Lot", "translated_entity_description": "Refers to a specific lot within an auction"},
        {"entity_type_code": "AUCTION_LOT", "language_code": "fr", "translated_entity_type_name": "Lot d'enchères", "translated_entity_description": "Fait référence à un lot spécifique dans une enchère"},
        {"entity_type_code": "AUCTION_LOT", "language_code": "ur", "translated_entity_type_name": "نیلامی لاٹ", "translated_entity_description": "ایک نیلامی کے اندر ایک مخصوص لاٹ کا حوالہ دیتا ہے۔"},
        {"entity_type_code": "AUCTION_LOT", "language_code": "hi", "translated_entity_type_name": "नीलामी लॉट", "translated_entity_description": "एक नीलामी के भीतर एक विशिष्ट लॉट को संदर्भित करता है"},
        {"entity_type_code": "AUCTION_LOT", "language_code": "bn", "translated_entity_type_name": "নিলামের লট", "translated_entity_description": "একটি নিলামের মধ্যে একটি নির্দিষ্ট লট বোঝায়"},
    ])

    # 8. أنواع الإشعارات
    notification_types = [
        {"notification_type_id": 1, "type_name_key": "ORDER_UPDATE"},
        {"notification_type_id": 2, "type_name_key": "AUCTION_ALERT"},
        {"notification_type_id": 3, "type_name_key": "PROMOTIONAL_OFFER", "can_user_disable": True},
    ]
    seed_main_table(db, NotificationType, "notification_type_id", notification_types)
    seed_translation_table(db, NotificationTypeTranslation, "notification_type_id", [
        # ORDER_UPDATE
        {"notification_type_id": 1, "type_translation_id": 1, "language_code": "ar", "translated_type_name": "تحديث الطلب"},
        # AUCTION_ALERT "type_translation_id": 1,
        {"notification_type_id": 2, "type_translation_id": 2, "language_code": "ar", "translated_type_name": "تنبيه مزاد"},
        # PROMOTIONAL_OFFER "type_translation_id": 1,
        {"notification_type_id": 3, "type_translation_id": 3, "language_code": "ar", "translated_type_name": "عرض ترويجي"},
    ])

    db.commit()

    logger.info("--- Seeding Geographic Data Tables ---")

    # 1. أنواع العناوين
    address_types = [
        {"address_type_id": 1, "address_type_name_key": "SHIPPING"},
        {"address_type_id": 2, "address_type_name_key": "BILLING"},
        {"address_type_id": 3, "address_type_name_key": "HOME"},
        {"address_type_id": 4, "address_type_name_key": "WORK"},
    ]
    seed_main_table(db, AddressType, "address_type_id", address_types)
    seed_translation_table(db, AddressTypeTranslation, "address_type_id", [
        # SHIPPING
        {"address_type_id": 1, "language_code": "ar", "translated_address_type_name": "عنوان الشحن"},
        {"address_type_id": 1, "language_code": "en", "translated_address_type_name": "Shipping Address"},
        {"address_type_id": 1, "language_code": "fr", "translated_address_type_name": "Adresse de livraison"},
        {"address_type_id": 1, "language_code": "ur", "translated_address_type_name": "شپنگ کا پتہ"},
        {"address_type_id": 1, "language_code": "hi", "translated_address_type_name": "शिपिंग पता"},
        {"address_type_id": 1, "language_code": "bn", "translated_address_type_name": "শিপিং ঠিকানা"},
        # BILLING
        {"address_type_id": 2, "language_code": "ar", "translated_address_type_name": "عنوان الفوترة"},
        {"address_type_id": 2, "language_code": "en", "translated_address_type_name": "Billing Address"},
        {"address_type_id": 2, "language_code": "fr", "translated_address_type_name": "Adresse de facturation"},
        {"address_type_id": 2, "language_code": "ur", "translated_address_type_name": "بلنگ کا پتہ"},
        {"address_type_id": 2, "language_code": "hi", "translated_address_type_name": "बिलिंग पता"},
        {"address_type_id": 2, "language_code": "bn", "translated_address_type_name": "বিলিং ঠিকানা"},
        # HOME
        {"address_type_id": 3, "language_code": "ar", "translated_address_type_name": "المنزل"},
        {"address_type_id": 3, "language_code": "en", "translated_address_type_name": "Home"},
        {"address_type_id": 3, "language_code": "fr", "translated_address_type_name": "Domicile"},
        {"address_type_id": 3, "language_code": "ur", "translated_address_type_name": "گھر"},
        {"address_type_id": 3, "language_code": "hi", "translated_address_type_name": "घर"},
        {"address_type_id": 3, "language_code": "bn", "translated_address_type_name": "বাড়ি"},
        # WORK
        {"address_type_id": 4, "language_code": "ar", "translated_address_type_name": "العمل"},
        {"address_type_id": 4, "language_code": "en", "translated_address_type_name": "Work"},
        {"address_type_id": 4, "language_code": "fr", "translated_address_type_name": "Travail"},
        {"address_type_id": 4, "language_code": "ur", "translated_address_type_name": "کام"},
        {"address_type_id": 4, "language_code": "hi", "translated_address_type_name": "काम"},
        {"address_type_id": 4, "language_code": "bn", "translated_address_type_name": "কর্মস্থল"},
    ])

    # 2. الدول (التركيز على السعودية)
    countries = [
        {"country_code": "SA", "country_name_key": "SAUDI_ARABIA", "phone_country_code": "+966", "is_active": True}
    ]
    seed_main_table(db, Country, "country_code", countries)
    seed_translation_table(db, CountryTranslation, "country_code", [
        {"country_code": "SA", "language_code": "ar", "translated_country_name": "المملكة العربية السعودية"},
        {"country_code": "SA", "language_code": "en", "translated_country_name": "Saudi Arabia"},
        {"country_code": "SA", "language_code": "fr", "translated_country_name": "Arabie Saoudite"},
        {"country_code": "SA", "language_code": "ur", "translated_country_name": "سعودی عرب"},
        {"country_code": "SA", "language_code": "hi", "translated_country_name": "सऊदी अरब"},
        {"country_code": "SA", "language_code": "bn", "translated_country_name": "সৌদি আরব"},
    ])
    db.commit()

    # 3. المناطق الإدارية / المحافظات
    governorates = [
        {"governorate_id": 1, "country_code": "SA", "governorate_name_key": "RIYADH_REGION"},
        {"governorate_id": 2, "country_code": "SA", "governorate_name_key": "MAKKAH_REGION"},
        {"governorate_id": 3, "country_code": "SA", "governorate_name_key": "MADINAH_REGION"},
        {"governorate_id": 4, "country_code": "SA", "governorate_name_key": "EASTERN_PROVINCE"},
    ]
    seed_main_table(db, Governorate, "governorate_id", governorates)
    seed_translation_table(db, GovernorateTranslation, "governorate_id", [
        # RIYADH_REGION
        {"governorate_id": 1, "language_code": "ar", "translated_governorate_name": "منطقة الرياض"},
        {"governorate_id": 1, "language_code": "en", "translated_governorate_name": "Riyadh Region"},
        {"governorate_id": 1, "language_code": "fr", "translated_governorate_name": "Région de Riyad"},
        {"governorate_id": 1, "language_code": "ur", "translated_governorate_name": "صوبہ ریاض"},
        {"governorate_id": 1, "language_code": "hi", "translated_governorate_name": "रियाद क्षेत्र"},
        {"governorate_id": 1, "language_code": "bn", "translated_governorate_name": "রিয়াদ অঞ্চল"},
        # MAKKAH_REGION
        {"governorate_id": 2, "language_code": "ar", "translated_governorate_name": "منطقة مكة المكرمة"},
        {"governorate_id": 2, "language_code": "en", "translated_governorate_name": "Makkah Region"},
        {"governorate_id": 2, "language_code": "fr", "translated_governorate_name": "Région de la Mecque"},
        {"governorate_id": 2, "language_code": "ur", "translated_governorate_name": "صوبہ مکہ"},
        {"governorate_id": 2, "language_code": "hi", "translated_governorate_name": "मक्का क्षेत्र"},
        {"governorate_id": 2, "language_code": "bn", "translated_governorate_name": "মক্কা অঞ্চল"},
        # MADINAH_REGION
        {"governorate_id": 3, "language_code": "ar", "translated_governorate_name": "منطقة المدينة المنورة"},
        {"governorate_id": 3, "language_code": "en", "translated_governorate_name": "Madinah Region"},
        {"governorate_id": 3, "language_code": "fr", "translated_governorate_name": "Région de Médine"},
        {"governorate_id": 3, "language_code": "ur", "translated_governorate_name": "صوبہ مدینہ"},
        {"governorate_id": 3, "language_code": "hi", "translated_governorate_name": "मदीना क्षेत्र"},
        {"governorate_id": 3, "language_code": "bn", "translated_governorate_name": "মদিনা অঞ্চল"},
        # EASTERN_PROVINCE
        {"governorate_id": 4, "language_code": "ar", "translated_governorate_name": "المنطقة الشرقية"},
        {"governorate_id": 4, "language_code": "en", "translated_governorate_name": "Eastern Province"},
        {"governorate_id": 4, "language_code": "fr", "translated_governorate_name": "Province de l'Est"},
        {"governorate_id": 4, "language_code": "ur", "translated_governorate_name": "مشرقی صوبہ"},
        {"governorate_id": 4, "language_code": "hi", "translated_governorate_name": "पूर्वी प्रांत"},
        {"governorate_id": 4, "language_code": "bn", "translated_governorate_name": "পূর্ব প্রদেশ"},
    ])
    db.commit()

    # 4. المدن الرئيسية
    cities = [
        {"city_id": 1, "governorate_id": 1, "city_name_key": "RIYADH"},
        {"city_id": 2, "governorate_id": 2, "city_name_key": "JEDDAH"},
        {"city_id": 3, "governorate_id": 2, "city_name_key": "MAKKAH"},
        {"city_id": 4, "governorate_id": 3, "city_name_key": "MADINAH"},
        {"city_id": 5, "governorate_id": 4, "city_name_key": "DAMMAM"},
        {"city_id": 6, "governorate_id": 4, "city_name_key": "KHOBAR"},
    ]
    seed_main_table(db, City, "city_id", cities)
    seed_translation_table(db, CityTranslation, "city_id", [
        # RIYADH
        {"city_id": 1, "language_code": "ar", "translated_city_name": "الرياض"},
        {"city_id": 1, "language_code": "en", "translated_city_name": "Riyadh"},
        {"city_id": 1, "language_code": "fr", "translated_city_name": "Riyad"},
        {"city_id": 1, "language_code": "ur", "translated_city_name": "ریاض"},
        {"city_id": 1, "language_code": "hi", "translated_city_name": "रियाद"},
        {"city_id": 1, "language_code": "bn", "translated_city_name": "রিয়াদ"},
        # JEDDAH
        {"city_id": 2, "language_code": "ar", "translated_city_name": "جدة"},
        {"city_id": 2, "language_code": "en", "translated_city_name": "Jeddah"},
        {"city_id": 2, "language_code": "fr", "translated_city_name": "Djeddah"},
        {"city_id": 2, "language_code": "ur", "translated_city_name": "جدہ"},
        {"city_id": 2, "language_code": "hi", "translated_city_name": "जेद्दा"},
        {"city_id": 2, "language_code": "bn", "translated_city_name": "জেদ্দা"},
        # MAKKAH
        {"city_id": 3, "language_code": "ar", "translated_city_name": "مكة المكرمة"},
        {"city_id": 3, "language_code": "en", "translated_city_name": "Makkah"},
        {"city_id": 3, "language_code": "fr", "translated_city_name": "La Mecque"},
        {"city_id": 3, "language_code": "ur", "translated_city_name": "مکہ"},
        {"city_id": 3, "language_code": "hi", "translated_city_name": "मक्का"},
        {"city_id": 3, "language_code": "bn", "translated_city_name": "মক্কা"},
        # MADINAH
        {"city_id": 4, "language_code": "ar", "translated_city_name": "المدينة المنورة"},
        {"city_id": 4, "language_code": "en", "translated_city_name": "Madinah"},
        {"city_id": 4, "language_code": "fr", "translated_city_name": "Médine"},
        {"city_id": 4, "language_code": "ur", "translated_city_name": "مدینہ"},
        {"city_id": 4, "language_code": "hi", "translated_city_name": "मदीना"},
        {"city_id": 4, "language_code": "bn", "translated_city_name": "মদিনা"},
        # DAMMAM
        {"city_id": 5, "language_code": "ar", "translated_city_name": "الدمام"},
        {"city_id": 5, "language_code": "en", "translated_city_name": "Dammam"},
        {"city_id": 5, "language_code": "fr", "translated_city_name": "Dammam"},
        {"city_id": 5, "language_code": "ur", "translated_city_name": "دمام"},
        {"city_id": 5, "language_code": "hi", "translated_city_name": "दम्माम"},
        {"city_id": 5, "language_code": "bn", "translated_city_name": "দাম্মাম"},
        # KHOBAR
        {"city_id": 6, "language_code": "ar", "translated_city_name": "الخبر"},
        {"city_id": 6, "language_code": "en", "translated_city_name": "Khobar"},
        {"city_id": 6, "language_code": "fr", "translated_city_name": "Khobar"},
        {"city_id": 6, "language_code": "ur", "translated_city_name": "خبر"},
        {"city_id": 6, "language_code": "hi", "translated_city_name": "खोबार"},
        {"city_id": 6, "language_code": "bn", "translated_city_name": "খোবার"},
    ])
    db.commit()

    # 5. بعض الأحياء النموذجية
    districts = [
        # Riyadh
        {"district_id": 1, "city_id": 1, "district_name_key": "OLAYA"},
        {"district_id": 2, "city_id": 1, "district_name_key": "MALAZ"},
        # Jeddah
        {"district_id": 3, "city_id": 2, "district_name_key": "AL_HAMRA"},
        {"district_id": 4, "city_id": 2, "district_name_key": "AL_RAWDAH"},
    ]
    seed_main_table(db, District, "district_id", districts)
    seed_translation_table(db, DistrictTranslation, "district_id", [
        # OLAYA
        {"district_id": 1, "language_code": "ar", "translated_district_name": "العليا"},
        {"district_id": 1, "language_code": "en", "translated_district_name": "Olaya"},
        {"district_id": 1, "language_code": "fr", "translated_district_name": "Olaya"},
        {"district_id": 1, "language_code": "ur", "translated_district_name": "اولایا"},
        {"district_id": 1, "language_code": "hi", "translated_district_name": "ओलाया"},
        {"district_id": 1, "language_code": "bn", "translated_district_name": "ওলায়া"},
        # MALAZ
        {"district_id": 2, "language_code": "ar", "translated_district_name": "الملز"},
        {"district_id": 2, "language_code": "en", "translated_district_name": "Malaz"},
        {"district_id": 2, "language_code": "fr", "translated_district_name": "Malaz"},
        {"district_id": 2, "language_code": "ur", "translated_district_name": "ملاز"},
        {"district_id": 2, "language_code": "hi", "translated_district_name": "मलाज़"},
        {"district_id": 2, "language_code": "bn", "translated_district_name": "মালাজ"},
        # AL_HAMRA
        {"district_id": 3, "language_code": "ar", "translated_district_name": "الحمراء"},
        {"district_id": 3, "language_code": "en", "translated_district_name": "Al-Hamra"},
        {"district_id": 3, "language_code": "fr", "translated_district_name": "Al-Hamra"},
        {"district_id": 3, "language_code": "ur", "translated_district_name": "الحمراء"},
        {"district_id": 3, "language_code": "hi", "translated_district_name": "अल-हमरा"},
        {"district_id": 3, "language_code": "bn", "translated_district_name": "আল-হামরা"},
        # AL_RAWDAH
        {"district_id": 4, "language_code": "ar", "translated_district_name": "الروضة"},
        {"district_id": 4, "language_code": "en", "translated_district_name": "Al-Rawdah"},
        {"district_id": 4, "language_code": "fr", "translated_district_name": "Al-Rawdah"},
        {"district_id": 4, "language_code": "ur", "translated_district_name": "الروضة"},
        {"district_id": 4, "language_code": "hi", "translated_district_name": "अल-रवदाह"},
        {"district_id": 4, "language_code": "bn", "translated_district_name": "আল-রাওদাহ"},
    ])

    db.commit()

    logger.info("--- Seeding Audit & Activity Log Type Tables ---")

    # 1. أنواع أحداث النظام العامة (System Event Types)
    system_event_types = [
        {"event_type_id": 1, "event_type_name_key": "USER_ACTION"},
        {"event_type_id": 2, "event_type_name_key": "SYSTEM_PROCESS"},
        {"event_type_id": 3, "event_type_name_key": "SECURITY_ALERT"},
    ]
    seed_main_table(db, SystemEventType, "event_type_id", system_event_types)
    seed_translation_table(db, SystemEventTypeTranslation, "event_type_id", [
        # USER_ACTION
        {"event_type_id": 1, "language_code": "ar", "translated_event_type_name": "إجراء مستخدم"},
        {"event_type_id": 1, "language_code": "en", "translated_event_type_name": "User Action"},
        {"event_type_id": 1, "language_code": "fr", "translated_event_type_name": "Action de l'utilisateur"},
        {"event_type_id": 1, "language_code": "ur", "translated_event_type_name": "صارف کی کارروائی"},
        {"event_type_id": 1, "language_code": "hi", "translated_event_type_name": "उपयोगकर्ता कार्रवाई"},
        {"event_type_id": 1, "language_code": "bn", "translated_event_type_name": "ব্যবহারকারীর ক্রিয়া"},
        # SYSTEM_PROCESS
        {"event_type_id": 2, "language_code": "ar", "translated_event_type_name": "عملية نظام"},
        {"event_type_id": 2, "language_code": "en", "translated_event_type_name": "System Process"},
        {"event_type_id": 2, "language_code": "fr", "translated_event_type_name": "Processus système"},
        {"event_type_id": 2, "language_code": "ur", "translated_event_type_name": "سسٹم کا عمل"},
        {"event_type_id": 2, "language_code": "hi", "translated_event_type_name": "सिस्टम प्रक्रिया"},
        {"event_type_id": 2, "language_code": "bn", "translated_event_type_name": "সিস্টেম প্রক্রিয়া"},
        # SECURITY_ALERT
        {"event_type_id": 3, "language_code": "ar", "translated_event_type_name": "تنبيه أمني"},
        {"event_type_id": 3, "language_code": "en", "translated_event_type_name": "Security Alert"},
        {"event_type_id": 3, "language_code": "fr", "translated_event_type_name": "Alerte de sécurité"},
        {"event_type_id": 3, "language_code": "ur", "translated_event_type_name": "سیکورٹی الرٹ"},
        {"event_type_id": 3, "language_code": "hi", "translated_event_type_name": "सुरक्षा चेतावनी"},
        {"event_type_id": 3, "language_code": "bn", "translated_event_type_name": "নিরাপত্তা সতর্কতা"},
    ])

    # 2. أنواع الأنشطة (Activity Types)
    activity_types = [
        {"activity_type_id": 1, "activity_name_key": "USER_LOGIN"},
        {"activity_type_id": 2, "activity_name_key": "CREATE_ORDER"},
        {"activity_type_id": 3, "activity_name_key": "VIEW_PRODUCT"},
    ]
    seed_main_table(db, ActivityType, "activity_type_id", activity_types)
    seed_translation_table(db, ActivityTypeTranslation, "activity_type_id", [
        # USER_LOGIN
        {"activity_type_id": 1, "language_code": "ar", "translated_activity_name": "تسجيل دخول مستخدم"},
        {"activity_type_id": 1, "language_code": "en", "translated_activity_name": "User Login"},
        {"activity_type_id": 1, "language_code": "fr", "translated_activity_name": "Connexion de l'utilisateur"},
        {"activity_type_id": 1, "language_code": "ur", "translated_activity_name": "صارف لاگ ان"},
        {"activity_type_id": 1, "language_code": "hi", "translated_activity_name": "उपयोगकर्ता लॉगिन"},
        {"activity_type_id": 1, "language_code": "bn", "translated_activity_name": "ব্যবহারকারী লগইন"},
        # CREATE_ORDER
        {"activity_type_id": 2, "language_code": "ar", "translated_activity_name": "إنشاء طلب"},
        {"activity_type_id": 2, "language_code": "en", "translated_activity_name": "Create Order"},
        {"activity_type_id": 2, "language_code": "fr", "translated_activity_name": "Créer une commande"},
        {"activity_type_id": 2, "language_code": "ur", "translated_activity_name": "آرڈر بنائیں"},
        {"activity_type_id": 2, "language_code": "hi", "translated_activity_name": "आर्डर बनाएं"},
        {"activity_type_id": 2, "language_code": "bn", "translated_activity_name": "অর্ডার তৈরি করুন"},
        # VIEW_PRODUCT
        {"activity_type_id": 3, "language_code": "ar", "translated_activity_name": "عرض منتج"},
        {"activity_type_id": 3, "language_code": "en", "translated_activity_name": "View Product"},
        {"activity_type_id": 3, "language_code": "fr", "translated_activity_name": "Voir le produit"},
        {"activity_type_id": 3, "language_code": "ur", "translated_activity_name": "پروڈکٹ دیکھیں"},
        {"activity_type_id": 3, "language_code": "hi", "translated_activity_name": "उत्पाद देखें"},
        {"activity_type_id": 3, "language_code": "bn", "translated_activity_name": "পণ্য দেখুন"},
    ])

    # 3. أنواع الأحداث الأمنية (Security Event Types)
    security_event_types = [
        {"security_event_type_id": 1, "event_name_key": "FAILED_LOGIN_ATTEMPT"},
        {"security_event_type_id": 2, "event_name_key": "PASSWORD_RESET_REQUEST"},
        {"security_event_type_id": 3, "event_name_key": "ACCOUNT_SUSPENDED"},
    ]
    seed_main_table(db, SecurityEventType, "security_event_type_id", security_event_types)
    seed_translation_table(db, SecurityEventTypeTranslation, "security_event_type_id",[
         # FAILED_LOGIN_ATTEMPT
        {"security_event_type_id": 1, "language_code": "ar", "translated_event_name": "محاولة دخول فاشلة"},
        {"security_event_type_id": 1, "language_code": "en", "translated_event_name": "Failed Login Attempt"},
        {"security_event_type_id": 1, "language_code": "fr", "translated_event_name": "Tentative de connexion échouée"},
        {"security_event_type_id": 1, "language_code": "ur", "translated_event_name": "ناکام لاگ ان کی کوشش"},
        {"security_event_type_id": 1, "language_code": "hi", "translated_event_name": "असफल लॉगिन प्रयास"},
        {"security_event_type_id": 1, "language_code": "bn", "translated_event_name": "ব্যর্থ লগইন প্রচেষ্টা"},
        # PASSWORD_RESET_REQUEST
        {"security_event_type_id": 2, "language_code": "ar", "translated_event_name": "طلب إعادة تعيين كلمة المرور"},
        {"security_event_type_id": 2, "language_code": "en", "translated_event_name": "Password Reset Request"},
        {"security_event_type_id": 2, "language_code": "fr", "translated_event_name": "Demande de réinitialisation de mot de passe"},
        {"security_event_type_id": 2, "language_code": "ur", "translated_event_name": "پاس ورڈ دوبارہ ترتیب دینے की درخواست"},
        {"security_event_type_id": 2, "language_code": "hi", "translated_event_name": "पासवर्ड रीसेट अनुरोध"},
        {"security_event_type_id": 2, "language_code": "bn", "translated_event_name": "পাসওয়ার্ড রিসেট অনুরোধ"},
        # ACCOUNT_SUSPENDED
        {"security_event_type_id": 3, "language_code": "ar", "translated_event_name": "تم إيقاف الحساب"},
        {"security_event_type_id": 3, "language_code": "en", "translated_event_name": "Account Suspended"},
        {"security_event_type_id": 3, "language_code": "fr", "translated_event_name": "Compte suspendu"},
        {"security_event_type_id": 3, "language_code": "ur", "translated_event_name": "اکاؤنٹ معطل कर दिया गया"},
        {"security_event_type_id": 3, "language_code": "hi", "translated_event_name": "खाता निलंबित"},
        {"security_event_type_id": 3, "language_code": "bn", "translated_event_name": "অ্যাকাউন্ট স্থগিত"},
    ])

    db.commit()

    logger.info("--- Seeding Criteria & Reasons Tables ---")

    # 1. معايير التقييم
    review_criteria = [
        {"criteria_id": 1, "criteria_name_key": "PRODUCT_QUALITY"},
        {"criteria_id": 2, "criteria_name_key": "PACKAGING_QUALITY"},
        {"criteria_id": 3, "criteria_name_key": "DELIVERY_SPEED"},
        {"criteria_id": 4, "criteria_name_key": "SELLER_COMMUNICATION"},
    ]
    seed_main_table(db, ReviewCriterion, "criteria_id", review_criteria)
    seed_translation_table(db, ReviewCriterionTranslation, "criteria_id", [
        # PRODUCT_QUALITY
        {"criteria_id": 1, "language_code": "ar", "translated_criteria_name": "جودة المنتج"},
        {"criteria_id": 1, "language_code": "en", "translated_criteria_name": "Product Quality"},
        {"criteria_id": 1, "language_code": "fr", "translated_criteria_name": "Qualité du produit"},
        {"criteria_id": 1, "language_code": "ur", "translated_criteria_name": "مصنوعات کا معیار"},
        {"criteria_id": 1, "language_code": "hi", "translated_criteria_name": "उत्पाद की गुणवत्ता"},
        {"criteria_id": 1, "language_code": "bn", "translated_criteria_name": "পণ্যের গুণমান"},
        # PACKAGING_QUALITY
        {"criteria_id": 2, "language_code": "ar", "translated_criteria_name": "جودة التغليف"},
        {"criteria_id": 2, "language_code": "en", "translated_criteria_name": "Packaging Quality"},
        {"criteria_id": 2, "language_code": "fr", "translated_criteria_name": "Qualité de l'emballage"},
        {"criteria_id": 2, "language_code": "ur", "translated_criteria_name": "پیکیجنگ کا معیار"},
        {"criteria_id": 2, "language_code": "hi", "translated_criteria_name": "पैकेजिंग की गुणवत्ता"},
        {"criteria_id": 2, "language_code": "bn", "translated_criteria_name": "প্যাকেজিংয়ের গুণমান"},
        # DELIVERY_SPEED
        {"criteria_id": 3, "language_code": "ar", "translated_criteria_name": "سرعة التوصيل"},
        {"criteria_id": 3, "language_code": "en", "translated_criteria_name": "Delivery Speed"},
        {"criteria_id": 3, "language_code": "fr", "translated_criteria_name": "Rapidité de livraison"},
        {"criteria_id": 3, "language_code": "ur", "translated_criteria_name": "ترسیل کی رفتار"},
        {"criteria_id": 3, "language_code": "hi", "translated_criteria_name": "वितरण की गति"},
        {"criteria_id": 3, "language_code": "bn", "translated_criteria_name": "ডেলিভারির গতি"},
        # SELLER_COMMUNICATION
        {"criteria_id": 4, "language_code": "ar", "translated_criteria_name": "تواصل البائع"},
        {"criteria_id": 4, "language_code": "en", "translated_criteria_name": "Seller Communication"},
        {"criteria_id": 4, "language_code": "fr", "translated_criteria_name": "Communication du vendeur"},
        {"criteria_id": 4, "language_code": "ur", "translated_criteria_name": "بیچنے والے کی مواصلت"},
        {"criteria_id": 4, "language_code": "hi", "translated_criteria_name": "विक्रेता संचार"},
        {"criteria_id": 4, "language_code": "bn", "translated_criteria_name": "বিক্রেতার যোগাযোগ"},
    ])

    # 2. أسباب الإبلاغ عن المراجعات
    review_report_reasons = [
        {"reason_id": 1, "reason_key": "INAPPROPRIATE_CONTENT"},
        {"reason_id": 2, "reason_key": "SPAM"},
        {"reason_id": 3, "reason_key": "OFFENSIVE_LANGUAGE"},
        {"reason_id": 4, "reason_key": "NOT_RELEVANT"},
    ]
    seed_main_table(db, ReviewReportReason, "reason_id", review_report_reasons)
    seed_translation_table(db, ReviewReportReasonTranslation, "reason_id", [
        # INAPPROPRIATE_CONTENT
        {"reason_id": 1, "language_code": "ar", "translated_reason_text": "محتوى غير لائق"},
        {"reason_id": 1, "language_code": "en", "translated_reason_text": "Inappropriate Content"},
        {"reason_id": 1, "language_code": "fr", "translated_reason_text": "Contenu inapproprié"},
        {"reason_id": 1, "language_code": "ur", "translated_reason_text": "نامناسب مواد"},
        {"reason_id": 1, "language_code": "hi", "translated_reason_text": "अनुचित सामग्री"},
        {"reason_id": 1, "language_code": "bn", "translated_reason_text": "অনুপযুক্ত বিষয়বস্তু"},
        # SPAM
        {"reason_id": 2, "language_code": "ar", "translated_reason_text": "بريد مزعج (سبام)"},
        {"reason_id": 2, "language_code": "en", "translated_reason_text": "Spam"},
        {"reason_id": 2, "language_code": "fr", "translated_reason_text": "Spam"},
        {"reason_id": 2, "language_code": "ur", "translated_reason_text": "سپام"},
        {"reason_id": 2, "language_code": "hi", "translated_reason_text": "स्पैम"},
        {"reason_id": 2, "language_code": "bn", "translated_reason_text": "স্প্যাম"},
        # OFFENSIVE_LANGUAGE
        {"reason_id": 3, "language_code": "ar", "translated_reason_text": "لغة مسيئة"},
        {"reason_id": 3, "language_code": "en", "translated_reason_text": "Offensive Language"},
        {"reason_id": 3, "language_code": "fr", "translated_reason_text": "Langage offensant"},
        {"reason_id": 3, "language_code": "ur", "translated_reason_text": "جارحانہ زبان"},
        {"reason_id": 3, "language_code": "hi", "translated_reason_text": "अपमानजनक भाषा"},
        {"reason_id": 3, "language_code": "bn", "translated_reason_text": "আপত্তিকর ভাষা"},
        # NOT_RELEVANT
        {"reason_id": 4, "language_code": "ar", "translated_reason_text": "لا علاقة لها بالمنتج/الخدمة"},
        {"reason_id": 4, "language_code": "en", "translated_reason_text": "Not Relevant"},
        {"reason_id": 4, "language_code": "fr", "translated_reason_text": "Non pertinent"},
        {"reason_id": 4, "language_code": "ur", "translated_reason_text": "غیر متعلقہ"},
        {"reason_id": 4, "language_code": "hi", "translated_reason_text": "अप्रासंगिक"},
        {"reason_id": 4, "language_code": "bn", "translated_reason_text": "প্রাসঙ্গিক নয়"},
    ])

    db.commit()


    logger.info("--- Seeding Product Lookup Tables ---")

    # 1. حالات المنتج
    product_statuses = [
        {"product_status_id": 1, "status_name_key": "DRAFT"},
        {"product_status_id": 2, "status_name_key": "ACTIVE"},
        {"product_status_id": 3, "status_name_key": "INACTIVE"},
        {"product_status_id": 4, "status_name_key": "DISCONTINUED"},
    ]
    seed_main_table(db, ProductStatus, "product_status_id", product_statuses)
    # --- بيانات الترجمة لحالات المنتج ---
    seed_translation_table(db, ProductStatusTranslation, "product_status_id", [
        # DRAFT
        {"product_status_id": 1, "language_code": "ar", "translated_status_name": "مسودة"},
        {"product_status_id": 1, "language_code": "en", "translated_status_name": "Draft"},
        {"product_status_id": 1, "language_code": "fr", "translated_status_name": "Brouillon"},
        {"product_status_id": 1, "language_code": "ur", "translated_status_name": "مسودہ"},
        {"product_status_id": 1, "language_code": "hi", "translated_status_name": "ड्राफ़्ट"},
        {"product_status_id": 1, "language_code": "bn", "translated_status_name": "খসড়া"},        
        # ACTIVE
        {"product_status_id": 2, "language_code": "ar", "translated_status_name": "نشط"},
        {"product_status_id": 2, "language_code": "en", "translated_status_name": "Active"},
        {"product_status_id": 2, "language_code": "fr", "translated_status_name": "Actif"},
        {"product_status_id": 2, "language_code": "ur", "translated_status_name": "فعال"},
        {"product_status_id": 2, "language_code": "hi", "translated_status_name": "सक्रिय"},
        {"product_status_id": 2, "language_code": "bn", "translated_status_name": "সক্রিয়"},
        # INACTIVE
        {"product_status_id": 3, "language_code": "ar", "translated_status_name": "غير نشط"},
        {"product_status_id": 3, "language_code": "en", "translated_status_name": "Inactive"},
        {"product_status_id": 3, "language_code": "fr", "translated_status_name": "Inactif"},
        {"product_status_id": 3, "language_code": "ur", "translated_status_name": "غیر فعال"},
        {"product_status_id": 3, "language_code": "hi", "translated_status_name": "निष्क्रिय"},
        {"product_status_id": 3, "language_code": "bn", "translated_status_name": "নিষ্ক্রিয়"},
        # DISCONTINUED
        {"product_status_id": 4, "language_code": "ar", "translated_status_name": "متوقف"},
        {"product_status_id": 4, "language_code": "en", "translated_status_name": "Discontinued"},
        {"product_status_id": 4, "language_code": "fr", "translated_status_name": "Arrêté"},
        {"product_status_id": 4, "language_code": "ur", "translated_status_name": "بند کر دیا گیا۔"},
        {"product_status_id": 4, "language_code": "hi", "translated_status_name": "बंद कर दिया गया"},
        {"product_status_id": 4, "language_code": "bn", "translated_status_name": "বন্ধ করা হয়েছে"},
    ])
    # --- نهاية بيانات الترجمة ---

    # 2. وحدات القياس
    units_of_measure = [
        {"unit_id": 1, "unit_name_key": "KILOGRAM", "unit_abbreviation_key": "kg"},
        {"unit_id": 2, "unit_name_key": "BOX", "unit_abbreviation_key": "box"},
        {"unit_id": 3, "unit_name_key": "BUNCH", "unit_abbreviation_key": "bunch"},
    ]
    seed_main_table(db, UnitOfMeasure, "unit_id", units_of_measure)
    # --- بيانات الترجمة لوحدات القياس ---
    seed_translation_table(db, UnitOfMeasureTranslation, "unit_id", [
        # KILOGRAM
        {"unit_id": 1, "language_code": "ar", "translated_unit_name": "كيلوجرام", "translated_unit_abbreviation": "كجم"},
        {"unit_id": 1, "language_code": "en", "translated_unit_name": "Kilogram", "translated_unit_abbreviation": "kg"},
        {"unit_id": 1, "language_code": "fr", "translated_unit_name": "Kilogramme", "translated_unit_abbreviation": "kg"},
        {"unit_id": 1, "language_code": "ur", "translated_unit_name": "کلوگرام", "translated_unit_abbreviation": "کلوگرام"},
        {"unit_id": 1, "language_code": "hi", "translated_unit_name": "किलोग्राम", "translated_unit_abbreviation": "किग्रा"},
        {"unit_id": 1, "language_code": "bn", "translated_unit_name": "কিলোগ্রাম", "translated_unit_abbreviation": "কেজি"},
        # BOX
        {"unit_id": 2, "language_code": "ar", "translated_unit_name": "صندوق", "translated_unit_abbreviation": "صندوق"},
        {"unit_id": 2, "language_code": "en", "translated_unit_name": "Box", "translated_unit_abbreviation": "box"},
        {"unit_id": 2, "language_code": "fr", "translated_unit_name": "Boîte", "translated_unit_abbreviation": "boîte"},
        {"unit_id": 2, "language_code": "ur", "translated_unit_name": "ڈبہ", "translated_unit_abbreviation": "ڈبہ"},
        {"unit_id": 2, "language_code": "hi", "translated_unit_name": "बक्सा", "translated_unit_abbreviation": "बक्सा"},
        {"unit_id": 2, "language_code": "bn", "translated_unit_name": "বাক্স", "translated_unit_abbreviation": "বাক্স"},
        # BUNCH
        {"unit_id": 3, "language_code": "ar", "translated_unit_name": "حزمة", "translated_unit_abbreviation": "حزمة"},
        {"unit_id": 3, "language_code": "en", "translated_unit_name": "Bunch", "translated_unit_abbreviation": "bunch"},
        {"unit_id": 3, "language_code": "fr", "translated_unit_name": "Botte", "translated_unit_abbreviation": "botte"},
        {"unit_id": 3, "language_code": "ur", "translated_unit_name": "گچھا", "translated_unit_abbreviation": "گچھا"},
        {"unit_id": 3, "language_code": "hi", "translated_unit_name": "गुच्छा", "translated_unit_abbreviation": "गुच्छा"},
        {"unit_id": 3, "language_code": "bn", "translated_unit_name": "গুচ্ছ", "translated_unit_abbreviation": "গুচ্ছ"},
    ])
    # --- نهاية بيانات الترجمة ---
    
    # 3. فئات المنتجات (مثال مع فئات فرعية)
    product_categories = [
        {"category_id": 1, "category_name_key": "VEGETABLES", "is_active": True},
        {"category_id": 2, "category_name_key": "FRUITS", "is_active": True},
        {"category_id": 3, "category_name_key": "LEAFY_GREENS", "parent_category_id": 1, "is_active": True}, # <- فئة فرعية من الخضروات
    ]
    seed_main_table(db, ProductCategory, "category_id", product_categories)
    
    # ترجمات فئات المنتجات (Product Categories)
    seed_translation_table(db, ProductCategoryTranslation, "category_id", [
        # VEGETABLES
        {"category_id": 1, "language_code": "ar", "translated_category_name": "خضروات"},
        {"category_id": 1, "language_code": "en", "translated_category_name": "Vegetables"},
        {"category_id": 1, "language_code": "fr", "translated_category_name": "Légumes"},
        {"category_id": 1, "language_code": "ur", "translated_category_name": "سبزیاں"},
        {"category_id": 1, "language_code": "hi", "translated_category_name": "सब्जियां"},
        {"category_id": 1, "language_code": "bn", "translated_category_name": "সবজি"},
        # FRUITS
        {"category_id": 2, "language_code": "ar", "translated_category_name": "فواكه"},
        {"category_id": 2, "language_code": "en", "translated_category_name": "Fruits"},
        {"category_id": 2, "language_code": "fr", "translated_category_name": "Fruits"},
        {"category_id": 2, "language_code": "ur", "translated_category_name": "پھل"},
        {"category_id": 2, "language_code": "hi", "translated_category_name": "फल"},
        {"category_id": 2, "language_code": "bn", "translated_category_name": "ফল"},
        # LEAFY_GREENS
        {"category_id": 3, "language_code": "ar", "translated_category_name": "ورقيات"},
        {"category_id": 3, "language_code": "en", "translated_category_name": "Leafy Greens"},
        {"category_id": 3, "language_code": "fr", "translated_category_name": "Légumes-feuilles"},
        {"category_id": 3, "language_code": "ur", "translated_category_name": "پتوں والی سبزیاں"},
        {"category_id": 3, "language_code": "hi", "translated_category_name": "पत्तेदार साग"},
        {"category_id": 3, "language_code": "bn", "translated_category_name": "শাক"},
    ])

    db.commit()

   
    logger.info("Seeding License Verification Statuses...")
    license_statuses = [
        {"license_verification_status_id": 1, "status_name_key": "PENDING_REVIEW"},
        {"license_verification_status_id": 2, "status_name_key": "APPROVED"},
        {"license_verification_status_id": 3, "status_name_key": "REJECTED"},
        {"license_verification_status_id": 4, "status_name_key": "EXPIRED"},
    ]
    seed_main_table(db, LicenseVerificationStatus, "license_verification_status_id", license_statuses)
    # # # #
    seed_translation_table(db, LicenseVerificationStatusTranslation, "license_verification_status_id", [
        # PENDING_REVIEW
        {"license_verification_status_id": 1, "language_code": "ar", "translated_status_name": "قيد المراجعة"},
        {"license_verification_status_id": 1, "language_code": "en", "translated_status_name": "Pending Review"},
        # ... (باقي الترجمات للغات الأخرى)

        # APPROVED
        {"license_verification_status_id": 2, "language_code": "ar", "translated_status_name": "موافق عليه"},
        {"license_verification_status_id": 2, "language_code": "en", "translated_status_name": "Approved"},
        # ...

        # REJECTED
        {"license_verification_status_id": 3, "language_code": "ar", "translated_status_name": "مرفوض"},
        {"license_verification_status_id": 3, "language_code": "en", "translated_status_name": "Rejected"},
        # ...
        
        # EXPIRED
        {"license_verification_status_id": 4, "language_code": "ar", "translated_status_name": "منتهي الصلاحية"},
        {"license_verification_status_id": 4, "language_code": "en", "translated_status_name": "Expired"},
        # ...
    ])

    db.commit()

# (أضف هذا الكود داخل دالة seed_all في seed_db.py)

    logger.info("Seeding Issuing Authorities...")
    issuing_authorities = [
        {"authority_id": 1, "authority_name_key": "MINISTRY_OF_COMMERCE", "country_code": "SA"},
        {"authority_id": 2, "authority_name_key": "MINISTRY_OF_ENVIRONMENT_WATER_AGRICULTURE", "country_code": "SA"},
        {"authority_id": 3, "authority_name_key": "FREELANCE_PLATFORM", "country_code": "SA"},
    ]
    seed_main_table(db, IssuingAuthority, "authority_id", issuing_authorities)

    seed_translation_table(db, IssuingAuthorityTranslation, "authority_id", [
        # MINISTRY_OF_COMMERCE
        {"authority_id": 1, "language_code": "ar", "translated_authority_name": "وزارة التجارة"},
        {"authority_id": 1, "language_code": "en", "translated_authority_name": "Ministry of Commerce"},
        # ... باقي الترجمات

        # MINISTRY_OF_ENVIRONMENT_WATER_AGRICULTURE
        {"authority_id": 2, "language_code": "ar", "translated_authority_name": "وزارة البيئة والمياه والزراعة"},
        {"authority_id": 2, "language_code": "en", "translated_authority_name": "Ministry of Environment, Water and Agriculture"},
        # ...
        
        # FREELANCE_PLATFORM
        {"authority_id": 3, "language_code": "ar", "translated_authority_name": "منصة العمل الحر"},
        {"authority_id": 3, "language_code": "en", "translated_authority_name": "Freelance Work Platform"},
        # ...
    ])

    db.commit()

    logger.info("Seeding Attributes and their Values...")

    # 1. بذر السمات الرئيسية
    attributes = [
        {"attribute_id": 1, "attribute_name_key": "COLOR", "is_filterable": True, "is_variant_defining": True},
        {"attribute_id": 2, "attribute_name_key": "SIZE", "is_filterable": True, "is_variant_defining": True},
        {"attribute_id": 3, "attribute_name_key": "RIPENESS", "is_filterable": True},
    ]
    seed_main_table(db, Attribute, "attribute_id", attributes)

    # 2. بذر ترجمات السمات
    seed_translation_table(db, AttributeTranslation, "attribute_id", [
        # COLOR
        {"attribute_id": 1, "language_code": "ar", "translated_attribute_name": "اللون"},
        {"attribute_id": 1, "language_code": "en", "translated_attribute_name": "Color"},
        # SIZE
        {"attribute_id": 2, "language_code": "ar", "translated_attribute_name": "الحجم"},
        {"attribute_id": 2, "language_code": "en", "translated_attribute_name": "Size"},
        # RIPENESS
        {"attribute_id": 3, "language_code": "ar", "translated_attribute_name": "درجة النضج"},
        {"attribute_id": 3, "language_code": "en", "translated_attribute_name": "Ripeness"},
    ])

    # 3. بذر قيم السمات الممكنة
    attribute_values = [
        # Values for COLOR
        {"attribute_value_id": 1, "attribute_id": 1, "attribute_value_key": "RED", "sort_order": 1},
        {"attribute_value_id": 2, "attribute_id": 1, "attribute_value_key": "GREEN", "sort_order": 2},
        {"attribute_value_id": 3, "attribute_id": 1, "attribute_value_key": "YELLOW", "sort_order": 3},
        # Values for SIZE
        {"attribute_value_id": 4, "attribute_id": 2, "attribute_value_key": "SMALL", "sort_order": 1},
        {"attribute_value_id": 5, "attribute_id": 2, "attribute_value_key": "MEDIUM", "sort_order": 2},
        {"attribute_value_id": 6, "attribute_id": 2, "attribute_value_key": "LARGE", "sort_order": 3},
        # Values for RIPENESS
        {"attribute_value_id": 7, "attribute_id": 3, "attribute_value_key": "UNRIPE", "sort_order": 1},
        {"attribute_value_id": 8, "attribute_id": 3, "attribute_value_key": "RIPE", "sort_order": 2},
        {"attribute_value_id": 9, "attribute_id": 3, "attribute_value_key": "OVERRIPE", "sort_order": 3},
    ]
    seed_main_table(db, AttributeValue, "attribute_value_id", attribute_values)

    # 4. بذر ترجمات قيم السمات
    seed_translation_table(db, AttributeValueTranslation, "attribute_value_id", [
        # RED
        {"attribute_value_id": 1, "language_code": "ar", "translated_value_name": "أحمر"},
        {"attribute_value_id": 1, "language_code": "en", "translated_value_name": "Red"},
        # GREEN
        {"attribute_value_id": 2, "language_code": "ar", "translated_value_name": "أخضر"},
        {"attribute_value_id": 2, "language_code": "en", "translated_value_name": "Green"},
        # YELLOW
        {"attribute_value_id": 3, "language_code": "ar", "translated_value_name": "أصفر"},
        {"attribute_value_id": 3, "language_code": "en", "translated_value_name": "Yellow"},
        # SMALL
        {"attribute_value_id": 4, "language_code": "ar", "translated_value_name": "صغير"},
        {"attribute_value_id": 4, "language_code": "en", "translated_value_name": "Small"},
        # MEDIUM
        {"attribute_value_id": 5, "language_code": "ar", "translated_value_name": "متوسط"},
        {"attribute_value_id": 5, "language_code": "en", "translated_value_name": "Medium"},
        # LARGE
        {"attribute_value_id": 6, "language_code": "ar", "translated_value_name": "كبير"},
        {"attribute_value_id": 6, "language_code": "en", "translated_value_name": "Large"},
    ])
    
    db.commit()

    logger.info("Seeding Inventory Lookup Tables...")
    # حالات بنود المخزون
    inventory_statuses = [
        {"inventory_item_status_id": 1, "status_name_key": "IN_STOCK"},
        {"inventory_item_status_id": 2, "status_name_key": "LOW_STOCK"},
        {"inventory_item_status_id": 3, "status_name_key": "OUT_OF_STOCK"},
    ]
    seed_main_table(db, InventoryItemStatus, "inventory_item_status_id", inventory_statuses)

    # أنواع حركات المخزون
    transaction_types = [
        {"transaction_type_id": 1, "transaction_type_name_key": "INITIAL_STOCK"},
        {"transaction_type_id": 2, "transaction_type_name_key": "SALE_DEDUCTION"},
        {"transaction_type_id": 3, "transaction_type_name_key": "RETURN_TO_STOCK"},
        {"transaction_type_id": 4, "transaction_type_name_key": "MANUAL_ADJUSTMENT_IN"},
        {"transaction_type_id": 5, "transaction_type_name_key": "MANUAL_ADJUSTMENT_OUT"},
    ]
    seed_main_table(db, InventoryTransactionType, "transaction_type_id", transaction_types)
    
    # يمكنك إضافة الترجمات لهذه الجداول بنفس النمط السابق
    db.commit()


    logger.info("Seeding Expected Crop Statuses...")
    expected_crop_statuses = [
        {"status_id": 1, "status_name_key": "AVAILABLE_FOR_BOOKING"},
        {"status_id": 2, "status_name_key": "FULLY_BOOKED"},
        {"status_id": 3, "status_name_key": "HARVESTED"},
        {"status_id": 4, "status_name_key": "CANCELLED"},
    ]
    seed_main_table(db, ExpectedCropStatus, "status_id", expected_crop_statuses)

    # أضف الترجمات بنفس النمط إذا أردت
    # ...
    
    db.commit()

    logger.info("Seeding Permissions...")
    PERMISSIONS = [        
        # ================================================================
        # --- صلاحيات المجموعة 1: إدارة المستخدمين والهوية والوصول
        # ================================================================
        # --- 1.أ: صلاحيات الملف الشخصي والحساب (للمستخدم نفسه) ---
        {"permission_id": 1001, "permission_name_key": "PROFILE_VIEW_OWN", "module_group": "User Profile", "description": "السماح للمستخدم بعرض بيانات ملفه الشخصي"},
        {"permission_id": 1002, "permission_name_key": "PROFILE_UPDATE_OWN", "module_group": "User Profile", "description": "السماح للمستخدم بتحديث بياناته الأساسية (الاسم، البريد)"},
        {"permission_id": 1003, "permission_name_key": "PROFILE_MANAGE_PREFERENCES_OWN", "module_group": "User Profile", "description": "إدارة تفضيلاته الخاصة"},
        {"permission_id": 1004, "permission_name_key": "PROFILE_VIEW_STATUS_HISTORY_OWN", "module_group": "User Profile", "description": "عرض سجل تغييرات حالة حسابه"},
        # --- 1.ب: صلاحيات إدارة الأدوار والصلاحيات (للمسؤولين) ---
        {"permission_id": 1101, "permission_name_key": "RBAC_MANAGE_ROLES", "module_group": "Admin: RBAC", "description": "إنشاء وتعديل وحذف الأدوار"},
        {"permission_id": 1102, "permission_name_key": "RBAC_MANAGE_PERMISSIONS", "module_group": "Admin: RBAC", "description": "إسناد وسحب الصلاحيات من الأدوار"},
        {"permission_id": 1103, "permission_name_key": "RBAC_ASSIGN_ROLES_TO_USERS", "module_group": "Admin: RBAC", "description": "إسناد وسحب الأدوار من المستخدمين"},
        # --- 1.ج: صلاحيات إدارة التراخيص والتحقق ---
        {"permission_id": 1201, "permission_name_key": "LICENSE_CREATE_OWN", "module_group": "Verification", "description": "رفع ترخيص أو وثيقة جديدة"},
        {"permission_id": 1202, "permission_name_key": "LICENSE_VIEW_OWN", "module_group": "Verification", "description": "عرض قائمة التراخيص الخاصة به"},
        {"permission_id": 1203, "permission_name_key": "LICENSE_DELETE_OWN", "module_group": "Verification", "description": "حذف ترخيص قيد المراجعة"},
        {"permission_id": 1210, "permission_name_key": "ADMIN_VERIFY_ANY_LICENSE", "module_group": "Admin: Verification", "description": "مراجعة والموافقة على أو رفض تراخيص المستخدمين"},
        {"permission_id": 1211, "permission_name_key": "ADMIN_MANAGE_LICENSES", "module_group": "Admin: Verification", "description": "إدارة شاملة للتراخيص والتحقق (عرض، تحديث، إدارة حالات التحقق)"},
        # --- 1.د: صلاحيات إدارة العناوين ---
        {"permission_id": 1301, "permission_name_key": "ADDRESS_CREATE_OWN", "module_group": "Addresses", "description": "إضافة عنوان جديد"},
        {"permission_id": 1302, "permission_name_key": "ADDRESS_VIEW_OWN", "module_group": "Addresses", "description": "عرض قائمة عناوينه"},
        {"permission_id": 1303, "permission_name_key": "ADDRESS_UPDATE_OWN", "module_group": "Addresses", "description": "تحديث أحد عناوينه"},
        {"permission_id": 1304, "permission_name_key": "ADDRESS_DELETE_OWN", "module_group": "Addresses", "description": "حذف أحد عناوينه"},
        # --- 1.هـ: صلاحيات إدارة أمان الحساب ---
        {"permission_id": 1401, "permission_name_key": "SECURITY_CHANGE_PASSWORD_OWN", "module_group": "Security", "description": "تغيير كلمة المرور الخاصة به"},
        {"permission_id": 1402, "permission_name_key": "SECURITY_VIEW_SESSIONS_OWN", "module_group": "Security", "description": "عرض جلسات الدخول النشطة الخاصة به"},
        {"permission_id": 1403, "permission_name_key": "SECURITY_TERMINATE_SESSION_OWN", "module_group": "Security", "description": "إنهاء جلسة دخول على جهاز آخر"},
        # --- صلاحيات إدارية عامة على المستخدمين ---
        {"permission_id": 1501, "permission_name_key": "ADMIN_VIEW_ANY_USER", "module_group": "Admin: Users", "description": "عرض ملف أي مستخدم في النظام"},
        {"permission_id": 1502, "permission_name_key": "ADMIN_UPDATE_ANY_USER", "module_group": "Admin: Users", "description": "تحديث ملف أي مستخدم في النظام"},
        {"permission_id": 1503, "permission_name_key": "ADMIN_MANAGE_USER_STATUS", "module_group": "Admin: Users", "description": "تغيير حالة حساب أي مستخدم"},
        {"permission_id": 1504, "permission_name_key": "ADMIN_MANAGE_USERS", "module_group": "Admin: Users", "description": "إدارة شاملة للمستخدمين (عرض، تحديث، تغيير حالة، حذف ناعم)"},

        # ================================================================
        # --- صلاحيات المجموعة 2: إدارة كتالوج المنتجات والمخزون NEW
        # ================================================================
        # --- صلاحيات البائعين على منتجاتهم ---
        {"permission_id": 2001, "permission_name_key": "PRODUCT_CREATE_OWN", "module_group": "Products", "description": "إنشاء منتج جديد خاص بالبائع"},
        {"permission_id": 2002, "permission_name_key": "PRODUCT_UPDATE_OWN", "module_group": "Products", "description": "تحديث منتجاته الخاصة فقط"},
        {"permission_id": 2003, "permission_name_key": "PRODUCT_DELETE_OWN", "module_group": "Products", "description": "حذف (ناعم) لمنتجاته الخاصة فقط"},
        {"permission_id": 2004, "permission_name_key": "PRODUCT_VIEW_OWN", "module_group": "Products", "description": "عرض قائمة منتجاته الخاصة (بما في ذلك المسودات)"},
        {"permission_id": 2005, "permission_name_key": "PRODUCT_MANAGE_PACKAGING_OWN", "module_group": "Products", "description": "إدارة خيارات التعبئة لمنتجاته"},
        {"permission_id": 2006, "permission_name_key": "PRODUCT_ASSIGN_ATTRIBUTES_OWN", "module_group": "Products", "description": "إسناد السمات المتاحة لمنتجاته وأصنافه"},
        
        # --- صلاحيات البائعين على المخزون والعروض المستقبلية ---
        {"permission_id": 2101, "permission_name_key": "INVENTORY_MANAGE_OWN", "module_group": "Inventory", "description": "تحديث كميات المخزون لمنتجاته"},
        {"permission_id": 2102, "permission_name_key": "INVENTORY_VIEW_HISTORY_OWN", "module_group": "Inventory", "description": "عرض سجل حركات المخزون لمنتجاته"},
        {"permission_id": 2103, "permission_name_key": "CROP_MANAGE_OWN", "module_group": "Future Stock", "description": "إدارة المحاصيل المتوقعة الخاصة به (خاص بالمزارعين)"},

        # --- صلاحيات المسؤولين على المنتجات والجداول المرجعية ---
        {"permission_id": 2201, "permission_name_key": "ADMIN_PRODUCT_VIEW_ANY", "module_group": "Admin: Products", "description": "عرض أي منتج في النظام"},
        {"permission_id": 2202, "permission_name_key": "ADMIN_PRODUCT_MANAGE_ANY", "module_group": "Admin: Products", "description": "تحديث أو حذف أي منتج في النظام"},
        {"permission_id": 2203, "permission_name_key": "ADMIN_MANAGE_CATEGORIES", "module_group": "Admin: Lookups", "description": "إدارة فئات المنتجات"},
        {"permission_id": 2204, "permission_name_key": "ADMIN_MANAGE_UNITS", "module_group": "Admin: Lookups", "description": "إدارة وحدات القياس"},
        {"permission_id": 2205, "permission_name_key": "ADMIN_MANAGE_ATTRIBUTES", "module_group": "Admin: Lookups", "description": "إدارة السمات وقيمها المرجعية"},
        # # ================================================================
        # # --- صلاحيات المجموعة 2: إدارة كتالوج المنتجات والمخزون OLD
        # # ================================================================
        # # --- 2.أ: صلاحيات إدارة المنتجات الأساسية (للبائعين) ---
        # {"permission_id": 2001, "permission_name_key": "PRODUCT_CREATE_OWN", "module_group": "Products", "description": "إنشاء منتج جديد خاص بالبائع"},
        # {"permission_id": 2002, "permission_name_key": "PRODUCT_UPDATE_OWN", "module_group": "Products", "description": "تحديث منتجاته الخاصة فقط"},
        # {"permission_id": 2003, "permission_name_key": "PRODUCT_DELETE_OWN", "module_group": "Products", "description": "حذف (ناعم) لمنتجاته الخاصة فقط"},
        # {"permission_id": 2004, "permission_name_key": "PRODUCT_VIEW_OWN", "module_group": "Products", "description": "عرض قائمة منتجاته الخاصة (بما في ذلك المسودات)"},
        # # --- 2.ب و 2.ج: صلاحيات إدارة تفاصيل المنتج (للبائعين) ---
        # {"permission_id": 2101, "permission_name_key": "PRODUCT_MANAGE_VARIETIES_OWN", "module_group": "Products", "description": "إدارة أصناف المنتج لمنتجاته"},
        # {"permission_id": 2102, "permission_name_key": "PRODUCT_MANAGE_ATTRIBUTES_OWN", "module_group": "Products", "description": "إسناد سمات وقيم لمنتجاته"},
        # {"permission_id": 2103, "permission_name_key": "PRODUCT_MANAGE_PACKAGING_OWN", "module_group": "Products", "description": "إدارة خيارات التعبئة لمنتجاته"},
        # {"permission_id": 2104, "permission_name_key": "PRODUCT_MANAGE_IMAGES_OWN", "module_group": "Products", "description": "إدارة صور منتجاته"},
        # # --- 2.د: صلاحيات إدارة المخزون (للبائعين) ---
        # {"permission_id": 2201, "permission_name_key": "INVENTORY_MANAGE_OWN", "module_group": "Inventory", "description": "تحديث كميات المخزون لمنتجاته"},
        # {"permission_id": 2202, "permission_name_key": "INVENTORY_VIEW_HISTORY_OWN", "module_group": "Inventory", "description": "عرض سجل حركات المخزون لمنتجاته"},
        # # --- 2.هـ: صلاحيات إدارة العروض المستقبلية (للمزارعين) ---
        # {"permission_id": 2301, "permission_name_key": "CROP_MANAGE_OWN", "module_group": "Future Stock", "description": "إدارة المحاصيل المتوقعة الخاصة به"},
        # # --- صلاحيات إدارية على المنتجات (للمسؤولين) ---
        # {"permission_id": 2501, "permission_name_key": "ADMIN_PRODUCT_VIEW_ANY", "module_group": "Admin: Products", "description": "عرض أي منتج في النظام"},
        # {"permission_id": 2502, "permission_name_key": "ADMIN_PRODUCT_UPDATE_ANY", "module_group": "Admin: Products", "description": "تحديث أي منتج في النظام"},
        # {"permission_id": 2503, "permission_name_key": "ADMIN_PRODUCT_DELETE_ANY", "module_group": "Admin: Products", "description": "حذف أي منتج في النظام"},
        # {"permission_id": 2504, "permission_name_key": "ADMIN_MANAGE_CATEGORIES", "module_group": "Admin: Lookups", "description": "إدارة فئات المنتجات"},
        # {"permission_id": 2505, "permission_name_key": "ADMIN_MANAGE_UNITS", "module_group": "Admin: Lookups", "description": "إدارة وحدات القياس"},
        # {"permission_id": 2506, "permission_name_key": "ADMIN_MANAGE_ATTRIBUTES", "module_group": "Admin: Lookups", "description": "إدارة السمات وقيمها"},

        # ================================================================
        # --- صلاحيات المجموعة 3: إدارة الأسعار الديناميكية
        # ================================================================
        # --- صلاحيات البائعين على قواعد التسعير الخاصة بهم ---
        {"permission_id": 3001, "permission_name_key": "PRICING_RULE_CREATE_OWN", "module_group": "Pricing", "description": "إنشاء قاعدة تسعير جديدة خاصة به"},
        {"permission_id": 3002, "permission_name_key": "PRICING_RULE_VIEW_OWN", "module_group": "Pricing", "description": "عرض قائمة بقواعد التسعير الخاصة به"},
        {"permission_id": 3003, "permission_name_key": "PRICING_RULE_UPDATE_OWN", "module_group": "Pricing", "description": "تحديث قواعد التسعير الخاصة به (بما في ذلك مستوياتها)"},
        {"permission_id": 3004, "permission_name_key": "PRICING_RULE_DELETE_OWN", "module_group": "Pricing", "description": "حذف قواعد التسعير الخاصة به"},
        {"permission_id": 3005, "permission_name_key": "PRICING_RULE_ASSIGN_OWN", "module_group": "Pricing", "description": "إسناد قواعد التسعير الخاصة به لخيارات التعبئة الخاصة به"},
        # --- صلاحيات المسؤولين على جميع قواعد التسعير ---
        {"permission_id": 3101, "permission_name_key": "ADMIN_PRICING_RULE_VIEW_ANY", "module_group": "Admin: Pricing", "description": "عرض أي قاعدة تسعير في النظام"},
        {"permission_id": 3102, "permission_name_key": "ADMIN_PRICING_RULE_MANAGE_ANY", "module_group": "Admin: Pricing", "description": "تعديل أو حذف أي قاعدة تسعير في النظام"},

        # ================================================================
        # --- صلاحيات المجموعة 4: إدارة عمليات السوق
        # ================================================================
        # --- 4.أ: صلاحيات الطلبات المباشرة ---
        {"permission_id": 4001, "permission_name_key": "ORDER_CREATE_DIRECT", "module_group": "Orders", "description": "إنشاء طلب شراء مباشر"},
        {"permission_id": 4002, "permission_name_key": "ORDER_VIEW_OWN", "module_group": "Orders", "description": "عرض طلباته الخاصة (سواء كان بائعًا أو مشتريًا)"},
        {"permission_id": 4003, "permission_name_key": "ORDER_UPDATE_OWN_STATUS", "module_group": "Orders", "description": "تحديث حالة الطلبات الواردة له كبائع (مثل 'تم الشحن')"},
        {"permission_id": 4004, "permission_name_key": "ORDER_CANCEL_OWN", "module_group": "Orders", "description": "إلغاء طلب (إذا كانت الحالة تسمح بذلك)"},
        # --- 4.ب: صلاحيات طلبات عروض الأسعار (RFQs) ---
        {"permission_id": 4101, "permission_name_key": "RFQ_CREATE_PURCHASE", "module_group": "RFQs", "description": "إنشاء طلب عرض سعر لغرض الشراء"},
        {"permission_id": 4102, "permission_name_key": "RFQ_MANAGE_OWN", "module_group": "RFQs", "description": "تعديل وإلغاء طلبات عروض الأسعار الخاصة به"},
        {"permission_id": 4103, "permission_name_key": "RFQ_VIEW_AVAILABLE", "module_group": "RFQs", "description": "عرض طلبات عروض الأسعار المتاحة التي يمكنه الرد عليها (للبائعين)"},
        # --- 4.ج: صلاحيات عروض الأسعار (Quotes) ---
        {"permission_id": 4201, "permission_name_key": "QUOTE_SUBMIT_OWN", "module_group": "Quotes", "description": "تقديم عرض سعر ردًا على RFQ"},
        {"permission_id": 4202, "permission_name_key": "QUOTE_MANAGE_OWN", "module_group": "Quotes", "description": "تعديل وسحب عروض الأسعار الخاصة به"},
        {"permission_id": 4203, "permission_name_key": "QUOTE_ACCEPT_ANY", "module_group": "Quotes", "description": "قبول عرض سعر مقدم لـ RFQ الخاص به (للمشتري)"},
        # --- 4.د: صلاحيات الشحنات ---
        {"permission_id": 4301, "permission_name_key": "SHIPMENT_CREATE_OWN", "module_group": "Shipments", "description": "إنشاء شحنة لطلب صادر منه (كبائع)"},
        {"permission_id": 4302, "permission_name_key": "SHIPMENT_UPDATE_OWN", "module_group": "Shipments", "description": "تحديث معلومات الشحن (مثل رقم التتبع) لشحناته"},
        # --- صلاحيات إدارية على عمليات السوق ---
        {"permission_id": 4501, "permission_name_key": "ADMIN_ORDER_VIEW_ANY", "module_group": "Admin: Market", "description": "عرض أي طلب في النظام"},
        {"permission_id": 4502, "permission_name_key": "ADMIN_ORDER_MANAGE_ANY", "module_group": "Admin: Market", "description": "تعديل أو إلغاء أي طلب في النظام"},
        {"permission_id": 4503, "permission_name_key": "ADMIN_RFQ_VIEW_ANY", "module_group": "Admin: Market", "description": "عرض أي طلب عرض سعر في النظام"},
        {"permission_id": 4504, "permission_name_key": "ADMIN_QUOTE_VIEW_ANY", "module_group": "Admin: Market", "description": "عرض أي عرض سعر في النظام"},

        # ================================================================
        # --- صلاحيات المجموعة 5: إدارة المزادات
        # ================================================================
        # --- صلاحيات البائعين على مزاداتهم ---
        {"permission_id": 5001, "permission_name_key": "AUCTION_CREATE_OWN", "module_group": "Auctions", "description": "إنشاء مزاد جديد خاص به"},
        {"permission_id": 5002, "permission_name_key": "AUCTION_MANAGE_OWN", "module_group": "Auctions", "description": "تعديل وإلغاء وإدارة (مثل قبول المشاركين) مزاداته الخاصة"},
        # --- صلاحيات المشترين والمزايدين ---
        {"permission_id": 5101, "permission_name_key": "AUCTION_VIEW_ANY_OPEN", "module_group": "Auctions", "description": "عرض قائمة المزادات المفتوحة"},
        {"permission_id": 5102, "permission_name_key": "AUCTION_PLACE_BID", "module_group": "Auctions", "description": "تقديم مزايدة في مزاد مفتوح ومسموح بالمشاركة فيه"},
        {"permission_id": 5103, "permission_name_key": "AUCTION_MANAGE_AUTOBID_OWN", "module_group": "Auctions", "description": "إدارة إعدادات المزايدة التلقائية الخاصة به"},
        {"permission_id": 5104, "permission_name_key": "AUCTION_MANAGE_WATCHLIST_OWN", "module_group": "Auctions", "description": "إضافة أو إزالة مزادات من قائمة المراقبة الخاصة به"},
        {"permission_id": 5105, "permission_name_key": "AUCTION_VIEW_OWN_BIDS_AND_WINS", "module_group": "Auctions", "description": "عرض مزايداته والمزادات التي فاز بها"},
        # --- صلاحيات المسؤولين على جميع المزادات ---
        {"permission_id": 5201, "permission_name_key": "ADMIN_AUCTION_MANAGE_ANY", "module_group": "Admin: Auctions", "description": "تعديل أو إلغاء أي مزاد في النظام"},
        {"permission_id": 5202, "permission_name_key": "ADMIN_MANAGE_BIDS", "module_group": "Admin: Auctions", "description": "إدارة المزايدات (مثل إلغاء مزايدة مشبوهة)"},
        {"permission_id": 5203, "permission_name_key": "ADMIN_MANAGE_SETTLEMENTS", "module_group": "Admin: Auctions", "description": "مراقبة وإدارة عمليات تسوية المزادات"},

        # ================================================================
        # --- صلاحيات المجموعة 6: إدارة المراجعات والتقييمات
        # ================================================================
        # --- صلاحيات المستخدمين العامة على المراجعات ---
        {"permission_id": 6001, "permission_name_key": "REVIEW_CREATE_OWN", "module_group": "Reviews", "description": "إنشاء مراجعة على منتج أو بائع بعد إتمام معاملة"},
        {"permission_id": 6002, "permission_name_key": "REVIEW_UPDATE_OWN", "module_group": "Reviews", "description": "تعديل مراجعة قام بها المستخدم نفسه (ضمن فترة زمنية محددة)"},
        {"permission_id": 6003, "permission_name_key": "REVIEW_DELETE_OWN", "module_group": "Reviews", "description": "حذف مراجعة قام بها المستخدم نفسه"},
        {"permission_id": 6004, "permission_name_key": "REVIEW_REPORT_ANY", "module_group": "Reviews", "description": "الإبلاغ عن أي مراجعة يعتقد أنها مخالفة"},
        # --- صلاحيات البائعين على المراجعات ---
        {"permission_id": 6101, "permission_name_key": "REVIEW_RESPOND_OWN", "module_group": "Reviews", "description": "الرد على المراجعات التي تمت على منتجاته أو ملفه التجاري"},
        # --- صلاحيات المسؤولين على المراجعات ---
        {"permission_id": 6201, "permission_name_key": "ADMIN_REVIEW_VIEW_ANY", "module_group": "Admin: Reviews", "description": "عرض أي مراجعة في النظام (بما في ذلك التي بانتظار الموافقة)"},
        {"permission_id": 6202, "permission_name_key": "ADMIN_REVIEW_MANAGE_STATUS", "module_group": "Admin: Reviews", "description": "الموافقة على، رفض، أو حذف أي مراجعة"},
        {"permission_id": 6203, "permission_name_key": "ADMIN_MANAGE_REVIEW_REPORTS", "module_group": "Admin: Reviews", "description": "مراجعة ومعالجة البلاغات على المراجعات"},
        {"permission_id": 6204, "permission_name_key": "ADMIN_MANAGE_REVIEW_CRITERIA", "module_group": "Admin: Lookups", "description": "إدارة معايير التقييم (مثل: جودة المنتج، سرعة التوصيل)"},
        
        # ================================================================
        # --- صلاحيات المجموعة 7: إدارة مخزون إعادة البيع
        # ================================================================
        # --- صلاحيات الموزع (Reseller) على مخزونه وعروضه ---
        {"permission_id": 7001, "permission_name_key": "RESELLER_INVENTORY_VIEW_OWN", "module_group": "Reselling", "description": "عرض المخزون الخاص به المتاح لإعادة البيع"},
        {"permission_id": 7002, "permission_name_key": "RESELLER_SALES_OFFER_MANAGE_OWN", "module_group": "Reselling", "description": "إنشاء وتعديل وحذف عروض البيع الخاصة به لعملائه"},
        {"permission_id": 7003, "permission_name_key": "RESELLER_CUSTOMER_ORDER_MANAGE_OWN", "module_group": "Reselling", "description": "إدارة الطلبات الواردة من عملائه"},
        # --- صلاحيات المسؤولين على عمليات الموزعين ---
        {"permission_id": 7101, "permission_name_key": "ADMIN_RESELLER_INVENTORY_VIEW_ANY", "module_group": "Admin: Reselling", "description": "عرض مخزون أي موزع في النظام"},
        {"permission_id": 7102, "permission_name_key": "ADMIN_RESELLER_ORDERS_VIEW_ANY", "module_group": "Admin: Reselling", "description": "عرض طلبات عملاء أي موزع في النظام"},
        
        # ================================================================
        # --- صلاحيات المجموعة 8: إدارة المحفظة والمدفوعات
        # ================================================================
        # --- صلاحيات المستخدم على محفظته الخاصة ---
        {"permission_id": 8001, "permission_name_key": "WALLET_VIEW_OWN", "module_group": "Wallet", "description": "عرض رصيد وتفاصيل محفظته الخاصة"},
        {"permission_id": 8002, "permission_name_key": "WALLET_VIEW_TRANSACTIONS_OWN", "module_group": "Wallet", "description": "عرض سجل المعاملات الخاص بمحفظته"},
        {"permission_id": 8003, "permission_name_key": "WALLET_REQUEST_WITHDRAWAL_OWN", "module_group": "Wallet", "description": "إنشاء طلب لسحب رصيد من محفظته"},
        {"permission_id": 8004, "permission_name_key": "WALLET_DEPOSIT_FUNDS_OWN", "module_group": "Wallet", "description": "إيداع الأموال في محفظته عبر بوابات الدفع"},
        # --- صلاحيات المسؤولين على جميع المحافظ والعمليات المالية ---
        {"permission_id": 8101, "permission_name_key": "ADMIN_WALLET_VIEW_ANY", "module_group": "Admin: Finance", "description": "عرض تفاصيل ورصيد محفظة أي مستخدم"},
        {"permission_id": 8102, "permission_name_key": "ADMIN_WALLET_ADJUST_BALANCE", "module_group": "Admin: Finance", "description": "تعديل رصيد محفظة أي مستخدم يدويًا (صلاحية حساسة جدًا)"},
        {"permission_id": 8103, "permission_name_key": "ADMIN_MANAGE_WITHDRAWAL_REQUESTS", "module_group": "Admin: Finance", "description": "مراجعة والموافقة على أو رفض طلبات السحب"},
        {"permission_id": 8104, "permission_name_key": "ADMIN_VIEW_ANY_TRANSACTION", "module_group": "Admin: Finance", "description": "عرض سجل معاملات أي محفظة في النظام"},
        {"permission_id": 8105, "permission_name_key": "ADMIN_VIEW_COMMISSIONS", "module_group": "Admin: Finance", "description": "عرض تقارير عمولات المنصة"},
        {"permission_id": 8106, "permission_name_key": "ADMIN_MANAGE_PAYMENT_GATEWAYS", "module_group": "Admin: Lookups", "description": "إدارة بوابات الدفع المعتمدة في النظام"},
        
        # ================================================================
        # --- صلاحيات المجموعة 9: إدارة اتفاقيات الدفع الآجل
        # ================================================================
        # --- صلاحيات البائعين على الاتفاقيات التي ينشئونها ---
        {"permission_id": 9001, "permission_name_key": "AGREEMENT_CREATE_OWN", "module_group": "Agreements", "description": "إنشاء اتفاقية دفع آجل جديدة لمشترٍ"},
        {"permission_id": 9002, "permission_name_key": "AGREEMENT_VIEW_OWN_AS_SELLER", "module_group": "Agreements", "description": "عرض الاتفاقيات التي أنشأها كبائع"},
        {"permission_id": 9003, "permission_name_key": "AGREEMENT_MANAGE_OWN", "module_group": "Agreements", "description": "تعديل أو إلغاء اتفاقياته (إذا كانت الحالة تسمح بذلك)"},
        {"permission_id": 9004, "permission_name_key": "AGREEMENT_RECORD_PAYMENT_OWN", "module_group": "Agreements", "description": "تسجيل دفعة يدوية تم استلامها من المشتري لأحد الأقساط"},
        # --- صلاحيات المشترين على الاتفاقيات الخاصة بهم ---
        {"permission_id": 9101, "permission_name_key": "AGREEMENT_VIEW_OWN_AS_BUYER", "module_group": "Agreements", "description": "عرض الاتفاقيات التي هو طرف فيها كمشترٍ"},
        {"permission_id": 9102, "permission_name_key": "AGREEMENT_ACCEPT_OR_REJECT", "module_group": "Agreements", "description": "قبول أو رفض اتفاقية دفع آجل معروضة عليه"},
        {"permission_id": 9103, "permission_name_key": "AGREEMENT_MAKE_PAYMENT_OWN", "module_group": "Agreements", "description": "دفع قسط مستحق عبر المنصة"},
        # --- صلاحيات المسؤولين على جميع الاتفاقيات ---
        {"permission_id": 9201, "permission_name_key": "ADMIN_AGREEMENT_VIEW_ANY", "module_group": "Admin: Agreements", "description": "عرض أي اتفاقية دفع آجل في النظام"},
        {"permission_id": 9202, "permission_name_key": "ADMIN_AGREEMENT_MANAGE_ANY", "module_group": "Admin: Agreements", "description": "تعديل أو إلغاء أي اتفاقية في حال وجود نزاع أو مشكلة"},
        
        # ================================================================
        # --- صلاحيات المجموعة 10: إدارة الضمان الذهبي
        # ================================================================
        # --- صلاحيات المستخدمين (المشترين والبائعين) على المطالبات ---
        {"permission_id": 10001, "permission_name_key": "GG_CLAIM_CREATE_OWN", "module_group": "Golden Guarantee", "description": "إنشاء مطالبة ضمان ذهبي على طلب قام به (للمشتري)"},
        {"permission_id": 10002, "permission_name_key": "GG_CLAIM_VIEW_OWN", "module_group": "Golden Guarantee", "description": "عرض المطالبات الخاصة به (كمشترٍ أو كبائع)"},
        {"permission_id": 10003, "permission_name_key": "GG_CLAIM_ADD_EVIDENCE_OWN", "module_group": "Golden Guarantee", "description": "إضافة أدلة (صور، ملاحظات) إلى مطالبته الخاصة"},
        {"permission_id": 10004, "permission_name_key": "GG_CLAIM_MANAGE_RESOLUTION_OWN", "module_group": "Golden Guarantee", "description": "قبول أو رفض الحل المقترح من الإدارة للمطالبة"},
        # --- صلاحيات المسؤولين على جميع المطالبات ---
        {"permission_id": 10101, "permission_name_key": "ADMIN_GG_CLAIM_VIEW_ANY", "module_group": "Admin: Golden Guarantee", "description": "عرض أي مطالبة ضمان ذهبي في النظام"},
        {"permission_id": 10102, "permission_name_key": "ADMIN_GG_CLAIM_MANAGE_ANY", "module_group": "Admin: Golden Guarantee", "description": "إدارة دورة حياة أي مطالبة (تغيير الحالة، طلب المزيد من المعلومات)"},
        {"permission_id": 10103, "permission_name_key": "ADMIN_GG_CLAIM_PROPOSE_RESOLUTION", "module_group": "Admin: Golden Guarantee", "description": "اقتراح حل للمطالبة (مثل استرداد مالي أو استبدال)"},
        
        # ================================================================
        # --- صلاحيات المجموعة 11: نظام الإشعارات والاتصالات ---
        # ================================================================
        {"permission_id": 11001, "permission_name_key": "ADMIN_MANAGE_NOTIFICATION_TEMPLATES", "module_group": "Admin: Notifications", "description": "إدارة قوالب الإشعارات (إنشاء، تعديل، حذف)"},
        {"permission_id": 11002, "permission_name_key": "ADMIN_SEND_BROADCAST_NOTIFICATIONS", "module_group": "Admin: Notifications", "description": "إرسال إشعارات جماعية لجميع المستخدمين أو لمجموعات محددة"},
        # ================================================================
        # --- صلاحيات المجموعة 12: الجداول المرجعية العامة ---
        # ================================================================
        {"permission_id": 12001, "permission_name_key": "ADMIN_MANAGE_GENERAL_LOOKUPS", "module_group": "Admin: Lookups", "description": "إدارة الجداول المرجعية العامة (مثل العملات، الدول، المدن)"},
        # ================================================================
        # --- صلاحيات المجموعة 13: سجلات التدقيق والأنشطة ---
        # ================================================================
        {"permission_id": 13001, "permission_name_key": "ADMIN_VIEW_AUDIT_LOGS", "module_group": "Admin: Auditing", "description": "عرض جميع سجلات التدقيق والأنشطة في النظام"},
        {"permission_id": 13002, "permission_name_key": "ADMIN_VIEW_SECURITY_LOGS", "module_group": "Admin: Auditing", "description": "عرض سجلات الأحداث الأمنية بشكل خاص"},
        # ================================================================
        # --- صلاحيات المجموعة 14: إدارة إعدادات النظام ---
        # ================================================================
        {"permission_id": 14001, "permission_name_key": "ADMIN_MANAGE_SYSTEM_SETTINGS", "module_group": "Admin: System Settings", "description": "تعديل إعدادات التطبيق العامة"},
        {"permission_id": 14002, "permission_name_key": "ADMIN_MANAGE_FEATURE_FLAGS", "module_group": "Admin: System Settings", "description": "تفعيل أو تعطيل الميزات التجريبية أو الجديدة في النظام"},
        # =====================================================================
        # --- صلاحيات إدارية جديدة للجداول المرجعية الخاصة بالمستخدمين
        # =====================================================================
        {"permission_id": 16001, "permission_name_key": "MANAGE_USER_LOOKUPS", "module_group": "Admin: User Lookups", "description": "إدارة الجداول المرجعية للمستخدمين (حالات الحساب، أنواع المستخدمين)"},
        {"permission_id": 16002, "permission_name_key": "VIEW_USER_LOOKUPS", "module_group": "Admin: User Lookups", "description": "عرض الجداول المرجعية للمستخدمين"},
        # =====================================================================
        # --- صلاحيات إدارية جديدة للجداول المرجعية الخاصة بالتراخيص
        # =====================================================================
        {"permission_id": 16003, "permission_name_key": "MANAGE_LICENSE_LOOKUPS", "module_group": "Admin: License Lookups", "description": "إدارة الجداول المرجعية للتراخيص (أنواع التراخيص، جهات الإصدار)"},
        {"permission_id": 16004, "permission_name_key": "VIEW_LICENSE_LOOKUPS", "module_group": "Admin: License Lookups", "description": "عرض الجداول المرجعية للتراخيص"},

        ]
    seed_main_table(db, Permission, "permission_id", PERMISSIONS)


    # ================================================================
    # --- المرحلة النهائية: بذر جدول الربط role_permissions (تطبيق المصفوفة)
    # ================================================================
    logger.info("Seeding Role-Permission Assignments...")
    
    # المصفوفة النهائية التي تربط الأدوار بالصلاحيات
    ROLE_PERMISSION_MAP = {
        "ADMIN": [
            # الصلاحية الخارقة التي تمنحه كل الصلاحيات الإدارية على النظام
            # "SUPER_ADMIN",
            # --- User Management Permissions ---
            "USER_VIEW_ANY",
            # --- 1.أ: صلاحيات الملف الشخصي والحساب (للمستخدم نفسه) ---
            "PROFILE_VIEW_OWN",
            "PROFILE_UPDATE_OWN",
            "PROFILE_MANAGE_PREFERENCES_OWN",
            "PROFILE_VIEW_STATUS_HISTORY_OWN",
            # --- 1.ب: صلاحيات إدارة الأدوار والصلاحيات (للمسؤولين) ---
            "RBAC_MANAGE_ROLES",
            "RBAC_MANAGE_PERMISSIONS",
            "RBAC_ASSIGN_ROLES_TO_USERS",
            # --- 1.ج: صلاحيات إدارة التراخيص والتحقق ---
            "LICENSE_CREATE_OWN",
            "LICENSE_VIEW_OWN",
            "LICENSE_DELETE_OWN",
            "ADMIN_VERIFY_ANY_LICENSE",
            "ADMIN_MANAGE_LICENSES",
            # --- 1.د: صلاحيات إدارة العناوين ---
            "ADDRESS_CREATE_OWN",
            "ADDRESS_VIEW_OWN",
            "ADDRESS_UPDATE_OWN",
            "ADDRESS_DELETE_OWN",
            # --- 1.هـ: صلاحيات إدارة أمان الحساب ---
            "SECURITY_CHANGE_PASSWORD_OWN",
            "SECURITY_VIEW_SESSIONS_OWN",
            "SECURITY_TERMINATE_SESSION_OWN",
            # --- صلاحيات إدارية عامة على المستخدمين ---
            "ADMIN_VIEW_ANY_USER",
            "ADMIN_UPDATE_ANY_USER",
            "ADMIN_MANAGE_USER_STATUS",
            "ADMIN_MANAGE_USERS",
            # --- 2.أ: صلاحيات إدارة المنتجات الأساسية (للبائعين) ---
            "PRODUCT_CREATE_OWN",
            "PRODUCT_UPDATE_OWN",
            "PRODUCT_DELETE_OWN",
            "PRODUCT_VIEW_OWN",
            # --- 2.ب و 2.ج: صلاحيات إدارة تفاصيل المنتج (للبائعين) ---
            "PRODUCT_MANAGE_VARIETIES_OWN",
            "PRODUCT_MANAGE_ATTRIBUTES_OWN",
            "PRODUCT_MANAGE_PACKAGING_OWN",
            "PRODUCT_MANAGE_IMAGES_OWN",
            # --- 2.د: صلاحيات إدارة المخزون (للبائعين) ---
            "INVENTORY_MANAGE_OWN",
            "INVENTORY_VIEW_HISTORY_OWN",
            # --- 2.هـ: صلاحيات إدارة العروض المستقبلية (للمزارعين) ---
            "CROP_MANAGE_OWN",
            # --- صلاحيات إدارية على المنتجات (للمسؤولين) ---
            "ADMIN_PRODUCT_VIEW_ANY",
            "ADMIN_PRODUCT_UPDATE_ANY",
            "ADMIN_PRODUCT_DELETE_ANY",
            "ADMIN_MANAGE_CATEGORIES",
            "ADMIN_MANAGE_UNITS",
            "ADMIN_MANAGE_ATTRIBUTES",
            # --- صلاحيات المجموعة 3: إدارة الأسعار الديناميكية ---
            "PRICING_RULE_CREATE_OWN",
            "PRICING_RULE_VIEW_OWN",
            "PRICING_RULE_UPDATE_OWN",
            "PRICING_RULE_DELETE_OWN",
            "PRICING_RULE_ASSIGN_OWN",
            "ADMIN_PRICING_RULE_VIEW_ANY",
            "ADMIN_PRICING_RULE_MANAGE_ANY",
            # --- 4.أ: صلاحيات الطلبات المباشرة ---
            "ORDER_CREATE_DIRECT",
            "ORDER_VIEW_OWN",
            "ORDER_UPDATE_OWN_STATUS",
            "ORDER_CANCEL_OWN",
            # --- 4.ب: صلاحيات طلبات عروض الأسعار (RFQs) ---
            "RFQ_CREATE_PURCHASE",
            "RFQ_MANAGE_OWN",
            "RFQ_VIEW_AVAILABLE",
            # --- 4.ج: صلاحيات عروض الأسعار (Quotes) ---
            "QUOTE_SUBMIT_OWN",
            "QUOTE_MANAGE_OWN",
            "QUOTE_ACCEPT_ANY",
            # --- 4.د: صلاحيات الشحنات ---
            "SHIPMENT_CREATE_OWN",
            "SHIPMENT_UPDATE_OWN",
            # --- صلاحيات إدارية على عمليات السوق ---
            "ADMIN_ORDER_VIEW_ANY",
            "ADMIN_ORDER_MANAGE_ANY",
            "ADMIN_RFQ_VIEW_ANY",
            "ADMIN_QUOTE_VIEW_ANY",
            # --- صلاحيات المجموعة 5: إدارة المزادات ---
            "AUCTION_CREATE_OWN",
            "AUCTION_MANAGE_OWN",
            "AUCTION_VIEW_ANY_OPEN",
            "AUCTION_PLACE_BID",
            "AUCTION_MANAGE_AUTOBID_OWN",
            "AUCTION_MANAGE_WATCHLIST_OWN",
            "AUCTION_VIEW_OWN_BIDS_AND_WINS",
            "ADMIN_AUCTION_MANAGE_ANY",
            "ADMIN_MANAGE_BIDS",
            "ADMIN_MANAGE_SETTLEMENTS",
            # --- صلاحيات المجموعة 6: إدارة المراجعات والتقييمات ---
            "REVIEW_CREATE_OWN",
            "REVIEW_UPDATE_OWN",
            "REVIEW_DELETE_OWN",
            "REVIEW_REPORT_ANY",
            "REVIEW_RESPOND_OWN",
            "ADMIN_REVIEW_VIEW_ANY",
            "ADMIN_REVIEW_MANAGE_STATUS",
            "ADMIN_MANAGE_REVIEW_REPORTS",
            "ADMIN_MANAGE_REVIEW_CRITERIA",
            # --- صلاحيات المجموعة 7: إدارة مخزون إعادة البيع ---
            "RESELLER_INVENTORY_VIEW_OWN",
            "RESELLER_SALES_OFFER_MANAGE_OWN",
            "RESELLER_CUSTOMER_ORDER_MANAGE_OWN",
            "ADMIN_RESELLER_INVENTORY_VIEW_ANY",
            "ADMIN_RESELLER_ORDERS_VIEW_ANY",
            # --- صلاحيات المجموعة 8: إدارة المحفظة والمدفوعات ---
            "WALLET_VIEW_OWN",
            "WALLET_VIEW_TRANSACTIONS_OWN",
            "WALLET_REQUEST_WITHDRAWAL_OWN",
            "WALLET_DEPOSIT_FUNDS_OWN",
            "ADMIN_WALLET_VIEW_ANY",
            "ADMIN_WALLET_ADJUST_BALANCE",
            "ADMIN_MANAGE_WITHDRAWAL_REQUESTS",
            "ADMIN_VIEW_ANY_TRANSACTION",
            "ADMIN_VIEW_COMMISSIONS",
            "ADMIN_MANAGE_PAYMENT_GATEWAYS",
            # --- صلاحيات المجموعة 9: إدارة اتفاقيات الدفع الآجل ---
            "AGREEMENT_CREATE_OWN",
            "AGREEMENT_VIEW_OWN_AS_SELLER",
            "AGREEMENT_MANAGE_OWN",
            "AGREEMENT_RECORD_PAYMENT_OWN",
            "AGREEMENT_VIEW_OWN_AS_BUYER",
            "AGREEMENT_ACCEPT_OR_REJECT",
            "AGREEMENT_MAKE_PAYMENT_OWN",
            "ADMIN_AGREEMENT_VIEW_ANY",
            "ADMIN_AGREEMENT_MANAGE_ANY",
            # --- صلاحيات المجموعة 10: إدارة الضمان الذهبي ---
            "GG_CLAIM_CREATE_OWN",
            "GG_CLAIM_VIEW_OWN",
            "GG_CLAIM_ADD_EVIDENCE_OWN",
            "GG_CLAIM_MANAGE_RESOLUTION_OWN",
            "ADMIN_GG_CLAIM_VIEW_ANY",
            "ADMIN_GG_CLAIM_MANAGE_ANY",
            "ADMIN_GG_CLAIM_PROPOSE_RESOLUTION",
            # --- صلاحيات المجموعة 11: نظام الإشعارات والاتصالات ---
            "ADMIN_MANAGE_NOTIFICATION_TEMPLATES",
            "ADMIN_SEND_BROADCAST_NOTIFICATIONS",
            # --- صلاحيات المجموعة 12: الجداول المرجعية العامة ---
            "ADMIN_MANAGE_GENERAL_LOOKUPS",
            # --- صلاحيات المجموعة 13: سجلات التدقيق والأنشطة ---
            "ADMIN_VIEW_AUDIT_LOGS",
            "ADMIN_VIEW_SECURITY_LOGS",
            # --- صلاحيات المجموعة 14: إدارة إعدادات النظام ---
            "ADMIN_MANAGE_SYSTEM_SETTINGS",
            "ADMIN_MANAGE_FEATURE_FLAGS",
            ],
        "FARMER": [
            # --- إدارة الحساب الشخصي (صلاحيات أساسية لكل المستخدمين) ---
            "PROFILE_VIEW_OWN",
            "PROFILE_UPDATE_OWN",
            "PROFILE_MANAGE_PREFERENCES_OWN",
            # --- 1.د: صلاحيات إدارة العناوين ---
            "ADDRESS_CREATE_OWN",
            "ADDRESS_VIEW_OWN",
            "ADDRESS_UPDATE_OWN",
            "ADDRESS_DELETE_OWN",
            "LICENSE_CREATE_OWN",
            "LICENSE_VIEW_OWN",
            "LICENSE_DELETE_OWN",
            "SECURITY_CHANGE_PASSWORD_OWN",
            # --- إدارة المنتجات (كوظيفة بائع) ---
            "PRODUCT_CREATE_OWN",
            "PRODUCT_UPDATE_OWN",
            "PRODUCT_DELETE_OWN",
            "PRODUCT_VIEW_OWN", # عرض منتجاته الخاصة بما فيها المسودات
            "PRODUCT_MANAGE_PACKAGING_OWN",
            # --- إدارة المخزون (كوظيفة بائع) ---
            "INVENTORY_MANAGE_OWN",
            "INVENTORY_VIEW_HISTORY_OWN",
            # --- إدارة العروض المستقبلية (ميزة خاصة بالمزارع) ---
            "CROP_MANAGE_OWN",
            # --- إدارة التسعير (كوظيفة بائع متقدم) ---
            "PRICING_RULE_MANAGE_OWN",
            "PRICING_RULE_ASSIGN_OWN",
            "PRICING_RULE_VIEW_OWN",
            # --- إدارة المزادات (كوظيفة بائع متقدم) ---
            "AUCTION_CREATE_OWN",
            "AUCTION_BID_ON_ANY", # يمكنه أيضًا المزايدة على مزادات الآخرين
            # --- إدارة طلبات عروض الأسعار (له صلاحية البيع والشراء) ---
            "RFQ_CREATE_FOR_SELLING", # لعرض محاصيله للبيع
            "RFQ_CREATE_FOR_PURCHASE", # لشراء احتياجاته
            # --- إدارة الطلبات ---
            "ORDER_CREATE_DIRECT", # يمكنه الشراء
            "ORDER_VIEW_OWN", # عرض طلباته كمشترٍ أو كبائع
            "ORDER_UPDATE_OWN_STATUS", # تحديث حالة الطلبات الواردة له
            # --- إدارة الدفع الآجل (بائع موثوق) ---
            "DEFERRED_PAYMENT_MANAGE",
            ],
        "WHOLESALER": [
            # --- إدارة الحساب الشخصي (صلاحيات أساسية) ---
            "PROFILE_VIEW_OWN",
            "PROFILE_UPDATE_OWN",
            "PROFILE_MANAGE_PREFERENCES_OWN",
            # --- 1.د: صلاحيات إدارة العناوين ---
            "ADDRESS_CREATE_OWN",
            "ADDRESS_VIEW_OWN",
            "ADDRESS_UPDATE_OWN",
            "ADDRESS_DELETE_OWN",
            "LICENSE_CREATE_OWN",
            "LICENSE_VIEW_OWN",
            "LICENSE_DELETE_OWN",
            "ADMIN_VERIFY_ANY_LICENSE",
            "SECURITY_CHANGE_PASSWORD_OWN",
            # --- إدارة المنتجات (كوظيفة بائع رئيسي) ---
            "PRODUCT_CREATE_OWN",
            "PRODUCT_UPDATE_OWN",
            "PRODUCT_DELETE_OWN",
            "PRODUCT_VIEW_OWN",
            "PRODUCT_MANAGE_PACKAGING_OWN",
            "PRODUCT_MANAGE_ATTRIBUTES_OWN", # يستطيع تحديد سمات لمنتجاته
            # --- إدارة المخزون ---
            "INVENTORY_MANAGE_OWN",
            "INVENTORY_VIEW_HISTORY_OWN",
            # --- إدارة التسعير (بائع متقدم) ---
            "PRICING_RULE_MANAGE_OWN",
            "PRICING_RULE_ASSIGN_OWN",
            "PRICING_RULE_VIEW_OWN",
            # --- إدارة المزادات (بائع متقدم) ---
            "AUCTION_CREATE_OWN",
            "AUCTION_BID_ON_ANY", # يمكنه أيضًا المزايدة
            # --- إدارة الطلبات وعروض الأسعار ---
            "ORDER_CREATE_DIRECT", # يمكنه الشراء أيضًا
            "ORDER_VIEW_OWN", # عرض طلباته كمشترٍ أو كبائع
            "ORDER_UPDATE_OWN_STATUS",
            "RFQ_CREATE_FOR_PURCHASE", # يمكنه طلب عروض أسعار لاحتياجاته
            "QUOTE_SUBMIT_OWN", # يمكنه الرد على طلبات عروض الأسعار
            # --- إدارة الدفع الآجل (بائع موثوق) ---
            "DEFERRED_PAYMENT_MANAGE",        ],
        "RESELLER": [
            # --- إدارة الحساب الشخصي (صلاحيات أساسية) ---
            "PROFILE_VIEW_OWN",
            "PROFILE_UPDATE_OWN",
            "PROFILE_MANAGE_PREFERENCES_OWN",
            # --- 1.د: صلاحيات إدارة العناوين ---
            "ADDRESS_CREATE_OWN",
            "ADDRESS_VIEW_OWN",
            "ADDRESS_UPDATE_OWN",
            "ADDRESS_DELETE_OWN",
            "LICENSE_CREATE_OWN",
            "LICENSE_VIEW_OWN",
            "LICENSE_DELETE_OWN", # لإدارة وثيقة العمل الحر
            "SECURITY_CHANGE_PASSWORD_OWN",
            # --- إدارة المنتجات (لإعادة بيعها) ---
            # قد لا ينشئون منتجات من الصفر، بل يختارون من الكتالوج
            # لكن سنمنحهم الصلاحية لإدارة عروضهم
            "PRODUCT_MANAGE_OWN", 
            # --- إدارة مخزون إعادة البيع (الميزة الأساسية) ---
            "RESELLER_INVENTORY_VIEW_OWN",
            "RESELLER_SALES_OFFER_MANAGE_OWN",
            "RESELLER_CUSTOMER_ORDER_MANAGE_OWN",
            # --- عمليات السوق (كمشترٍ وبائع) ---
            "ORDER_CREATE_DIRECT", # لشراء مخزونه من تجار الجملة
            "ORDER_VIEW_OWN", 
            "AUCTION_BID_ON_ANY", # يمكنه الشراء من المزادات
            "RFQ_CREATE_FOR_PURCHASE", # يمكنه طلب عروض أسعار لشراء مخزونه
            ],
        "PRODUCING_FAMILY": [
            # --- إدارة الحساب الشخصي (صلاحيات أساسية) ---
            "PROFILE_VIEW_OWN",
            "PROFILE_UPDATE_OWN",
            "PROFILE_MANAGE_PREFERENCES_OWN",
            # --- 1.د: صلاحيات إدارة العناوين ---
            "ADDRESS_CREATE_OWN",
            "ADDRESS_VIEW_OWN",
            "ADDRESS_UPDATE_OWN",
            "ADDRESS_DELETE_OWN",
            "LICENSE_CREATE_OWN",
            "LICENSE_VIEW_OWN",
            "LICENSE_DELETE_OWN", # لإدارة شهادة الأسر المنتجة
            "SECURITY_CHANGE_PASSWORD_OWN",
            # --- إدارة المنتجات (كوظيفة بائع) ---
            "PRODUCT_CREATE_OWN",
            "PRODUCT_UPDATE_OWN",
            "PRODUCT_DELETE_OWN",
            "PRODUCT_VIEW_OWN",
            "PRODUCT_MANAGE_PACKAGING_OWN",
            # --- إدارة المخزون ---
            "INVENTORY_MANAGE_OWN",
            "INVENTORY_VIEW_HISTORY_OWN",
            # --- عمليات السوق (كمشترٍ وبائع) ---
            "ORDER_CREATE_DIRECT", # يمكنهم الشراء أيضًا
            "ORDER_VIEW_OWN", # عرض طلباتهم كمشترين أو كبائعين
            "ORDER_UPDATE_OWN_STATUS", # تحديث حالة الطلبات الواردة لهم
            "AUCTION_BID_ON_ANY", # يمكنهم المشاركة في المزادات كمشترين
            "RFQ_CREATE_FOR_PURCHASE", # يمكنهم طلب عروض أسعار لاحتياجاتهم
            ],
        "COMMERCIAL_BUYER": [
            # --- إدارة الحساب الشخصي (صلاحيات أساسية) ---
            "PROFILE_VIEW_OWN",
            "PROFILE_UPDATE_OWN",
            "PROFILE_MANAGE_PREFERENCES_OWN",
            # --- 1.د: صلاحيات إدارة العناوين ---
            "ADDRESS_CREATE_OWN",
            "ADDRESS_VIEW_OWN",
            "ADDRESS_UPDATE_OWN",
            "ADDRESS_DELETE_OWN",
            "LICENSE_CREATE_OWN",
            "LICENSE_VIEW_OWN",
            "LICENSE_DELETE_OWN", # لإدارة السجل التجاري
            "SECURITY_CHANGE_PASSWORD_OWN",
            # --- عمليات السوق (كمشترٍ رئيسي) ---
            "ORDER_CREATE_DIRECT",
            "ORDER_VIEW_OWN", # عرض طلباته كمشترٍ
            "AUCTION_BID_ON_ANY", # يمكنه المشاركة في المزادات
            "RFQ_CREATE_FOR_PURCHASE", # الميزة الأساسية له لطلب كميات
            "QUOTE_ACCEPT_ANY", # قبول عروض الأسعار المقدمة له
            "GG_CLAIM_CREATE_OWN", # إنشاء مطالبة ضمان ذهبي
            "REVIEW_CREATE_OWN", # كتابة مراجعة بعد الشراء
            # --- إدارة المحفظة (كمشترٍ) ---
            "WALLET_VIEW_OWN",
            "WALLET_VIEW_TRANSACTIONS_OWN",
            "WALLET_DEPOSIT_FUNDS_OWN",
            ],
        "BASE_USER": [
            # --- إدارة الحساب الشخصي (صلاحيات أساسية) ---
            "PROFILE_VIEW_OWN",
            "PROFILE_UPDATE_OWN",
            "PROFILE_MANAGE_PREFERENCES_OWN",
            # --- 1.د: صلاحيات إدارة العناوين ---
            "ADDRESS_CREATE_OWN",
            "ADDRESS_VIEW_OWN",
            "ADDRESS_UPDATE_OWN",
            "ADDRESS_DELETE_OWN",
            "SECURITY_CHANGE_PASSWORD_OWN",

            # --- عمليات السوق (كمشترٍ فردي) ---
            "ORDER_CREATE_DIRECT", # مع تطبيق قيود الكمية التجارية في الخدمة
            "ORDER_VIEW_OWN", # عرض طلباته كمشترٍ
            "RFQ_CREATE_FOR_PURCHASE", # يمكنه طلب عروض أسعار لاحتياجاته الشخصية
            "QUOTE_ACCEPT_ANY", # قبول عروض الأسعار المقدمة له
            
            # --- المراجعات والضمان (كمشترٍ) ---
            "REVIEW_CREATE_OWN",
            "GG_CLAIM_CREATE_OWN",

            # --- إدارة المحفظة (كمشترٍ) ---
            "WALLET_VIEW_OWN",
            "WALLET_VIEW_TRANSACTIONS_OWN",
            "WALLET_DEPOSIT_FUNDS_OWN",
        ]
    }

    # جلب كل الأدوار والصلاحيات من قاعدة البيانات لتسهيل الربط
    db.commit() # نضمن حفظ الأدوار والصلاحيات قبل جلبها
    roles_map = {r.role_name_key: r.role_id for r in db.query(Role).all()}
    permissions_map = {p.permission_name_key: p.permission_id for p in db.query(Permission).all()}

    assignments_to_create = []
    assignment_id = 1
    for role_name, permission_keys in ROLE_PERMISSION_MAP.items():
        if role_name in roles_map:
            role_id = roles_map[role_name]
            for p_key in permission_keys:
                if p_key in permissions_map:
                    permission_id = permissions_map[p_key]
                    assignments_to_create.append({"role_permission_id": assignment_id,"role_id": role_id, "permission_id": permission_id})
                    assignment_id += 1

    # بذر جدول الربط
    for assignment in assignments_to_create:
        if not db.query(RolePermission).filter_by(role_id=assignment["role_id"], permission_id=assignment["permission_id"]).first():
            db.add(RolePermission(**assignment))
            
    db.commit()
    logger.info("Role-Permission matrix seeded successfully.")

    # ================================================================
    # --- بذر المستخدمين النموذجيين (أخيرًا، بعد بذر كل الاعتماديات)
    # ================================================================
    logger.info("--- Seeding Sample Users ---")
    
    # USERS_TO_CREATE = [
    #     {"role_key": "ADMIN", "user_data": core_schemas.UserCreate(phone_number="+966500000000", password="admin_password_123", first_name="Admin", last_name="User", user_type_id=2, email="admin@mothmerah.com")},
    #     {"role_key": "WHOLESALER", "user_data": core_schemas.UserCreate(phone_number="+966511111111", password="password123", first_name="تاجر", last_name="جملة", user_type_id=3, email="wholesaler@example.com")},
    #     {"role_key": "PRODUCING_FAMILY", "user_data": core_schemas.UserCreate(phone_number="+966522222222", password="password123", first_name="أسرة", last_name="منتجة", user_type_id=4, email="family@example.com")},
    #     {"role_key": "BASE_USER", "user_data": core_schemas.UserCreate(phone_number="+966533333333", password="password123", first_name="مشتري", last_name="عادي", user_type_id=4, email="bayer@example.com")},
    #     {"role_key": "COMMERCIAL_BUYER", "user_data": core_schemas.UserCreate(phone_number="+966544444444", password="password123", first_name="مشتري", last_name="تجاري", user_type_id=4, email="horica@example.com")},
    #     {"role_key": "RESELLER", "user_data": core_schemas.UserCreate(phone_number="+966555555555", password="password123", first_name="مندوب", last_name="مشتريات", user_type_id=4, email="reseler@example.com")},
    #     {"role_key": "FARMER", "user_data": core_schemas.UserCreate(phone_number="+966566666666", password="password123", first_name="مزارع", last_name="نموذجي", user_type_id=7, email="farmer@example.com")},
    # ]
    USERS_TO_CREATE = [
        {"role_key": "ADMIN", "user_data": core_schemas.UserCreate(phone_number="+966500000000", password="admin_password_123", first_name="Admin", last_name="User", user_type_key="ADMIN", email="admin@mothmerah.com")},
        {"role_key": "WHOLESALER", "user_data": core_schemas.UserCreate(phone_number="+966511111111", password="password123", first_name="تاجر", last_name="جملة", user_type_key="WHOLESALER", email="wholesaler@example.com")},
        {"role_key": "PRODUCING_FAMILY", "user_data": core_schemas.UserCreate(phone_number="+966522222222", password="password123", first_name="أسرة", last_name="منتجة", user_type_key="PRODUCING_FAMILY", email="family@example.com")},
        {"role_key": "BASE_USER", "user_data": core_schemas.UserCreate(phone_number="+966533333333", password="password123", first_name="مشتري", last_name="عادي", user_type_key="BASE_USER", email="buyer@example.com")},
        {"role_key": "COMMERCIAL_BUYER", "user_data": core_schemas.UserCreate(phone_number="+966544444444", password="password123", first_name="مشتري", last_name="تجاري", user_type_key="COMMERCIAL_BUYER", email="horeca@example.com")},
        {"role_key": "RESELLER", "user_data": core_schemas.UserCreate(phone_number="+966555555555", password="password123", first_name="مندوب", last_name="مبيعات", user_type_key="RESELLER", email="reseller@example.com")},
        {"role_key": "FARMER", "user_data": core_schemas.UserCreate(phone_number="+966566666666", password="password123", first_name="مزارع", last_name="نموذجي", user_type_key="FARMER", email="farmer@example.com")},
    ]

    #     {"user_type_id": 1, "user_type_name_key": "BASE_USER"},
    #     {"user_type_id": 2, "user_type_name_key": "ADMIN"},
    #     {"user_type_id": 3, "user_type_name_key": "WHOLESALER"},
    #     {"user_type_id": 4, "user_type_name_key": "PRODUCING_FAMILY"},
    #     {"user_type_id": 5, "user_type_name_key": "COMMERCIAL_BUYER"},
    #     {"user_type_id": 6, "user_type_name_key": "RESELLER"},

#     {
#   "name": "تمر سكري",
#   "description": "تمر سكري فاخر من القصيم",
#   "category_id": 2,
#   "unit_of_measure_id": 2,
#   "country_of_origin_code": "SA",
#   "base_price_per_unit": 50.0
#     }

    # استبدل هذا الجزء من الكود:
    for item in USERS_TO_CREATE:
        user_in = item["user_data"]
        role_key = item["role_key"]

        # تحقق من وجود المستخدم
        user_exists = core_crud.get_user_by_phone_number(db, phone_number=user_in.phone_number)
        if not user_exists:
            try:
                # استدعاء الخدمة بالـ parameters الصحيحة
                new_user = core_service.register_new_user(
                    db=db,
                    user_in=user_in,
                    user_type_key=user_in.user_type_key,  # مثل: "ADMIN", "WHOLESALER"
                    default_role_key=role_key              # مثل: "ADMIN", "WHOLESALER"
                )
                logger.info(f"✓ User {user_in.phone_number} created with role {role_key}.")
            except Exception as e:
                logger.error(f"✗ Failed to create user {user_in.phone_number}: {e}")
                db.rollback()
        else:
            logger.info(f"○ User {user_in.phone_number} already exists, skipping.")
        # --- نهاية التعديل ---
            
    logger.info("Sample users seeded successfully.")

    # ================================================================
    # --- بذر منتج نموذجي وخيار تعبئة لأغراض الاختبار
    # ================================================================
    logger.info("--- Seeding Sample Product and Packaging for testing ---")
    
    # 1. ابحث عن البائع النموذجي الذي أنشأناه
    seller = core_crud.get_user_by_phone_number(db, phone_number="+966511111111")
    
    if seller:
        # 2. ابحث عن الكيانات المرجعية التي سنحتاجها
        category = db.query(ProductCategory).filter(ProductCategory.category_id == 2).first() # فواكه
        unit = db.query(UnitOfMeasure).filter(UnitOfMeasure.unit_name_key == "KILOGRAM").first()
        status = db.query(ProductStatus).filter(ProductStatus.status_name_key == "ACTIVE").first()
        country = db.query(Country).filter(Country.country_code == "SA").first()

        if category and unit and status and country:
            # 3. تحقق إذا كان المنتج النموذجي موجودًا، وإلا قم بإنشائه
            sample_product = db.query(Product).filter(Product.seller_user_id == seller.user_id).first()
            if not sample_product:
                # لا يوجد اسم للمنتج في الجدول الأساسي، بل في الترجمة
                product_data = {
                    "seller_user_id": seller.user_id,
                    "category_id": category.category_id,
                    "base_price_per_unit": 20.00,
                    "unit_of_measure_id": unit.unit_id,
                    "country_of_origin_code": country.country_code,
                    "product_status_id": status.product_status_id
                }
                sample_product = Product(**product_data)
                
                initial_translation = ProductTranslation(language_code='ar', translated_product_name='تمر سكري ملكي', translated_description='أجود أنواع التمر السكري')
                sample_product.translations.append(initial_translation)
                
                db.add(sample_product)
                db.commit()
                db.refresh(sample_product)
                logger.info("Created sample product 'تمر سكري ملكي' for testing.")

            # 4. تحقق إذا كان خيار التغليف موجودًا، وإلا قم بإنشائه (بالحقول الصحيحة)
            sample_packaging = db.query(ProductPackagingOption).filter(ProductPackagingOption.product_id == sample_product.product_id).first()
            if not sample_packaging:
                packaging_data = {
                    "product_id": sample_product.product_id,
                    "packaging_option_name_key": "ROYAL_BOX_3KG",
                    "quantity_in_packaging": 3.0,
                    "unit_of_measure_id_for_quantity": unit.unit_id,
                    "base_price": 75.00,
                    "is_default_option": True,
                    "is_active": True
                }
                db.add(ProductPackagingOption(**packaging_data))
                db.commit()
                logger.info("Created sample packaging option for the sample product.")


    # --- بذر العملات ---
    logger.info("Seeding Currencies...")
    currencies = [
        {"currency_code": "SAR", "currency_name_key": "saudi_riyal", "symbol": "ر.س", "decimal_places": 2, "is_active": True},
    ]
    seed_main_table(db, Currency, "currency_code", currencies)
    seed_translation_table(db, CurrencyTranslation, "currency_code", [
        {"currency_code": "SAR", "language_code": "ar", "translated_currency_name": "ريال سعودي"},
        {"currency_code": "SAR", "language_code": "en", "translated_currency_name": "Saudi Riyal"},
        {"currency_code": "SAR", "language_code": "fr", "translated_currency_name": "Riyal saoudien"},
        {"currency_code": "SAR", "language_code": "ur", "translated_currency_name": "سعودی ریال"},
        {"currency_code": "SAR", "language_code": "hi", "translated_currency_name": "सऊदी रियाल"},
        {"currency_code": "SAR", "language_code": "bn", "translated_currency_name": "সৌদি রিয়াল"},
    ])

    # --- بذر حالات الدفع ---
    logger.info("Seeding Payment Statuses...")
    payment_statuses = [
        {"payment_status_id": 1, "status_name_key": "PENDING"},
        {"payment_status_id": 2, "status_name_key": "PAID"},
        {"payment_status_id": 3, "status_name_key": "FAILED"},
        {"payment_status_id": 4, "status_name_key": "REFUNDED"},
    ]
    seed_main_table(db, PaymentStatus, "payment_status_id", payment_statuses)
    seed_translation_table(db, PaymentStatusTranslation, "payment_status_id", [
        # PENDING
        {"payment_status_id": 1, "language_code": "ar", "translated_status_name": "بانتظار الدفع"},
        {"payment_status_id": 1, "language_code": "en", "translated_status_name": "Pending"},
        {"payment_status_id": 1, "language_code": "fr", "translated_status_name": "En attente"},
        {"payment_status_id": 1, "language_code": "ur", "translated_status_name": "زیر التواء"},
        {"payment_status_id": 1, "language_code": "hi", "translated_status_name": "लंबित"},
        {"payment_status_id": 1, "language_code": "bn", "translated_status_name": "অপেক্ষমাণ"},
        # PAID
        {"payment_status_id": 2, "language_code": "ar", "translated_status_name": "مدفوع"},
        {"payment_status_id": 2, "language_code": "en", "translated_status_name": "Paid"},
        {"payment_status_id": 2, "language_code": "fr", "translated_status_name": "Payé"},
        {"payment_status_id": 2, "language_code": "ur", "translated_status_name": "ادا کیا"},
        {"payment_status_id": 2, "language_code": "hi", "translated_status_name": "भुगतान किया गया"},
        {"payment_status_id": 2, "language_code": "bn", "translated_status_name": "পরিশোধিত"},
        # FAILED
        {"payment_status_id": 3, "language_code": "ar", "translated_status_name": "فشل الدفع"},
        {"payment_status_id": 3, "language_code": "en", "translated_status_name": "Failed"},
        {"payment_status_id": 3, "language_code": "fr", "translated_status_name": "Échoué"},
        {"payment_status_id": 3, "language_code": "ur", "translated_status_name": "ناکام"},
        {"payment_status_id": 3, "language_code": "hi", "translated_status_name": "विफल"},
        {"payment_status_id": 3, "language_code": "bn", "translated_status_name": "ব্যর্থ"},
        # REFUNDED
        {"payment_status_id": 4, "language_code": "ar", "translated_status_name": "مسترد"},
        {"payment_status_id": 4, "language_code": "en", "translated_status_name": "Refunded"},
        {"payment_status_id": 4, "language_code": "fr", "translated_status_name": "Remboursé"},
        {"payment_status_id": 4, "language_code": "ur", "translated_status_name": "رقم واپس"},
        {"payment_status_id": 4, "language_code": "hi", "translated_status_name": "धनवापसी"},
        {"payment_status_id": 4, "language_code": "bn", "translated_status_name": "ফেরত দেওয়া হয়েছে"},
    ])

    db.commit()



    logger.info("Database seeding finished.")

if __name__ == "__main__":
    logger.info("Starting database seeding...")
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()
    logger.info("Seeding complete. DB session closed.")

