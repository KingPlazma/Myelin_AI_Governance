"""
Firebase Database Connection and Client
Provides async database operations for Myelin backend
"""

from typing import Optional, Dict, Any, List
import firebase_admin
from firebase_admin import credentials, firestore
from .settings import settings
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

logger = logging.getLogger(__name__)

# Thread pool for running sync Firestore operations asynchronously
_executor = ThreadPoolExecutor(max_workers=5)


class Database:
    """Firebase Firestore database client wrapper"""
    
    def __init__(self):
        self.client: Optional[Any] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Firebase client"""
        try:
            if not settings.FIREBASE_CREDENTIALS_JSON:
                logger.warning("Firebase credentials not configured. Database features will be disabled.")
                return
            
            # Initialize Firebase app only if not already initialized
            try:
                firebase_admin.get_app()
            except ValueError:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_JSON)
                firebase_admin.initialize_app(cred)
            
            self.client = firestore.client()
            logger.info("✅ Firebase Firestore client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firebase client: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.client is not None
    
    async def _run_async(self, func, *args, **kwargs):
        """Run a blocking function asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, func, *args)

    def _doc_to_dict(self, doc) -> Optional[Dict[str, Any]]:
        """Convert a Firestore document snapshot to a dict with id."""
        if not doc or not doc.exists:
            return None
        data = doc.to_dict() or {}
        return {"id": doc.id, **data}
    
    # Organizations
    async def create_organization(self, name: str, tier: str = "free") -> Dict[str, Any]:
        """Create a new organization"""
        if not self.client:
            return None
        
        data = {
            "name": name,
            "tier": tier,
            "is_active": True,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        
        try:
            _, doc_ref = self.client.collection("organizations").add(data)
            created_doc = doc_ref.get()
            created = self._doc_to_dict(created_doc)
            if created and created.get("created_at") is None:
                created["created_at"] = datetime.utcnow()
            return created
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            return None
    
    async def get_organization(self, org_id: str) -> Optional[Dict[str, Any]]:
        """Get organization by ID"""
        if not self.client:
            return None
        
        try:
            doc = self.client.collection("organizations").document(org_id).get()
            if doc.exists:
                return {
                    "id": doc.id,
                    **doc.to_dict()
                }
            return None
        except Exception as e:
            logger.error(f"Error getting organization: {e}")
            return None
    
    async def get_organization_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get organization by name"""
        if not self.client:
            return None
        
        try:
            docs = self.client.collection("organizations").where("name", "==", name).stream()
            for doc in docs:
                return {
                    "id": doc.id,
                    **doc.to_dict()
                }
            return None
        except Exception as e:
            logger.error(f"Error getting organization by name: {e}")
            return None
    
    # Users
    async def create_user(self, email: str, password_hash: str, organization_id: str,
                         full_name: Optional[str] = None, role: str = "developer") -> Dict[str, Any]:
        """Create a new user"""
        if not self.client:
            return None
        
        data = {
            "email": email,
            "password_hash": password_hash,
            "organization_id": organization_id,
            "full_name": full_name,
            "role": role,
            "email_verified": False,
            "email_verification_token_hash": None,
            "email_verification_expires_at": None,
            "email_verified_at": None,
            "is_active": True,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        
        try:
            _, doc_ref = self.client.collection("users").add(data)
            created_doc = doc_ref.get()
            created = self._doc_to_dict(created_doc)
            if created and created.get("created_at") is None:
                created["created_at"] = datetime.utcnow()
            return created
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None

    async def set_user_email_verification_token(self, user_id: str, token_hash: str,
                                                expires_at: datetime) -> bool:
        """Store email verification token hash and expiration for a user."""
        if not self.client:
            return False

        try:
            self.client.collection("users").document(user_id).update({
                "email_verification_token_hash": token_hash,
                "email_verification_expires_at": expires_at,
                "email_verified": False,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            logger.error(f"Error setting email verification token: {e}")
            return False

    async def get_user_by_email_verification_token_hash(self, token_hash: str) -> Optional[Dict[str, Any]]:
        """Get user by email verification token hash."""
        if not self.client:
            return None

        try:
            docs = self.client.collection("users")\
                .where("email_verification_token_hash", "==", token_hash)\
                .limit(1)\
                .stream()
            for doc in docs:
                return {
                    "id": doc.id,
                    **doc.to_dict()
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user by verification token hash: {e}")
            return None

    async def mark_user_email_verified(self, user_id: str) -> bool:
        """Mark user's email as verified and clear verification token fields."""
        if not self.client:
            return False

        try:
            self.client.collection("users").document(user_id).update({
                "email_verified": True,
                "email_verified_at": firestore.SERVER_TIMESTAMP,
                "email_verification_token_hash": None,
                "email_verification_expires_at": None,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            logger.error(f"Error marking user email verified: {e}")
            return False
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        if not self.client:
            return None
        
        try:
            docs = self.client.collection("users").where("email", "==", email).stream()
            for doc in docs:
                return {
                    "id": doc.id,
                    **doc.to_dict()
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        if not self.client:
            return None
        
        try:
            doc = self.client.collection("users").document(user_id).get()
            if doc.exists:
                return {
                    "id": doc.id,
                    **doc.to_dict()
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    # API Keys
    async def create_api_key(self, organization_id: str, user_id: str, key_hash: str,
                            key_prefix: str, name: Optional[str] = None,
                            rate_limit_per_minute: int = 60) -> Dict[str, Any]:
        """Create a new API key"""
        if not self.client:
            return None
        
        data = {
            "organization_id": organization_id,
            "user_id": user_id,
            "key_hash": key_hash,
            "key_prefix": key_prefix,
            "name": name,
            "is_active": True,
            "rate_limit_per_minute": rate_limit_per_minute,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        
        try:
            _, doc_ref = self.client.collection("api_keys").add(data)
            created_doc = doc_ref.get()
            created = self._doc_to_dict(created_doc)
            if created and created.get("created_at") is None:
                created["created_at"] = datetime.utcnow()
            return created
        except Exception as e:
            logger.error(f"Error creating API key: {e}")
            return None
    
    async def get_api_key_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """Get API key by hash"""
        if not self.client:
            return None
        
        try:
            docs = self.client.collection("api_keys")\
                .where("key_hash", "==", key_hash)\
                .where("is_active", "==", True)\
                .stream()
            for doc in docs:
                return {
                    "id": doc.id,
                    **doc.to_dict()
                }
            return None
        except Exception as e:
            logger.error(f"Error getting API key by hash: {e}")
            return None
    
    async def list_api_keys(self, organization_id: str) -> List[Dict[str, Any]]:
        """List all API keys for an organization"""
        if not self.client:
            return []
        
        try:
            docs = self.client.collection("api_keys")\
                .where("organization_id", "==", organization_id)\
                .stream()
            
            keys = []
            for doc in docs:
                keys.append({
                    "id": doc.id,
                    **doc.to_dict()
                })
            return keys
        except Exception as e:
            logger.error(f"Error listing API keys: {e}")
            return []
    
    async def update_api_key_last_used(self, key_id: str):
        """Update last_used_at timestamp for API key"""
        if not self.client:
            return
        
        try:
            self.client.collection("api_keys").document(key_id).update({
                "last_used_at": firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            logger.error(f"Error updating API key last_used: {e}")
    
    async def revoke_api_key(self, key_id: str, organization_id: str):
        """Revoke an API key"""
        if not self.client:
            return
        
        try:
            self.client.collection("api_keys").document(key_id).update({
                "is_active": False,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            logger.error(f"Error revoking API key: {e}")
    
    # Custom Rules
    async def create_custom_rule(self, organization_id: str, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom rule"""
        if not self.client:
            return None
        
        data = {
            "organization_id": organization_id,
            **rule_data,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        
        try:
            _, doc_ref = self.client.collection("custom_rules").add(data)
            created_doc = doc_ref.get()
            created = self._doc_to_dict(created_doc)
            if created and created.get("created_at") is None:
                created["created_at"] = datetime.utcnow()
            return created
        except Exception as e:
            logger.error(f"Error creating custom rule: {e}")
            return None
    
    async def get_custom_rule(self, rule_id: str, organization_id: str) -> Optional[Dict[str, Any]]:
        """Get a custom rule by ID"""
        if not self.client:
            return None
        
        try:
            docs = self.client.collection("custom_rules")\
                .where("rule_id", "==", rule_id)\
                .where("organization_id", "==", organization_id)\
                .limit(1)\
                .stream()
            for doc in docs:
                return self._doc_to_dict(doc)
            return None
        except Exception as e:
            logger.error(f"Error getting custom rule: {e}")
            return None
    
    async def list_custom_rules(self, organization_id: str, pillar: Optional[str] = None,
                               is_active: bool = True) -> List[Dict[str, Any]]:
        """List custom rules for an organization"""
        if not self.client:
            return []
        
        try:
            query = self.client.collection("custom_rules")\
                .where("organization_id", "==", organization_id)
            
            if pillar:
                query = query.where("pillar", "==", pillar)
            if is_active is not None:
                query = query.where("is_active", "==", is_active)
            
            docs = query.stream()
            rules = []
            for doc in docs:
                rules.append({
                    "id": doc.id,
                    **doc.to_dict()
                })
            return rules
        except Exception as e:
            logger.error(f"Error listing custom rules: {e}")
            return []
    
    async def update_custom_rule(self, rule_id: str, organization_id: str, 
                                update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a custom rule"""
        if not self.client:
            return None
        
        try:
            docs = self.client.collection("custom_rules")\
                .where("rule_id", "==", rule_id)\
                .where("organization_id", "==", organization_id)\
                .limit(1)\
                .stream()

            target_doc = None
            for doc in docs:
                target_doc = doc
                break

            if not target_doc:
                return None

            update_data["updated_at"] = firestore.SERVER_TIMESTAMP
            self.client.collection("custom_rules").document(target_doc.id).update(update_data)
            
            doc = self.client.collection("custom_rules").document(target_doc.id).get()
            if doc.exists:
                return self._doc_to_dict(doc)
            return None
        except Exception as e:
            logger.error(f"Error updating custom rule: {e}")
            return None
    
    async def delete_custom_rule(self, rule_id: str, organization_id: str):
        """Delete a custom rule"""
        if not self.client:
            return
        
        try:
            docs = self.client.collection("custom_rules")\
                .where("rule_id", "==", rule_id)\
                .where("organization_id", "==", organization_id)\
                .limit(1)\
                .stream()
            for doc in docs:
                self.client.collection("custom_rules").document(doc.id).delete()
                break
        except Exception as e:
            logger.error(f"Error deleting custom rule: {e}")
    
    # Audit Logs
    async def create_audit_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an audit log entry"""
        if not self.client:
            return None
        
        data = {
            **log_data,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        
        try:
            _, doc_ref = self.client.collection("audit_logs").add(data)
            created_doc = doc_ref.get()
            created = self._doc_to_dict(created_doc)
            if created and created.get("created_at") is None:
                created["created_at"] = datetime.utcnow()
            return created
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
            return None
    
    async def get_audit_logs(self, organization_id: str, limit: int = 100,
                            offset: int = 0) -> List[Dict[str, Any]]:
        """Get audit logs for an organization"""
        if not self.client:
            return []
        
        try:
            query = self.client.collection("audit_logs")\
                .where("organization_id", "==", organization_id)\
                .order_by("created_at", direction=firestore.Query.DESCENDING)\
                .offset(offset)\
                .limit(limit)
            
            docs = query.stream()
            logs = []
            for doc in docs:
                logs.append({
                    "id": doc.id,
                    **doc.to_dict()
                })
            return logs
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return []
    
    async def get_audit_stats(self, organization_id: str) -> Dict[str, Any]:
        """Get audit statistics for an organization"""
        # Fetch logs for aggregation
        logs = await self.get_audit_logs(organization_id, limit=1000)
        
        total = len(logs)
        blocked = sum(1 for log in logs if log.get("overall_decision") == "BLOCK")
        warned = sum(1 for log in logs if log.get("overall_decision") == "WARN")
        allowed = sum(1 for log in logs if log.get("overall_decision") == "ALLOW")
        
        return {
            "total_audits": total,
            "blocked": blocked,
            "warned": warned,
            "allowed": allowed,
            "block_rate": blocked / total if total > 0 else 0
        }
    
    # Rule Templates
    async def list_rule_templates(self, pillar: Optional[str] = None) -> List[Dict[str, Any]]:
        """List public rule templates"""
        if not self.client:
            return []
        
        try:
            query = self.client.collection("rule_templates")\
                .where("is_public", "==", True)
            
            if pillar:
                query = query.where("pillar", "==", pillar)
            
            docs = query.stream()
            templates = []
            for doc in docs:
                templates.append({
                    "id": doc.id,
                    **doc.to_dict()
                })
            return templates
        except Exception as e:
            logger.error(f"Error listing rule templates: {e}")
            return []


# Global database instance
db = Database()


def get_db() -> Database:
    """Get database instance"""
    return db
