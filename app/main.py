import os
import shutil

from fastapi import FastAPI, UploadFile, File, HTTPException

from app.services.pipeline import process_log


app = FastAPI(
    title="AI Drone Performance Optimizer API",
    version="1.0.0"
)


UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.get("/")
def root():
    return {
        "message": "AI Drone Performance Optimizer API",
        "status": "running"
    }


@app.post("/api/v1/logs/upload")
async def upload_log(file: UploadFile = File(...)):

    # Check file extension
    allowed_extensions = {
        ".bin",
        ".ulg",
        ".bfl",
        ".bbl"
    }

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {extension}"
        )

    # Save uploaded file
    file_path = os.path.join(
        UPLOAD_DIR,
        file.filename
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:

        # Run your complete processing pipeline
        output_path = process_log(file_path)

        return {
            "status": "success",
            "filename": file.filename,
            "parser_output": output_path
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )