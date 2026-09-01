"""
AEGIS-X API Dataset Registry Endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from api.core.auth import UserContext, get_current_user
from api.schemas.datasets import DatasetListResponse, DatasetResponse
from api.services.dataset_service import DatasetService

router = APIRouter(prefix="/api/v1/datasets", tags=["Dataset Registry"])


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED, summary="Upload Dataset CSV")
async def register_dataset(
    model_id: str = Form(..., description="ID of associated registered model"),
    dataset_type: str = Form(..., description="Dataset type: REFERENCE or EVALUATION"),
    target_column: Optional[str] = Form(None, description="Optional name of target label column"),
    file: UploadFile = File(..., description="Tabular dataset CSV file"),
    user: UserContext = Depends(get_current_user),
):
    """
    Upload and register a CSV dataset (REFERENCE baseline or EVALUATION batch).
    Validates numeric feature types, schema consistency, and compatibility with the target model.
    """
    return await DatasetService.register_dataset(
        model_id=model_id,
        dataset_type=dataset_type,
        file=file,
        target_column=target_column,
        user_id=user.user_id,
    )


@router.get("", response_model=DatasetListResponse, summary="List Datasets")
async def list_datasets(
    model_id: Optional[str] = Query(None, description="Optional model ID filter"),
    user: UserContext = Depends(get_current_user),
):
    """List registered datasets, optionally filtered by model_id."""
    datasets = DatasetService.list_datasets(model_id=model_id, user_id=user.user_id)
    return DatasetListResponse(total=len(datasets), datasets=datasets)


@router.get("/{dataset_id}", response_model=DatasetResponse, summary="Get Dataset Metadata")
async def get_dataset(dataset_id: str, user: UserContext = Depends(get_current_user)):
    """Retrieve dataset metadata by ID."""
    ds = DatasetService.get_dataset(dataset_id, user_id=user.user_id)
    if not ds:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found.")
    return ds


@router.delete("/{dataset_id}", summary="Delete Dataset")
async def delete_dataset(dataset_id: str, user: UserContext = Depends(get_current_user)):
    """Delete a registered dataset metadata record and stored CSV file."""
    success = DatasetService.delete_dataset(dataset_id, user_id=user.user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found.")
    return {"status": "deleted", "dataset_id": dataset_id}

