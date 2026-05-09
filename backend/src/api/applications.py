from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database.session import get_db, get_cursor
from dependencies.auth import get_current_student, get_current_recruiter
from utils.db_helpers import (
    call_apply_for_job,
    call_update_application_status
)

router = APIRouter()


class ApplyInput(BaseModel):
    job_id: int


class StatusUpdateInput(BaseModel):
    application_id: int
    new_status: str


@router.post("/apply")
def apply_for_job(
    data: ApplyInput,
    current_user: dict = Depends(get_current_student)
):
    student_id = current_user["account_id"]
    result = call_apply_for_job(student_id, data.job_id)

    if result.startswith("ERROR"):
        raise HTTPException(status_code=400, detail=result)

    return {"message": result}


@router.get("/my")
def get_my_applications(current_user: dict = Depends(get_current_student)):
    conn = get_db()
    cur = get_cursor(conn)
    try:
        student_id = current_user["account_id"]

        cur.execute(
            """
            SELECT
                app.application_id,
                jp.title AS job_title,
                c.name AS company_name,
                app.match_score,
                app.rank_position,
                app.status,
                app.apply_date
            FROM Applications app
            JOIN Job_Posts jp ON app.job_id = jp.job_id
            JOIN Companies c ON jp.company_id = c.company_id
            WHERE app.student_id = %s
            ORDER BY app.apply_date DESC
            """,
            (student_id,)
        )
        applications = cur.fetchall()
        return [dict(a) for a in applications]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.get("/ranked/{job_id}")
def get_ranked_applicants(
    job_id: int,
    current_user: dict = Depends(get_current_recruiter)
):
    conn = get_db()
    cur = get_cursor(conn)
    try:
        cur.execute(
            "SELECT * FROM Top_Ranked_Applicants_View WHERE job_id = %s",
            (job_id,)
        )
        applicants = cur.fetchall()
        return [dict(a) for a in applicants]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.get("/eligible/{job_id}")
def get_eligible_students(
    job_id: int,
    current_user: dict = Depends(get_current_recruiter)
):
    conn = get_db()
    cur = get_cursor(conn)
    try:
        cur.execute(
            "SELECT * FROM Eligible_Students_View WHERE job_id = %s",
            (job_id,)
        )
        students = cur.fetchall()
        return [dict(s) for s in students]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.put("/status")
def update_status(
    data: StatusUpdateInput,
    current_user: dict = Depends(get_current_recruiter)
):
    performed_by = current_user["account_id"]
    result = call_update_application_status(
        data.application_id,
        data.new_status,
        performed_by
    )

    if result.startswith("ERROR"):
        raise HTTPException(status_code=400, detail=result)

    return {"message": result}


@router.post("/rerank/{job_id}")
def rerank_applicants(
    job_id: int,
    current_user: dict = Depends(get_current_recruiter)
):
    conn = get_db()
    cur = get_cursor(conn)
    try:
        cur.execute(
            """
            SELECT application_id FROM Applications
            WHERE job_id = %s AND status != 'rejected'
            ORDER BY application_id
            """,
            (job_id,)
        )
        applications = cur.fetchall()

        if not applications:
            return {"message": "No applications found for this job."}

        for app in applications:
            cur.execute(
                "SELECT Calculate_Match_Score(%s)",
                (app["application_id"],)
            )

        conn.commit()
        return {
            "message": f"Scores recalculated for {len(applications)} applications.",
            "job_id": job_id
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()