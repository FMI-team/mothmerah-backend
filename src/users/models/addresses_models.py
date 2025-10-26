# backend/src/users/models/addresses_models.py
from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, BigInteger, Numeric,
    func, TIMESTAMP, text, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING,Optional

from src.db.base_class import Base

from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

# يمنع الأخطاء الناتجة عن الاستيراد الدائري
if TYPE_CHECKING:
    from .core_models import User


class AddressType(Base):
    """(1.د.1) أنواع العناوين (فوترة، شحن...)."""
    __tablename__ = 'address_types'
    address_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('address_types.address_type_id', ondelete="CASCADE"), primary_key=True)
    address_type_name_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    translations: Mapped[List["AddressTypeTranslation"]] = relationship(
        back_populates="address_type", cascade="all, delete-orphan" # علاقة بترجمات نوع العنوان
    )
    # العناوين التي تحمل هذا النوع (علاقة عكسية)
    addresses: Mapped[List["Address"]] = relationship("Address", back_populates="address_type")

class AddressTypeTranslation(Base):
    """(1.د.2) ترجمات أنواع العناوين."""
    __tablename__ = 'address_type_translations'
    # جعلنا المفتاح الأجنبي ورمز اللغة هما المفتاح الأساسي المركب
    address_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('address_types.address_type_id'), primary_key=True) 
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True)
    # --- نهاية التعديل الجذري ---
    translated_address_type_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    address_type: Mapped["AddressType"] = relationship(back_populates="translations") # علاقة بنوع العنوان الأب

class Country(Base):
    """(1.د.3) جدول الدول."""
    __tablename__ = 'countries'
    country_code: Mapped[str] = mapped_column(String(2), primary_key=True)
    country_name_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    phone_country_code: Mapped[str] = mapped_column(String(5), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    translations: Mapped[List["CountryTranslation"]] = relationship(
        back_populates="country", cascade="all, delete-orphan" # علاقة بترجمات الدولة
    )
    # المحافظات في هذه الدولة (علاقة عكسية)
    governorates: Mapped[List["Governorate"]] = relationship("Governorate", back_populates="country")
    # العناوين في هذه الدولة (علاقة عكسية)
    addresses: Mapped[List["Address"]] = relationship("Address", back_populates="country")

class CountryTranslation(Base):
    """(1.د.4) ترجمات الدول."""
    __tablename__ = 'country_translations'
    country_code: Mapped[str] = mapped_column(String(2), ForeignKey('countries.country_code', ondelete="CASCADE"), primary_key=True)    
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_country_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    country: Mapped["Country"] = relationship(back_populates="translations") # علاقة بالدولة الأم

class Governorate(Base):
    """(1.د.5) جدول المحافظات/المناطق الإدارية."""
    __tablename__ = 'governorates'
    governorate_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country_code: Mapped[str] = mapped_column(String(2), ForeignKey('countries.country_code'), nullable=False)
    governorate_name_key: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    translations: Mapped[List["GovernorateTranslation"]] = relationship(
        back_populates="governorate", cascade="all, delete-orphan" # علاقة بترجمات المحافظة
    )
    country: Mapped["Country"] = relationship("Country", foreign_keys=[country_code], back_populates="governorates", lazy="selectin") # علاقة بالدولة الأم
    # المدن في هذه المحافظة (علاقة عكسية)
    cities: Mapped[List["City"]] = relationship("City", back_populates="governorate")
    # العناوين في هذه المحافظة (علاقة عكسية)
    addresses: Mapped[List["Address"]] = relationship("Address", back_populates="governorate")

class GovernorateTranslation(Base):
    """(1.د.6) ترجمات المحافظات."""
    __tablename__ = 'governorate_translations'
    # governorate_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    governorate_id: Mapped[int] = mapped_column(Integer, ForeignKey('governorates.governorate_id', ondelete="CASCADE"), primary_key=True)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_governorate_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    governorate: Mapped["Governorate"] = relationship(back_populates="translations") # علاقة بالمحافظة الأم

class City(Base):
    """(1.د.7) جدول المدن."""
    __tablename__ = 'cities'
    city_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    governorate_id: Mapped[int] = mapped_column(Integer, ForeignKey('governorates.governorate_id'), nullable=False)
    city_name_key: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    translations: Mapped[List["CityTranslation"]] = relationship(
        back_populates="city", cascade="all, delete-orphan" # علاقة بترجمات المدينة
    )
    governorate: Mapped["Governorate"] = relationship("Governorate", foreign_keys=[governorate_id], back_populates="cities", lazy="selectin") # علاقة بالمحافظة الأم
    # الأحياء في هذه المدينة (علاقة عكسية)
    districts: Mapped[List["District"]] = relationship("District", back_populates="city")
    # العناوين في هذه المدينة (علاقة عكسية)
    addresses: Mapped[List["Address"]] = relationship("Address", back_populates="city")

class CityTranslation(Base):
    """(1.د.8) ترجمات المدن."""
    __tablename__ = 'city_translations'
    # city_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    city_id: Mapped[int] = mapped_column(Integer, ForeignKey('cities.city_id', ondelete="CASCADE"), primary_key=True)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_city_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    city: Mapped["City"] = relationship(back_populates="translations") # علاقة بالمدينة الأم

class District(Base):
    """(1.د.9) جدول الأحياء."""
    __tablename__ = 'districts'
    district_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city_id: Mapped[int] = mapped_column(Integer, ForeignKey('cities.city_id'), nullable=False)
    district_name_key: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    translations: Mapped[List["DistrictTranslation"]] = relationship(
        back_populates="district", cascade="all, delete-orphan" # علاقة بترجمات الحي
    )
    city: Mapped["City"] = relationship("City", foreign_keys=[city_id], back_populates="districts", lazy="selectin") # علاقة بالمدينة الأم
    # العناوين في هذا الحي (علاقة عكسية)
    addresses: Mapped[List["Address"]] = relationship("Address", back_populates="district")

class DistrictTranslation(Base):
    """(1.د.10) ترجمات الأحياء."""
    __tablename__ = 'district_translations'
    # district_translation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey('districts.district_id', ondelete="CASCADE"), primary_key=True)
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey('languages.language_code'), primary_key=True) # nullable=False)
    translated_district_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقات:
    district: Mapped["District"] = relationship(back_populates="translations") # علاقة بالحي الأب

