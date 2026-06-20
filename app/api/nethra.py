"""
API endpoints for Nethra OCR Annotation Tool.
"""
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.auth import require_admin
from app.database import get_db
from app.models import NethraBatch, NethraImage
from app.schemas.nethra import (
    NethraBatchResponse,
    NethraImageResponse,
    NethraImageUpdate,
    NethraStatsResponse,
    OCRResponse,
)
from app.services.ocr_service import extract_telugu_text, check_tesseract_available

router = APIRouter()

# Base path for nethra images
NETHRA_BASE_PATH = Path(__file__).parent.parent.parent / "nethra"


def folder_name_to_display_name(folder_name: str) -> str:
    """Convert folder_name like 'parvateesa_satakam' to 'Parvateesa Satakam'."""
    # Replace underscores with spaces and title case
    return folder_name.replace("_", " ").title()


def extract_sort_key(filename: str) -> int:
    """Extract numeric sort key from filename for proper ordering."""
    # Try to extract leading numbers
    match = re.match(r'^(\d+)', filename)
    if match:
        return int(match.group(1))

    # Try to extract any number in the filename
    numbers = re.findall(r'\d+', filename)
    if numbers:
        return int(numbers[0])

    # Fall back to alphabetical (use hash for consistent ordering)
    return hash(filename) % 1000000


# ============== Batch Endpoints ==============

