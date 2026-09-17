from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.models import JobProfile, Profile
from app.schemas.profile import JobProfileCreate, JobProfileOut, ProfileOut, ProfileUpdate

router = APIRouter(tags=["profile"])

DEV_USER_ID = "00000000-0000-0000-0000-000000000000"


@router.get("/profile", response_model=ProfileOut)
async def get_profile(db: DbSession) -> ProfileOut:
    result = await db.execute(select(Profile).limit(1))
    profile = result.scalars().first()
    if profile is None:
        profile = Profile(user_id=DEV_USER_ID, name="Candidate")
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return ProfileOut(
        user_id=profile.user_id,
        name=profile.name,
        resume_summary=profile.resume_summary,
        skills=profile.skills or [],
        projects=[],
        experience_years=profile.experience_years,
        target_role=profile.target_role,
        education=profile.education or [],
        certifications=profile.certifications or [],
    )


@router.put("/profile", response_model=ProfileOut)
async def update_profile(body: ProfileUpdate, db: DbSession) -> ProfileOut:
    result = await db.execute(select(Profile).limit(1))
    profile = result.scalars().first()
    if profile is None:
        profile = Profile(user_id=DEV_USER_ID, name=body.name or "Candidate")
        db.add(profile)

    if body.name is not None:
        profile.name = body.name
    if body.resume_summary is not None:
        profile.resume_summary = body.resume_summary
    if body.skills is not None:
        profile.skills = body.skills
    if body.experience_years is not None:
        profile.experience_years = body.experience_years
    if body.target_role is not None:
        profile.target_role = body.target_role
    if body.education is not None:
        profile.education = body.education
    if body.certifications is not None:
        profile.certifications = body.certifications

    await db.commit()
    await db.refresh(profile)
    return await get_profile(db)


@router.get("/job-profile", response_model=JobProfileOut | None)
async def get_job_profile(db: DbSession) -> JobProfileOut | None:
    result = await db.execute(select(JobProfile).limit(1))
    jp = result.scalars().first()
    if jp is None:
        return None
    return JobProfileOut(
        id=jp.id,
        user_id=jp.user_id,
        company=jp.company,
        role=jp.role,
        requirements=jp.requirements or [],
        technologies=jp.technologies or [],
        description=jp.description,
        notes=jp.notes,
    )


@router.post("/job-profile", response_model=JobProfileOut)
async def upsert_job_profile(body: JobProfileCreate, db: DbSession) -> JobProfileOut:
    result = await db.execute(select(JobProfile).limit(1))
    jp = result.scalars().first()
    if jp is None:
        jp = JobProfile(user_id=DEV_USER_ID, company=body.company, role=body.role)
        db.add(jp)

    jp.company = body.company
    jp.role = body.role
    jp.requirements = body.requirements
    jp.technologies = body.technologies
    jp.description = body.description
    jp.notes = body.notes

    await db.commit()
    await db.refresh(jp)
    return JobProfileOut(
        id=jp.id,
        user_id=jp.user_id,
        company=jp.company,
        role=jp.role,
        requirements=jp.requirements,
        technologies=jp.technologies,
        description=jp.description,
        notes=jp.notes,
    )