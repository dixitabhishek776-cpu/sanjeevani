"""
profile_page.py  -  Profile screens (overview, account & security, edit).

    from profile_page import render_profile_page
    render_profile_page(svc, user_id,
                        on_add_contact=lambda: go("Contacts"),   # optional
                        on_setup_2fa=lambda: go("Settings"),     # optional
                        on_sign_out=sign_out,                    # optional
                        on_account_deleted=sign_out)             # optional
"""
from __future__ import annotations
import re
from datetime import datetime, time
from typing import Callable
import streamlit as st
from sj_ui_theme import (card, row, badge, chips, kv_rows, avatar_ring, progress_bar, danger_note, safety_banner, icon, _md)
from sj_profile_service import ProfileService, make_avatar_data_uri

LANGUAGES = ["English", "Hindi", "Hinglish", "Tamil", "Telugu", "Bengali", "Marathi", "Gujarati"]
GOALS = ["Manage stress", "Sleep better", "Build daily routines", "Feel less anxious", "Understand my moods", "Just exploring"]
_COMMON_TZ = ["Asia/Kolkata", "UTC", "Asia/Dubai", "Asia/Singapore", "Europe/London", "America/New_York", "America/Los_Angeles", "Australia/Sydney"]


def _timezones() -> list[str]:
    try:
        from zoneinfo import available_timezones
        z = sorted(available_timezones())
        return _COMMON_TZ + [t for t in z if t not in _COMMON_TZ and "/" in t]
    except Exception:
        return _COMMON_TZ


def _completeness(p: dict, stats: dict) -> tuple[int, str]:
    checks = [("Add a display name", bool(p.get("display_name"))), ("Verify your email", bool(p.get("email_verified"))),
              ("Add a phone number", bool(p.get("phone"))), ("Pick your goals", bool(p.get("goals"))),
              ("Add a profile photo", bool(p.get("avatar_data_uri"))), ("Add a trusted contact", stats.get("contacts", 0) > 0)]
    done = sum(ok for _, ok in checks)
    todo = next((t for t, ok in checks if not ok), "All set")
    return round(100 * done / len(checks)), todo


def _go(mode: str) -> None:                      # callback: no st.rerun() needed
    st.session_state["profile_mode"] = mode


# ------------------------------------------------------------------ overview
def _overview(svc, uid, p, stats, on_add_contact):
    pct, todo = _completeness(p, stats)
    with card("c1"):
        _md('<div class="sj-hero">' + avatar_ring(p["display_name"] or p["full_name"], pct, p.get("avatar_data_uri")) +
            f'<div class="sj-name">{_esc(p["full_name"])}</div>'
            f'<div class="sj-sub">{_esc(p["email"])}</div>'
            f'<div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;justify-content:center">'
            + (badge("Email verified", "ok", True) if p["email_verified"] else badge("Email not verified", "warn"))
            + badge(f'Member since {p["created_at"]:%b %Y}', "plain") + '</div>'
            + progress_bar(f"Profile {pct}% complete", todo if pct < 100 else "Looking good", pct) + '</div>')
        st.button("Edit profile", type="primary", use_container_width=True, on_click=_go, args=("edit",), key="pf_edit")

    with row("stats"):
        c1, c2, c3 = st.columns(3)
        c1.metric("Day streak", stats["streak"])
        c2.metric("Check-ins", stats["checkins"])
        c3.metric("Entries", stats["entries"])

    st.subheader("Personal details")
    with card("c2"):
        kv_rows([("user", "Display name", p["display_name"] or "—", None),
                 ("chat", "Companion name", p["companion_name"], None),
                 ("globe", "Reply language", p["language"], None),
                 ("clock", "Time zone", p["timezone"], None),
                 ("bell", "Daily reminder", f'{p["reminder_time"]:%I:%M %p}'.lstrip("0") + ", by email" if p["reminder_enabled"] else "Off", None)])

    st.subheader("What you're here for")
    chips(p.get("goals", []))

    with card("c3"):
        a, b = st.columns([3, 1], vertical_alignment="center")
        a.markdown(f"**Trusted contacts**  \n<span style='color:#6b5b8a;font-size:13px'>"
                   f"{stats['contacts'] or 'None'} added</span>", unsafe_allow_html=True)
        if b.button("Add" if not stats["contacts"] else "View", key="pf_contacts", use_container_width=True) and on_add_contact:
            on_add_contact()


