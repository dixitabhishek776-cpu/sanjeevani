import datetime as dt
from statistics import mean
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.core.auth import get_current_user
router=APIRouter(prefix="/v1/summary",tags=["summary"])
@router.get("/weekly",response_model=schemas.WeeklySummaryOut)
def weekly(db:Session=Depends(get_db),user=Depends(get_current_user)):
    end=dt.datetime.now(dt.timezone.utc); start=end-dt.timedelta(days=7)
    moods=db.query(models.MoodEntry).filter(models.MoodEntry.user_id==user.id,models.MoodEntry.logged_at>=start).all()
    journals=db.query(models.Journal).filter(models.Journal.user_id==user.id,models.Journal.created_at>=start).count()
    chats=db.query(models.Chat).filter(models.Chat.user_id==user.id,models.Chat.started_at>=start).count()
    elevated=db.query(models.SafetyAssessment).filter(models.SafetyAssessment.user_id==user.id,models.SafetyAssessment.created_at>=start,models.SafetyAssessment.concern_level.in_(['moderate','high','immediate'])).count()
    avg=round(mean([m.mood_score for m in moods]),2) if moods else None
    highlights=[]
    if avg is not None: highlights.append(f"Average logged mood: {avg}/10")
    if moods: highlights.append(f"You logged your mood {len(moods)} time(s) this week")
    if journals: highlights.append(f"You wrote {journals} journal entr{'y' if journals==1 else 'ies'}")
    if elevated: highlights.append("There were elevated wellbeing check-ins; review how you are feeling today.")
    if not highlights: highlights.append("No activity was recorded this week. A small check-in can be a useful place to start.")
    return schemas.WeeklySummaryOut(period_start=start,period_end=end,mood_average=avg,mood_count=len(moods),journal_count=journals,chat_count=chats,elevated_safety_events=elevated,highlights=highlights)
