from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routers.ai import chat
from app.schemas.ai import ChatRequest

router = APIRouter(prefix="/ivr", tags=["ivr"])


@router.post("/webhook")
def ivr_webhook(
    From: str = Form(...),
    SpeechResult: str = Form(""),
    db: Session = Depends(get_db),
):
    """Provider-agnostic placeholder for an Exotel/MSG91 speech webhook: the provider
    posts the caller's number and speech-to-text result, we run it through the same
    grounded AI brain that powers in-app chat (spec 6.1), and hand back plain text for
    the provider to speak via its own text-to-speech step. Exact request/response shape
    to be adjusted once a provider account and its webhook contract are provisioned."""
    response = chat(ChatRequest(message=SpeechResult or "help"), db=db)
    return {"say": response.reply}


@router.post("/sms")
def sms_webhook(
    From: str = Form(...),
    Body: str = Form(""),
    db: Session = Depends(get_db),
):
    response = chat(ChatRequest(message=Body or "help"), db=db)
    return {"reply": response.reply}
