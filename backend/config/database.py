"""
Supabase Database Connection and Client
Provides async database operations for Myelin backend
"""

from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from .settings import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """Supabase database client wrapper"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client"""
        try:
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                logger.warning("Supabase credentials not configured. Database features will be disabled.")
                return
            
            self.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            logger.info("✅ Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.client is not None
    
    # Organizations
    async def create_organization(self, name: str, tier: str = "free") -> Dict[str, Any]:
        """Create a new organization"""
        data = {
            "name": name,
            "tier": tier,
            "is_active": True
        }
        response = self.client.table("organizations").insert(data).execute()
        return response.data[0] if response.data else None
    
    async def get_organization(self, org_id: str) -> Optional[Dict[str, Any]]:
        """Get organization by ID"""
        response = self.client.table("organizations").select("*").eq("id", org_id).execute()
        return response.data[0] if response.data else None
    
    async def get_organization_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get organization by name"""
        response = self.client.table("organizations").select("*").eq("name", name).execute()
        return response.data[0] if response.data else None
    
    # Users
    async def create_user(self, email: str, password_hash: str, organization_id: str, 
                         full_name: Optional[str] = None, role: str = "developer") -> Dict[str, Any]:
        """Create a new user"""
        data = {
            "email": email,
            "password_hash": password_hash,
            "organization_id": organization_id,
            "full_name": full_name,
            "role": role,
            "is_active": True
        }
        response = self.client.table("users").insert(data).execute()
        return response.data[0] if response.data else None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        response = self.client.table("users").select("*").eq("email", email).execute()
        return response.data[0] if response.data else None
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        response = self.client.table("users").select("*").eq("id", user_id).execute()
        return response.data[0] if response.data else None
    
    # API Keys
    async def create_api_key(self, organization_id: str, user_id: str, key_hash: str,
                            key_prefix: str, name: Optional[str] = None,
                            rate_limit_per_minute: int = 60) -> Dict[str, Any]:
        """Create a new API key"""
        data = {
            "organization_id": organization_id,
            "user_id": user_id,
            "key_hash": key_hash,
            "key_prefix": key_prefix,
            "name": name,
            "is_active": True,
            "rate_limit_per_minute": rate_limit_per_minute
        }
        response = self.client.table("api_keys").insert(data).execute()
        return response.data[0] if response.data else None
    
    async def get_api_key_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """Get API key by hash"""
        response = self.client.table("api_keys").select("*").eq("key_hash", key_hash).eq("is_active", True).execute()
        return response.data[0] if response.data else None
    
    async def list_api_keys(self, organization_id: str) -> List[Dict[str, Any]]:
        """List all API keys for an organization"""
        response = self.client.table("api_keys").select("*").eq("organization_id", organization_id).execute()
        return response.data if response.data else []
    
    async def update_api_key_last_used(self, key_id: str):
        """Update last_used_at timestamp for API key"""
        self.client.table("api_keys").update({"last_used_at": "now()"}).eq("id", key_id).execute()
    
    async def revoke_api_key(self, key_id: str, organization_id: str):
        """Revoke an API key"""
        self.client.table("api_keys").update({"is_active": False}).eq("id", key_id).eq("organization_id", organization_id).execute()
    
    # Custom Rules
    async def create_custom_rule(self, organization_id: str, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom rule"""
        data = {
            "organization_id": organization_id,
            **rule_data
        }
        response = self.client.table("custom_rules").insert(data).execute()
        return response.data[0] if response.data else None
    
    async def get_custom_rule(self, rule_id: str, organization_id: str) -> Optional[Dict[str, Any]]:
        """Get a custom rule by ID"""
        response = self.client.table("custom_rules").select("*").eq("id", rule_id).eq("organization_id", organization_id).execute()
        return response.data[0] if response.data else None
    
    async def list_custom_rules(self, organization_id: str, pillar: Optional[str] = None,
                               is_active: bool = True) -> List[Dict[str, Any]]:
        """List custom rules for an organization"""
        query = self.client.table("custom_rules").select("*").eq("organization_id", organization_id)
        
        if pillar:
            query = query.eq("pillar", pillar)
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        response = query.execute()
        return response.data if response.data else []
    
    async def update_custom_rule(self, rule_id: str, organization_id: str, 
                                update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a custom rule"""
        response = self.client.table("custom_rules").update(update_data).eq("id", rule_id).eq("organization_id", organization_id).execute()
        return response.data[0] if response.data else None
    
    async def delete_custom_rule(self, rule_id: str, organization_id: str):
        """Delete a custom rule"""
        self.client.table("custom_rules").delete().eq("id", rule_id).eq("organization_id", organization_id).execute()
    
    # Audit Logs
    async def create_audit_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an audit log entry"""
        response = self.client.table("audit_logs").insert(log_data).execute()
        return response.data[0] if response.data else None
    
    async def get_audit_logs(self, organization_id: str, limit: int = 100,
                            offset: int = 0) -> List[Dict[str, Any]]:
        """Get audit logs for an organization"""
        response = self.client.table("audit_logs").select("*").eq("organization_id", organization_id).order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        return response.data if response.data else []
    
    async def get_audit_stats(self, organization_id: str) -> Dict[str, Any]:
        """Get audit statistics for an organization"""
        # This would require aggregation queries - simplified version
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
        query = self.client.table("rule_templates").select("*").eq("is_public", True)
        
        if pillar:
            query = query.eq("pillar", pillar)
        
        response = query.execute()
        return response.data if response.data else []


# Global database instance
db = Database()


def get_db() -> Database:
    """Get database instance"""
    return db
