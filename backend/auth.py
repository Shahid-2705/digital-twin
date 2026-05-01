import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from backend import config

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

class TokenRequest(BaseModel):
    username: str
    password: str

def get_users() -> list[dict]:
    users_file = config.DATA_DIR / "users.json"
    if not users_file.exists():
        return []
    try:
        with open(users_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    # Use API_AUTH_TOKEN as the secret key for signing JWTs
    encoded_jwt = jwt.encode(to_encode, config.API_AUTH_TOKEN, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/token")
async def login_for_access_token(req: TokenRequest):
    users = get_users()
    user = next((u for u in users if u.get("username") == req.username), None)
    
    if not user or not verify_password(req.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["username"], "role": user.get("role")})
    return {"access_token": access_token, "token_type": "bearer"}

async def verify_jwt(request: Request, creds: HTTPAuthorizationCredentials = Depends(security)):
    exempt_paths = {"/", "/health", "/app.js", "/styles.css", "/auth/token"}
    if request.url.path in exempt_paths or request.url.path.startswith("/components/"):
        return None
        
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(creds.credentials, config.API_AUTH_TOKEN, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        request.state.user = payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload
