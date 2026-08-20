from fastapi import APIRouter, Depends, Header, HTTPException
import hashlib, json
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.core.auth import get_current_user
from app.core.crypto import UserCipher
from app.core.encryption_dep import get_user_cipher
from app.agents.emotion_agent import EmotionAnalysisAgent
from app.agents.safety_agent import SafetyIntelligenceAgent, decision_router
from app.agents.conversation_agent import ConversationAgent
from app.services import rate_limiter, enqueue_notification

router = APIRouter(prefix="/v1/chat", tags=["chat"])

emotion_agent = EmotionAnalysisAgent()
safety_agent = SafetyIntelligenceAgent()
conversation_agent = ConversationAgent()


def _log_audit(db: Session, actor_id, action: str, target_type: str, target_id, metadata: dict):
    entry = models.AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        audit_metadata=metadata,
    )
    db.add(entry)


@router.post("/message", response_model=schemas.ChatMessageOut)
def send_message(
    payload: schemas.ChatMessageIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    cipher: UserCipher = Depends(get_user_cipher),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if idempotency_key is not None:
        if len(idempotency_key) > 128 or not idempotency_key.strip():
            raise HTTPException(status_code=400, detail="Invalid Idempotency-Key")
        # Serialize identical idempotency keys inside PostgreSQL so concurrent
        # retries cannot execute the safety/LLM pipeline twice.
        db.execute(__import__("sqlalchemy").text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"), {"lock_key": f"{user.id}:{idempotency_key}"})
        request_hash = hashlib.sha256(
            json.dumps(payload.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        existing = db.query(models.IdempotencyRecord).filter(
            models.IdempotencyRecord.user_id == user.id,
            models.IdempotencyRecord.key == idempotency_key,
        ).first()
        if existing:
            if existing.request_hash != request_hash:
                raise HTTPException(status_code=409, detail="Idempotency-Key was already used for a different request")
            return schemas.ChatMessageOut.model_validate(json.loads(cipher.decrypt(existing.response_encrypted)))

    if not rate_limiter.allow(f"chat:{user.id}"):
        raise HTTPException(status_code=429, detail="Too many messages. Please wait a moment and try again.")
    # 1. Resolve or create chat
    if payload.chat_id:
        chat = db.query(models.Chat).filter(
            models.Chat.id == payload.chat_id, models.Chat.user_id == user.id
        ).first()
    else:
        chat = None
    if not chat:
        chat = models.Chat(user_id=user.id)
        db.add(chat)
        db.flush()

    # 2. Persist user message (encrypted)
    user_msg = models.Message(
        chat_id=chat.id, sender="user", content_encrypted=cipher.encrypt(payload.content)
    )
    db.add(user_msg)
    db.flush()

    # 3. Emotion analysis
    emotion_signal = emotion_agent.analyze(payload.content)

    # 4. Recent concern-level trend for this user (last 10 assessments)
    recent = (
        db.query(models.SafetyAssessment.concern_level)
        .filter(models.SafetyAssessment.user_id == user.id)
        .order_by(models.SafetyAssessment.created_at.desc())
        .limit(10)
        .all()
    )
    recent_levels = [r[0] for r in reversed(recent)]

    # 5. Safety assessment (gates everything downstream — Ch.1 Sec.2)
    # An unresolved high/immediate alert is a human-owned safety state. New
    # model output may escalate it, but cannot silently lower it.
    active_alert = (
        db.query(models.Alert)
        .join(models.SafetyAssessment, models.Alert.safety_assessment_id == models.SafetyAssessment.id)
        .filter(
            models.SafetyAssessment.user_id == user.id,
            models.SafetyAssessment.concern_level.in_(["high", "immediate"]),
            models.Alert.status.in_(["pending_review", "acknowledged"]),
        )
        .order_by(models.SafetyAssessment.created_at.desc())
        .first()
    )
    active_floor = None
    if active_alert:
        active_floor = db.query(models.SafetyAssessment.concern_level).filter(
            models.SafetyAssessment.id == active_alert.safety_assessment_id
        ).scalar()
    assessment = safety_agent.assess(payload.content, emotion_signal, recent_levels, active_floor)
    directive = decision_router(assessment)

    safety_record = models.SafetyAssessment(
        user_id=user.id,
        message_id=user_msg.id,
        concern_level=assessment.concern_level,
        contributing_factors=assessment.contributing_factors,
        explanation=assessment.explanation,
        confidence=assessment.confidence,
    )
    db.add(safety_record)
    db.flush()

    if directive["create_alert"]:
        alert = models.Alert(safety_assessment_id=safety_record.id, status="pending_review")
        db.add(alert)
        db.flush()
        prefs = db.query(models.UserPreferences).filter(models.UserPreferences.user_id == user.id).first()
        contacts = []
        if directive["notify_emergency_contact"] and prefs and prefs.emergency_contacts_enabled:
            contacts = db.query(models.EmergencyContact).filter(
                models.EmergencyContact.user_id == user.id,
                models.EmergencyContact.active.is_(True),
                models.EmergencyContact.consent_given_at.isnot(None),
            ).all()
        for contact in contacts:
            recipient = cipher.decrypt(contact.email_encrypted) if contact.email_encrypted else None
            if not recipient:
                continue
            enqueue_notification(
                db, user_id=user.id, alert_id=alert.id, cipher=cipher, channel="email",
                recipient=recipient,
                subject=f"Sanjeevani safety check-in for {user.display_name or 'a user'}",
                body=("Sanjeevani detected an elevated safety concern and routed it to the authorized review workflow. "
                      "Please check in with the person using your agreed safety plan. This message is not an emergency dispatch."),
            )
            db.add(models.NotificationEvent(user_id=user.id, alert_id=alert.id, channel="email", status="queued"))
        _log_audit(
            db, user.id, "safety_alert_created", "safety_assessment", safety_record.id,
            {"concern_level": assessment.concern_level, "escalation": directive["human_escalation"], "contact_count": len(contacts)},
        )

    # 6. Conversation Agent generates reply — cannot bypass safety directive
    ai_reply = conversation_agent.generate_response(
        payload.content, directive, assessment.concern_level
    )

    ai_msg = models.Message(
        chat_id=chat.id, sender="ai", content_encrypted=cipher.encrypt(ai_reply["text"])
    )
    db.add(ai_msg)

    response = schemas.ChatMessageOut(
        message_id=ai_msg.id,
        chat_id=chat.id,
        ai_response=ai_reply["text"],
        resources_text=ai_reply["resources_text"],
        safety=schemas.SafetyInfoOut(
            concern_level=assessment.concern_level,
            resources_shown=ai_reply["resources_shown"],
        ),
        intervention=ai_reply.get("intervention"),
    )
    if idempotency_key is not None:
        db.add(models.IdempotencyRecord(
            user_id=user.id, key=idempotency_key, request_hash=request_hash,
            response_encrypted=cipher.encrypt(json.dumps(response.model_dump(mode="json"), separators=(",", ":"))), status_code=200
        ))
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        # A concurrent duplicate request may have committed the same key.
        if idempotency_key is not None:
            existing = db.query(models.IdempotencyRecord).filter(
                models.IdempotencyRecord.user_id == user.id,
                models.IdempotencyRecord.key == idempotency_key,
            ).first()
            if existing and existing.request_hash == request_hash:
                return schemas.ChatMessageOut.model_validate(json.loads(cipher.decrypt(existing.response_encrypted)))
        raise exc

    return response
