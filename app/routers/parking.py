from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.parking import ParkingBooking, ParkingZone, VEHICLE_TYPES
from app.models.user import ROLE_ADMIN, User
from app.schemas.parking import (
    ParkingBookingCreate,
    ParkingBookingOut,
    ParkingZoneCreate,
    ParkingZoneOut,
    ParkingZoneUpdate,
)

router = APIRouter(prefix="/parking", tags=["parking"])


def _with_occupancy(db: Session, zones: list[ParkingZone]) -> list[dict]:
    counts: Counter[tuple[int, str]] = Counter()
    for zone_id, vehicle_type in db.query(ParkingBooking.parking_zone_id, ParkingBooking.vehicle_type).all():
        counts[(zone_id, vehicle_type)] += 1

    out = []
    for z in zones:
        out.append(
            {
                "id": z.id,
                "name": z.name,
                "center_lat": z.center_lat,
                "center_lng": z.center_lng,
                "capacity_two_wheeler": z.capacity_two_wheeler,
                "capacity_three_wheeler": z.capacity_three_wheeler,
                "capacity_four_wheeler": z.capacity_four_wheeler,
                "capacity_six_wheeler": z.capacity_six_wheeler,
                "occupied_two_wheeler": counts[(z.id, "two_wheeler")],
                "occupied_three_wheeler": counts[(z.id, "three_wheeler")],
                "occupied_four_wheeler": counts[(z.id, "four_wheeler")],
                "occupied_six_wheeler": counts[(z.id, "six_wheeler")],
                "updated_at": z.updated_at,
            }
        )
    return out


@router.get("", response_model=list[ParkingZoneOut])
def list_parking(db: Session = Depends(get_db)):
    zones = db.query(ParkingZone).all()
    return _with_occupancy(db, zones)


@router.post("", response_model=ParkingZoneOut)
def create_parking(
    payload: ParkingZoneCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    zone = ParkingZone(**payload.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return _with_occupancy(db, [zone])[0]


@router.patch("/{zone_id}", response_model=ParkingZoneOut)
def update_parking(
    zone_id: int,
    payload: ParkingZoneUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    zone = db.query(ParkingZone).filter(ParkingZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Parking zone not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(zone, field, value)
    db.commit()
    db.refresh(zone)
    return _with_occupancy(db, [zone])[0]


@router.delete("/{zone_id}", status_code=204)
def delete_parking(
    zone_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    zone = db.query(ParkingZone).filter(ParkingZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Parking zone not found")
    db.query(ParkingBooking).filter(ParkingBooking.parking_zone_id == zone_id).delete()
    db.delete(zone)
    db.commit()


@router.post("/bookings", response_model=ParkingBookingOut)
def create_booking(
    payload: ParkingBookingCreate,
    db: Session = Depends(get_db),
):
    if payload.vehicle_type not in VEHICLE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid vehicle type")

    zone = db.query(ParkingZone).filter(ParkingZone.id == payload.parking_zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Parking zone not found")

    capacity = getattr(zone, f"capacity_{payload.vehicle_type}")
    occupied = (
        db.query(ParkingBooking)
        .filter(
            ParkingBooking.parking_zone_id == payload.parking_zone_id,
            ParkingBooking.vehicle_type == payload.vehicle_type,
        )
        .count()
    )
    if occupied >= capacity:
        raise HTTPException(status_code=409, detail="This parking zone is full for the selected vehicle type")

    booking = ParkingBooking(**payload.model_dump())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking
