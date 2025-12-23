"""
Service layer for admin user management operations.
"""
import secrets
import string
from typing import Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func 

from src.users import models
from src.users.schemas.management_schemas import AdminUserCreate, AdminUserCreatedResponse
from src.exceptions import BadRequestException, NotFoundException, ConflictException
from src.core.security import get_password_hash

from src.lookups.models.lookups_models import Language

class AdminUserService:
    """Service for admin user management operations."""
    
    # Default values based on your seed data
    DEFAULT_ACCOUNT_STATUS_ID = 2  # ACTIVE
    DEFAULT_VERIFICATION_STATUS_ID = 3  # VERIFIED
    DEFAULT_LANGUAGE_CODE = "ar"
    
    @staticmethod
    def generate_temporary_password(length: int = 12) -> str:
        """Generate a secure temporary password."""
        alphabet = string.ascii_letters + string.digits + string.punctuation
        
        # Ensure at least one of each required character type
        password_chars = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice(string.punctuation)
        ]
        
        # Fill the rest with random characters
        for _ in range(length - 4):
            password_chars.append(secrets.choice(alphabet))
        
        # Shuffle the characters
        secrets.SystemRandom().shuffle(password_chars)
        return ''.join(password_chars)
    
    @staticmethod
    def get_reference_object(db: Session, model_class, id_field: str, id_value: Any, 
                           error_message: str) -> Any:
        """Helper to get reference object or raise NotFoundException."""
        obj = db.query(model_class).filter(
            getattr(model_class, id_field) == id_value
        ).first()
        
        if not obj:
            raise NotFoundException(detail=error_message)
        return obj
    
    @staticmethod
    def validate_user_references(db: Session, user_data: AdminUserCreate) -> Dict[str, Any]:
        """
        Validate all foreign key references exist in database.
        
        Returns:
            Dict with validated reference objects
        """
        references = {}
        
        # 1. Validate UserType (from src.users.models)
        user_type = AdminUserService.get_reference_object(
            db, models.UserType, "user_type_id", user_data.user_type_id,
            f"UserType with ID {user_data.user_type_id} not found."
        )
        references['user_type'] = user_type
        
        # 2. Validate AccountStatus (from src.users.models)
        account_status = AdminUserService.get_reference_object(
            db, models.AccountStatus, "account_status_id", user_data.account_status_id,
            f"AccountStatus with ID {user_data.account_status_id} not found."
        )
        references['account_status'] = account_status
        
        # 3. Validate Role if provided (from src.users.models)
        if user_data.default_user_role_id:
            role = AdminUserService.get_reference_object(
                db, models.Role, "role_id", user_data.default_user_role_id,
                f"Role with ID {user_data.default_user_role_id} not found."
            )
            references['role'] = role
        
        # 4. Validate Verification Status if provided (from src.users.models)
        if user_data.user_verification_status_id:
            verification_status = AdminUserService.get_reference_object(
                db, models.UserVerificationStatus, 
                "user_verification_status_id", user_data.user_verification_status_id,
                f"UserVerificationStatus with ID {user_data.user_verification_status_id} not found."
            )
            references['verification_status'] = verification_status
        else:
            # Use default verification status
            verification_status = db.query(models.UserVerificationStatus).filter(
                models.UserVerificationStatus.user_verification_status_id == 
                AdminUserService.DEFAULT_VERIFICATION_STATUS_ID
            ).first()
            references['verification_status'] = verification_status
        
        # 5. Validate Language - ONLY THIS IS FROM lookups_models
        language = AdminUserService.get_reference_object(
            db, Language, "language_code", user_data.preferred_language_code,
            f"Language with code '{user_data.preferred_language_code}' not found."
            "Valid codes: 'ar', 'en', 'bn', 'hi', 'ur', 'fr'"
        )
        references['language'] = language
        
        return references
    
    @staticmethod
    def check_duplicate_identifiers(db: Session, phone_number: str, email: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if phone or email already exists in the system.
        
        Returns:
            Tuple[is_duplicate, error_message]
        """
        # Check for duplicate phone number
        existing_user = db.query(models.User).filter(
            models.User.phone_number == phone_number
        ).first()
        
        if existing_user:
            return True, (
                f"User with phone number {phone_number} already exists. "
            )
        
        # Check for duplicate email if provided
        if email:
            existing_email = db.query(models.User).filter(
                models.User.email == email
            ).first()
            
            if existing_email:
                return True, (
                    f"User with email {email} already exists. "
                )
        
        return False, None
    
    @staticmethod
    def prepare_additional_data(user_data: AdminUserCreate) -> dict:
        """Prepare additional_data JSON field with business-specific information."""
        additional_data = user_data.additional_data or {}
        
        # Add business info if provided
        if hasattr(user_data, 'business_name') and user_data.business_name:
            additional_data['business_name'] = user_data.business_name
        
        if hasattr(user_data, 'tax_number') and user_data.tax_number:
            additional_data['tax_number'] = user_data.tax_number
        
        # Add role-specific data
        if hasattr(user_data, 'freelance_document_number') and user_data.freelance_document_number:
            additional_data['freelance_document_number'] = user_data.freelance_document_number
        
        if hasattr(user_data, 'license_number') and user_data.license_number:
            additional_data['license_number'] = user_data.license_number
        
        return additional_data if additional_data else None
    
    @staticmethod
    def create_user_license(db: Session, user_id: UUID, user_type_id: int, 
                          user_data: AdminUserCreate, created_by_admin_id: UUID):
        """
        Create license record for users that require licenses.
        Based on SRS: FREELANCE_DOCUMENT for RESELLER, COMMERCIAL_REGISTER for commercial users.
        """
        pass
        # # Determine license type based on user type
        # license_type_id = None
        
        # if user_type_id == 6:  # RESELLER
        #     license_type_id = 2  # FREELANCE_DOCUMENT
        # elif user_type_id in [3, 5]:  # WHOLESALER, COMMERCIAL_BUYER
        #     license_type_id = 1  # COMMERCIAL_REGISTER
        
        # if license_type_id:
        #     # Check if license type exists (from src.users.models)
        #     license_type = db.query(models.LicenseType).filter(
        #         models.LicenseType.license_type_id == license_type_id
        #     ).first()
            
        #     if license_type:
        #         # Create license record (from src.users.models)
        #         license_data = {
        #             "user_id": user_id,
        #             "license_type_id": license_type_id,
        #             "license_number": f"ADMIN-CREATED-{user_id}",
        #             "license_verification_status_id": 2,  # PENDING_REVIEW
        #             "issued_by_user_id": created_by_admin_id,
        #             "notes": "License created automatically by admin during user creation"
        #         }
                
        #         license_record = models.License(**license_data)
        #         db.add(license_record)
    
    @staticmethod
    def assign_user_roles(db: Session, user_id: UUID, role_id: int, assigned_by_user_id: Optional[UUID] = None):
        """Assign roles to the new user."""
        # Check if the user already has this role
        existing_role = db.query(models.UserRole).filter(
            models.UserRole.user_id == user_id,
            models.UserRole.role_id == role_id
        ).first()
        
        if existing_role:
            # User already has this role, skip creation
            return
            
        # If assigned_by_user_id is not provided, use the user_id itself
        if assigned_by_user_id is None:
            assigned_by_user_id = user_id
        
        try:
            # Get the next user_role_id by finding max + 1
            max_id_result = db.query(func.max(models.UserRole.user_role_id)).first()
            next_id = (max_id_result[0] or 0) + 1
            
            # Create UserRole record
            user_role = models.UserRole(
                user_role_id=next_id,  # Manually set the ID
                user_id=user_id,
                role_id=role_id,
                assigned_by_user_id=assigned_by_user_id
                # created_at and updated_at are automatically set by database
            )
            db.add(user_role)
            
        except Exception as e:
            # Fallback: Let database handle it or use alternative approach
            user_role = models.UserRole(
                user_id=user_id,
                role_id=role_id,
                assigned_by_user_id=assigned_by_user_id
            )
            db.add(user_role)
    
    @staticmethod
    def create_user_by_admin(
        db: Session, 
        user_data: AdminUserCreate, 
        created_by_admin_id: UUID
    ) -> AdminUserCreatedResponse:
        """
        Create a new user by administrator.
        
        Args:
            db: Database session
            user_data: User creation data
            created_by_admin_id: ID of admin creating the user
            
        Returns:
            AdminUserCreatedResponse with creation details
        """
        try:
            # 1. Validate all foreign key references
            references = AdminUserService.validate_user_references(db, user_data)
            
            # 2. Check for duplicate phone/email
            is_duplicate, error_msg = AdminUserService.check_duplicate_identifiers(
                db, user_data.phone_number, user_data.email
            )
            if is_duplicate:
                raise ConflictException(detail=error_msg)
            
            # 3. Validate role-specific requirements
            if hasattr(user_data, 'freelance_document_number') and user_data.user_type_id == 6 and not user_data.freelance_document_number:
                raise BadRequestException(
                    detail="رقم وثيقة العمل الحر مطلوب للمندوبين التجاريين (RESELLER)"
                )
            
            if hasattr(user_data, 'license_number') and user_data.user_type_id == 4 and not user_data.license_number:
                raise BadRequestException(
                    detail="رقم الترخيص مطلوب للأسر المنتجة (PRODUCING_FAMILY)"
                )
            
            # 4. Generate password if not provided
            password_to_hash = user_data.password
            temporary_password = None
            
            if not password_to_hash:
                password_to_hash = AdminUserService.generate_temporary_password()
                temporary_password = password_to_hash
            
            # 5. Hash the password
            password_hash = get_password_hash(password_to_hash)
            
            # 6. Prepare additional data
            additional_data = AdminUserService.prepare_additional_data(user_data)
            
            # 7. Determine final role ID (use provided or default to user_type_id)
            final_role_id = user_data.default_user_role_id or user_data.user_type_id
            
            # 8. Create user model instance - FIXED: use func.now() instead of db.func.now()
            new_user = models.User(
                phone_number=user_data.phone_number,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                email=user_data.email,
                password_hash=password_hash,
                user_type_id=user_data.user_type_id,
                account_status_id=user_data.account_status_id,
                default_user_role_id=final_role_id,
                user_verification_status_id=references['verification_status'].user_verification_status_id,
                preferred_language_code=user_data.preferred_language_code,
                additional_data=additional_data,
                updated_by_user_id=created_by_admin_id,
                # Set phone as verified for admin-created users
                phone_verified_at=func.now()  # FIXED HERE: func.now() instead of db.func.now()
            )
            
            # 9. Save to database
            db.add(new_user)
            db.flush()  # Get the user_id without committing
            
            # 10. Create license if required
            AdminUserService.create_user_license(
                db, new_user.user_id, user_data.user_type_id, 
                user_data, created_by_admin_id
            )
            
            # 11. Assign roles
            AdminUserService.assign_user_roles(db, new_user.user_id, final_role_id)
            
            # 12. Commit all changes
            db.commit()
            db.refresh(new_user)
            
            # 13. Load translations for response (from src.users.models)
            user_type_translation = db.query(models.UserTypeTranslation).filter(
                models.UserTypeTranslation.user_type_id == new_user.user_type_id,
                models.UserTypeTranslation.language_code == user_data.preferred_language_code
            ).first()
            
            account_status_translation = db.query(models.AccountStatusTranslation).filter(
                models.AccountStatusTranslation.account_status_id == new_user.account_status_id,
                models.AccountStatusTranslation.language_code == user_data.preferred_language_code
            ).first()
            
            # 14. TODO: Implement notification services (commented for now)
            welcome_sent = False
            sms_sent = False
            
            # if hasattr(user_data, 'send_welcome_email') and user_data.send_welcome_email and user_data.email:
            #     # email_service.send_welcome_email(...)
            #     welcome_sent = True
            
            # if hasattr(user_data, 'send_sms_credentials') and user_data.send_sms_credentials:
            #     # sms_service.send_credentials_sms(...)
            #     sms_sent = True
            
            # 16. Return success response
            return AdminUserCreatedResponse(
                user_id=new_user.user_id,
                phone_number=new_user.phone_number,
                email=new_user.email,
                first_name=new_user.first_name,
                last_name=new_user.last_name,
                full_name=f"{new_user.first_name} {new_user.last_name}",
                user_type=user_type_translation.translated_user_type_name if user_type_translation else references['user_type'].user_type_name_key,
                account_status=account_status_translation.translated_status_name if account_status_translation else references['account_status'].status_name_key,
                default_role=references.get('role', references['user_type']).role_name_key if references.get('role') else None,
                verification_status=references['verification_status'].status_name_key,
                temporary_password=temporary_password,
                message=f"User created successfully as {user_type_translation.translated_user_type_name if user_type_translation else 'user'}",
                welcome_sent=welcome_sent,
                sms_sent=sms_sent,
                created_at=new_user.created_at
            )
            
        except IntegrityError as e:
            db.rollback()
            # Extract more specific error message
            error_detail = str(e.orig) if hasattr(e, 'orig') else str(e)
            raise ConflictException(
                detail=f"Database integrity error. Possible duplicate entry or constraint violation: {error_detail}"
            )
        except Exception as e:
            db.rollback()
            if isinstance(e, (BadRequestException, NotFoundException, ConflictException)):
                raise
            raise BadRequestException(
                detail=f"Failed to create user: {str(e)}"
            )