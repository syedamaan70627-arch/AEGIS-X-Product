"""
AEGIS-X Reports API Router.

Exposes REST endpoints for generating, fetching, listing, and exporting integrated reports.
Strictly authenticated and owner-isolated via AuthUser dependency.
"""

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from api.core.auth import UserContext, get_current_user
from api.core.dependencies import get_report_repository
from api.services.reports_service import ReportsService, ReportServiceError


router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


class GenerateReportRequest(BaseModel):
    model_id: str = Field(..., description="ID of the model context")
    analysis_id: str = Field(..., description="ID of the target analysis run")
    report_type: str = Field("integrated", description="Type of report: integrated, reliability, model_trust, or governance")


class ReportResponse(BaseModel):
    id: str
    user_id: str
    model_id: str
    analysis_id: str
    report_type: str
    title: str
    disposition: str
    completeness_score: float
    result_path: str
    snapshot_json: dict
    created_at: str


@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report(
    req: GenerateReportRequest,
    current_user: UserContext = Depends(get_current_user),
) -> ReportResponse:
    """Generates an immutable AEGIS-X report for the given analysis context."""
    service = ReportsService()
    try:
        record = service.generate_report(
            user_id=current_user.user_id,
            model_id=req.model_id,
            analysis_id=req.analysis_id,
            report_type=req.report_type,
        )
        return ReportResponse(
            id=record.id,
            user_id=record.user_id,
            model_id=record.model_id,
            analysis_id=record.analysis_id,
            report_type=record.report_type,
            title=record.title,
            disposition=record.disposition,
            completeness_score=record.completeness_score,
            result_path=record.result_path,
            snapshot_json=record.snapshot_json if isinstance(record.snapshot_json, dict) else json.loads(record.snapshot_json),
            created_at=record.created_at,
        )
    except ReportServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": e.message,
                "reason": e.reason,
                "action": e.action,
                "technical_details": e.technical_details,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{report_id}", response_model=ReportResponse)
def get_report_by_id(
    report_id: str,
    current_user: UserContext = Depends(get_current_user),
) -> ReportResponse:
    """Retrieves a persisted report by ID."""
    service = ReportsService()
    try:
        record = service.get_report(report_id, user_id=current_user.user_id)
        return ReportResponse(
            id=record.id,
            user_id=record.user_id,
            model_id=record.model_id,
            analysis_id=record.analysis_id,
            report_type=record.report_type,
            title=record.title,
            disposition=record.disposition,
            completeness_score=record.completeness_score,
            result_path=record.result_path,
            snapshot_json=record.snapshot_json if isinstance(record.snapshot_json, dict) else json.loads(record.snapshot_json),
            created_at=record.created_at,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/model/{model_id}", response_model=List[ReportResponse])
def list_reports_by_model(
    model_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: UserContext = Depends(get_current_user),
) -> List[ReportResponse]:
    """Lists historical reports for a specific model."""
    service = ReportsService()
    records = service.list_reports_by_model(model_id=model_id, user_id=current_user.user_id, limit=limit, offset=offset)
    return [
        ReportResponse(
            id=r.id,
            user_id=r.user_id,
            model_id=r.model_id,
            analysis_id=r.analysis_id,
            report_type=r.report_type,
            title=r.title,
            disposition=r.disposition,
            completeness_score=r.completeness_score,
            result_path=r.result_path,
            snapshot_json=r.snapshot_json if isinstance(r.snapshot_json, dict) else json.loads(r.snapshot_json),
            created_at=r.created_at,
        )
        for r in records
    ]


@router.get("/{report_id}/export")
def export_report(
    report_id: str,
    format: str = Query("json", description="Export format: json, csv, or pdf"),
    current_user: UserContext = Depends(get_current_user),
) -> Response:
    """Exports a report in JSON, CSV, or PDF/HTML format."""
    service = ReportsService()
    try:
        content, media_type = service.export_report(report_id=report_id, user_id=current_user.user_id, export_format=format)
        filename = f"aegis_x_report_{report_id}.{format.lower()}"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return Response(content=content, media_type=media_type, headers=headers)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
