from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi import Form
from pydantic import BaseModel
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.utils.helpers import serialize_doc, now
from app.services.job_ranking        import job_ranking_service
from app.services.bulk_cv_parser     import bulk_cv_parser_service
from app.services.hr_analytics       import hr_analytics_service
from app.services.interview_scheduler import interview_scheduler_service
from app.ml.skill_extractor          import skill_extractor

router = APIRouter()


def _require_hr(current_user):
    if current_user["role"] not in ("hr", "admin"):
        raise HTTPException(status_code=403, detail="HR access only")


# ═══════════════════════════════════════════════════════════════
# Feature 9 — Job Post Management
# ═══════════════════════════════════════════════════════════════

class JobPostCreate(BaseModel):
    title:               str
    description:         str
    required_skills:     Optional[List[str]] = []
    experience_required: Optional[float] = None
    location:            Optional[str] = None
    salary_min:          Optional[float] = None
    salary_max:          Optional[float] = None
    is_template:         Optional[bool] = False


class JobPostUpdate(BaseModel):
    title:               Optional[str] = None
    description:         Optional[str] = None
    required_skills:     Optional[List[str]] = None
    experience_required: Optional[float] = None
    location:            Optional[str] = None
    salary_min:          Optional[float] = None
    salary_max:          Optional[float] = None
    status:              Optional[str] = None
    is_template:         Optional[bool] = None


