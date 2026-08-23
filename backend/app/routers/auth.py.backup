import hashlib, secrets
import datetime as dt
import os
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.core.auth import hash_password, verify_password, create_access_token
from app.services import notifications, rate_limiter

router=APIRouter(prefix="/v1/auth",tags=["auth"])
REFRESH_DAYS=30
VERIFY_HOURS=24
RESET_MINUTES=30
MAX_LOGIN_FAILURES=5
LOCK_MINUTES=15


def _cookie_mode() -> bool:
    return os.getenv("SANJEEVANI_ENV", "development").lower() in {"production", "prod", "staging"}


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="mb_refresh", value=token, httponly=True, secure=_cookie_mode(),
        samesite="lax", max_age=REFRESH_DAYS * 86400, path="/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key="mb_refresh", path="/v1/auth")

def _token_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()

def _issue_one_time_token(db, model, user_id, expires_at):
    raw=secrets.token_urlsafe(48)
    db.add(model(user_id=user_id, token_hash=_token_hash(raw), expires_at=expires_at))
    return raw

def _issue_refresh(db,user):
    raw=secrets.token_urlsafe(48); digest=hashlib.sha256(raw.encode()).hexdigest()
    db.add(models.RefreshToken(user_id=user.id,token_hash=digest,expires_at=dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=REFRESH_DAYS)))
    return raw

@router.post("/register",response_model=schemas.UserOut,status_code=201)
def register(request: Request, payload:schemas.UserCreate,db:Session=Depends(get_db)):
    if payload.password.strip()!=payload.password or len(payload.password)<12:
        raise HTTPException(400,"Password must be at least 12 characters and must not have leading/trailing whitespace")
    email=payload.email.strip().lower()
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.allow(f"register:{client_ip}"):
        raise HTTPException(429,"Too many registration attempts. Please try again later.")
    if db.query(models.User).filter(models.User.email==email).first(): raise HTTPException(400,"Email already registered")
    user=models.User(email=email,password_hash=hash_password(payload.password),display_name=payload.display_name)
    db.add(user); db.flush(); db.add(models.UserPreferences(user_id=user.id))
    db.add(models.ConsentRecord(user_id=user.id,consent_type="terms",version=os.getenv("SANJEEVANI_TERMS_VERSION","1.0"),granted=True))
    verify_raw=_issue_one_time_token(db, models.VerificationToken, user.id, dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=VERIFY_HOURS))
    db.commit(); db.refresh(user)
    # Delivery is provider-backed; never return the verification token in production.
    if os.getenv("SANJEEVANI_ENV","development").lower() not in {"production","prod"}:
        notifications.send(subject="Verify your Sanjeevani email", body=f"Verification token (development only): {verify_raw}", to=email)
    return user

