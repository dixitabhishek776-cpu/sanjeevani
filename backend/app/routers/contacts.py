import datetime as dt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.core.auth import get_current_user
from app.core.crypto import UserCipher
from app.core.encryption_dep import get_user_cipher

router=APIRouter(prefix="/v1/emergency-contacts", tags=["emergency-contacts"])
def mask(v):
    return ("*"*max(0,len(v)-4)+v[-4:]) if v else ""
def out(c,cipher):
    email = cipher.decrypt(c.email_encrypted) if c.email_encrypted else None
    return schemas.EmergencyContactOut(id=c.id,name=c.name,phone_masked=mask(cipher.decrypt(c.phone_encrypted)),email_masked=(email[:2]+"***"+email[email.find('@'):] if email and '@' in email else None),relationship_label=c.relationship_label,consent_given_at=c.consent_given_at,active=c.active)
@router.get("",response_model=list[schemas.EmergencyContactOut])
def list_contacts(db:Session=Depends(get_db),user=Depends(get_current_user),cipher:UserCipher=Depends(get_user_cipher)):
    return [out(c,cipher) for c in db.query(models.EmergencyContact).filter(models.EmergencyContact.user_id==user.id,models.EmergencyContact.active.is_(True)).all()]
@router.post("",response_model=schemas.EmergencyContactOut,status_code=201)
def add_contact(payload:schemas.EmergencyContactIn,db:Session=Depends(get_db),user=Depends(get_current_user),cipher:UserCipher=Depends(get_user_cipher)):
    if not payload.consent: raise HTTPException(400,"Explicit consent is required before an emergency contact can be activated")
    c=models.EmergencyContact(user_id=user.id,name=payload.name,phone_encrypted=cipher.encrypt(payload.phone),email_encrypted=cipher.encrypt(str(payload.email)) if payload.email else None,relationship_label=payload.relationship_label,consent_given_at=dt.datetime.utcnow(),active=True)
    db.add(c); db.commit(); db.refresh(c); return out(c,cipher)
@router.delete("/{contact_id}",status_code=204)
def remove_contact(contact_id:str,db:Session=Depends(get_db),user=Depends(get_current_user)):
    c=db.query(models.EmergencyContact).filter(models.EmergencyContact.id==contact_id,models.EmergencyContact.user_id==user.id).first()
    if not c: raise HTTPException(404,"Contact not found")
    c.active=False; db.commit()
