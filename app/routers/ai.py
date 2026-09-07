from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.facility import Facility
from app.models.incident import SOSAlert
from app.models.report import REPORT_CROWDED, CrowdReport
from app.models.user import ROLE_ADMIN, User
from app.models.zone import CROWD_GREEN, CROWD_RED, CROWD_YELLOW, Zone
from app.schemas.ai import ChatRequest, ChatResponse, FacilitySuggestion, PredictiveAlert
from app.services.clustering import grid_cluster
from app.services.geo import haversine_km

router = APIRouter(prefix="/ai", tags=["ai"])

FACILITY_KEYWORDS = {
    "medical": ["hospital", "medical", "doctor", "clinic", "ambulance"],
    "toilet": ["toilet", "washroom", "restroom", "shauchalay"],
    "water": ["water", "paani", "drinking"],
    "help_desk": ["help", "helpdesk", "information", "madad"],
}


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    """Speech/text goes in, an answer comes out - grounded ONLY in this platform's
    verified facility/zone data. This is a keyword-retrieval stand-in for the real
    pipeline (STT -> LLM constrained to retrieved context -> TTS); swapping in an
    actual LLM later just means replacing this matching step, the "never free-answer"
    contract for the caller stays identical."""
    message_lower = payload.message.lower()

    matched_type = None
    for facility_type, keywords in FACILITY_KEYWORDS.items():
        if any(kw in message_lower for kw in keywords):
            matched_type = facility_type
            break

    if matched_type:
        query = db.query(Facility).filter(Facility.type == matched_type, Facility.status == "active")
        facilities = query.all()
        if payload.lat is not None and payload.lng is not None:
            facilities.sort(key=lambda f: haversine_km(payload.lat, payload.lng, f.lat, f.lng))

        if not facilities:
            return ChatResponse(reply=f"No {matched_type.replace('_', ' ')} is registered on the platform yet.", grounded_on=[])

        nearest = facilities[0]
        distance_note = ""
        if payload.lat is not None and payload.lng is not None:
            km = haversine_km(payload.lat, payload.lng, nearest.lat, nearest.lng)
            distance_note = f", about {km:.1f} km away"
        return ChatResponse(
            reply=f"Nearest {matched_type.replace('_', ' ')} is '{nearest.name}'{distance_note}.",
            grounded_on=[nearest.name],
        )

    zones = db.query(Zone).all()
    if "crowd" in message_lower or "bhiid" in message_lower or "bheed" in message_lower:
        summary = ", ".join(f"{z.name}: {z.crowd_level}" for z in zones) or "No zone data available yet."
        return ChatResponse(reply=f"Current crowd levels — {summary}.", grounded_on=[z.name for z in zones])

    return ChatResponse(
        reply="I can help with nearby medical centers, toilets, water points, help desks, and current crowd levels. Try asking about one of those.",
        grounded_on=[],
    )


@router.get("/predictive-alerts", response_model=list[PredictiveAlert])
def predictive_alerts(db: Session = Depends(get_db)):
    """Hackathon-honest: a trend heuristic over recent report velocity, not a trained
    forecasting model. Zones with rising crowded-reports in the last 30 min are flagged
    as likely to escalate within ~40 minutes."""
    since = datetime.now(timezone.utc) - timedelta(minutes=30)
    zones = db.query(Zone).all()
    alerts = []
    order = [CROWD_GREEN, CROWD_YELLOW, CROWD_RED]

    for zone in zones:
        recent_reports = (
            db.query(CrowdReport)
            .filter(CrowdReport.zone_id == zone.id, CrowdReport.type == REPORT_CROWDED, CrowdReport.created_at >= since)
            .count()
        )
        current_index = order.index(zone.crowd_level)
        if recent_reports >= 3 and current_index < len(order) - 1:
            alerts.append(
                PredictiveAlert(
                    zone_id=zone.id,
                    zone_name=zone.name,
                    current_level=zone.crowd_level,
                    forecast_minutes=40,
                    forecast_level=order[current_index + 1],
                    note=f"{recent_reports} crowd reports in the last 30 minutes suggest rising pressure.",
                )
            )

    return alerts


@router.get("/facility-suggestions", response_model=list[FacilitySuggestion])
def facility_suggestions(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    report_points = [(r.lat, r.lng) for r in db.query(CrowdReport).all() if r.lat is not None and r.lng is not None]
    sos_points = [(s.lat, s.lng) for s in db.query(SOSAlert).all()]
    clusters = grid_cluster(report_points + sos_points)

    return [
        FacilitySuggestion(
            cluster_center_lat=c["lat"],
            cluster_center_lng=c["lng"],
            report_count=c["count"],
            suggestion=f"{c['count']} reports/SOS clustering here - consider a new water point or medical post.",
        )
        for c in clusters
    ]
