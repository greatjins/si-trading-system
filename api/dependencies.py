"""
공통 의존성
"""
from fastapi import Depends

from api.auth.security import get_current_active_user, require_role


# 인증된 사용자 필요
RequireAuth = Depends(get_current_active_user)

# 트레이더 역할 필요
RequireTrader = Depends(require_role("trader"))

# 관리자 역할 필요
RequireAdmin = Depends(require_role("admin"))
