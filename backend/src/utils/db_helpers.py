from database.session import get_db, get_cursor

def call_apply_for_job(student_id: int, job_id: int) -> str:
    conn = get_db()
    cur = get_cursor(conn)
    try:
        cur.execute(
            "SELECT Apply_For_Job(%s, %s) AS result",
            (student_id, job_id)
        )
        row = cur.fetchone()
        conn.commit()
        if row is None:
            return "ERROR: No response from database!"
        return row["result"]
    except Exception as e:
        conn.rollback()
        return f"ERROR: {str(e)}"
    finally:
        cur.close()
        conn.close()


def call_calculate_match_score(application_id: int) -> None:
    conn = get_db()
    cur = get_cursor(conn)
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
    conn = get_db()
    cur = get_cursor(conn)
    try:
        cur.execute(
            "SELECT Update_Application_Status(%s, %s, %s) AS result",
            (application_id, new_status, performed_by)
        )
        row = cur.fetchone()
        conn.commit()
        if row is None:
            return "ERROR: No response from database!"
        return row["result"]
    except Exception as e:
        conn.rollback()
        return f"ERROR: {str(e)}"
    finally:
        cur.close()
        conn.close()


def call_generate_recommendations(student_id: int) -> list:
    conn = get_db()
    cur = get_cursor(conn)
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