import io
import csv
import calendar
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, verify_org_access
from app.models.models import (
    Organization,
    AttendanceRecord,
    AttendanceStatus,
    Person,
    PersonStatus,
    Department,
    Shift,
    User,
)
from app.schemas.schemas import (
    ReportDailyResponse,
    ReportMonthlyResponse,
    ReportCustomResponse,
    AttendanceRecordResponse,
)

router = APIRouter(prefix="/api/organizations/{org_id}/reports", tags=["Reports"])


async def fetch_report_records(
    db: AsyncSession,
    org_id: UUID,
    start_date: date,
    end_date: date,
    department_id: Optional[UUID] = None,
):
    query = (
        select(AttendanceRecord, Person, Department.name.label("dept_name"))
        .join(Person, AttendanceRecord.person_id == Person.id)
        .outerjoin(Department, Person.department_id == Department.id)
        .where(
            AttendanceRecord.organization_id == org_id,
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date,
        )
    )
    if department_id:
        query = query.where(Person.department_id == department_id)

    result = await db.execute(query.order_by(AttendanceRecord.date.asc(), Person.full_name.asc()))
    return result.all()


# ═══════════════════════════════════════════════════════════════════════════
# JSON REPORTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/daily", response_model=ReportDailyResponse)
async def get_daily_report(
    org_id: UUID,
    report_date: Optional[date] = Query(None, alias="date"),
    department_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    target_date = report_date or date.today()
    rows = await fetch_report_records(db, org_id, target_date, target_date, department_id)

    total_active_people = await db.scalar(
        select(func.count(Person.id)).where(
            Person.organization_id == org_id,
            Person.status == PersonStatus.ACTIVE,
        )
    ) or 0

    items = []
    present_count = 0
    late_count = 0
    half_day_count = 0
    leave_count = 0
    total_hours_sum = 0.0

    for rec, person, dept_name in rows:
        resp = AttendanceRecordResponse.model_validate(rec)
        resp.person_name = person.full_name
        resp.person_unique_id = person.unique_id
        resp.department_name = dept_name
        items.append(resp)

        if rec.status in (AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY):
            present_count += 1
        if rec.status == AttendanceStatus.LATE or rec.is_late:
            late_count += 1
        if rec.status == AttendanceStatus.HALF_DAY:
            half_day_count += 1
        if rec.status == AttendanceStatus.LEAVE:
            leave_count += 1
        if rec.total_hours:
            total_hours_sum += rec.total_hours

    absent_count = max(0, total_active_people - present_count - leave_count)
    rate = round((present_count / total_active_people * 100), 2) if total_active_people > 0 else 0.0
    avg_hours = round((total_hours_sum / present_count), 2) if present_count > 0 else 0.0

    summary = {
        "total_people": total_active_people,
        "present": present_count,
        "absent": absent_count,
        "late": late_count,
        "half_day": half_day_count,
        "on_leave": leave_count,
        "attendance_rate": rate,
        "average_work_hours": avg_hours,
    }

    return ReportDailyResponse(date=target_date, records=items, summary=summary)


@router.get("/monthly", response_model=ReportMonthlyResponse)
async def get_monthly_report(
    org_id: UUID,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    _, last_day = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    rows = await fetch_report_records(db, org_id, start_date, end_date)

    total_people = await db.scalar(
        select(func.count(Person.id)).where(
            Person.organization_id == org_id,
            Person.status == PersonStatus.ACTIVE,
        )
    ) or 0

    total_records = len(rows)
    present_total = 0
    late_total = 0
    hours_total = 0.0

    dept_stats: Dict[str, Dict[str, Any]] = {}

    for rec, person, dept_name in rows:
        d_name = dept_name or "Unassigned"
        if d_name not in dept_stats:
            dept_stats[d_name] = {"present": 0, "late": 0, "total_records": 0, "total_hours": 0.0}

        dept_stats[d_name]["total_records"] += 1

        if rec.status in (AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY):
            present_total += 1
            dept_stats[d_name]["present"] += 1
        if rec.is_late or rec.status == AttendanceStatus.LATE:
            late_total += 1
            dept_stats[d_name]["late"] += 1
        if rec.total_hours:
            hours_total += rec.total_hours
            dept_stats[d_name]["total_hours"] += rec.total_hours

    dept_breakdown = [
        {
            "department": k,
            "present_count": v["present"],
            "late_count": v["late"],
            "total_records": v["total_records"],
            "total_hours": round(v["total_hours"], 2),
        }
        for k, v in dept_stats.items()
    ]

    summary = {
        "total_active_people": total_people,
        "total_days_in_month": last_day,
        "total_attendance_records": total_records,
        "total_present_entries": present_total,
        "total_late_entries": late_total,
        "total_hours_worked": round(hours_total, 2),
    }

    return ReportMonthlyResponse(
        year=year,
        month=month,
        total_days=last_day,
        summary=summary,
        department_breakdown=dept_breakdown,
    )


@router.get("/custom", response_model=ReportCustomResponse)
async def get_custom_report(
    org_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    department_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    if start_date > end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before end_date")

    rows = await fetch_report_records(db, org_id, start_date, end_date, department_id)

    items = []
    present_cnt = 0
    late_cnt = 0
    total_hrs = 0.0

    for rec, person, dept_name in rows:
        resp = AttendanceRecordResponse.model_validate(rec)
        resp.person_name = person.full_name
        resp.person_unique_id = person.unique_id
        resp.department_name = dept_name
        items.append(resp)

        if rec.status in (AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY):
            present_cnt += 1
        if rec.is_late or rec.status == AttendanceStatus.LATE:
            late_cnt += 1
        if rec.total_hours:
            total_hrs += rec.total_hours

    summary = {
        "start_date": str(start_date),
        "end_date": str(end_date),
        "total_records": len(items),
        "present_count": present_cnt,
        "late_count": late_cnt,
        "total_hours": round(total_hrs, 2),
    }

    return ReportCustomResponse(
        start_date=start_date,
        end_date=end_date,
        total_records=len(items),
        records=items,
        summary=summary,
    )


# ═══════════════════════════════════════════════════════════════════════════
# FILE EXPORTS: CSV, EXCEL, PDF
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/export/csv")
async def export_attendance_csv(
    org_id: UUID,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    department_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    s_date = start_date or date.today() - timedelta(days=30)
    e_date = end_date or date.today()

    rows = await fetch_report_records(db, org_id, s_date, e_date, department_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Date",
        "Unique ID",
        "Full Name",
        "Department",
        "Status",
        "Check-In Time",
        "Check-Out Time",
        "Total Hours",
        "Is Late",
        "Late (Mins)",
        "Early Departure (Mins)",
        "Overtime (Mins)",
        "Marked By",
        "Notes",
    ])

    for rec, person, dept_name in rows:
        writer.writerow([
            rec.date.isoformat(),
            person.unique_id,
            person.full_name,
            dept_name or "N/A",
            rec.status.value if hasattr(rec.status, "value") else str(rec.status),
            rec.check_in_time.strftime("%Y-%m-%d %H:%M:%S") if rec.check_in_time else "",
            rec.check_out_time.strftime("%Y-%m-%d %H:%M:%S") if rec.check_out_time else "",
            f"{rec.total_hours:.2f}" if rec.total_hours is not None else "",
            "Yes" if rec.is_late else "No",
            rec.late_minutes or 0,
            rec.early_departure_minutes or 0,
            rec.overtime_minutes or 0,
            rec.marked_by or "",
            rec.notes or "",
        ])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="attendance_report_{s_date}_{e_date}.csv"'},
    )


@router.get("/export/excel")
async def export_attendance_excel(
    org_id: UUID,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    department_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    s_date = start_date or date.today() - timedelta(days=30)
    e_date = end_date or date.today()

    rows = await fetch_report_records(db, org_id, s_date, e_date, department_id)

    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance Report"

    # Header styling
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    border_side = Side(border_style="thin", color="D3D3D3")
    thin_border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)
    center_align = Alignment(horizontal="center", vertical="center")

    headers = [
        "Date",
        "Unique ID",
        "Full Name",
        "Department",
        "Status",
        "Check-In Time",
        "Check-Out Time",
        "Total Hours",
        "Late",
        "Late (Mins)",
        "Early Dep (Mins)",
        "Marked By",
        "Notes",
    ]

    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = thin_border

    # Data rows
    for r_idx, (rec, person, dept_name) in enumerate(rows, start=2):
        row_data = [
            rec.date.isoformat(),
            person.unique_id,
            person.full_name,
            dept_name or "N/A",
            rec.status.value.upper() if hasattr(rec.status, "value") else str(rec.status).upper(),
            rec.check_in_time.strftime("%H:%M:%S") if rec.check_in_time else "",
            rec.check_out_time.strftime("%H:%M:%S") if rec.check_out_time else "",
            rec.total_hours if rec.total_hours is not None else 0.0,
            "Yes" if rec.is_late else "No",
            rec.late_minutes or 0,
            rec.early_departure_minutes or 0,
            rec.marked_by or "",
            rec.notes or "",
        ]
        ws.append(row_data)
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=r_idx, column=col_idx)
            cell.border = thin_border
            if col_idx in (1, 2, 5, 6, 7, 9):
                cell.alignment = center_align

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="attendance_report_{s_date}_{e_date}.xlsx"'},
    )


