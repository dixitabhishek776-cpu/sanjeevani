from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models, schemas
from app.database import get_db
from app.core.auth import get_current_user
from app.core.crypto import UserCipher
from app.core.encryption_dep import get_user_cipher
router=APIRouter(prefix="/v1/chats",tags=["chats"])
@router.get("",response_model=list[schemas.ChatSummaryOut])
def list_chats(db:Session=Depends(get_db),user=Depends(get_current_user)):
    rows=db.query(models.Chat,func.count(models.Message.id)).outerjoin(models.Message,models.Message.chat_id==models.Chat.id).filter(models.Chat.user_id==user.id).group_by(models.Chat.id).order_by(models.Chat.started_at.desc()).limit(50).all()
    return [schemas.ChatSummaryOut(id=c.id,title=c.title,started_at=c.started_at,ended_at=c.ended_at,message_count=int(n)) for c,n in rows]
@router.get("/{chat_id}/messages",response_model=list[schemas.ChatHistoryMessageOut])
def chat_messages(chat_id:str,db:Session=Depends(get_db),user=Depends(get_current_user),cipher:UserCipher=Depends(get_user_cipher)):
    c=db.query(models.Chat).filter(models.Chat.id==chat_id,models.Chat.user_id==user.id).first()
    if not c: raise HTTPException(404,"Chat not found")
    return [schemas.ChatHistoryMessageOut(id=m.id,sender=m.sender,content=cipher.decrypt(m.content_encrypted),created_at=m.created_at) for m in db.query(models.Message).filter(models.Message.chat_id==c.id).order_by(models.Message.created_at.asc()).all()]
@router.patch("/{chat_id}")
def rename_chat(chat_id:str,title:str,db:Session=Depends(get_db),user=Depends(get_current_user)):
    c=db.query(models.Chat).filter(models.Chat.id==chat_id,models.Chat.user_id==user.id).first()
    if not c: raise HTTPException(404,"Chat not found")
    c.title=title[:150]; db.commit(); return {"status":"updated"}
