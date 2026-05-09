from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from database.session import get_db, get_cursor
from dependencies.auth import get_current_recruiter

router = APIRouter()


class SkillRequirement(BaseModel):
    skill_id: int
    weight: float 


class JobPostInput(BaseModel):
    title: str
    description: str
    min_cgpa: float
    deadline: str 
    salary: float
    skills: List[SkillRequirement]


class CompanyInput(BaseModel):
    name: str
    industry: str
    location: str


@router.get("/")
def get_active_jobs():
    """
    Returns all active job postings using Active_Jobs_View.
    No login required => any visitor can browse jobs.
    """
    conn = get_db()
    cur = get_cursor(conn)
    try:
        cur.execute(
            "SELECT * FROM Active_Jobs_View ORDER BY posted_at DESC"
        )
        jobs = cur.fetchall()
        return [dict(j) for j in jobs]
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))
    finally:
        cur.close()
        conn.close()


@router.get("/companies/all")
def get_all_companies():
    """
    Returns all companies from the Companies table.
    Used to populate the company dropdown on the recruiter registration page.
    No login required.
    """
    conn = get_db()
    cur = get_cursor(conn)
    try:
        cur.execute(
            "SELECT company_id, name, industry, location FROM Companies ORDER BY name"
        )
        companies = cur.fetchall()
        return [dict(c) for c in companies]
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))
    finally:
        cur.close()
        conn.close()


@router.post("/companies/create")
def create_company(data: CompanyInput):
    """
    Creates a new company in the database.
    Called during recruiter registration when the company does not exist yet.
    No login required: this is called before the recruiter account is created.
    """
    conn = get_db()
    cur = get_cursor(conn)
    try:
        cur.execute(
            "SELECT company_id FROM Companies WHERE LOWER(name) = LOWER(%s)",
            (data.name.strip(),)
        )
        existing = cur.fetchone()
        if existing:
            raise HTTPException(
                status_code = 400,
                detail = "A company with this name already exists! Please select it from the dropdown instead."
            )

        cur.execute(
            """
            INSERT INTO Companies (name, industry, location)
            VALUES (%s, %s, %s)
            RETURNING company_id
            """,
            (data.name.strip(), data.industry.strip(), data.location.strip())
        )
        company_id = cur.fetchone()["company_id"]
        conn.commit()
        return {
            "message": "Company created successfully!",
            "company_id": company_id,
            "name": data.name.strip()
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code = 500, detail = str(e))
    finally:
        cur.close()
        conn.close()


@router.get("/my/postings")
def get_my_job_postings(current_user: dict = Depends(get_current_recruiter)):
    """
    Returns all jobs posted by the logged-in recruiter with application counts per status from Application_Funnel_View.
    """
    conn = get_db()
    cur = get_cursor(conn)
    try:
        recruiter_id = current_user["account_id"]

        cur.execute(
            "SELECT company_id FROM Recruiters WHERE recruiter_id = %s",
            (recruiter_id,)
        )
        recruiter = cur.fetchone()

        if not recruiter:
            raise HTTPException(
                status_code = 404,
                detail = "Recruiter profile not found!"
            )

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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))
    finally:
        cur.close()
        conn.close()


@router.patch("/{job_id}/close")
def close_job(
    job_id: int,
    current_user: dict = Depends(get_current_recruiter)
):
    """
    Allows a recruiter to close one of their own active job postings.
    Once closed, no new applications can be submitted to it.
    Only the recruiter whose company owns the job can close it.
    """
    conn = get_db()
    cur = get_cursor(conn)
    try:
        recruiter_id = current_user["account_id"]

        cur.execute(
            "SELECT company_id FROM Recruiters WHERE recruiter_id = %s",
            (recruiter_id,)
        )
        recruiter = cur.fetchone()

        if not recruiter:
            raise HTTPException(
                status_code = 404,
                detail = "Recruiter profile not found!"
            )

        cur.execute(
            "SELECT company_id, status FROM Job_Posts WHERE job_id = %s",
            (job_id,)
        )
        job = cur.fetchone()

        if not job:
            raise HTTPException(
                status_code = 404,
                detail = "Job not found!"
            )

        if job["company_id"] != recruiter["company_id"]:
            raise HTTPException(
                status_code = 403,
                detail = "Access denied! This job does not belong to your company."
            )

        if job["status"] == "closed":
            raise HTTPException(
                status_code = 400,
                detail = "This job is already closed!"
            )

        cur.execute(
            "UPDATE Job_Posts SET status = 'closed' WHERE job_id = %s",
            (job_id,)
        )
        conn.commit()
        return {"message": f"Job {job_id} has been closed successfully!"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code = 500, detail = str(e))
    finally:
        cur.close()
        conn.close()


@router.patch("/{job_id}/reopen")
def reopen_job(
    job_id: int,
    current_user: dict = Depends(get_current_recruiter)
):
    """
    Allows a recruiter to reopen one of their own closed job postings.
    Once reopened, students can apply to it again.
    Only the recruiter whose company owns the job can reopen it.
    """
    conn = get_db()
    cur = get_cursor(conn)
    try:
        recruiter_id = current_user["account_id"]

        cur.execute(
            "SELECT company_id FROM Recruiters WHERE recruiter_id = %s",
            (recruiter_id,)
        )
        recruiter = cur.fetchone()

        if not recruiter:
            raise HTTPException(
                status_code = 404,
                detail = "Recruiter profile not found!"
            )

        cur.execute(
            "SELECT company_id, status FROM Job_Posts WHERE job_id = %s",
            (job_id,)
        )
        job = cur.fetchone()

        if not job:
            raise HTTPException(
                status_code = 404,
                detail = "Job not found!"
            )

        if job["company_id"] != recruiter["company_id"]:
            raise HTTPException(
                status_code = 403,
                detail = "Access denied! This job does not belong to your company."
            )

        if job["status"] == "active":
            raise HTTPException(
                status_code = 400,
                detail = "This job is already active!"
            )

        cur.execute(
            "UPDATE Job_Posts SET status = 'active' WHERE job_id = %s",
            (job_id,)
        )
        conn.commit()
        return {"message": f"Job {job_id} has been reopened successfully!"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code = 500, detail = str(e))
    finally:
        cur.close()
        conn.close()


