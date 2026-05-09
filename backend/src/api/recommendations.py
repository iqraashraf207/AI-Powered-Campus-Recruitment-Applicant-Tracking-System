from fastapi import APIRouter, HTTPException, Depends
from database.session import get_db, get_cursor
from dependencies.auth import get_current_student
from utils.db_helpers import call_generate_recommendations

router = APIRouter()


@router.get("/")
def get_recommendations(current_user: dict = Depends(get_current_student)):
    """
    Agent 3: Goal-Based + Utility-Based Recommendation Agent.

    Goal: Maximize the student's probability of finding a
    relevant job by surfacing the best matches from all
    active postings.

    Flow:
    1. Checks student has skills on their profile
    2. Checks student has submitted a resume
    3. Calls Generate_Job_Recommendations stored procedure
    4. Returns top 5 jobs ranked by fit score
    """
    student_id = current_user["account_id"]
    conn       = get_db()
    cur        = get_cursor(conn)

    try:
        cur.execute(
            "SELECT COUNT(*) AS skill_count FROM Student_Skills WHERE student_id = %s",
            (student_id,)
        )
        skill_count = cur.fetchone()["skill_count"]

        if skill_count == 0:
            return {
                "message": (
                    "No skills found on your profile. "
                    "Please submit your resume first so we can extract your skills."
                ),
                "recommendations": []
            }

        cur.execute(
            "SELECT experience_years FROM Resumes WHERE student_id = %s",
            (student_id,)
        )
        resume = cur.fetchone()

        if not resume:
            return {
                "message": (
                    "Please submit your resume first "
                    "to get accurate job recommendations."
                ),
                "recommendations": []
            }

        recommendations = call_generate_recommendations(student_id)

        if not recommendations:
            return {
                "message": (
                    "No eligible jobs found. "
                    "You may not meet the minimum CGPA for any active job right now."
                ),
                "recommendations": []
            }

        return {
            "message":         f"{len(recommendations)} job recommendations found.",
            "recommendations": recommendations
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()