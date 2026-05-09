from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import api.auth as auth
import api.jobs as jobs
import api.applications as applications
import api.students as students
import api.recommendations as recommendations

app = FastAPI(
    title="Campus Recruitment & Applicant Tracking System",
    description="AI-Powered Campus Recruitment Portal API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,            prefix="/auth",            tags=["Authentication"])
app.include_router(jobs.router,            prefix="/jobs",            tags=["Jobs"])
app.include_router(applications.router,    prefix="/applications",    tags=["Applications"])
app.include_router(students.router,        prefix="/students",        tags=["Students"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])


@app.get("/")
def root():
    return {"message": "Campus Recruitment API is running."}