class Address(Base):
    """(1.د.11) جدول العناوين الفعلية للمستخدمين."""
    __tablename__ = 'addresses'
    address_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete="CASCADE"), nullable=False)
    address_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('address_types.address_type_id'), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), ForeignKey('countries.country_code'), nullable=False)
    governorate_id: Mapped[int] = mapped_column(Integer, ForeignKey('governorates.governorate_id'), nullable=True)
    city_id: Mapped[int] = mapped_column(Integer, ForeignKey('cities.city_id'), nullable=False)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey('districts.district_id'), nullable=True)
    street_name: Mapped[str] = mapped_column(String(255), nullable=False)
    building_number: Mapped[str] = mapped_column(String(50), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=True)
    additional_details: Mapped[str] = mapped_column(Text, nullable=True)
    latitude: Mapped[float] = mapped_column(Numeric(10, 8), nullable=True)
    longitude: Mapped[float] = mapped_column(Numeric(11, 8), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # --- SQLAlchemy Relationships ---
    # علاقات مع مودلات من جداول lookups و users
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="addresses", lazy="selectin") # علاقة بالمستخدم المالك للعنوان
    address_type: Mapped["AddressType"] = relationship("AddressType", foreign_keys=[address_type_id], back_populates="addresses", lazy="selectin") # علاقة بنوع العنوان
    country: Mapped["Country"] = relationship("Country", foreign_keys=[country_code], back_populates="addresses", lazy="selectin") # علاقة بالدولة
    governorate: Mapped[Optional["Governorate"]] = relationship("Governorate", foreign_keys=[governorate_id], back_populates="addresses", lazy="selectin") # علاقة بالمحافظة
    city: Mapped["City"] = relationship("City", foreign_keys=[city_id], back_populates="addresses", lazy="selectin") # علاقة بالمدينة
    district: Mapped[Optional["District"]] = relationship("District", foreign_keys=[district_id], back_populates="addresses", lazy="selectin") # علاقة بالحي
