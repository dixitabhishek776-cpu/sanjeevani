"""
ui_theme.py  -  Sanjeevani visual system (violet theme, same palette as before).

Usage (once per run, at the very top of app.py after st.set_page_config):
    from ui_theme import inject_theme
    inject_theme()

Everything here is CSS + small HTML helpers rendered with st.markdown(..., unsafe_allow_html=True).
No colours were changed: #7c3aed / #6d28d9 / #805DE0 / #41336E / #6b5b8a / #F7F4FF / #F0EBFF->#FFF2FA.
Streamlit's alert colours (yellow / red / green) are intentionally left alone.
"""
from __future__ import annotations
import html
import streamlit as st

# ---------------------------------------------------------------- tokens
PRIMARY, PRIMARY_DARK = "#7c3aed", "#6d28d9"
LABEL, INK, MUTE = "#805DE0", "#41336E", "#6b5b8a"
TINT, PAGE = "#F7F4FF", "#FBF9FF"
RING, RING_BG, SCORE = "#7956E8", "#ECE8F8", "#292351"

# ---------------------------------------------------------------- icons (24x24, stroke)
ICONS = {
    "phone": '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 20c1-4 4-6 8-6s7 2 8 6"/>',
    "chat": '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "bell": '<path d="M6 17V11a6 6 0 0 1 12 0v6l1.5 2h-15zM10 21h4"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "key": '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M16 7l3 3"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z"/><path d="M9 12l2 2 4-4"/>',
    "device": '<rect x="7" y="2.5" width="10" height="19" rx="2.5"/><path d="M11 18h2"/>',
    "lock": '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "check": '<path d="M5 12l5 5 9-10"/>',
    "heart": '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
    "camera": '<path d="M4 8h3l1.5-2h7L17 8h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
}


def icon(name: str, size: int = 20, color: str = "currentColor") -> str:
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')


# ---------------------------------------------------------------- global CSS
_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Lora:wght@500;600&display=swap');
:root {{
  --p:{PRIMARY}; --pd:{PRIMARY_DARK}; --label:{LABEL}; --ink:{INK}; --mute:{MUTE};
  --tint:{TINT}; --page:{PAGE}; --bd:rgba(124,58,237,.12); --bd2:rgba(124,58,237,.4);
  --ring:{RING}; --ringbg:{RING_BG}; --score:{SCORE};
}}
html, body, [class*="css"], .stApp {{ font-family:'Inter',system-ui,sans-serif; color:var(--ink); }}
.stApp {{
  background:
    radial-gradient(520px 300px at 88% -60px,#F0EBFF 0%,rgba(240,235,255,0) 70%),
    radial-gradient(460px 280px at -10% 100%,#FFF2FA 0%,rgba(255,242,250,0) 70%),
    var(--page);
}}
.block-container {{ max-width:720px; padding-top:4rem; padding-bottom:5rem; }}
[data-testid="stHeader"] {{ background:transparent; }}
h1,h2,h3 {{ font-family:'Lora',Georgia,serif !important; color:var(--ink) !important; letter-spacing:-.01em; font-weight:600 !important; }}
h1 {{ font-size:1.9rem !important; }} h2 {{ font-size:1.3rem !important; }} h3 {{ font-size:1.1rem !important; }}
p, label, .stMarkdown {{ color:var(--ink); }}
[data-testid="stCaptionContainer"], .stCaption {{ color:var(--mute) !important; }}

/* ---- buttons */
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {{
  min-height:48px; border-radius:14px; font-weight:600; font-size:15px;
  border:1.5px solid var(--bd2); background:transparent; color:var(--p); transition:all .15s ease;
}}
.stButton>button p, .stFormSubmitButton>button p, .stDownloadButton>button p {{ color:inherit !important; font-weight:600; }}
.stButton>button[kind="primary"] *, .stFormSubmitButton>button[kind="primaryFormSubmit"] *, .stFormSubmitButton>button[kind="primary"] * {{ color:#fff !important; }}
.stButton>button:hover, .stFormSubmitButton>button:hover, .stDownloadButton>button:hover {{
  border-color:var(--p); background:var(--tint); color:var(--pd);
}}
.stButton>button[kind="primary"], .stFormSubmitButton>button[kind="primary"], .stFormSubmitButton>button[kind="primaryFormSubmit"] {{
  background:linear-gradient(135deg,var(--p),var(--pd)); color:#fff; border:none;
  box-shadow:0 10px 22px -10px rgba(109,40,217,.7);
}}
.stButton>button[kind="primary"]:hover, .stFormSubmitButton>button[kind="primary"]:hover, .stFormSubmitButton>button[kind="primaryFormSubmit"]:hover {{
  background:linear-gradient(135deg,var(--pd),var(--pd)); color:#fff;
}}

/* ---- inputs */
.stTextInput input, .stTextArea textarea, .stNumberInput input, .stTimeInput input,
div[data-baseweb="select"]>div, .stDateInput input {{
  border-radius:12px !important; background:#fff !important; color:var(--ink) !important;
  border:1.5px solid rgba(124,58,237,.18) !important; min-height:48px;
}}
.stTextArea textarea {{ min-height:96px; }}
.stTextInput input:focus, .stTextArea textarea:focus, div[data-baseweb="select"]>div:focus-within {{
  border-color:var(--p) !important; box-shadow:0 0 0 4px rgba(124,58,237,.12) !important;
}}
.stTextInput input:disabled {{ background:#F4F0FB !important; color:var(--mute) !important; -webkit-text-fill-color:var(--mute); }}
.stTextInput label, .stTextArea label, .stSelectbox label, .stTimeInput label, .stMultiSelect label,
.stToggle label, .stCheckbox label {{ font-weight:600; color:var(--ink); font-size:13.5px; }}
span[data-baseweb="tag"] {{ background:var(--tint) !important; color:var(--p) !important; border:1px solid var(--bd2); border-radius:99px !important; }}

/* ---- tabs */
.stTabs [data-baseweb="tab-list"] {{ gap:22px; border-bottom:1.5px solid var(--bd); }}
.stTabs [data-baseweb="tab"] {{ color:var(--mute); font-weight:500; padding:10px 0; background:transparent; }}
.stTabs [aria-selected="true"] {{ color:var(--p) !important; font-weight:600; }}
.stTabs [data-baseweb="tab-highlight"] {{ background:var(--p) !important; height:3px; border-radius:3px; }}

/* ---- cards: use ui_theme.card("name") -> st.container(key="sjcard_name"). Forms + expanders get the same look. */
[class*="st-key-sjcard"], [data-testid="stForm"], [data-testid="stExpander"] {{
  background:linear-gradient(180deg,var(--tint),#fff); border:1px solid var(--bd) !important;
  border-radius:20px !important; padding:6px 18px 14px; box-shadow:0 1px 2px rgba(65,51,110,.04),0 12px 28px -16px rgba(124,58,237,.28);
}}
[data-testid="stExpander"] {{ padding:0 4px; }} [data-testid="stExpander"] details {{ border:none; }}
[data-testid="stForm"] {{ padding:18px; }}
/* keep column rows side by side on phones (Streamlit stacks them by default) */
[class*="st-key-sjrow"] [data-testid="stHorizontalBlock"], [class*="st-key-sjcard"] [data-testid="stHorizontalBlock"] {{ flex-wrap:nowrap !important; gap:.75rem; }}
[class*="st-key-sjrow"] [data-testid="stColumn"], [class*="st-key-sjcard"] [data-testid="stColumn"] {{ min-width:0 !important; }}

/* ---- metrics */
[data-testid="stMetric"] {{
  background:linear-gradient(180deg,var(--tint),#fff); border:1px solid var(--bd);
  border-radius:20px; padding:14px 16px; box-shadow:0 12px 28px -16px rgba(124,58,237,.28);
}}
[data-testid="stMetricLabel"] p {{ color:var(--label) !important; font-weight:600; font-size:12px !important; }}
[data-testid="stMetricValue"] {{ font-family:'Lora',serif; color:var(--ink); font-weight:600; }}

/* ---- toggles, progress, chat input, sidebar */
[data-testid="stProgress"] > div > div > div {{ background:var(--ringbg) !important; height:8px; border-radius:8px; }}
[data-testid="stProgress"] > div > div > div > div {{ background:linear-gradient(90deg,#8B5CF6,var(--p)) !important; border-radius:8px; }}
[data-testid="stChatInput"] {{ border-radius:26px; border:1.5px solid rgba(124,58,237,.2); background:#fff; }}
[data-testid="stSidebar"] {{ background:var(--page); border-right:1px solid var(--bd); }}
[data-testid="stSidebar"] .stButton>button {{ justify-content:flex-start; border-color:transparent; color:var(--mute); font-weight:500; }}
[data-testid="stSidebar"] .stButton>button:hover {{ background:#EFE8FF; color:var(--p); }}
hr {{ border-color:var(--bd) !important; }}

/* ---- custom components (html helpers below) */
.sj-safe {{ background:#fff; border:1px solid var(--bd); border-left:4px solid var(--p); border-radius:14px;
  padding:12px 14px; font-size:12.5px; line-height:1.5; color:var(--mute); margin-bottom:12px; }}
.sj-safe b {{ color:var(--ink); font-weight:600; }}
.sj-pills {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; }}
.sj-pill {{ display:inline-flex; align-items:center; gap:6px; height:28px; padding:0 12px; border-radius:99px;
  background:var(--tint); border:1px solid var(--bd); color:var(--p) !important; font-weight:600; font-size:12px; text-decoration:none !important; }}
.sj-badge {{ display:inline-flex; align-items:center; gap:6px; height:28px; padding:0 12px; border-radius:99px; font-size:12px; font-weight:600; }}
.sj-badge.ok {{ background:#E6F6EA; border:1px solid #B7E1C2; color:#1b6b35; }}
.sj-badge.warn {{ background:#FFF4D6; border:1px solid #F2D98B; color:#7a5a00; }}
.sj-badge.plain {{ background:var(--tint); border:1px solid var(--bd); color:var(--mute); font-weight:500; }}
.sj-chip {{ display:inline-flex; align-items:center; height:34px; padding:0 14px; border-radius:99px; background:var(--tint);
  border:1.5px solid var(--p); color:var(--p); font-size:13px; font-weight:600; margin:0 8px 8px 0; }}
.sj-kv {{ display:flex; align-items:center; gap:14px; padding:13px 0; border-bottom:1px solid var(--bd); }}
.sj-kv:last-child {{ border-bottom:0; }}
.sj-kv .ic {{ color:var(--p); flex:none; display:grid; place-items:center; }}
.sj-kv .k {{ font-size:12px; color:var(--label); font-weight:600; }}
.sj-kv .v {{ font-size:14.5px; color:var(--ink); font-weight:500; margin-top:2px; }}
.sj-kv .grow {{ flex:1; min-width:0; }}
.sj-hero {{ display:flex; flex-direction:column; align-items:center; text-align:center; padding:8px 0 4px; }}
.sj-avatar {{ position:relative; width:132px; height:132px; display:grid; place-items:center; }}
.sj-avatar svg.ring {{ position:absolute; inset:0; }}
.sj-avatar .face {{ width:100px; height:100px; border-radius:50%; overflow:hidden; display:grid; place-items:center;
  background:linear-gradient(135deg,#8B5CF6,#6752D7); color:#fff; font-family:'Lora',serif; font-size:42px; font-weight:600;
  box-shadow:0 14px 28px -10px rgba(103,82,215,.6); }}
.sj-avatar .face img {{ width:100%; height:100%; object-fit:cover; }}
.sj-name {{ font-family:'Lora',serif; font-size:26px; font-weight:600; color:var(--ink); margin-top:14px; }}
.sj-sub {{ font-size:14px; color:var(--mute); margin-top:4px; }}
.sj-prog-row {{ display:flex; justify-content:space-between; font-size:12px; font-weight:600; color:var(--label); width:100%; margin:16px 0 8px; }}
.sj-prog-row span:last-child {{ color:var(--mute); font-weight:500; }}
.sj-prog {{ width:100%; height:8px; border-radius:8px; background:var(--ringbg); overflow:hidden; }}
.sj-prog i {{ display:block; height:100%; border-radius:8px; background:linear-gradient(90deg,#8B5CF6,var(--p)); }}
.sj-danger {{ background:#FFF7F7; border:1px solid #F0C4C4; border-radius:16px; padding:14px 16px; }}
.sj-danger b {{ color:#a02525; }} .sj-danger span {{ color:var(--mute); font-size:12.5px; line-height:1.45; display:block; margin-top:2px; }}
</style>
"""


def inject_theme() -> None:
    """Call once per script run, right after st.set_page_config()."""
    st.markdown(_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- html helpers
def _md(s: str) -> None:
    st.markdown(s, unsafe_allow_html=True)


def safety_banner(show_pills: bool = True) -> None:
    pills = (f'<div class="sj-pills"><a class="sj-pill" href="tel:112">{icon("phone",14)}Call 112</a>'
             f'<a class="sj-pill" href="tel:14416">{icon("phone",14)}Tele-MANAS 14416</a></div>') if show_pills else ""
    _md(f'<div class="sj-safe"><b>AI-guided support, not a substitute for therapy or emergency care.</b>{pills}</div>')


def badge(text: str, kind: str = "plain", with_check: bool = False) -> str:
    chk = icon("check", 13) if with_check else ""
    return f'<span class="sj-badge {kind}">{chk}{html.escape(text)}</span>'


def chips(items: list[str]) -> None:
    _md("".join(f'<span class="sj-chip">{html.escape(i)}</span>' for i in items) or
        '<span class="sj-sub">Nothing selected yet.</span>')


def kv_rows(rows: list[tuple[str, str, str, str | None]]) -> None:
    """rows = [(icon_name, label, value, right_html_or_None), ...]  - value is escaped, right_html is trusted."""
    out = []
    for ic, k, v, right in rows:
        out.append(f'<div class="sj-kv"><span class="ic">{icon(ic)}</span>'
                   f'<div class="grow"><div class="k">{html.escape(k)}</div><div class="v">{html.escape(v)}</div></div>'
                   f'{right or ""}</div>')
    _md("".join(out))


def avatar_ring(initial: str, pct: int, photo_data_uri: str | None = None, size: int = 132) -> str:
    c = 2 * 3.14159 * 60
    face = (f'<img src="{photo_data_uri}" alt="profile photo">' if photo_data_uri else html.escape(initial[:1].upper() or "?"))
    return (f'<div class="sj-avatar" style="width:{size}px;height:{size}px">'
            f'<svg class="ring" viewBox="0 0 132 132"><circle cx="66" cy="66" r="60" fill="none" stroke="{RING_BG}" stroke-width="7"/>'
            f'<circle cx="66" cy="66" r="60" fill="none" stroke="{RING}" stroke-width="7" stroke-linecap="round" '
            f'stroke-dasharray="{c*pct/100:.1f} {c:.1f}" transform="rotate(-90 66 66)"/></svg>'
            f'<div class="face">{face}</div></div>')


def progress_bar(label: str, hint: str, pct: int) -> str:
    return (f'<div class="sj-prog-row"><span>{html.escape(label)}</span><span>{html.escape(hint)}</span></div>'
            f'<div class="sj-prog"><i style="width:{pct}%"></i></div>')


def danger_note(title: str, body: str) -> None:
    _md(f'<div class="sj-danger"><b>{html.escape(title)}</b><span>{html.escape(body)}</span></div>')


def card(name: str):
    """A styled card. Use as:  with card("details"): ...   (name must be unique on the page)."""
    return st.container(key=f"sjcard_{name}")


def row(name: str):
    """Wrapper that keeps st.columns side by side on mobile:  with row("stats"): a, b = st.columns(2)"""
    return st.container(key=f"sjrow_{name}")
