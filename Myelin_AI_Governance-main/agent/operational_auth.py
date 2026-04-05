from fastapi import Header, HTTPException

from config import AgentSettings


def require_operational_token(settings: AgentSettings):
    async def _require_token(x_myelin_ops_token: str | None = Header(default=None)):
        expected = settings.operational_token.strip()
        if not expected:
            return True
        if x_myelin_ops_token != expected:
            raise HTTPException(status_code=401, detail="Operational endpoint token is invalid")
        return True

    return _require_token
