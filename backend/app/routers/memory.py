from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.core.auth import get_current_user
from app.core.crypto import UserCipher
from app.core.encryption_dep import get_user_cipher

router=APIRouter(prefix="/v1/memories", tags=["memory"])

def _enabled(db,user):
    prefs=db.query(models.UserPreferences).filter(models.UserPreferences.user_id==user.id).first()
    return bool(prefs and prefs.long_term_memory_enabled)

@router.get("", response_model=list[schemas.MemoryOut])
def list_memories(db:Session=Depends(get_db), user=Depends(get_current_user), cipher:UserCipher=Depends(get_user_cipher)):
    if not _enabled(db,user): return []
    rows=db.query(models.Memory).filter(models.Memory.user_id==user.id, models.Memory.active.is_(True)).order_by(models.Memory.created_at.desc()).limit(100).all()
    return [schemas.MemoryOut(id=r.id,content=cipher.decrypt(r.content_encrypted),category=r.category,source=r.source,created_at=r.created_at) for r in rows]

@router.post("", response_model=schemas.MemoryOut, status_code=201)
def create_memory(payload:schemas.MemoryIn, db:Session=Depends(get_db), user=Depends(get_current_user), cipher:UserCipher=Depends(get_user_cipher)):
    if not _enabled(db,user): raise HTTPException(403,"Long-term memory is disabled. Enable it in Privacy settings first.")
    row=models.Memory(user_id=user.id,content_encrypted=cipher.encrypt(payload.content.strip()),category=payload.category.strip().lower(),source="user",active=True)
    db.add(row); db.commit(); db.refresh(row)
    return schemas.MemoryOut(id=row.id,content=payload.content.strip(),category=row.category,source=row.source,created_at=row.created_at)

@router.patch("/{memory_id}", response_model=schemas.MemoryOut)
def update_memory(memory_id:str,payload:schemas.MemoryUpdate,db:Session=Depends(get_db),user=Depends(get_current_user),cipher:UserCipher=Depends(get_user_cipher)):
    if not _enabled(db,user): raise HTTPException(403,"Long-term memory is disabled")
    row=db.query(models.Memory).filter(models.Memory.id==memory_id,models.Memory.user_id==user.id,models.Memory.active.is_(True)).first()
    if not row: raise HTTPException(404,"Memory not found")
    if payload.content is not None: row.content_encrypted=cipher.encrypt(payload.content.strip())
    if payload.category is not None: row.category=payload.category.strip().lower()
    db.commit(); db.refresh(row)
    return schemas.MemoryOut(id=row.id,content=cipher.decrypt(row.content_encrypted),category=row.category,source=row.source,created_at=row.created_at)

@router.delete("/{memory_id}", status_code=204)
def delete_memory(memory_id:str,db:Session=Depends(get_db),user=Depends(get_current_user)):
    row=db.query(models.Memory).filter(models.Memory.id==memory_id,models.Memory.user_id==user.id,models.Memory.active.is_(True)).first()
    if not row: raise HTTPException(404,"Memory not found")
    row.active=False; db.commit()