@router.post("/jobs", status_code=201)
async def create_job(
    payload: JobPostCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    # Auto-extract skills from description if not provided
    skills = payload.required_skills
    if not skills and payload.description:
        skills = skill_extractor.extract(payload.description)

    doc = {
        "hr_id":               current_user["_id"],
        "title":               payload.title,
        "description_text":    payload.description,
        "required_skills":     skills,
        "experience_required": payload.experience_required,
        "location":            payload.location,
        "salary_range": {
            "min": payload.salary_min,
            "max": payload.salary_max,
            "currency": "USD",
        },
        "status":      "open",
        "is_template": payload.is_template,
        "created_at":  now(),
        "updated_at":  now(),
    }

    result = await db["job_posts"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return serialize_doc(doc)


@router.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    is_template: Optional[bool] = None,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    _require_hr(current_user)

    query = {"hr_id": current_user["_id"]}
    if status:
        query["status"] = status
    if is_template is not None:
        query["is_template"] = is_template

    cursor = db["job_posts"].find(query).sort("created_at", -1).skip(skip).limit(limit)
    jobs = await cursor.to_list(length=limit)
    total = await db["job_posts"].count_documents(query)

    return {
        "jobs": [serialize_doc(j) for j in jobs],
        "total": total,
    }


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    job = await db["job_posts"].find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return serialize_doc(job)


@router.put("/jobs/{job_id}")
async def update_job(
    job_id: str,
    payload: JobPostUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    updates = {k: v for k, v in payload.dict().items() if v is not None}
    updates["updated_at"] = now()

    await db["job_posts"].update_one(
        {"_id": ObjectId(job_id), "hr_id": current_user["_id"]},
        {"$set": updates},
    )
    updated = await db["job_posts"].find_one({"_id": ObjectId(job_id)})
    return serialize_doc(updated)


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    await db["job_posts"].delete_one(
        {"_id": ObjectId(job_id), "hr_id": current_user["_id"]}
    )
    return {"message": "Job post deleted"}


@router.post("/jobs/{job_id}/duplicate")
async def duplicate_job(
    job_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Duplicate a job post or template."""
    _require_hr(current_user)
    job = await db["job_posts"].find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.pop("_id")
    job["title"]      = f"Copy of {job['title']}"
    job["status"]     = "draft"
    job["created_at"] = now()
    job["updated_at"] = now()

    result = await db["job_posts"].insert_one(job)
    job["_id"] = result.inserted_id
    return serialize_doc(job)


# ═══════════════════════════════════════════════════════════════
# Feature 8 — Bulk CV Upload & Parsing
# ═══════════════════════════════════════════════════════════════

@router.post("/bulk-cv-upload/{job_id}")
async def bulk_cv_upload(
    job_id: str,
    files: List[UploadFile] = File(...),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    # Verify job exists
    job = await db["job_posts"].find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job post not found")

    result = await bulk_cv_parser_service.parse_multiple(
        db, current_user["_id"], job_id, files
    )
    return result


@router.post("/bulk-cv-upload-zip/{job_id}")
async def bulk_cv_upload_zip(
    job_id: str,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Please upload a .zip file")

    result = await bulk_cv_parser_service.parse_zip(
        db, current_user["_id"], job_id, file
    )
    return result


# ═══════════════════════════════════════════════════════════════
# Feature 7 — Job Ranking
# ═══════════════════════════════════════════════════════════════

class RankFromTextRequest(BaseModel):
    jd_text:  str
    top_n:    Optional[int] = 20
    job_id:   Optional[str] = None


@router.post("/job-ranking/{job_id}")
async def rank_job_cvs(
    job_id: str,
    top_n: int = 20,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Rank all CVs already uploaded for a job."""
    _require_hr(current_user)
    result = await job_ranking_service.rank_from_db(
        db, current_user["_id"], job_id, top_n=top_n
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/job-ranking-text")
async def rank_from_text(
    payload: RankFromTextRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Rank resumes directly from text (no prior upload needed)."""
    _require_hr(current_user)

    # Load resumes from DB for this job
    if payload.job_id:
        cursor = db["ranking_queue"].find({"job_id": payload.job_id})
        queue = await cursor.to_list(length=500)
        resumes = []
        for q in queue:
            r = await db["resumes"].find_one({"_id": q["resume_id"]})
            if r and r.get("extracted_text"):
                resumes.append({
                    "id":       str(r["_id"]),
                    "text":     r["extracted_text"],
                    "filename": r.get("original_filename", ""),
                    "candidate_name": q.get("candidate_name", ""),
                })
    else:
        resumes = []

    if not resumes:
        raise HTTPException(status_code=400, detail="No resumes found. Upload CVs first.")

    result = await job_ranking_service.rank_from_texts(
        db,
        current_user["_id"],
        payload.jd_text,
        resumes,
        job_id=payload.job_id,
        top_n=payload.top_n,
    )
    return result


@router.get("/rankings/{job_id}")
async def get_rankings(
    job_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Get most recent ranking for a job."""
    _require_hr(current_user)
    ranking = await db["rankings"].find_one(
        {"job_id": ObjectId(job_id), "hr_id": current_user["_id"]},
        sort=[("created_at", -1)],
    )
    if not ranking:
        raise HTTPException(status_code=404, detail="No ranking found for this job")
    return serialize_doc(ranking)


# ═══════════════════════════════════════════════════════════════
# Feature 10 — Candidate Shortlisting
# ═══════════════════════════════════════════════════════════════

class ShortlistAction(BaseModel):
    candidate_id: str
    action:       str    # shortlisted | rejected | archived
    rating:       Optional[int] = None     # 1–5
    comment:      Optional[str] = None


class ExportShortlist(BaseModel):
    format: str = "json"   # json | csv


@router.post("/shortlist/{job_id}")
async def shortlist_candidate(
    job_id: str,
    payload: ShortlistAction,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    valid_actions = ["shortlisted", "rejected", "archived"]
    if payload.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Action must be one of: {valid_actions}")

    entry = {
        "candidate_id": ObjectId(payload.candidate_id),
        "status":       payload.action,
        "rating":       payload.rating,
        "comments":     [payload.comment] if payload.comment else [],
        "reviewer_id":  current_user["_id"],
        "actioned_at":  now(),
    }

    await db["shortlists"].update_one(
        {"job_id": ObjectId(job_id), "hr_id": current_user["_id"]},
        {
            "$set":  {"job_id": ObjectId(job_id), "hr_id": current_user["_id"], "updated_at": now()},
            "$pull": {"shortlisted_candidates": {"candidate_id": ObjectId(payload.candidate_id)}},
        },
        upsert=True,
    )
    await db["shortlists"].update_one(
        {"job_id": ObjectId(job_id), "hr_id": current_user["_id"]},
        {"$push": {"shortlisted_candidates": entry}},
    )

    return {"message": f"Candidate {payload.action}", "entry": serialize_doc(entry)}


@router.get("/shortlist/{job_id}")
async def get_shortlist(
    job_id: str,
    status: Optional[str] = None,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    shortlist = await db["shortlists"].find_one({
        "job_id": ObjectId(job_id),
        "hr_id":  current_user["_id"],
    })
    if not shortlist:
        return {"candidates": [], "total": 0}

    candidates = shortlist.get("shortlisted_candidates", [])
    if status:
        candidates = [c for c in candidates if c.get("status") == status]

    return {
        "job_id":     job_id,
        "candidates": [serialize_doc(c) for c in candidates],
        "total":      len(candidates),
        "breakdown": {
            "shortlisted": sum(1 for c in candidates if c.get("status") == "shortlisted"),
            "rejected":    sum(1 for c in candidates if c.get("status") == "rejected"),
            "archived":    sum(1 for c in candidates if c.get("status") == "archived"),
        },
    }


@router.get("/shortlist/{job_id}/export")
async def export_shortlist(
    job_id: str,
    format: str = "json",
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    shortlist = await db["shortlists"].find_one({
        "job_id": ObjectId(job_id),
        "hr_id":  current_user["_id"],
    })
    if not shortlist:
        raise HTTPException(status_code=404, detail="No shortlist found")

    candidates = shortlist.get("shortlisted_candidates", [])
    shortlisted = [c for c in candidates if c.get("status") == "shortlisted"]

    if format == "csv":
        import csv, io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["candidate_id", "status", "rating", "actioned_at"])
        writer.writeheader()
        for c in shortlisted:
            writer.writerow({
                "candidate_id": str(c.get("candidate_id", "")),
                "status":       c.get("status", ""),
                "rating":       c.get("rating", ""),
                "actioned_at":  str(c.get("actioned_at", "")),
            })
        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=shortlist_{job_id}.csv"},
        )

    return {
        "job_id": job_id,
        "shortlisted_candidates": [serialize_doc(c) for c in shortlisted],
        "total": len(shortlisted),
        "exported_at": now().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════
# Feature 11 — Skill Gap Analysis
# ═══════════════════════════════════════════════════════════════

class SkillGapRequest(BaseModel):
    resume_id: str
    job_id:    Optional[str] = None
    jd_text:   Optional[str] = None


@router.post("/skill-gap")
async def skill_gap_analysis(
    payload: SkillGapRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    resume = await db["resumes"].find_one({"_id": ObjectId(payload.resume_id)})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_text = resume.get("extracted_text", "")
    jd_text = payload.jd_text

    if not jd_text and payload.job_id:
        job = await db["job_posts"].find_one({"_id": ObjectId(payload.job_id)})
        if job:
            jd_text = job.get("description_text", "")
            required_skills = job.get("required_skills", [])
        else:
            required_skills = []
    else:
        required_skills = skill_extractor.extract(jd_text) if jd_text else []

    if not jd_text:
        raise HTTPException(status_code=400, detail="Provide job_id or jd_text")

    resume_skills  = set(skill_extractor.extract(resume_text))
    required_set   = set(required_skills)

    matched  = list(resume_skills & required_set)
    missing  = list(required_set - resume_skills)
    extra    = list(resume_skills - required_set)

    match_pct = round(len(matched) / max(len(required_set), 1) * 100, 1)

    # Prioritize missing skills by position in JD (earlier = more important)
    def priority(skill):
        try:
            return jd_text.lower().index(skill.lower())
        except ValueError:
            return 9999

    missing_prioritized = sorted(missing, key=priority)

    return {
        "candidate_name":    resume.get("candidate_name", "Unknown"),
        "resume_id":         str(resume["_id"]),
        "match_percentage":  match_pct,
        "matched_skills":    matched,
        "missing_skills":    missing_prioritized,
        "additional_skills": extra[:10],
        "total_required":    len(required_set),
        "total_matched":     len(matched),
        "total_missing":     len(missing),
        "gap_severity": (
            "Low"    if len(missing) <= 2 else
            "Medium" if len(missing) <= 5 else
            "High"
        ),
        "recommendation": (
            f"Strong candidate — only {len(missing)} skills missing."
            if len(missing) <= 2 else
            f"Moderate gap — missing {len(missing)} skills: {', '.join(missing_prioritized[:3])}."
            if len(missing) <= 5 else
            f"Significant gap — {len(missing)} required skills absent. Consider other candidates."
        ),
    }


# ═══════════════════════════════════════════════════════════════
# Feature 12 — Interview Scheduler
# ═══════════════════════════════════════════════════════════════

class ScheduleInterviewRequest(BaseModel):
    candidate_id:     str
    job_id:           Optional[str] = None
    scheduled_date:   datetime
    duration_minutes: Optional[int] = 60
    meeting_link:     Optional[str] = None
    notes:            Optional[str] = None


class UpdateInterviewRequest(BaseModel):
    status:   str
    feedback: Optional[str] = None


@router.post("/interviews")
async def schedule_interview(
    payload: ScheduleInterviewRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    result = await interview_scheduler_service.schedule(
        db, current_user["_id"], payload.dict()
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/interviews")
async def list_interviews(
    job_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    return await interview_scheduler_service.list_interviews(
        db, current_user["_id"], job_id, status
    )


@router.get("/interviews/upcoming")
async def upcoming_interviews(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    return await interview_scheduler_service.get_upcoming(db, current_user["_id"])


@router.put("/interviews/{interview_id}")
async def update_interview(
    interview_id: str,
    payload: UpdateInterviewRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    return await interview_scheduler_service.update_status(
        db, current_user["_id"], interview_id, payload.status, payload.feedback
    )


# ═══════════════════════════════════════════════════════════════
# Feature 13 — HR Analytics Dashboard
# ═══════════════════════════════════════════════════════════════

@router.get("/analytics")
async def hr_analytics(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    return await hr_analytics_service.get_dashboard(db, current_user["_id"])


# ═══════════════════════════════════════════════════════════════
# Feature 14 — Collaborative Hiring
# ═══════════════════════════════════════════════════════════════

class AddTeamMember(BaseModel):
    member_email: str
    role:         str = "reviewer"    # reviewer | admin


class AddComment(BaseModel):
    candidate_id: str
    comment:      str
    rating:       Optional[int] = None   # 1–5


class CastVote(BaseModel):
    candidate_id: str
    vote:         str   # hire | reject | maybe


@router.post("/team-members")
async def add_team_member(
    payload: AddTeamMember,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    member = await db["users"].find_one({"email": payload.member_email})
    if not member:
        raise HTTPException(status_code=404, detail="User not found with that email")

    await db["hr_profiles"].update_one(
        {"user_id": current_user["_id"]},
        {"$addToSet": {
            "team_members": {
                "member_user_id": member["_id"],
                "email":          payload.member_email,
                "role":           payload.role,
                "added_at":       now(),
            }
        }},
        upsert=True,
    )

    # Notify new team member
    await db["notifications"].insert_one({
        "user_id":     member["_id"],
        "title":       "Added to Hiring Team",
        "message":     f"You have been added to {current_user.get('name', 'an HR team')} as a {payload.role}.",
        "type":        "info",
        "read":        False,
        "action_link": None,
        "created_at":  now(),
    })

    return {"message": f"{payload.member_email} added as {payload.role}"}


@router.get("/team-members")
async def get_team_members(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    profile = await db["hr_profiles"].find_one({"user_id": current_user["_id"]})
    if not profile:
        return {"team_members": []}
    return {"team_members": serialize_doc(profile).get("team_members", [])}


@router.post("/comment/{job_id}")
async def add_comment(
    job_id: str,
    payload: AddComment,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    comment_doc = {
        "reviewer_id":   current_user["_id"],
        "reviewer_name": current_user.get("name", "HR"),
        "comment":       payload.comment,
        "rating":        payload.rating,
        "commented_at":  now(),
    }

    await db["candidate_reviews"].update_one(
        {
            "job_id":       ObjectId(job_id),
            "candidate_id": ObjectId(payload.candidate_id),
        },
        {
            "$set":  {
                "job_id":       ObjectId(job_id),
                "candidate_id": ObjectId(payload.candidate_id),
            },
            "$push": {"comments": comment_doc},
        },
        upsert=True,
    )

    return {"message": "Comment added", "comment": serialize_doc(comment_doc)}


@router.get("/comments/{job_id}/{candidate_id}")
async def get_comments(
    job_id: str,
    candidate_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    review = await db["candidate_reviews"].find_one({
        "job_id":       ObjectId(job_id),
        "candidate_id": ObjectId(candidate_id),
    })
    if not review:
        return {"comments": [], "votes": {}}

    return serialize_doc(review)


@router.post("/vote/{job_id}")
async def cast_vote(
    job_id: str,
    payload: CastVote,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    valid_votes = ["hire", "reject", "maybe"]
    if payload.vote not in valid_votes:
        raise HTTPException(status_code=400, detail=f"Vote must be: {valid_votes}")

    vote_key = f"votes.{str(current_user['_id'])}"

    await db["candidate_reviews"].update_one(
        {
            "job_id":       ObjectId(job_id),
            "candidate_id": ObjectId(payload.candidate_id),
        },
        {
            "$set": {
                "job_id":       ObjectId(job_id),
                "candidate_id": ObjectId(payload.candidate_id),
                vote_key:       payload.vote,
            }
        },
        upsert=True,
    )

    # Tally votes
    review = await db["candidate_reviews"].find_one({
        "job_id":       ObjectId(job_id),
        "candidate_id": ObjectId(payload.candidate_id),
    })
    votes = review.get("votes", {}) if review else {}
    tally = {"hire": 0, "reject": 0, "maybe": 0}
    for v in votes.values():
        if v in tally:
            tally[v] += 1

    return {"message": "Vote recorded", "tally": tally}