# ------------------------------------------------------------------ account & security
def _account(svc, uid, p, on_setup_2fa, on_sign_out, on_account_deleted):
    st.subheader("Sign-in & security")
    changed = p.get("password_changed_at")
    days = (datetime.utcnow() - changed).days if changed else None
    with card("c4"):
        kv_rows([("mail", "Email", p["email"], badge("Verified", "ok") if p["email_verified"] else badge("Unverified", "warn")),
                 ("key", "Password", f"Last changed {days} days ago" if days is not None else "Never changed", None),
                 ("shield", "Two-factor authentication", "Authenticator app", badge("On", "ok") if p["two_factor_enabled"] else badge("Off", "warn"))])
        c1, c2 = st.columns(2)
        with c1.popover("Change password", use_container_width=True):
            with st.form("pf_pw", clear_on_submit=True, border=False):
                cur = st.text_input("Current password", type="password")
                new = st.text_input("New password", type="password", help="At least 12 characters.")
                new2 = st.text_input("Confirm new password", type="password")
                if st.form_submit_button("Update password", type="primary", use_container_width=True):
                    if len(new) < 12: st.error("Use at least 12 characters.")
                    elif new != new2: st.error("The two new passwords don't match.")
                    else:
                        err = svc.change_password(uid, cur, new)
                        st.error(err) if err else st.success("Password updated.")
        if not p["two_factor_enabled"] and c2.button("Set up 2FA", use_container_width=True, key="pf_2fa") and on_setup_2fa:
            on_setup_2fa()

    sessions = svc.list_sessions(uid)
    if sessions:
        st.subheader("Signed-in devices")
        with card("c5"):
            for s in sessions:
                a, b = st.columns([3, 1], vertical_alignment="center")
                a.markdown(f"**{_esc(s['label'])}**  \n<span style='color:#6b5b8a;font-size:12.5px'>{_esc(s['place'])} · {_esc(s['last_active'])}</span>", unsafe_allow_html=True)
                if s["current"]: b.markdown(badge("This device", "ok"), unsafe_allow_html=True)
                elif b.button("Sign out", key=f"pf_rev_{s['id']}", use_container_width=True):
                    svc.revoke_session(uid, s["id"]); st.rerun()

    st.subheader("Notifications")
    with card("c6"):
        r = st.toggle("Daily check-in reminder", value=p["reminder_enabled"], key="pf_rem", help="A gentle email if you haven't logged your mood by your reminder time.")
        if r != p["reminder_enabled"]:
            svc.save_profile(uid, {"reminder_enabled": r}); st.rerun()

    st.subheader("Your data")
    with card("c7"):
        st.download_button("Export my data (JSON)", svc.export_data(uid), file_name="sanjeevani-export.json",
                           mime="application/json", use_container_width=True, key="pf_export")
        st.caption("Includes your profile, moods, journal entries and settings. Encrypted entries are decrypted for you only.")

    if on_sign_out:
        st.button("Sign out", use_container_width=True, on_click=on_sign_out, key="pf_signout")
    with st.expander("Delete account"):
        danger_note("This can't be undone", "Permanently removes your mood, journal and chat history.")
        pw = st.text_input("Confirm your password", type="password", key="pf_del_pw")
        ok = st.checkbox("I understand this cannot be undone", key="pf_del_ok")
        if st.button("Delete my account", disabled=not (pw and ok), key="pf_del_btn"):
            err = svc.delete_account(uid, pw)
            if err: st.error(err)
            elif on_account_deleted: on_account_deleted()
    st.caption("Sanjeevani · version 1.0")


