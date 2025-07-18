from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

# رمزنگاری
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# تنظیمات JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
