"""
Audit Service
Handles audit logging and statistics
"""

from typing import Dict, Any, List
import logging

from backend.config.database import get_db
from backend.models.audit_log import AuditLogCreate

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit logging"""
    
    def __init__(self):
        self.db = get_db()
    
    async def log_audit(self, log_data: AuditLogCreate) -> Dict[str, Any]:
        """Create an audit log entry"""
        log_dict = log_data.model_dump()
        audit_log = await self.db.create_audit_log(log_dict)
        
        logger.debug(f"Audit logged: {log_data.audit_type} - {log_data.overall_decision}")
        
        return audit_log
    
    async def get_audit_history(self, organization_id: str, limit: int = 100,
                               offset: int = 0) -> List[Dict[str, Any]]:
        """Get audit history for an organization"""
        logs = await self.db.get_audit_logs(organization_id, limit, offset)
        return logs
    
    async def get_audit_stats(self, organization_id: str) -> Dict[str, Any]:
        """Get audit statistics for an organization"""
        stats = await self.db.get_audit_stats(organization_id)
        return stats


# Global audit service instance
audit_service = AuditService()


def get_audit_service() -> AuditService:
    """Get audit service instance"""
    return audit_service
