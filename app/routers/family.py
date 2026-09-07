import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.family import FamilyGroup, FamilyMember, FamilyShareLink
from app.models.zone import Zone
from app.schemas.family import (
    FamilyGroupCreate,
    FamilyGroupJoin,
    FamilyLocationUpdate,
    FamilyShareLinkCreate,
    FamilyShareLinkOut,
    PublicFamilyStatus,
)
from app.services.geo import haversine_km

router = APIRouter(prefix="/family", tags=["family"])


@router.post("/groups")
def create_group(payload: FamilyGroupCreate, db: Session = Depends(get_db)):
    group = FamilyGroup(
        created_by_device_id=payload.created_by_device_id,
        meeting_point_lat=payload.meeting_point_lat,
        meeting_point_lng=payload.meeting_point_lng,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=payload.duration_hours),
    )
    db.add(group)
    db.flush()

    member = FamilyMember(group_id=group.id, device_id=payload.created_by_device_id, name=payload.member_name)
    db.add(member)
    db.commit()
    return {"group_id": group.id, "expires_at": group.expires_at}


@router.post("/groups/{group_id}/join")
def join_group(group_id: int, payload: FamilyGroupJoin, db: Session = Depends(get_db)):
    group = db.query(FamilyGroup).filter(FamilyGroup.id == group_id).first()
    if not group or group.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=404, detail="Family group not found or expired")
    member = FamilyMember(group_id=group_id, device_id=payload.device_id, name=payload.name)
    db.add(member)
    db.commit()
    return {"ok": True}


@router.get("/groups/{group_id}")
def get_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(FamilyGroup).filter(FamilyGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Family group not found")
    members = db.query(FamilyMember).filter(FamilyMember.group_id == group_id).all()

    separation_alerts = []
    located = [m for m in members if m.last_lat is not None and m.last_lng is not None]
    for i, a in enumerate(located):
        for b in located[i + 1 :]:
            distance_km = haversine_km(a.last_lat, a.last_lng, b.last_lat, b.last_lng)
            if distance_km > 0.5:  # >500m apart counts as separated for a family group
                separation_alerts.append(
                    {
                        "member_a": a.name,
                        "member_b": b.name,
                        "distance_km": round(distance_km, 2),
                        "suggested_reunion": {"lat": group.meeting_point_lat, "lng": group.meeting_point_lng},
                    }
                )

    return {
        "group_id": group.id,
        "expires_at": group.expires_at,
        "meeting_point": {"lat": group.meeting_point_lat, "lng": group.meeting_point_lng},
        "members": [
            {
                "device_id": m.device_id,
                "name": m.name,
                "last_lat": m.last_lat,
                "last_lng": m.last_lng,
                "last_seen_at": m.last_seen_at,
            }
            for m in members
        ],
        "separation_alerts": separation_alerts,
    }


@router.patch("/groups/{group_id}/location")
def update_location(group_id: int, payload: FamilyLocationUpdate, db: Session = Depends(get_db)):
    member = (
        db.query(FamilyMember)
        .filter(FamilyMember.group_id == group_id, FamilyMember.device_id == payload.device_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in this group")
    member.last_lat = payload.lat
    member.last_lng = payload.lng
    member.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}


@router.post("/share-link", response_model=FamilyShareLinkOut)
def create_share_link(payload: FamilyShareLinkCreate, db: Session = Depends(get_db)):
    link = FamilyShareLink(
        token=secrets.token_urlsafe(16),
        device_id=payload.device_id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=payload.duration_hours),
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return FamilyShareLinkOut(token=link.token, expires_at=link.expires_at)


@router.delete("/share-link/{token}")
def revoke_share_link(token: str, db: Session = Depends(get_db)):
    link = db.query(FamilyShareLink).filter(FamilyShareLink.token == token).first()
    if not link:
        raise HTTPException(status_code=404, detail="Share link not found")
    link.revoked = True
    db.commit()
    return {"ok": True}


@router.get("/public/{token}", response_model=PublicFamilyStatus)
def public_family_status(token: str, db: Session = Depends(get_db)):
    """No login required by design - shows only last-known location (if recently
    shared) and general area safety status, never precise continuous tracking."""
    link = db.query(FamilyShareLink).filter(FamilyShareLink.token == token).first()
    if not link or link.revoked or link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=404, detail="Link not found, revoked, or expired")

    member = (
        db.query(FamilyMember)
        .filter(FamilyMember.device_id == link.device_id)
        .order_by(FamilyMember.last_seen_at.desc())
        .first()
    )

    zone_name = None
    crowd_level = None
    if member and member.last_lat is not None:
        zones = db.query(Zone).all()
        if zones:
            nearest = min(zones, key=lambda z: haversine_km(member.last_lat, member.last_lng, z.center_lat, z.center_lng))
            zone_name = nearest.name
            crowd_level = nearest.crowd_level

    return PublicFamilyStatus(
        last_known_lat=member.last_lat if member else None,
        last_known_lng=member.last_lng if member else None,
        last_seen_at=member.last_seen_at if member else None,
        zone_name=zone_name,
        crowd_level=crowd_level,
    )
