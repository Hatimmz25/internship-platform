from fastapi import APIRouter, Depends, HTTPException, Query
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.preference import AlertFrequency
from app.models.user import User

router = APIRouter()


@router.get("/unsubscribe")
def unsubscribe(token: str = Query(...), db: Session = Depends(get_db)):
    """Validates the signed token and turns off email alerts for the user."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("action") != "unsubscribe":
            raise ValueError("wrong action")
        user_id = int(payload["user_id"])
    except (JWTError, ValueError, KeyError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid or expired unsubscribe token.")

    user = db.get(User, user_id)
    if not user or not user.preference:
        raise HTTPException(status_code=404, detail="Subscriber not found.")

    user.preference.alert_frequency = AlertFrequency.OFF.value
    db.commit()
    return {"message": "You have been successfully unsubscribed from all email alerts."}