# ------------------------------------------------------------------ edit
def _edit(svc, uid, p):
    with st.form("pf_edit_form"):
        _md('<div class="sj-hero">' + avatar_ring(p["display_name"] or p["full_name"], 100, p.get("avatar_data_uri"), 104) + '</div>')
        photo = st.file_uploader("Profile photo", type=["png", "jpg", "jpeg", "webp"], help="Square photos look best. Resized and stored privately.")
        remove = st.checkbox("Remove current photo", value=False) if p.get("avatar_data_uri") else False

        st.markdown("##### About you")
        full = st.text_input("Full name", value=p["full_name"], max_chars=80)
        disp = st.text_input("What should we call you?", value=p["display_name"], max_chars=30, help="Shown in greetings and in the menu.")
        st.text_input("Email", value=p["email"], disabled=True, help="Verified. To change it, contact support.")
        phone = st.text_input("Phone (optional)", value=p["phone"], placeholder="+91 …", max_chars=20)

        st.markdown("##### Preferences")
        comp = st.text_input("Companion name", value=p["companion_name"], max_chars=24)
        lang = st.selectbox("Reply language", LANGUAGES, index=LANGUAGES.index(p["language"]) if p["language"] in LANGUAGES else 0)
        tzs = _timezones()
        tz = st.selectbox("Time zone", tzs, index=tzs.index(p["timezone"]) if p["timezone"] in tzs else 0)
        goals = st.multiselect("What are you here for?", GOALS, default=[g for g in p.get("goals", []) if g in GOALS])
        bio = st.text_area("About you (optional · private)", value=p.get("bio", ""), max_chars=500, placeholder="Anything you'd like your companion to know.")
        c1, c2 = st.columns([1, 1])
        rem_on = c1.toggle("Daily reminder", value=p["reminder_enabled"])
        rem_t = c2.time_input("Reminder time", value=p["reminder_time"], step=900, disabled=False)

        save = st.form_submit_button("Save changes", type="primary", use_container_width=True)
        cancel = st.form_submit_button("Cancel", use_container_width=True)
    st.caption("Only you can see your profile.")

    if cancel:
        _go("view"); st.rerun()
    if save:
        errs = []
        if not full.strip(): errs.append("Full name is required.")
        if not disp.strip(): errs.append("Add the name you'd like to be called.")
        if phone and not re.fullmatch(r"\+?[0-9 ()\-]{7,20}", phone.strip()): errs.append("Phone number looks incomplete.")
        if errs:
            for e in errs: st.error(e)
            return
        changes = {"full_name": full.strip(), "display_name": disp.strip(), "phone": phone.strip(),
                   "companion_name": comp.strip() or "Papa", "language": lang, "timezone": tz, "goals": goals,
                   "bio": bio.strip(), "reminder_enabled": rem_on, "reminder_time": rem_t}
        if photo is not None:
            try: changes["avatar_data_uri"] = make_avatar_data_uri(photo.getvalue())
            except Exception: st.error("That image couldn't be read. Try a JPG or PNG."); return
        elif remove: changes["avatar_data_uri"] = None
        svc.save_profile(uid, changes)
        st.session_state["profile_flash"] = "Profile saved."
        _go("view"); st.rerun()


# ------------------------------------------------------------------ entry point
def _esc(s) -> str:
    import html; return html.escape(str(s or ""))


def render_profile_page(svc: ProfileService, user_id, *, on_add_contact: Callable | None = None,
                        on_setup_2fa: Callable | None = None, on_sign_out: Callable | None = None,
                        on_account_deleted: Callable | None = None) -> None:
    mode = st.session_state.get("profile_mode", "view")
    p, stats = svc.get_profile(user_id), svc.get_stats(user_id)
    safety_banner()
    st.title("Edit profile" if mode == "edit" else "Profile")
    if (flash := st.session_state.pop("profile_flash", None)): st.success(flash)
    if mode == "edit":
        _edit(svc, user_id, p); return
    t1, t2 = st.tabs(["Overview", "Account & security"])
    with t1: _overview(svc, user_id, p, stats, on_add_contact)
    with t2: _account(svc, user_id, p, on_setup_2fa, on_sign_out, on_account_deleted)
