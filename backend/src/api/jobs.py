from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from database.session import get_db, get_cursor
from dependencies.auth import get_current_recruiter

router = APIRouter()


class SkillRequirement(BaseModel):
    skill_id: int
    weight:   float 


class JobPostInput(BaseModel):
    title:       str
    description: str
    min_cgpa:    float
    deadline:    str   # format: YYYY-MM-DD
    salary:      float
    skills:      List[SkillRequirement]


@router.get("/")
def get_active_jobs():
    """
    Returns all active job postings using Active_Jobs_View.
    No login required — any visitor can browse jobs.
    """
    conn = get_db()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            "SELECT * FROM Active_Jobs_View ORDER BY posted_at DESC"
        )
        jobs = cur.fetchall()
        return [dict(j) for j in jobs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.get("/companies/all")
def get_all_companies():
    """
    Returns all companies from the Companies table.
    Used to populate the company dropdown on the
    recruiter registration page.
    No login required.
    """
    conn = get_db()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            "SELECT company_id, name, industry, location FROM Companies ORDER BY name"
        )
        companies = cur.fetchall()
        return [dict(c) for c in companies]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.get("/{job_id}")
def get_job_detail(job_id: int):
    """
    Returns full details of one job including all
    required and preferred skills.
    No login required.
    """
    conn = get_db()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT jp.*, c.name AS company_name, c.location
            FROM Job_Posts jp
            JOIN Companies c ON jp.company_id = c.company_id
            WHERE jp.job_id = %s
            """,
            (job_id,)
        )
        job = cur.fetchone()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")

        cur.execute(
            """
            SELECT sk.skill_id, sk.skill_name, sk.category, jrs.weight
            FROM Job_Required_Skills jrs
            JOIN Skills sk ON jrs.skill_id = sk.skill_id
            WHERE jrs.job_id = %s
            ORDER BY jrs.weight DESC, sk.skill_name
            """,
            (job_id,)
        )
        skills = cur.fetchall()

        return {
            "job":    dict(job),
            "skills": [dict(s) for s in skills]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.post("/")
def post_job(
    data: JobPostInput,
    current_user: dict = Depends(get_current_recruiter)
):
    """
    Allows a recruiter to post a new job opening.
    Also saves the required and preferred skills for the job.
    The BEFORE INSERT trigger fires automatically and rejects
    the insert if the deadline is in the past.
    """
    conn = get_db()
    cur  = get_cursor(conn)
    try:
        recruiter_id = current_user["account_id"]

        cur.execute(
            "SELECT company_id FROM Recruiters WHERE recruiter_id = %s",
            (recruiter_id,)
        )
        recruiter = cur.fetchone()

        if not recruiter:
            raise HTTPException(
                status_code=404,
                detail="Recruiter profile not found."
            )

        company_id = recruiter["company_id"]

        cur.execute(
            """
            INSERT INTO Job_Posts
                (company_id, title, description, min_cgpa, deadline, salary, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'active')
            RETURNING job_id
            """,
            (
                company_id,
                data.title,
                data.description,
                data.min_cgpa,
                data.deadline,
                data.salary
            )
        )
        job_id = cur.fetchone()["job_id"]

        for skill in data.skills:
            cur.execute(
                """
                INSERT INTO Job_Required_Skills (job_id, skill_id, weight)
                VALUES (%s, %s, %s)
                """,
                (job_id, skill.skill_id, skill.weight)
            )

        conn.commit()
        return {
            "message": "Job posted successfully.",
            "job_id":  job_id
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.get("/my/postings")
def get_my_job_postings(current_user: dict = Depends(get_current_recruiter)):
    """
    Returns all jobs posted by the logged-in recruiter
    with application counts per status
    from Application_Funnel_View.
    """
    conn = get_db()
    cur  = get_cursor(conn)
    try:
        recruiter_id = current_user["account_id"]

        cur.execute(
            "SELECT company_id FROM Recruiters WHERE recruiter_id = %s",
            (recruiter_id,)
        )
        recruiter  = cur.fetchone()
        company_id = recruiter["company_id"]

        cur.execute(
            """
            SELECT afv.*
            FROM Application_Funnel_View afv
            JOIN Companies c ON afv.company_name = c.name
            WHERE c.company_id = %s
            """,
            (company_id,)
        )
        postings = cur.fetchall()
        return [dict(p) for p in postings]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()