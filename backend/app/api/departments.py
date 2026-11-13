from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, verify_org_access
from app.models.models import (
    Department,
    Team,
    Designation,
    Person,
    User,
    UserRole,
    utcnow,
)
from app.schemas.schemas import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentListResponse,
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamListResponse,
    DesignationCreate,
    DesignationUpdate,
    DesignationResponse,
    DesignationListResponse,
    MessageResponse,
)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/organizations/{org_id}", tags=["Departments, Teams & Designations"])


# ═══════════════════════════════════════════════════════════════════════════
# DEPARTMENTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/departments", response_model=DepartmentListResponse)
async def list_departments(
    org_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    query = select(Department).where(Department.organization_id == org_id)
    count_query = select(func.count(Department.id)).where(Department.organization_id == org_id)

    filters = []
    if is_active is not None:
        filters.append(Department.is_active == is_active)
    if search:
        filters.append(Department.name.ilike(f"%{search.strip()}%"))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = await db.scalar(count_query) or 0
    result = await db.execute(query.order_by(Department.name.asc()).offset(skip).limit(limit))
    departments = result.scalars().all()

    items = []
    for dept in departments:
        cnt = await db.scalar(
            select(func.count(Person.id)).where(Person.department_id == dept.id)
        ) or 0
        resp = DepartmentResponse.model_validate(dept)
        resp.member_count = cnt
        items.append(resp)

    return DepartmentListResponse(total=total, items=items)


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    org_id: UUID,
    req: DepartmentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create departments")

    # Check duplicate
    existing = await db.execute(
        select(Department).where(Department.organization_id == org_id, Department.name == req.name.strip())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department with this name already exists")

    dept = Department(
        organization_id=org_id,
        name=req.name.strip(),
        description=req.description,
        head_person_id=req.head_person_id,
        is_active=req.is_active if req.is_active is not None else True,
    )
    db.add(dept)
    await db.flush()

    await log_audit_event(
        db=db,
        action="create_department",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Department",
        resource_id=str(dept.id),
        details={"name": dept.name},
    )

    resp = DepartmentResponse.model_validate(dept)
    resp.member_count = 0
    return resp


@router.get("/departments/{dept_id}", response_model=DepartmentResponse)
async def get_department(
    org_id: UUID,
    dept_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    result = await db.execute(
        select(Department).where(Department.id == dept_id, Department.organization_id == org_id)
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    cnt = await db.scalar(select(func.count(Person.id)).where(Person.department_id == dept.id)) or 0
    resp = DepartmentResponse.model_validate(dept)
    resp.member_count = cnt
    return resp


@router.put("/departments/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    org_id: UUID,
    dept_id: UUID,
    req: DepartmentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can update departments")

    result = await db.execute(
        select(Department).where(Department.id == dept_id, Department.organization_id == org_id)
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    if req.name and req.name.strip() != dept.name:
        dup = await db.execute(
            select(Department).where(Department.organization_id == org_id, Department.name == req.name.strip())
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department name already in use")
        dept.name = req.name.strip()

    if req.description is not None:
        dept.description = req.description
    if req.head_person_id is not None:
        dept.head_person_id = req.head_person_id
    if req.is_active is not None:
        dept.is_active = req.is_active

    dept.updated_at = utcnow()
    await db.flush()

    cnt = await db.scalar(select(func.count(Person.id)).where(Person.department_id == dept.id)) or 0
    resp = DepartmentResponse.model_validate(dept)
    resp.member_count = cnt
    return resp


@router.delete("/departments/{dept_id}", response_model=MessageResponse)
async def delete_department(
    org_id: UUID,
    dept_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete departments")

    result = await db.execute(
        select(Department).where(Department.id == dept_id, Department.organization_id == org_id)
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    name = dept.name
    await db.delete(dept)
    await db.flush()

    await log_audit_event(
        db=db,
        action="delete_department",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Department",
        resource_id=str(dept_id),
        details={"name": name},
    )

    return MessageResponse(message=f"Department '{name}' deleted successfully")


# ═══════════════════════════════════════════════════════════════════════════
# TEAMS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/teams", response_model=TeamListResponse)
async def list_teams(
    org_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    department_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    query = select(Team).where(Team.organization_id == org_id)
    count_query = select(func.count(Team.id)).where(Team.organization_id == org_id)

    filters = []
    if department_id is not None:
        filters.append(Team.department_id == department_id)
    if is_active is not None:
        filters.append(Team.is_active == is_active)
    if search:
        filters.append(Team.name.ilike(f"%{search.strip()}%"))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = await db.scalar(count_query) or 0
    result = await db.execute(query.order_by(Team.name.asc()).offset(skip).limit(limit))
    teams = result.scalars().all()

    items = []
    for t in teams:
        cnt = await db.scalar(select(func.count(Person.id)).where(Person.team_id == t.id)) or 0
        resp = TeamResponse.model_validate(t)
        resp.member_count = cnt
        items.append(resp)

    return TeamListResponse(total=total, items=items)


@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    org_id: UUID,
    req: TeamCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    existing = await db.execute(
        select(Team).where(Team.organization_id == org_id, Team.name == req.name.strip())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team with this name already exists")

    team = Team(
        organization_id=org_id,
        name=req.name.strip(),
        department_id=req.department_id,
        description=req.description,
        is_active=req.is_active if req.is_active is not None else True,
    )
    db.add(team)
    await db.flush()

    await log_audit_event(
        db=db,
        action="create_team",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Team",
        resource_id=str(team.id),
        details={"name": team.name},
    )

    resp = TeamResponse.model_validate(team)
    resp.member_count = 0
    return resp


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    org_id: UUID,
    team_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    result = await db.execute(select(Team).where(Team.id == team_id, Team.organization_id == org_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    cnt = await db.scalar(select(func.count(Person.id)).where(Person.team_id == team.id)) or 0
    resp = TeamResponse.model_validate(team)
    resp.member_count = cnt
    return resp


@router.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    org_id: UUID,
    team_id: UUID,
    req: TeamUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    result = await db.execute(select(Team).where(Team.id == team_id, Team.organization_id == org_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    if req.name and req.name.strip() != team.name:
        dup = await db.execute(
            select(Team).where(Team.organization_id == org_id, Team.name == req.name.strip())
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team name already in use")
        team.name = req.name.strip()

    if req.department_id is not None:
        team.department_id = req.department_id
    if req.description is not None:
        team.description = req.description
    if req.is_active is not None:
        team.is_active = req.is_active

    team.updated_at = utcnow()
    await db.flush()

    cnt = await db.scalar(select(func.count(Person.id)).where(Person.team_id == team.id)) or 0
    resp = TeamResponse.model_validate(team)
    resp.member_count = cnt
    return resp


@router.delete("/teams/{team_id}", response_model=MessageResponse)
async def delete_team(
    org_id: UUID,
    team_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete teams")

    result = await db.execute(select(Team).where(Team.id == team_id, Team.organization_id == org_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    name = team.name
    await db.delete(team)
    await db.flush()

    await log_audit_event(
        db=db,
        action="delete_team",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Team",
        resource_id=str(team_id),
        details={"name": name},
    )

    return MessageResponse(message=f"Team '{name}' deleted successfully")


# ═══════════════════════════════════════════════════════════════════════════
# DESIGNATIONS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/designations", response_model=DesignationListResponse)
async def list_designations(
    org_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    query = select(Designation).where(Designation.organization_id == org_id)
    count_query = select(func.count(Designation.id)).where(Designation.organization_id == org_id)

    if search:
        query = query.where(Designation.name.ilike(f"%{search.strip()}%"))
        count_query = count_query.where(Designation.name.ilike(f"%{search.strip()}%"))

    total = await db.scalar(count_query) or 0
    result = await db.execute(query.order_by(Designation.level.desc(), Designation.name.asc()).offset(skip).limit(limit))
    items = result.scalars().all()

    return DesignationListResponse(
        total=total,
        items=[DesignationResponse.model_validate(d) for d in items],
    )


@router.post("/designations", response_model=DesignationResponse, status_code=status.HTTP_201_CREATED)
async def create_designation(
    org_id: UUID,
    req: DesignationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create designations")

    existing = await db.execute(
        select(Designation).where(Designation.organization_id == org_id, Designation.name == req.name.strip())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Designation already exists")

    desig = Designation(
        organization_id=org_id,
        name=req.name.strip(),
        level=req.level or 0,
    )
    db.add(desig)
    await db.flush()

    await log_audit_event(
        db=db,
        action="create_designation",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Designation",
        resource_id=str(desig.id),
        details={"name": desig.name, "level": desig.level},
    )

    return DesignationResponse.model_validate(desig)


@router.get("/designations/{desig_id}", response_model=DesignationResponse)
async def get_designation(
    org_id: UUID,
    desig_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    result = await db.execute(
        select(Designation).where(Designation.id == desig_id, Designation.organization_id == org_id)
    )
    desig = result.scalar_one_or_none()
    if not desig:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Designation not found")

    return DesignationResponse.model_validate(desig)


@router.put("/designations/{desig_id}", response_model=DesignationResponse)
async def update_designation(
    org_id: UUID,
    desig_id: UUID,
    req: DesignationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can update designations")

    result = await db.execute(
        select(Designation).where(Designation.id == desig_id, Designation.organization_id == org_id)
    )
    desig = result.scalar_one_or_none()
    if not desig:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Designation not found")

    if req.name and req.name.strip() != desig.name:
        dup = await db.execute(
            select(Designation).where(Designation.organization_id == org_id, Designation.name == req.name.strip())
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Designation name already in use")
        desig.name = req.name.strip()

    if req.level is not None:
        desig.level = req.level

    await db.flush()
    return DesignationResponse.model_validate(desig)


@router.delete("/designations/{desig_id}", response_model=MessageResponse)
async def delete_designation(
    org_id: UUID,
    desig_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete designations")

    result = await db.execute(
        select(Designation).where(Designation.id == desig_id, Designation.organization_id == org_id)
    )
    desig = result.scalar_one_or_none()
    if not desig:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Designation not found")

    name = desig.name
    await db.delete(desig)
    await db.flush()

    await log_audit_event(
        db=db,
        action="delete_designation",
        organization_id=org_id,
        user_id=current_user.id,
        resource_type="Designation",
        resource_id=str(desig_id),
        details={"name": name},
    )

    return MessageResponse(message=f"Designation '{name}' deleted successfully")
