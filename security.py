from jose import jwt
from fastapi import HTTPException
from fastapi.security import HTTPBearer

# Define your JWT secret key (should be securely stored)
SECRET_KEY = os.environ.get("AUTH0_CLIENT_SECRET")
ALGORITHM = "HS256"

# Define a security scheme for JWT tokens
security_scheme = HTTPBearer()

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

