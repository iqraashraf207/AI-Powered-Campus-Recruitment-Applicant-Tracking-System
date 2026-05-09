from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database.session import get_db, get_cursor
from dependencies.auth import get_current_student
import re

router = APIRouter()

class ProfileUpdate(BaseModel):
    cgpa: float
    major: str
    graduation_year: int


class ResumeInput(BaseModel):
    raw_text: str


class SkillUpdate(BaseModel):
    skill_id: int
    proficiency_level: str


def extract_experience_years(text: str) -> int:
    """
    Agent 1: Resume Keyword Matching Agent.
    Finds month-year date ranges in the resume text and calculates
    total years of experience from them.

    Handles patterns like:
    - June 2021 - August 2023
    - Jan 2020 to Dec 2022

    Year-only ranges are intentionally excluded to avoid
    double counting and false positives from education dates.
    """
    total_months = 0
    text_lower   = text.lower()

    month_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4,
        "may": 5, "jun": 6, "jul": 7, "aug": 8,
        "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }

    pattern = (
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{4})'
        r'\s*(?:-|to|–)\s*'
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{4})'
    )
    matches = re.findall(pattern, text_lower)

    for match in matches:
        start_month = month_map.get(match[0][:3], 1)
        start_year  = int(match[1])
        end_month   = month_map.get(match[2][:3], 1)
        end_year    = int(match[3])
        months      = (end_year - start_year) * 12 + (end_month - start_month)
        if months > 0:
            total_months += months

    return max(0, total_months // 12)


@router.get("/profile")
def get_profile(current_user: dict = Depends(get_current_student)):
    """
    Returns the full profile of the logged-in student
    including their skills and resume info.
    """
    conn = get_db()
    cur  = get_cursor(conn)
    try:
        student_id = current_user["account_id"]

        cur.execute(
            """
            SELECT a.name, a.email, s.cgpa, s.major, s.graduation_year
            FROM Students s
            JOIN Accounts a ON s.student_id = a.account_id
            WHERE s.student_id = %s
            """,
            (student_id,)
        )
        profile = cur.fetchone()

        if not profile:
            raise HTTPException(
                status_code = 404,
                detail = "Student profile not found!"
            )

        cur.execute(
            """
            SELECT sk.skill_id, sk.skill_name, sk.category, ss.proficiency_level
            FROM Student_Skills ss
            JOIN Skills sk ON ss.skill_id = sk.skill_id
            WHERE ss.student_id = %s
            ORDER BY sk.skill_name
            """,
            (student_id,)
        )
        skills = cur.fetchall()

        cur.execute(
            """
            SELECT raw_text, parsed_skills, experience_years, last_parsed_at
            FROM Resumes
            WHERE student_id = %s
            """,
            (student_id,)
        )
        resume = cur.fetchone()

        return {
            "profile": dict(profile),
            "skills":  [dict(s) for s in skills],
            "resume":  dict(resume) if resume else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))
    finally:
        cur.close()
        conn.close()


@router.put("/profile")
def update_profile(
    data: ProfileUpdate,
    current_user: dict = Depends(get_current_student)
):
    """
    Updates the student's CGPA, major, and graduation year.
    """
    conn = get_db()
    cur  = get_cursor(conn)
    try:
        student_id = current_user["account_id"]

        cur.execute(
            """
            UPDATE Students
            SET cgpa = %s, major = %s, graduation_year = %s
            WHERE student_id = %s
            """,
            (data.cgpa, data.major, data.graduation_year, student_id)
        )
        conn.commit()
        return {"message": "Profile updated successfully!"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code = 500, detail = str(e))
    finally:
        cur.close()
        conn.close()