@router.get("/batches")
async def list_batches(
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all batches with statistics."""
    query = select(NethraBatch)

    if search:
        query = query.where(
            or_(
                NethraBatch.folder_name.ilike(f"%{search}%"),
                NethraBatch.display_name.ilike(f"%{search}%")
            )
        )

    query = query.order_by(NethraBatch.display_name)
    result = await db.execute(query)
    batches = result.scalars().all()

    batch_list = []
    for batch in batches:
        progress = (batch.annotated_count / batch.total_images * 100) if batch.total_images > 0 else 0
        batch_list.append({
            "id": batch.id,
            "folder_name": batch.folder_name,
            "display_name": batch.display_name,
            "description": batch.description,
            "total_images": batch.total_images,
            "annotated_count": batch.annotated_count,
            "progress_percent": round(progress, 1),
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
        })

    return {"batches": batch_list, "total": len(batch_list)}


@router.get("/batches/{batch_id}")
async def get_batch(batch_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific batch by ID."""
    result = await db.execute(select(NethraBatch).where(NethraBatch.id == batch_id))
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    progress = (batch.annotated_count / batch.total_images * 100) if batch.total_images > 0 else 0

    return {
        "id": batch.id,
        "folder_name": batch.folder_name,
        "display_name": batch.display_name,
        "description": batch.description,
        "total_images": batch.total_images,
        "annotated_count": batch.annotated_count,
        "progress_percent": round(progress, 1),
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
        "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
    }


@router.post("/batches/scan")
async def scan_folders(
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Scan nethra folder and sync batches/images to database."""
    if not NETHRA_BASE_PATH.exists():
        raise HTTPException(status_code=404, detail=f"Nethra folder not found: {NETHRA_BASE_PATH}")

    created_batches = 0
    updated_batches = 0
    total_images_added = 0

    # Scan for subfolders
    for folder in NETHRA_BASE_PATH.iterdir():
        if not folder.is_dir() or folder.name.startswith('.'):
            continue

        folder_name = folder.name
        display_name = folder_name_to_display_name(folder_name)

        # Get image files in folder
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
        image_files = [
            f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]

        # Sort images by extracted number or name
        image_files.sort(key=lambda f: (extract_sort_key(f.name), f.name))

        # Check if batch exists
        result = await db.execute(
            select(NethraBatch).where(NethraBatch.folder_name == folder_name)
        )
        batch = result.scalar_one_or_none()

        if batch:
            # Update existing batch
            batch.total_images = len(image_files)
            updated_batches += 1
        else:
            # Create new batch
            batch = NethraBatch(
                folder_name=folder_name,
                display_name=display_name,
                total_images=len(image_files),
                annotated_count=0
            )
            db.add(batch)
            await db.flush()  # Get batch.id
            created_batches += 1

        # Get existing image paths for this batch
        existing_result = await db.execute(
            select(NethraImage.image_path).where(NethraImage.batch_id == batch.id)
        )
        existing_paths = {row[0] for row in existing_result.fetchall()}

        # Add new images
        for idx, image_file in enumerate(image_files):
            relative_path = f"{folder_name}/{image_file.name}"

            if relative_path not in existing_paths:
                image = NethraImage(
                    batch_id=batch.id,
                    filename=image_file.name,
                    image_path=relative_path,
                    sort_order=idx
                )
                db.add(image)
                total_images_added += 1

        # Update annotated count
        annotated_result = await db.execute(
            select(func.count(NethraImage.id)).where(
                NethraImage.batch_id == batch.id,
                or_(
                    NethraImage.label.isnot(None),
                    NethraImage.corrected_text.isnot(None)
                )
            )
        )
        batch.annotated_count = annotated_result.scalar() or 0

    await db.commit()

    return {
        "message": "Scan complete",
        "created_batches": created_batches,
        "updated_batches": updated_batches,
        "images_added": total_images_added
    }


# ============== Image Endpoints ==============

@router.get("/batches/{batch_id}/images")
async def list_batch_images(
    batch_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """List images in a batch with pagination."""
    # Verify batch exists
    batch_result = await db.execute(select(NethraBatch).where(NethraBatch.id == batch_id))
    batch = batch_result.scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Get images
    query = (
        select(NethraImage)
        .where(NethraImage.batch_id == batch_id)
        .order_by(NethraImage.sort_order)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    images = result.scalars().all()

    image_list = []
    for img in images:
        image_list.append({
            "id": img.id,
            "batch_id": img.batch_id,
            "filename": img.filename,
            "image_path": img.image_path,
            "sort_order": img.sort_order,
            "ocr_text": img.ocr_text,
            "corrected_text": img.corrected_text,
            "label": img.label,
            "is_annotated": img.label is not None or img.corrected_text is not None,
            "annotated_at": img.annotated_at.isoformat() if img.annotated_at else None,
            "image_url": f"/api/nethra/images/{img.id}/file"
        })

    return {
        "images": image_list,
        "total": batch.total_images,
        "batch_id": batch_id,
        "batch_name": batch.display_name
    }


@router.get("/images/{image_id}")
async def get_image(image_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific image by ID."""
    result = await db.execute(select(NethraImage).where(NethraImage.id == image_id))
    img = result.scalar_one_or_none()

    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    # Get batch info
    batch_result = await db.execute(select(NethraBatch).where(NethraBatch.id == img.batch_id))
    batch = batch_result.scalar_one_or_none()

    return {
        "id": img.id,
        "batch_id": img.batch_id,
        "batch_name": batch.display_name if batch else None,
        "filename": img.filename,
        "image_path": img.image_path,
        "sort_order": img.sort_order,
        "ocr_text": img.ocr_text,
        "corrected_text": img.corrected_text,
        "label": img.label,
        "is_annotated": img.label is not None or img.corrected_text is not None,
        "annotated_at": img.annotated_at.isoformat() if img.annotated_at else None,
        "image_url": f"/api/nethra/images/{img.id}/file"
    }


@router.put("/images/{image_id}")
async def update_image_annotation(
    image_id: int,
    update_data: NethraImageUpdate,
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Update image annotation (OCR text, corrected text, label)."""
    result = await db.execute(select(NethraImage).where(NethraImage.id == image_id))
    img = result.scalar_one_or_none()

    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    # Track if this is newly annotated
    was_annotated = img.label is not None or img.corrected_text is not None

    # Update fields
    if update_data.ocr_text is not None:
        img.ocr_text = update_data.ocr_text
    if update_data.corrected_text is not None:
        img.corrected_text = update_data.corrected_text
    if update_data.label is not None:
        img.label = update_data.label  # Now accepts comma-separated labels as string

    # Update annotation timestamp
    img.annotated_at = datetime.utcnow()

    # Update batch annotated count if newly annotated
    is_annotated = img.label is not None or img.corrected_text is not None
    if is_annotated and not was_annotated:
        batch_result = await db.execute(select(NethraBatch).where(NethraBatch.id == img.batch_id))
        batch = batch_result.scalar_one_or_none()
        if batch:
            batch.annotated_count += 1

    await db.commit()
    await db.refresh(img)

    return {
        "id": img.id,
        "ocr_text": img.ocr_text,
        "corrected_text": img.corrected_text,
        "label": img.label,
        "annotated_at": img.annotated_at.isoformat() if img.annotated_at else None,
        "message": "Annotation saved successfully"
    }


@router.get("/images/{image_id}/file")
async def serve_image_file(image_id: int, db: AsyncSession = Depends(get_db)):
    """Serve the actual image file."""
    result = await db.execute(select(NethraImage).where(NethraImage.id == image_id))
    img = result.scalar_one_or_none()

    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    # Construct full path
    file_path = NETHRA_BASE_PATH / img.image_path

    # Security check: ensure path is within nethra directory
    try:
        file_path = file_path.resolve()
        if not str(file_path).startswith(str(NETHRA_BASE_PATH.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid path")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(
        file_path,
        media_type="image/png",
        filename=img.filename
    )


# ============== OCR Endpoints ==============

@router.post("/images/{image_id}/ocr")
async def run_ocr(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Run Tesseract OCR on an image and update its ocr_text field."""
    # Check OCR availability
    available, message = check_tesseract_available()
    if not available:
        raise HTTPException(status_code=503, detail=message)

    # Get image
    result = await db.execute(select(NethraImage).where(NethraImage.id == image_id))
    img = result.scalar_one_or_none()

    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    # Get full path
    file_path = NETHRA_BASE_PATH / img.image_path

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    # Run OCR
    text, error = extract_telugu_text(str(file_path))

    if error:
        return OCRResponse(
            image_id=image_id,
            ocr_text="",
            success=False,
            error=error
        )

    # Update image record
    img.ocr_text = text
    await db.commit()

    return OCRResponse(
        image_id=image_id,
        ocr_text=text,
        success=True,
        error=None
    )


@router.get("/ocr/status")
async def check_ocr_status():
    """Check if Tesseract OCR is available."""
    available, message = check_tesseract_available()
    return {
        "available": available,
        "message": message
    }


# ============== Statistics Endpoints ==============

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get overall annotation statistics."""
    # Total batches
    batch_count = await db.scalar(select(func.count(NethraBatch.id)))

    # Total images
    total_images = await db.scalar(select(func.count(NethraImage.id)))

    # Annotated images (has label or corrected_text)
    annotated_images = await db.scalar(
        select(func.count(NethraImage.id)).where(
            or_(
                NethraImage.label.isnot(None),
                NethraImage.corrected_text.isnot(None)
            )
        )
    )

    # Label counts (handles comma-separated labels)
    label_counts = {}
    for label in ['unreadable', 'correct', 'incorrect', 'needs_review']:
        # Count images that have this label (exact match or as part of comma-separated list)
        count = await db.scalar(
            select(func.count(NethraImage.id)).where(
                or_(
                    NethraImage.label == label,  # Exact match
                    NethraImage.label.like(f"{label},%"),  # At start
                    NethraImage.label.like(f"%,{label}"),  # At end
                    NethraImage.label.like(f"%,{label},%")  # In middle
                )
            )
        )
        label_counts[label] = count or 0

    pending = (total_images or 0) - (annotated_images or 0)
    progress = ((annotated_images or 0) / total_images * 100) if total_images else 0

    return NethraStatsResponse(
        total_batches=batch_count or 0,
        total_images=total_images or 0,
        annotated_images=annotated_images or 0,
        pending_images=pending,
        progress_percent=round(progress, 1),
        label_counts=label_counts
    )


# ============== Export Endpoints ==============

@router.post("/batches/{batch_id}/export")
async def export_batch(
    batch_id: int,
    format: str = Query("json", regex="^(json|csv)$"),
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Export batch annotations as JSON or CSV."""
    # Get batch
    batch_result = await db.execute(select(NethraBatch).where(NethraBatch.id == batch_id))
    batch = batch_result.scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Get all images
    images_result = await db.execute(
        select(NethraImage)
        .where(NethraImage.batch_id == batch_id)
        .order_by(NethraImage.sort_order)
    )
    images = images_result.scalars().all()

    data = []
    for img in images:
        data.append({
            "image_path": img.image_path,
            "filename": img.filename,
            "ocr_text": img.ocr_text or "",
            "corrected_text": img.corrected_text or "",
            "label": img.label or "",
            "annotated_at": img.annotated_at.isoformat() if img.annotated_at else ""
        })

    if format == "csv":
        import csv
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["image_path", "filename", "ocr_text", "corrected_text", "label", "annotated_at"])
        writer.writeheader()
        writer.writerows(data)
        csv_content = output.getvalue()
        return JSONResponse(content={
            "batch_id": batch_id,
            "batch_name": batch.display_name,
            "format": "csv",
            "total_images": len(data),
            "csv_data": csv_content
        })

    return {
        "batch_id": batch_id,
        "batch_name": batch.display_name,
        "format": "json",
        "total_images": len(data),
        "data": data
    }
