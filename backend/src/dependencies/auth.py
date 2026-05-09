from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from security import decode_access_token

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Reads the JWT token from the request and returns the current logged-in user's account_id and role.
    Raises a 401 error if the token is missing or invalid.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid or expired token! Please log in again."
        )
    return payload

def get_current_student(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Ensures the logged-in user is a student.
    Raises a 403 error if they are a recruiter.
    We use this as a dependency on any student-only endpoint.
    """
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "Access denied! Students only."
        )
    return current_user

def get_current_recruiter(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Ensures the logged-in user is a recruiter.
    Raises a 403 error if they are a student.
    We use this as a dependency on any recruiter-only endpoint.
    """
    if current_user.get("role") != "recruiter":
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "Access denied! Recruiters only."
        )
    return current_user