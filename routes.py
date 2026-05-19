from fastapi import APIRouter, File, Form, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from config import MAX_BYTES, MAX_UPLOAD_MB, MODEL_NAME, SUPPORTED_EXTENSIONS
from services.data_service import df_preview, export_dataframe, filter_dataframe, profile_dataframe
from services.file_service import (
    delete_dataset_files,
    get_df,
    load_dataframe_from_path,
    register_dataset,
    save_uploaded_file,
)
from services.llm_service import ask_insight
from services.sql_service import execute_sql
from state import datasets_registry

router = APIRouter()


@router.get("/", response_class=FileResponse)
async def index() -> FileResponse:
    return FileResponse("static/index.html")


@router.get("/health")
async def health() -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "datasets_loaded": len(datasets_registry),
            "model": MODEL_NAME,
            "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
        }
    )


@router.post("/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)) -> JSONResponse:
    raw = await file.read()
    if not raw:
        return JSONResponse(status_code=400, content={"detail": "Файл пустой."})
    if len(raw) > MAX_BYTES:
        return JSONResponse(status_code=400, content={"detail": f"Файл больше лимита {MAX_UPLOAD_MB} MB."})

    target_path, dataset_id = save_uploaded_file(raw, file.filename or "dataset")
    df = load_dataframe_from_path(target_path)
    meta = register_dataset(dataset_id, df, file.filename or "dataset", target_path)
    return JSONResponse({"status": "ok", "dataset": meta})


@router.get("/datasets")
async def list_datasets() -> JSONResponse:
    return JSONResponse({"datasets": list(datasets_registry.values())})


@router.get("/datasets/{dataset_id}/preview")
async def preview_dataset(dataset_id: str, rows: int = Query(default=20, ge=1, le=200)) -> JSONResponse:
    df = get_df(dataset_id)
    return JSONResponse(
        {
            "dataset_id": dataset_id,
            "rows": int(df.shape[0]),
            "columns": [str(c) for c in df.columns],
            "preview": df_preview(df, rows),
        }
    )


@router.get("/datasets/{dataset_id}/profile")
async def profile_dataset(dataset_id: str) -> JSONResponse:
    df = get_df(dataset_id)
    return JSONResponse({"dataset_id": dataset_id, "profile": profile_dataframe(df)})


@router.post("/datasets/{dataset_id}/filter")
async def filter_dataset(
    dataset_id: str,
    column: str = Form(...),
    operator: str = Form(...),
    value: str = Form(...),
    limit: int = Form(default=100),
) -> JSONResponse:
    df = get_df(dataset_id)
    result = filter_dataframe(df, column, operator, value, limit)
    return JSONResponse({"dataset_id": dataset_id, **result})


@router.post("/datasets/{dataset_id}/sql")
async def run_sql(dataset_id: str, sql: str = Form(...), limit: int = Form(default=500)) -> JSONResponse:
    df = get_df(dataset_id)
    result_df = execute_sql(df, sql, limit)
    return JSONResponse(
        {
            "dataset_id": dataset_id,
            "rows": int(result_df.shape[0]),
            "columns": [str(c) for c in result_df.columns],
            "result": result_df.fillna("").to_dict(orient="records"),
        }
    )


@router.get("/datasets/{dataset_id}/export")
async def export_dataset(dataset_id: str, format: str = Query(default="csv")) -> FileResponse:
    df = get_df(dataset_id)
    path, filename, media = export_dataframe(df, dataset_id, format)
    return FileResponse(path=path, filename=filename, media_type=media)


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str) -> JSONResponse:
    delete_dataset_files(dataset_id)
    return JSONResponse({"status": "deleted", "dataset_id": dataset_id})


@router.post("/datasets/{dataset_id}/insight")
async def insight(dataset_id: str, question: str = Form(...)) -> JSONResponse:
    df = get_df(dataset_id)
    result = await ask_insight(df, question)
    return JSONResponse({"dataset_id": dataset_id, **result})