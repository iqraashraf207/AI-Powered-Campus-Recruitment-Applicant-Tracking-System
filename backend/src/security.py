from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

pwd_context = CryptContext(
    schemes = ["bcrypt"],
    deprecated = "auto",
    bcrypt__rounds = 12
)

def hash_password(plain_password: str) -> str:
    """
    Converts a plain text password into a secure hash.
    The hash is what gets stored in the database (never the plain password).
    Example: "mypassword123" => "$2b$12$...long hash string..."
    """
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain password matches a stored hash.
    Used during login to verify the entered password.
    Returns True if they match and False if not.
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    """
    Creates a JWT token containing the user's account_id and role.
    This token is sent to the browser after login and used to identify the user on every subsequent request.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm = ALGORITHM)

def decode_access_token(token: str) -> dict:
    """
    Decodes a JWT token and returns the data inside it.
    Returns None if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])
        return payload
    except JWTError:
        return None