@router.post("/resume")
def submit_resume(
    data: ResumeInput,
    current_user: dict = Depends(get_current_student)
):
    """
    Agent 1: Resume Keyword Matching Agent.

    Flow:
    1. Loads all known skills from the Skills table
    2. Scans resume text for matching skill names
    3. Extracts years of experience from month-year date ranges only
    4. Saves resume to Resumes table
    5. Adds found skills to Student_Skills with default proficiency 'beginner'
    6. Student can manually update proficiency levels from their profile page
    """
    conn = get_db()
    cur  = get_cursor(conn)
    try:
        student_id = current_user["account_id"]

        cur.execute("SELECT skill_id, skill_name FROM Skills")
        all_skills = cur.fetchall()

        found_skill_ids   = []
        found_skill_names = []
        resume_lower      = data.raw_text.lower()

        for skill in all_skills:
            if skill["skill_name"].lower() in resume_lower:
                found_skill_ids.append(skill["skill_id"])
                found_skill_names.append(skill["skill_name"])

        experience_years = extract_experience_years(data.raw_text)

        cur.execute(
            "SELECT resume_id FROM Resumes WHERE student_id = %s",
            (student_id,)
        )
        existing_resume = cur.fetchone()

        if existing_resume:
            cur.execute(
                """
                UPDATE Resumes
                SET raw_text         = %s,
                    parsed_skills    = %s,
                    experience_years = %s,
                    last_parsed_at   = NOW()
                WHERE student_id = %s
                """,
                (
                    data.raw_text,
                    str(found_skill_names),
                    experience_years,
                    student_id
                )
            )
        else:
            cur.execute(
                """
                INSERT INTO Resumes
                    (student_id, raw_text, parsed_skills, experience_years, last_parsed_at)
                VALUES (%s, %s, %s, %s, NOW())
                """,
                (
                    student_id,
                    data.raw_text,
                    str(found_skill_names),
                    experience_years
                )
            )

        for skill_id in found_skill_ids:
            cur.execute(
                """
                SELECT 1 FROM Student_Skills
                WHERE student_id = %s AND skill_id = %s
                """,
                (student_id, skill_id)
            )
            if not cur.fetchone():
                cur.execute(
                    """
                    INSERT INTO Student_Skills (student_id, skill_id, proficiency_level)
                    VALUES (%s, %s, 'beginner')
                    """,
                    (student_id, skill_id)
                )

        conn.commit()
        return {
            "message":        "Resume saved and skills extracted successfully!",
            "skills_found":   found_skill_names,
            "skills_count":   len(found_skill_ids),
            "experience_years": experience_years
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code = 500, detail = str(e))
    finally:
        cur.close()
        conn.close()


@router.put("/skills")
def update_skill_proficiency(
    data: SkillUpdate,
    current_user: dict = Depends(get_current_student)
):
    """
    Allows a student to manually update the proficiency level
    of one of their skills from their profile page.
    Default is 'beginner' => student upgrades it here.
    """
    conn = get_db()
    cur  = get_cursor(conn)
    try:
        student_id = current_user["account_id"]

        if data.proficiency_level not in ("beginner", "intermediate", "advanced"):
            raise HTTPException(
                status_code = 400,
                detail = "Proficiency must be beginner, intermediate, or advanced!"
            )

        cur.execute(
            """
            UPDATE Student_Skills
            SET proficiency_level = %s
            WHERE student_id = %s AND skill_id = %s
            """,
            (data.proficiency_level, student_id, data.skill_id)
        )

        if cur.rowcount == 0:
            raise HTTPException(
                status_code = 404,
                detail = "This skill was not found on your profile!"
            )

        conn.commit()
        return {"message": "Skill proficiency updated successfully!"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code = 500, detail = str(e))
    finally:
        cur.close()
        conn.close()

@router.get("/all-skills")
def get_all_skills():
    """
    Returns all skills from the Skills table.
    Used to populate skill dropdowns on the frontend.
    No login required.
    """
    conn = get_db()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            "SELECT skill_id, skill_name, category FROM Skills ORDER BY skill_name"
        )
        skills = cur.fetchall()
        return [dict(s) for s in skills]
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))
    finally:
        cur.close()
        conn.close()