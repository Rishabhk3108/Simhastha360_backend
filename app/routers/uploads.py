import base64
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.upload import UploadedDocument

router = APIRouter(prefix="/uploads", tags=["uploads"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB - generous for a phone photo or scanned ID, cheap to store as base64 text


@router.post("")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 5MB)")

    doc = UploadedDocument(
        id=str(uuid4()),
        content_type=file.content_type or "application/octet-stream",
        filename=file.filename or "upload",
        data_base64=base64.b64encode(content).decode(),
    )
    db.add(doc)
    db.commit()
    return {"id": doc.id}


@router.get("/{doc_id}")
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(UploadedDocument).filter(UploadedDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return Response(content=base64.b64decode(doc.data_base64), media_type=doc.content_type)
