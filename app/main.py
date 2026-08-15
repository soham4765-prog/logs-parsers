import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.parsers.factory import LogParserFactory
from app.parsers.normalizer import NormalizationEngine

app = FastAPI(
    title="AI Drone Performance Optimizer - Parser API",
    version="1.0.0",
    description="Universal Telemetry Log Ingestion & 50Hz UTS Normalization Backend"
)

# 1. Enable CORS for all frontend development ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from Vite (5173), React (3000), Next.js, etc.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Setup Upload and Output Directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/", summary="Health Check")
async def root():
    """Simple ping endpoint for frontend developers to verify backend status."""
    return {
        "status": "online",
        "service": "Drone Telemetry Parser API",
        "version": "1.0.0",
        "supported_formats": [".bin", ".ulg", ".bfl", ".bbl"]
    }


@app.post("/api/v1/logs/upload", summary="Upload and Parse Flight Log")
async def upload_and_parse_log(file: UploadFile = File(...)):
    """
    Accepts raw flight log files (.bin, .ulg, .bfl, .bbl).
    Parses and standardizes them into 50 Hz Universal Telemetry Schema (UTS).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    filename = file.filename
    temp_file_path = UPLOAD_DIR / filename

    # Save uploaded log file locally
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload on server: {str(e)}")

    # Parse and Normalize
    try:
        parser = LogParserFactory.get_parser(str(temp_file_path))
        fc_type = parser.get_fc_type()

        # Extract raw records
        raw_df = parser.extract_raw_df(str(temp_file_path))
        if raw_df is None or raw_df.empty:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Log file decoded successfully, but contains no valid telemetry records."
            )

        # Normalize to 50 Hz UTS
        uts_df = NormalizationEngine.normalize_to_uts(raw_df, target_freq_hz=50)

        # Save standardized CSV and Parquet files
        base_name = temp_file_path.stem
        csv_filename = f"{base_name}.uts.csv"
        parquet_filename = f"{base_name}.uts.parquet"

        csv_path = OUTPUT_DIR / csv_filename
        parquet_path = OUTPUT_DIR / parquet_filename

        uts_df.to_csv(csv_path, index=False)
        uts_df.to_parquet(parquet_path, engine="pyarrow", compression="snappy")

        # Prepare NaN-safe preview for Frontend (first 100 rows)
        preview_df = uts_df.head(100).replace({np.nan: None})
        preview_records = preview_df.to_dict(orient="records")

        duration = round(float(uts_df['time_sec'].max()), 2) if 'time_sec' in uts_df.columns else 0.0

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": f"Successfully parsed {fc_type} flight log.",
                "flight_controller": fc_type,
                "filename": filename,
                "total_samples": len(uts_df),
                "flight_duration_sec": duration,
                "available_columns": [col for col in uts_df.columns if not uts_df[col].isna().all()],
                "csv_file": csv_filename,
                "preview": preview_records
            }
        )

    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Parsing error: {str(err)}")


@app.get("/api/v1/logs/download/{filename}", summary="Download Converted CSV")
async def download_file(filename: str):
    """Allows frontend to download the generated .uts.csv dataset."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested file not found.")
    return FileResponse(path=file_path, filename=filename, media_type="text/csv")