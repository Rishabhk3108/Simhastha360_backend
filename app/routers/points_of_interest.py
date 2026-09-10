from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.point_of_interest import PointOfInterest
from app.schemas.point_of_interest import PointOfInterestOut

router = APIRouter(prefix="/points-of-interest", tags=["points-of-interest"])


@router.get("", response_model=list[PointOfInterestOut])
def list_points_of_interest(db: Session = Depends(get_db)):
    return db.query(PointOfInterest).order_by(PointOfInterest.name).all()