@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    current_user: dict = Depends(get_current_recruiter)
):
    """
    Deletes a job posting if no applications exist for it.
    If applications exist, closes the job instead to protect application history.
    Only the recruiter whose company owns the job can delete it.
    """
    conn = get_db()
    cur = get_cursor(conn)
    try:
        recruiter_id = current_user["account_id"]

        cur.execute(
            "SELECT company_id FROM Recruiters WHERE recruiter_id = %s",
            (recruiter_id,)
        )
        recruiter = cur.fetchone()

        if not recruiter:
            raise HTTPException(
                status_code = 404,
                detail = "Recruiter profile not found!"
            )

        cur.execute(
            "SELECT company_id, status FROM Job_Posts WHERE job_id = %s",
            (job_id,)
        )
        job = cur.fetchone()

        if not job:
            raise HTTPException(
                status_code = 404,
                detail = "Job not found!"
            )

        if job["company_id"] != recruiter["company_id"]:
            raise HTTPException(
                status_code = 403,
                detail = "Access denied! This job does not belong to your company."
            )

        cur.execute(
            "SELECT COUNT(*) AS app_count FROM Applications WHERE job_id = %s",
            (job_id,)
        )
        app_count = cur.fetchone()["app_count"]

        if app_count > 0:
            cur.execute(
                "UPDATE Job_Posts SET status = 'closed' WHERE job_id = %s",
                (job_id,)
            )
            conn.commit()
            return {
                "action":  "closed",
                "message": f"This job has {app_count} existing application(s) so it has been closed instead of deleted to protect applicant history."
            }

        cur.execute(
            "DELETE FROM Job_Required_Skills WHERE job_id = %s",
            (job_id,)
        )
        cur.execute(
            "DELETE FROM Job_Posts WHERE job_id = %s",
            (job_id,)
        )
        conn.commit()
        return {
            "action":  "deleted",
            "message": f"Job {job_id} has been permanently deleted."
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code = 500, detail = str(e))
    finally:
        cur.close()
        conn.close()


@router.get("/{job_id}/audit-log")
def get_job_audit_log(
    job_id: int,
    current_user: dict = Depends(get_current_recruiter)
):
    """
    Returns all AuditLog entries for applications belonging to this job.
    Shows who changed which status and when.
    Powered by the AuditLog trigger that fires on every status change.
    """
    conn = get_db()
    cur = get_cursor(conn)
    try:
        recruiter_id = current_user["account_id"]

        cur.execute(
            "SELECT company_id FROM Recruiters WHERE recruiter_id = %s",
            (recruiter_id,)
        )
        recruiter = cur.fetchone()

        if not recruiter:
            raise HTTPException(status_code = 404, detail = "Recruiter profile not found!")

        cur.execute(
            "SELECT company_id FROM Job_Posts WHERE job_id = %s",
            (job_id,)
        )
        job = cur.fetchone()

        if not job:
            raise HTTPException(status_code = 404, detail = "Job not found!")

        if job["company_id"] != recruiter["company_id"]:
            raise HTTPException(status_code = 403, detail = "Access denied!")

        cur.execute(
            """
            SELECT
                al.log_id,
                al.action,
                al.entity_id AS application_id,
                al.timestamp,
                a.name AS performed_by_name
            FROM AuditLog al
            LEFT JOIN Accounts a ON al.performed_by = a.account_id
            WHERE al.entity = 'Applications'
              AND al.entity_id IN (
                SELECT application_id FROM Applications WHERE job_id = %s
              )
            ORDER BY al.timestamp DESC
            """,
            (job_id,)
        )
        logs = cur.fetchall()
        return [dict(l) for l in logs]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))
    finally:
        cur.close()
        conn.close()


@router.get("/{job_id}")
def get_job_detail(job_id: int):
    """
    Returns full details of one job including all required and preferred skills.
    No login required.
    """
    conn = get_db()
    cur = get_cursor(conn)
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
            raise HTTPException(status_code = 404, detail = "Job not found!")

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
        raise HTTPException(status_code = 500, detail = str(e))
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
    The BEFORE INSERT trigger fires automatically and rejects the insert
    if the deadline is in the past.
    """
    conn = get_db()
    cur = get_cursor(conn)
    try:
        recruiter_id = current_user["account_id"]

        cur.execute(
            "SELECT company_id FROM Recruiters WHERE recruiter_id = %s",
            (recruiter_id,)
        )
        recruiter = cur.fetchone()

        if not recruiter:
            raise HTTPException(
                status_code = 404,
                detail = "Recruiter profile not found!"
            )

        company_id = recruiter["company_id"]

        cur.execute(
            """
            SELECT job_id FROM Job_Posts
            WHERE company_id = %s AND title = %s AND status = 'active'
            """,
            (company_id, data.title)
        )
        if cur.fetchone():
            raise HTTPException(
                status_code = 400,
                detail = "An active job posting with this title already exists for your company!"
            )

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
            "message": "Job posted successfully!",
            "job_id":  job_id
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code = 500, detail = str(e))
    finally:
        cur.close()
        conn.close()