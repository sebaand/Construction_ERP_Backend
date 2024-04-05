from fastapi import Depends, APIRouter
from security import security_scheme, verify_token

router = APIRouter()

@router.get("/protected")
def protected_route(token: str = Depends(security_scheme)):
    payload = verify_token(token)
    return {"message": "Authenticated", "user": payload}
