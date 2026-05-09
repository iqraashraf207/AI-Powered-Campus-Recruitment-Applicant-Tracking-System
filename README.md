# AI-Powered Campus Recruitment & Applicant Tracking System

A full-stack web application that connects students with recruiters through an intelligent, skills-based matching engine. Students can build profiles, upload resumes, and receive personalized job recommendations. Recruiters can post jobs, browse ranked applicants, and manage the full hiring pipeline — powered by AI scoring and database-driven automation.

---

## Live Deployment

| Layer | Platform | URL |
|---|---|---|
| Frontend | Netlify | campus-recruit-pk.netlify.app |
| Backend | Railway | ai-powered-campus-recruitment...up.railway.app |
| Database | Supabase | PostgreSQL (hosted) |

---

## How the AI Works

Three purpose-built agents implemented as database stored procedures and Python logic:

**Agent 1 — Resume Keyword Matching**
Scans resume text against all known skills in the database, extracts matches automatically, and parses date ranges to calculate total years of experience.

**Agent 2 — Match Score Calculation**
Fires via a database trigger when a student applies. Computes a weighted match score (0–100) by comparing the student's skills and proficiency levels against the job's required and preferred skills.

**Agent 3 — Goal-Based Recommendation**
Runs on demand when a student visits recommendations. Calls a stored procedure that filters active jobs by minimum CGPA, computes a fit score for each, and returns the top 5 ranked matches.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, Vanilla JavaScript |
| Backend | Python 3.13, FastAPI, Uvicorn |
| Database | PostgreSQL (Supabase), psycopg2 |
| Auth | JWT (python-jose), bcrypt (passlib) |
| AI / Scoring | PostgreSQL stored procedures + Python regex |
| Deployment | Railway (backend), Netlify (frontend), Supabase (DB) |

---

## Project Structure

    ai_dbs_project/
    ├── backend/
    │   └── src/
    │       ├── main.py
    │       ├── security.py
    │       ├── api/
    │       │   ├── auth.py
    │       │   ├── jobs.py
    │       │   ├── applications.py
    │       │   ├── students.py
    │       │   └── recommendations.py
    │       ├── database/
    │       │   └── session.py
    │       ├── dependencies/
    │       │   └── auth.py
    │       └── utils/
    │           └── db_helpers.py
    └── frontend/
        ├── index.html
        ├── register.html
        ├── student/
        │   ├── dashboard.html
        │   ├── jobs.html
        │   ├── job_detail.html
        │   ├── applications.html
        │   ├── profile.html
        │   └── recommendations.html
        └── recruiter/
            ├── dashboard.html
            ├── post_job.html
            ├── my_jobs.html
            └── applicants.html

---

## Local Development Setup

**Prerequisites:** Python 3.11+, PostgreSQL instance or Supabase project

    git clone <your-repo-url>
    cd ai_dbs_project/backend

    python -m venv .venv
    source .venv/bin/activate

    pip install -r requirements.txt

Create a `.env` file inside `backend/`:

    DB_HOST=your-supabase-host
    DB_PORT=5432
    DB_NAME=postgres
    DB_USER=your-db-user
    DB_PASSWORD=your-db-password
    SECRET_KEY=your-secret-key-here
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=60

Run the backend:

    cd src
    uvicorn main:app --reload

API available at `http://localhost:8000` — interactive docs at `http://localhost:8000/docs`.

Serve the frontend:

    cd frontend
    npx serve .

---

## API Reference

All endpoints use Railway backend URL. Auth via `Bearer JWT` in the `Authorization` header.

**Auth — /auth**

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /register | No | Register a student or recruiter |
| POST | /login | No | Login and receive a JWT token |

**Jobs — /jobs**

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | / | No | List all active job postings |
| GET | /{job_id} | No | Get full details of a single job |
| GET | /companies/all | No | List all companies |
| GET | /my/postings | Recruiter | Get recruiter's own jobs |
| POST | / | Recruiter | Post a new job |
| DELETE | /{job_id} | Recruiter | Delete or close a job posting |

**Applications — /applications**

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /apply | Student | Apply for a job |
| GET | /my | Student | Get all student's applications |
| GET | /ranked/{job_id} | Recruiter | Get ranked applicants for a job |
| GET | /eligible/{job_id} | Recruiter | Get eligible students for a job |
| PUT | /status | Recruiter | Update application status |
| POST | /rerank/{job_id} | Recruiter | Recalculate match scores |

**Students — /students**

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | /profile | Student | Get profile, skills, and resume |
| PUT | /profile | Student | Update CGPA, major, graduation year |
| POST | /resume | Student | Submit resume → auto-extract skills |
| PUT | /skills | Student | Update skill proficiency level |
| GET | /all-skills | No | List all skills |

**Recommendations — /recommendations**

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | / | Student | Get top 5 AI-matched job suggestions |

---

## Key Database Objects

| Object | Type | Purpose |
|---|---|---|
| `Active_Jobs_View` | View | All jobs with status = 'active' |
| `Application_Funnel_View` | View | Per-job counts: submitted / shortlisted / accepted |
| `Top_Ranked_Applicants_View` | View | Applicants sorted by match_score |
| `Eligible_Students_View` | View | Students meeting a job's minimum CGPA |
| `Apply_For_Job` | Stored Procedure | Validates and inserts application + scores it |
| `Calculate_Match_Score` | Stored Function | Weighted skill overlap score (0–100) |
| `Update_Application_Status` | Stored Procedure | Updates status with audit logging |
| `Generate_Job_Recommendations` | Stored Function | Returns top 5 ranked job matches |

---

## Environment Variables

| Variable | Description |
|---|---|
| `DB_HOST` | PostgreSQL host |
| `DB_PORT` | PostgreSQL port |
| `DB_NAME` | Database name |
| `DB_USER` | Database user |
| `DB_PASSWORD` | Database password |
| `SECRET_KEY` | Secret key for signing JWT tokens |
| `ALGORITHM` | JWT algorithm (e.g. HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes |