from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from database.session import get_db, get_cursor
from security import hash_password, verify_password, create_access_token

router = APIRouter()

class RegisterInput(BaseModel):
    name:     str
    email:    str
    password: str
    role:     str 
    cgpa:            float = None
    major:           str   = None
    graduation_year: int   = None
    company_id: int = None


class LoginInput(BaseModel):
    email:    str
    password: str


@router.post("/register")
def register(data: RegisterInput):
    """
    Registers a new student or recruiter.
    Creates a row in Accounts first, then in Students or Recruiters.
    """
    conn = get_db()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            "SELECT account_id FROM Accounts WHERE email = %s",
            (data.email,)
        )
        if cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists."
            )

        if data.role not in ("student", "recruiter"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be either 'student' or 'recruiter'."
            )

        hashed = hash_password(data.password)

        cur.execute(
            """
            INSERT INTO Accounts (name, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
            RETURNING account_id
            """,
            (data.name, data.email, hashed, data.role)
        )
        account_id = cur.fetchone()["account_id"]

        if data.role == "student":
            cur.execute(
                """
                INSERT INTO Students (student_id, cgpa, major, graduation_year)
                VALUES (%s, %s, %s, %s)
                """,
                (account_id, data.cgpa, data.major, data.graduation_year)
            )
        elif data.role == "recruiter":
            cur.execute(
                """
                INSERT INTO Recruiters (recruiter_id, company_id)
                VALUES (%s, %s)
                """,
                (account_id, data.company_id)
            )

        conn.commit()
        return {
            "message":    "Account created successfully.",
            "account_id": account_id,
            "role":       data.role
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.post("/login")
def login(data: LoginInput):
    """
    Logs in a student or recruiter.
    Returns a JWT token that must be sent with every subsequent request.
    """
    conn = get_db()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT account_id, name, password_hash, role
            FROM Accounts
            WHERE email = %s
            """,
            (data.email,)
        )
        account = cur.fetchone()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No account found with this email."
            )

        if not verify_password(data.password, account["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password."
            )

        token = create_access_token({
            "account_id": account["account_id"],
            "name":       account["name"],
            "role":       account["role"]
        })

        return {
            "access_token": token,
            "token_type":   "bearer",
            "account_id":   account["account_id"],
            "name":         account["name"],
            "role":         account["role"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()