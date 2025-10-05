import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()
UPLOAD_DIR = Path("uploads")
LOGO_PATH = UPLOAD_DIR / "logo.png"

# Ensure the upload directory exists
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/api/logo", status_code=201)
async def upload_logo(file: UploadFile = File(...)):
    """
    Handles the upload of a new PNG logo.
    The uploaded file will replace any existing logo.
    """
    if file.content_type != "image/png":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PNG image.")

    try:
        with LOGO_PATH.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    return {"filename": "logo.png", "path": str(LOGO_PATH)}

@router.get("/logo.png", response_class=FileResponse)
async def get_logo():
    """
    Serves the custom logo if it exists.
    """
    if not LOGO_PATH.is_file():
        raise HTTPException(status_code=404, detail="Custom logo not found.")

    return FileResponse(LOGO_PATH)