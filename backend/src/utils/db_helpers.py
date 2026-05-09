import psycopg2
from database.session import get_db, get_cursor


def call_apply_for_job(student_id: int, job_id: int) -> str:
    """
    Calls the Apply_For_Job stored procedure.
    Returns the result message (SUCCESS, REJECTED, or ERROR).
    """
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT Apply_For_Job(%s, %s) AS result",
            (student_id, job_id)
        )
        row = cur.fetchone()
        conn.commit()
        if row is None:
            return "ERROR: No response from database."
        return row[0]
    except Exception as e:
        conn.rollback()
        return f"ERROR: {str(e)}"
    finally:
        cur.close()
        conn.close()


def call_calculate_match_score(application_id: int) -> None:
    """
    Calls the Calculate_Match_Score stored procedure manually.
    Normally called automatically by the database trigger.
    """
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT Calculate_Match_Score(%s)",
            (application_id,)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise Exception(f"Score calculation failed: {str(e)}")
    finally:
        cur.close()
        conn.close()


def call_update_application_status(
    application_id: int,
    new_status: str,
    performed_by: int
) -> str:
    """
    Calls the Update_Application_Status stored procedure.
    Returns the result message (SUCCESS or ERROR).
    """
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT Update_Application_Status(%s, %s, %s) AS result",
            (application_id, new_status, performed_by)
        )
        row = cur.fetchone()
        conn.commit()
        if row is None:
            return "ERROR: No response from database."
        return row[0]
    except Exception as e:
        conn.rollback()
        return f"ERROR: {str(e)}"
    finally:
        cur.close()
        conn.close()


def call_generate_recommendations(student_id: int) -> list:
    """
    Calls the Generate_Job_Recommendations stored procedure.
    Returns a list of recommended jobs with fit scores.
    """
    conn = get_db()
    cur  = get_cursor(conn)
    try:
        cur.execute(
            "SELECT * FROM Generate_Job_Recommendations(%s)",
            (student_id,)
        )
        results = cur.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        raise Exception(f"Recommendations failed: {str(e)}")
    finally:
        cur.close()
        conn.close()