@router.post("/login",response_model=schemas.Token)
def login(response: Response, form_data:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
    email=form_data.username.strip().lower()
    if not rate_limiter.allow(f"login:{email}"):
        raise HTTPException(429,"Too many login attempts. Please try again later.")
    user=db.query(models.User).filter(models.User.email==email).first()
    now=dt.datetime.now(dt.timezone.utc)
    if not user or user.deleted_at is not None:
        raise HTTPException(401,"Incorrect email or password")
    if user.locked_until and user.locked_until > now:
        raise HTTPException(423,"Account temporarily locked. Please try again later.")
    if os.getenv("SANJEEVANI_ENV","development").lower() in {"production","prod"} and user.email_verified_at is None:
        raise HTTPException(403,"Please verify your email before signing in")
    if not verify_password(form_data.password,user.password_hash):
        user.failed_login_count=(user.failed_login_count or 0)+1
        if user.failed_login_count >= MAX_LOGIN_FAILURES:
            user.locked_until=now+dt.timedelta(minutes=LOCK_MINUTES); user.failed_login_count=0
        db.commit()
        raise HTTPException(401,"Incorrect email or password")
    user.failed_login_count=0; user.locked_until=None
    refresh=_issue_refresh(db,user); db.commit()
    _set_refresh_cookie(response, refresh)
    return schemas.Token(access_token=create_access_token(str(user.id),user.role),refresh_token=None if _cookie_mode() else refresh)

@router.post("/refresh",response_model=schemas.Token)
def refresh(response: Response, payload: schemas.RefreshTokenIn | None = None, refresh_cookie: str | None = Cookie(default=None, alias="mb_refresh"), db:Session=Depends(get_db)):
    raw_token = refresh_cookie if _cookie_mode() else (payload.refresh_token if payload else None)
    if not raw_token:
        raise HTTPException(401,"Invalid refresh token")
    digest=hashlib.sha256(raw_token.encode()).hexdigest(); row=db.query(models.RefreshToken).filter(models.RefreshToken.token_hash==digest).with_for_update().first()
    now=dt.datetime.now(dt.timezone.utc)
    if not row or row.revoked_at or row.expires_at<=now: raise HTTPException(401,"Invalid refresh token")
    user=db.query(models.User).filter(models.User.id==row.user_id,models.User.deleted_at.is_(None)).first()
    if not user: raise HTTPException(401,"Invalid refresh token")
    row.revoked_at=now; new=_issue_refresh(db,user); db.commit()
    _set_refresh_cookie(response, new)
    return schemas.Token(access_token=create_access_token(str(user.id),user.role),refresh_token=None if _cookie_mode() else new)

@router.post("/logout")
def logout(response: Response, payload: schemas.RefreshTokenIn | None = None, refresh_cookie: str | None = Cookie(default=None, alias="mb_refresh"), db:Session=Depends(get_db)):
    raw_token = refresh_cookie if _cookie_mode() else (payload.refresh_token if payload else None)
    if raw_token:
        digest=hashlib.sha256(raw_token.encode()).hexdigest(); row=db.query(models.RefreshToken).filter(models.RefreshToken.token_hash==digest).first()
        if row: row.revoked_at=dt.datetime.now(dt.timezone.utc); db.commit()
    _clear_refresh_cookie(response)
    return {"status":"logged_out"}


@router.post("/verify-email")
def verify_email(payload: schemas.EmailVerificationRequest, db: Session = Depends(get_db)):
    row=db.query(models.VerificationToken).filter(models.VerificationToken.token_hash==_token_hash(payload.token)).first()
    now=dt.datetime.now(dt.timezone.utc)
    if not row or row.used_at or row.expires_at <= now:
        raise HTTPException(400,"Invalid or expired verification token")
    user=db.query(models.User).filter(models.User.id==row.user_id, models.User.deleted_at.is_(None)).first()
    if not user: raise HTTPException(400,"Invalid verification token")
    row.used_at=now; user.email_verified_at=now; db.commit()
    return {"status":"verified"}

@router.post("/password-reset/request")
def password_reset_request(request: Request, payload: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    email=payload.email.strip().lower()
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.allow(f"reset:{client_ip}") or not rate_limiter.allow(f"reset_email:{email}"):
        raise HTTPException(429,"Too many password reset requests. Please try again later.")
    user=db.query(models.User).filter(models.User.email==email, models.User.deleted_at.is_(None)).first()
    # Deliberately identical response to prevent account enumeration.
    if user:
        raw=_issue_one_time_token(db, models.PasswordResetToken, user.id, dt.datetime.now(dt.timezone.utc)+dt.timedelta(minutes=RESET_MINUTES))
        if os.getenv("SANJEEVANI_ENV","development").lower() not in {"production","prod"}:
            notifications.send(subject="Sanjeevani password reset", body=f"Reset token (development only): {raw}", to=email)
        db.commit()
    return {"status":"If the account exists, reset instructions have been queued."}

@router.post("/password-reset/confirm")
def password_reset_confirm(payload: schemas.PasswordResetConfirm, db: Session = Depends(get_db)):
    row=db.query(models.PasswordResetToken).filter(models.PasswordResetToken.token_hash==_token_hash(payload.token)).first()
    now=dt.datetime.now(dt.timezone.utc)
    if not row or row.used_at or row.expires_at <= now: raise HTTPException(400,"Invalid or expired reset token")
    user=db.query(models.User).filter(models.User.id==row.user_id, models.User.deleted_at.is_(None)).first()
    if not user: raise HTTPException(400,"Invalid reset token")
    if payload.new_password.strip()!=payload.new_password: raise HTTPException(400,"Password must not have leading/trailing whitespace")
    user.password_hash=hash_password(payload.new_password); user.failed_login_count=0; user.locked_until=None
    # Revoke all sessions after a password reset.
    for token in db.query(models.RefreshToken).filter(models.RefreshToken.user_id==user.id, models.RefreshToken.revoked_at.is_(None)).all():
        token.revoked_at=now
    row.used_at=now; db.commit()
    return {"status":"password_reset"}


@router.post("/resend-verification")
def resend_verification(request: Request, payload: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.allow(f"verify:{client_ip}") or not rate_limiter.allow(f"verify_email:{email}"):
        raise HTTPException(429,"Too many verification requests. Please try again later.")
    user = db.query(models.User).filter(models.User.email == email, models.User.deleted_at.is_(None)).first()
    if user and user.email_verified_at is None:
        raw = _issue_one_time_token(db, models.VerificationToken, user.id, dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=VERIFY_HOURS))
        if os.getenv("SANJEEVANI_ENV","development").lower() not in {"production","prod"}:
            notifications.send(subject="Verify your Sanjeevani email", body=f"Verification token (development only): {raw}", to=email)
        else:
            notifications.send(subject="Verify your Sanjeevani email", body="Please use the verification link from Sanjeevani.", to=email)
        db.commit()
    return {"status":"If the account exists and is unverified, verification instructions have been queued."}
