from typing import List, Optional
import datetime as dt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.core.auth import require_role
from app.core.crypto import UserCipher
from app.core.encryption_dep import get_user_cipher

router=APIRouter(prefix="/v1/safety",tags=["safety"])

@router.get("/alerts",response_model=List[schemas.AlertOut])
def list_alerts(status_filter:Optional[str]="pending_review",db:Session=Depends(get_db),reviewer=Depends(require_role("reviewer","super_admin"))):
    q=db.query(models.Alert,models.SafetyAssessment).join(models.SafetyAssessment,models.Alert.safety_assessment_id==models.SafetyAssessment.id)
    if status_filter: q=q.filter(models.Alert.status==status_filter)
    return [schemas.AlertOut(id=a.id,status=a.status,concern_level=s.concern_level,explanation=s.explanation,created_at=s.created_at) for a,s in q.order_by(models.SafetyAssessment.created_at.desc()).limit(100).all()]

@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id:str,db:Session=Depends(get_db),reviewer=Depends(require_role("reviewer","super_admin"))):
    alert=db.query(models.Alert).filter(models.Alert.id==alert_id).first()
    if not alert: raise HTTPException(404,"Alert not found")
    if alert.status != "pending_review":
        raise HTTPException(409, "Alert is not awaiting acknowledgment")
    now=dt.datetime.now(dt.timezone.utc)
    alert.status="acknowledged"; alert.assigned_reviewer_id=reviewer.id; alert.acknowledged_at=now; alert.last_escalated_at=now
    db.add(models.AuditLog(actor_id=reviewer.id,action="alert_acknowledged",target_type="alert",target_id=alert.id,audit_metadata={"status":"acknowledged","reviewer_id":str(reviewer.id)})); db.commit()
    return {"status":"acknowledged","alert_id":str(alert.id)}

@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id:str,notes:str="",db:Session=Depends(get_db),reviewer=Depends(require_role("reviewer","super_admin")),cipher:UserCipher=Depends(get_user_cipher)):
    alert=db.query(models.Alert).filter(models.Alert.id==alert_id).first()
    if not alert: raise HTTPException(404,"Alert not found")
    if alert.status != "acknowledged":
        raise HTTPException(409, "Alert must be acknowledged before resolution")
    if not notes.strip():
        raise HTTPException(400, "Resolution notes are required for auditability")
    now=dt.datetime.now(dt.timezone.utc)
    alert.status="resolved"; alert.assigned_reviewer_id=reviewer.id; alert.resolved_at=now
    alert.resolution_notes_encrypted=cipher.encrypt(notes.strip())
    db.add(models.AuditLog(actor_id=reviewer.id,action="alert_resolved",target_type="alert",target_id=alert.id,audit_metadata={"has_notes":True,"reviewer_id":str(reviewer.id)})); db.commit()
    return {"status":"resolved","alert_id":str(alert.id)}