@router.get("/export/pdf")
async def export_attendance_pdf(
    org_id: UUID,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    department_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_org_access(current_user, org_id)

    s_date = start_date or date.today() - timedelta(days=7)
    e_date = end_date or date.today()

    # Get Organization Name
    org_name = await db.scalar(select(Organization.name).where(Organization.id == org_id)) or "ATTENDORA"

    rows = await fetch_report_records(db, org_id, s_date, e_date, department_id)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1F4E79"),
        alignment=1,  # Center
    )
    subtitle_style = ParagraphStyle(
        name="SubtitleStyle",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#555555"),
        alignment=1,
    )
    cell_style = ParagraphStyle(
        name="CellStyle",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
    )
    header_cell_style = ParagraphStyle(
        name="HeaderCellStyle",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        textColor=colors.white,
        fontName="Helvetica-Bold",
    )

    story = [
        Paragraph(f"{org_name} - Attendance Report", title_style),
        Spacer(1, 6),
        Paragraph(f"Period: {s_date} to {e_date} | Total Records: {len(rows)}", subtitle_style),
        Spacer(1, 16),
    ]

    table_data = [[
        Paragraph("Date", header_cell_style),
        Paragraph("ID", header_cell_style),
        Paragraph("Name", header_cell_style),
        Paragraph("Department", header_cell_style),
        Paragraph("Status", header_cell_style),
        Paragraph("Check-In", header_cell_style),
        Paragraph("Check-Out", header_cell_style),
        Paragraph("Hours", header_cell_style),
        Paragraph("Late", header_cell_style),
    ]]

    # Limit to top 200 rows for PDF generation to keep file concise
    for rec, person, dept_name in rows[:200]:
        table_data.append([
            Paragraph(rec.date.strftime("%Y-%m-%d"), cell_style),
            Paragraph(person.unique_id, cell_style),
            Paragraph(person.full_name, cell_style),
            Paragraph(dept_name or "N/A", cell_style),
            Paragraph(rec.status.value.upper() if hasattr(rec.status, "value") else str(rec.status), cell_style),
            Paragraph(rec.check_in_time.strftime("%H:%M") if rec.check_in_time else "-", cell_style),
            Paragraph(rec.check_out_time.strftime("%H:%M") if rec.check_out_time else "-", cell_style),
            Paragraph(f"{rec.total_hours:.1f}" if rec.total_hours is not None else "-", cell_style),
            Paragraph(f"{rec.late_minutes}m" if rec.is_late else "No", cell_style),
        ])

    pdf_table = Table(
        table_data,
        colWidths=[70, 60, 150, 110, 80, 75, 75, 55, 55],
    )
    pdf_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D3D3D3")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9F9F9")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    story.append(pdf_table)
    doc.build(story)
    buf.seek(0)

    return Response(
        content=buf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="attendance_report_{s_date}_{e_date}.pdf"'},
    )
