from pathlib import Path
import base64
import mimetypes
from urllib.parse import quote

import streamlit as st


DOCU_PURPLE = "#7462E8"
DOCU_PURPLE_DARK = "#5E4FD0"
DOCU_PURPLE_SOFT = "#F1EFFE"
DOCU_BG = "#FFFFFF"
DOCU_PANEL = "#FFFFFF"
DOCU_TEXT = "#1D1D1F"
DOCU_MUTED = "#6B6A75"
DOCU_BORDER = "#ECEBF2"
DOCU_GREEN = "#22B14C"


# ==================================================
# INLINE ICONS (stroke icons, inherit currentColor)
# ==================================================

# st.html sanitizes inline <svg> and <img>, so icons are drawn by CSS:
# each icon is an empty <span class="docu-icon ic-NAME"> whose background
# is a data-URI SVG defined in THEME_CSS.

_ICON_SVGS: dict[str, tuple[str, str, str]] = {}


def _register(
    name: str,
    body: str,
    color: str = "#6B6A75",
    view_box: str = "0 0 24 24",
    stroke: float = 1.8,
) -> str:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" '
        f'fill="none" stroke="{color}" stroke-width="{stroke}" '
        'stroke-linecap="round" stroke-linejoin="round">'
        f'{body}</svg>'
    )
    _ICON_SVGS[name] = svg
    return f'<span class="docu-icon ic-{name}" aria-hidden="true"></span>'


def _icon_css() -> str:
    return "\n".join(
        f'.ic-{name} {{ background-image: url("data:image/svg+xml,'
        f'{quote(svg)}"); }}'
        for name, svg in _ICON_SVGS.items()
    )


ICON_FILE = _register(
    "file",
    '<path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8z"/>'
    '<path d="M14 3v5h5"/>',
    color="#E5484D",
)

ICON_LOCK = _register(
    "lock",
    '<rect x="5" y="11" width="14" height="10" rx="2"/>'
    '<path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    color="#22B14C",
)

# Used only as a CSS background for Streamlit's sidebar toggle buttons.
_register(
    "sidebar",
    '<rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/>'
    '<line x1="9.5" y1="4.5" x2="9.5" y2="19.5"/>',
    color="#6B6A75",
)

LOGO_SVG = _register(
    "logo",
    '<path d="M16 2H5a2 2 0 0 0-2 2v22a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9z"/>'
    '<path d="M16 2v7h7"/>'
    '<path d="M9 16.5c.35 2.1 1.1 2.85 3.2 3.2-2.1.35-2.85 1.1-3.2 3.2'
    '-.35-2.1-1.1-2.85-3.2-3.2 2.1-.35 2.85-1.1 3.2-3.2z" '
    'fill="#1D1D1F" stroke-width="1"/>',
    color="#1D1D1F",
    view_box="0 0 26 30",
).replace("docu-icon ", "docu-brand-mark ")


def image_data_uri(
    path: Path,
) -> str | None:
    """Return a data URI for a non-empty image file, else None."""

    if (
        not path.exists()
        or not path.is_file()
        or path.stat().st_size == 0
    ):
        return None

    mime_type, _ = mimetypes.guess_type(path.name)

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")

    return f"data:{mime_type or 'image/png'};base64,{encoded}"


# ==================================================
# THEME
# ==================================================

_UPLOAD_ARROW = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "width='18' height='18' viewBox='0 0 24 24' fill='none' "
    "stroke='%233B6FE0' stroke-width='2' stroke-linecap='round' "
    "stroke-linejoin='round'%3E%3Cpath d='M12 15V4'/%3E"
    "%3Cpath d='m7 9 5-5 5 5'/%3E%3Cpath d='M5 15v4h14v-4'/%3E%3C/svg%3E"
)

THEME_CSS = """
:root {
    --docu-purple: #7462E8;
    --docu-purple-dark: #5E4FD0;
    --docu-purple-ink: #6C5AE4;
    --docu-purple-soft: #F1EFFE;
    --docu-text: #1D1D1F;
    --docu-text-2: #4A4953;
    --docu-muted: #6B6A75;
    --docu-faint: #9A99A3;
    --docu-border: #ECEBF2;
    --docu-sidebar: #F7F6FE;
    --docu-preview: #F8F8FB;
    --docu-green: #22B14C;
    --docu-sidebar-icon: url("__SIDEBAR_ICON__");
    --docu-blue: #3B5BDB;
    --docu-blue-soft: #EDF0FD;
}

html, body, [class*="css"], .stApp {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", Inter,
        "Segoe UI", system-ui, sans-serif;
}

.stApp {
    background: #FFFFFF;
    color: var(--docu-text);
}

.docu-icon {
    flex: none;
    display: inline-block;
    width: 16px;
    height: 16px;
    background: center / contain no-repeat;
    vertical-align: middle;
}

.docu-brand-mark {
    flex: none;
    width: 23px;
    height: 27px;
    background: center / contain no-repeat;
}

/* ---------- chrome ---------- */

header[data-testid="stHeader"] {
    background: transparent;
    height: 0;
}

[data-testid="stToolbarActions"],
[data-testid="stAppDeployButton"],
[data-testid="stMainMenu"],
[data-testid="stDecoration"],
#MainMenu,
footer {
    display: none !important;
}

.block-container,
[data-testid="stMainBlockContainer"] {
    max-width: none;
    padding: 0 !important;
}

/* ---------- sidebar ---------- */

[data-testid="stSidebar"] {
    background: var(--docu-sidebar);
    border-right: 1px solid var(--docu-border);
}

/* Fixed width only while open, so collapsing really hides the sidebar. */
[data-testid="stSidebar"][aria-expanded="true"] {
    min-width: 222px !important;
    max-width: 222px !important;
}

/* Collapsed: nothing of the sidebar may leak out; the floating expand
   button is the only affordance left. */
[data-testid="stSidebar"][aria-expanded="false"] {
    overflow: hidden;
    border-right: 0;
}

[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarContent"] {
    visibility: hidden;
}

[data-testid="stSidebarHeader"] {
    position: absolute;
    top: 0;
    right: 0;
    height: auto;
    padding: 17px 12px 0 0;
    z-index: 2;
}

[data-testid="stSidebarHeader"] [data-testid="stLogoSpacer"] { display: none; }

/* Sidebar toggle: the same panel icon whether open (inside the sidebar,
   level with the logo) or closed (a small floating button, top-left). */
[data-testid="stSidebarCollapseButton"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}

[data-testid="stSidebarCollapseButton"] button,
[data-testid="stExpandSidebarButton"] {
    width: 30px !important;
    height: 30px !important;
    padding: 0 !important;
    border-radius: 8px !important;
    background: transparent center / 17px no-repeat !important;
    transition: background-color .15s ease;
}

[data-testid="stSidebarCollapseButton"] button,
[data-testid="stExpandSidebarButton"] {
    background-image: var(--docu-sidebar-icon) !important;
}

[data-testid="stSidebarCollapseButton"] button:hover,
[data-testid="stExpandSidebarButton"]:hover {
    background-color: #ECEAF6 !important;
}

[data-testid="stSidebarCollapseButton"] button:focus-visible,
[data-testid="stExpandSidebarButton"]:focus-visible {
    outline: 2px solid var(--docu-purple);
    outline-offset: 2px;
}

[data-testid="stSidebarCollapseButton"] button > span,
[data-testid="stExpandSidebarButton"] > span {
    display: none !important;
}

[data-testid="stExpandSidebarButton"] {
    position: fixed !important;
    top: 16px;
    left: 16px;
    z-index: 1000;
    border: 1px solid var(--docu-border) !important;
    background-color: #FFFFFF !important;
    box-shadow: 0 2px 8px rgba(29, 29, 31, 0.06);
}

[data-testid="stSidebarUserContent"] {
    padding: 18px 15px 16px 15px !important;
    height: 100vh;
}

[data-testid="stSidebarUserContent"] > div,
[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] {
    height: 100%;
}

[data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"] {
    gap: 0;
}

.stElementContainer:has(.sidebar-footer) { margin-top: auto; }

.docu-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 2px 4px 22px 4px;
}

.docu-brand-logo { flex: none; width: 28px; height: 28px; background: center / contain no-repeat; }

.docu-brand-name {
    color: var(--docu-text);
    font-size: 19px;
    font-weight: 700;
    letter-spacing: -0.02em;
}

.st-key-new_chat button {
    width: 100%;
    min-height: 41px;
    border: 0 !important;
    border-radius: 9px !important;
    color: #FFFFFF !important;
    background: var(--docu-purple) !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    box-shadow: 0 6px 16px rgba(116, 98, 232, 0.22);
    transition: background .15s ease;
}

.st-key-new_chat button:hover { background: var(--docu-purple-dark) !important; }
.st-key-new_chat button p { font-size: 13.5px !important; font-weight: 600 !important; }

.sidebar-section-label {
    margin: 26px 0 10px 0;
    color: var(--docu-muted);
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}


.sidebar-empty {
    padding: 4px 9px;
    color: var(--docu-faint);
    font-size: 12px;
    line-height: 1.5;
}

.st-key-sidebar_docs [data-testid="stVerticalBlock"] { gap: 3px; }

.st-key-sidebar_docs button {
    width: 100%;
    justify-content: flex-start !important;
    height: 42px;
    padding: 0 9px !important;
    border: 0 !important;
    border-radius: 8px !important;
    background: transparent !important;
    color: var(--docu-text-2) !important;
    box-shadow: none !important;
}

.st-key-sidebar_docs button:hover { background: #EFEEF8 !important; }

.st-key-sidebar_docs button p {
    overflow: hidden;
    font-size: 12.5px !important;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.st-key-sidebar_docs button [data-testid="stIconMaterial"] {
    color: #E5484D;
    font-size: 17px;
    margin-right: 6px;
}

.st-key-sidebar_docs [class*="st-key-doc_active_"] button {
    background: var(--docu-blue-soft) !important;
    color: var(--docu-blue) !important;
}

.sidebar-footer {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 12px 0 0 0;
}

.sidebar-avatar {
    width: 30px;
    height: 30px;
    border-radius: 999px;
    background: #E3DEFB;
    flex: none;
}

.sidebar-footer-title {
    color: var(--docu-text);
    font-size: 11.5px;
    font-weight: 600;
}

.sidebar-footer-meta {
    margin-top: 1px;
    color: var(--docu-muted);
    font-size: 9.5px;
}

/* ---------- upload / empty state ---------- */

.upload-shell {
    max-width: 600px;
    margin: 0 auto;
    padding: clamp(56px, 18vh, 160px) 24px 0 24px;
    text-align: center;
}

.upload-title {
    margin: 0;
    padding: 0;
    color: var(--docu-text);
    font-size: 30px;
    font-weight: 700;
    line-height: 1.2;
    letter-spacing: -0.02em;
}

.upload-subtitle {
    margin-top: 12px;
    color: var(--docu-muted);
    font-size: 14px;
}

[data-testid="stFileUploader"] {
    width: 600px !important;
    max-width: calc(100vw - 2rem);
    margin: 16px auto 0 auto;
}

[data-testid="stFileUploaderDropzone"] {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0;
    min-height: 298px;
    padding: 44px 24px 50px 24px !important;
    border: 1.5px dashed #BFD2F4 !important;
    border-radius: 16px !important;
    background: #FAFAFE !important;
    text-align: center;
}

[data-testid="stFileUploaderDropzone"]::before {
    content: "";
    order: 0;
    width: 54px;
    height: 54px;
    margin-bottom: 22px;
    border-radius: 999px;
    background: #EEECFD url("__UPLOAD_ARROW__") center / 18px no-repeat;
}

[data-testid="stFileUploaderDropzoneInstructions"] {
    order: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    margin: 0 !important;
}

[data-testid="stFileUploaderDropzoneInstructions"] > div { display: none; }

[data-testid="stFileUploaderDropzoneInstructions"]::before {
    content: "Drag and drop your PDF here";
    color: var(--docu-text);
    font-size: 17px;
    font-weight: 600;
}

[data-testid="stFileUploaderDropzoneInstructions"]::after {
    content: "or choose a file from your computer";
    margin-top: 14px;
    color: var(--docu-muted);
    font-size: 12.5px;
}

[data-testid="stFileUploaderDropzone"] > span {
    order: 2;
    margin-top: 14px;
}

[data-testid="stFileUploaderDropzone"]::after {
    content: "PDF files · Up to 50 MB · Processed locally on your device";
    order: 3;
    margin-top: 16px;
    color: var(--docu-muted);
    font-size: 10.5px;
}

[data-testid="stFileUploaderDropzone"] button {
    display: inline-flex !important;
    align-items: center;
    justify-content: center;
    min-width: 120px;
    height: 41px;
    min-height: 41px !important;
    padding: 0 22px !important;
    border: 0 !important;
    border-radius: 9px !important;
    background: var(--docu-purple) !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 12px rgba(116, 98, 232, 0.22);
    transition: background-color .15s ease, box-shadow .15s ease;
}

[data-testid="stFileUploaderDropzone"] button:hover {
    background: var(--docu-purple-dark) !important;
    box-shadow: 0 6px 16px rgba(116, 98, 232, 0.28);
}

[data-testid="stFileUploaderDropzone"] button:active { transform: translateY(1px); }

[data-testid="stFileUploaderDropzone"] button:focus-visible {
    outline: 2px solid var(--docu-purple) !important;
    outline-offset: 3px;
}

/* Streamlit renders [icon-slot][label]; hide the slot entirely, not just
   the glyph, otherwise the label is pushed off-centre by the slot + gap. */
[data-testid="stFileUploaderDropzone"] button > div,
[data-testid="stFileUploaderDropzone"] button > div > span {
    display: flex !important;
    align-items: center;
    justify-content: center;
    gap: 0 !important;
    margin: 0 !important;
}

[data-testid="stFileUploaderDropzone"] button span:has(> [data-testid="stIconMaterial"]) {
    display: none !important;
}

[data-testid="stFileUploaderDropzone"] button [data-testid="stMarkdownContainer"],
[data-testid="stFileUploaderDropzone"] button p {
    margin: 0 !important;
    font-size: 0 !important;
    line-height: 1 !important;
}

[data-testid="stFileUploaderDropzone"] button p::after {
    content: "Choose PDF";
    font-size: 14px;
    font-weight: 600;
    line-height: 1;
    letter-spacing: 0.005em;
}

.upload-after {
    text-align: center;
}

.privacy-note {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-top: 12px;
    color: var(--docu-green);
    font-size: 12px;
}

.suggestion-title {
    margin-top: 18px;
    color: var(--docu-text-2);
    font-size: 11.5px;
}

.suggestion-row {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 10px;
    margin-top: 20px;
}

.suggestion-chip {
    padding: 10px 13px;
    border: 1px solid #DEDDE6;
    border-radius: 8px;
    background: #FFFFFF;
    color: var(--docu-text-2);
    font-size: 11.5px;
    cursor: default;
}

.st-key-intro_suggestions {
    flex-wrap: wrap !important;
    gap: 10px !important;
    margin-top: 22px;
}

.st-key-intro_suggestions button {
    min-height: 0 !important;
    padding: 9px 13px !important;
    border: 1px solid #DEDDE6 !important;
    border-radius: 8px !important;
    background: #FFFFFF !important;
    color: var(--docu-text-2) !important;
    box-shadow: none !important;
}

.st-key-intro_suggestions button p { font-size: 12px !important; }

.st-key-intro_suggestions button:hover {
    border-color: #CFC8F4 !important;
    background: var(--docu-purple-soft) !important;
    color: var(--docu-purple-ink) !important;
}

/* ---------- document chat ---------- */

[data-testid="stHorizontalBlock"]:has(.st-key-chat_pane) { gap: 0 !important; }

[data-testid="stLayoutWrapper"]:has(> .st-key-chat_pane),
[data-testid="stLayoutWrapper"]:has(> .st-key-preview_panel) {
    height: 100vh;
}

.st-key-chat_pane {
    height: 100%;
    gap: 0 !important;
    flex-wrap: nowrap !important;
}

.chat-page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 20px 32px 22px 32px;
    border-bottom: 1px solid var(--docu-border);
    transition: padding-left .2s ease;
}

.stApp:has([data-testid="stSidebar"][aria-expanded="false"]) .chat-page-header {
    padding-left: 64px;
}

.chat-page-heading { min-width: 0; }

.chat-page-title {
    color: var(--docu-text);
    font-size: 19px;
    font-weight: 500;
}

.chat-page-meta {
    display: flex;
    min-width: 0;
    margin-top: 6px;
    color: var(--docu-muted);
    font-size: 12.5px;
    white-space: nowrap;
}

.chat-page-file {
    overflow: hidden;
    text-overflow: ellipsis;
}

.chat-page-pages { flex: none; }

[data-testid="stLayoutWrapper"]:has(> .st-key-chat_scroll) {
    flex: 1 1 auto;
    min-height: 0;
}

.st-key-chat_scroll {
    height: 100%;
    min-height: 0;
    overflow-y: auto;
    padding: 28px 38px 24px 38px;
    gap: 0 !important;
}

.chat-kicker { min-width: 0; white-space: nowrap; }

.chat-kicker-file {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
}

.chat-kicker,
.assistant-meta {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--docu-purple-ink);
    font-size: 12.5px;
    font-weight: 500;
}

.kicker-dot {
    flex: none;
    width: 9px;
    height: 9px;
    border-radius: 999px;
    background: var(--docu-purple);
    margin-right: 4px;
}

.chat-intro-title {
    margin-top: 12px;
    color: var(--docu-text);
    font-size: 22px;
    font-weight: 500;
    letter-spacing: -0.01em;
}

.chat-intro-subtitle {
    margin-top: 14px;
    color: var(--docu-muted);
    font-size: 14.5px;
}

.user-bubble {
    width: fit-content;
    max-width: 78%;
    margin: 28px 0 32px auto;
    padding: 12px 16px;
    border-radius: 16px;
    background: #EFEDFD;
    color: var(--docu-text);
    font-size: 14.5px;
    line-height: 1.45;
}

.assistant-meta { margin: 4px 0 14px 0; }

[class*="st-key-answer_"] [data-testid="stMarkdownContainer"] {
    color: var(--docu-text-2);
    font-size: 14.5px;
    line-height: 1.6;
}

[class*="st-key-answer_"] [data-testid="stMarkdownContainer"] p,
[class*="st-key-answer_"] [data-testid="stMarkdownContainer"] li {
    font-size: 14.5px;
}

[class*="st-key-answer_"] [data-testid="stMarkdownContainer"] strong,
[class*="st-key-answer_"] [data-testid="stMarkdownContainer"] h1,
[class*="st-key-answer_"] [data-testid="stMarkdownContainer"] h2,
[class*="st-key-answer_"] [data-testid="stMarkdownContainer"] h3 {
    color: var(--docu-text);
    font-weight: 600;
}

[class*="st-key-answer_"] [data-testid="stMarkdownContainer"] h1,
[class*="st-key-answer_"] [data-testid="stMarkdownContainer"] h2,
[class*="st-key-answer_"] [data-testid="stMarkdownContainer"] h3 {
    font-size: 16px;
    padding: 0.4rem 0 0.2rem 0;
}

.source-heading {
    margin-top: 18px;
    color: var(--docu-text);
    font-size: 12.5px;
    font-weight: 600;
}

.source-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    margin-top: 14px;
}

.source-card {
    padding: 14px 15px;
    border: 1px solid #E4E1F6;
    border-radius: 12px;
    background: #F6F5FE;
}

.source-card-label {
    color: var(--docu-purple-ink);
    font-size: 10.5px;
    font-weight: 500;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}

.source-card-text {
    margin-top: 8px;
    color: var(--docu-text-2);
    font-size: 12.5px;
    line-height: 1.45;
}

[class*="st-key-actions_"] { gap: 10px !important; margin-top: 10px; }

[class*="st-key-actions_"] button {
    min-height: 0 !important;
    padding: 2px 4px !important;
    color: var(--docu-muted) !important;
}

[class*="st-key-actions_"] button p { font-size: 11.5px !important; }
[class*="st-key-actions_"] button [data-testid="stIconMaterial"] { font-size: 14px; }
[class*="st-key-actions_"] button:hover { color: var(--docu-purple-ink) !important; }
[class*="st-key-helpful_on_"] button { color: var(--docu-purple-ink) !important; }

.st-key-chat_composer {
    flex: none;
    padding: 18px 32px 14px 32px;
    border-top: 1px solid var(--docu-border);
    gap: 0 !important;
}

[data-testid="stChatInput"] {
    border: 0 !important;
    border-radius: 14px !important;
    background: transparent !important;
    box-shadow: none !important;
}

[data-testid="stChatInput"] > div {
    border: 1px solid #D5DEF3 !important;
    border-radius: 14px !important;
    background: #FFFFFF !important;
}

[data-testid="stChatInput"] > div:focus-within { border-color: var(--docu-purple) !important; }

[data-testid="stChatInput"] textarea {
    color: var(--docu-text) !important;
    font-size: 14.5px !important;
}

[data-testid="stChatInputSubmitButton"] {
    width: 42px !important;
    height: 42px !important;
    border-radius: 10px !important;
    background: var(--docu-purple) !important;
    color: #FFFFFF !important;
}

[data-testid="stChatInputSubmitButton"]:disabled {
    background: var(--docu-purple) !important;
    opacity: 1 !important;
}

[data-testid="stChatInputSubmitButton"] svg { color: #FFFFFF !important; fill: #FFFFFF !important; }

.composer-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-top: 10px;
    color: var(--docu-muted);
    font-size: 10.5px;
}

.processed-note {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    color: var(--docu-green);
}

.processed-dot {
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: var(--docu-green);
}

/* ---------- preview pane ---------- */

.st-key-preview_panel {
    height: 100%;
    overflow-y: auto;
    flex-wrap: nowrap !important;
    padding: 16px 22px 20px 22px;
    border-left: 1px solid var(--docu-border);
    background: var(--docu-preview);
    gap: 0 !important;
}

[data-testid="stColumn"]:has(> [data-testid="stVerticalBlock"] .st-key-preview_panel) {
    min-width: 280px;
}

.preview-file-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    padding-bottom: 14px;
}

.preview-file {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    min-width: 0;
}

.preview-file > .docu-icon { margin-top: 2px; }

.preview-file-name {
    overflow: hidden;
    color: var(--docu-text);
    font-size: 13px;
    font-weight: 500;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.preview-file-meta {
    margin-top: 2px;
    color: var(--docu-muted);
    font-size: 10.5px;
}

.st-key-preview_nav {
    height: 38px;
    margin-bottom: 18px;
    padding: 0 6px;
    border: 1px solid #E3E3EA;
    border-radius: 10px;
    background: #FFFFFF;
    align-items: center !important;
    flex-wrap: nowrap !important;
}

.st-key-preview_nav .stElementContainer:has(.preview-nav-label) { flex: 1 1 auto; }

.preview-nav-label {
    color: var(--docu-text-2);
    font-size: 11.5px;
    text-align: center;
}

.st-key-preview_nav button {
    min-height: 0 !important;
    height: 28px;
    padding: 0 8px !important;
    border: 0 !important;
    background: transparent !important;
    color: var(--docu-text-2) !important;
}

.st-key-preview_nav button:disabled { color: #C9C8D0 !important; }

.pdf-paper {
    min-height: 655px;
    padding: 34px 28px 28px 28px;
    border: 1px solid #E8E8EE;
    border-radius: 3px;
    background: #FFFFFF;
}

.pdf-paper-kicker {
    overflow-wrap: anywhere;
    color: var(--docu-purple-ink);
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.pdf-paper-title {
    overflow-wrap: anywhere;
    margin-top: 18px;
    color: var(--docu-text);
    font-size: 24px;
    font-weight: 700;
    line-height: 1.2;
    letter-spacing: -0.01em;
}

.pdf-paper-meta {
    margin-top: 14px;
    padding-bottom: 16px;
    border-bottom: 1px solid #E8E8EE;
    color: var(--docu-text-2);
    font-size: 9.5px;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}

.pdf-paper-body {
    margin-top: 18px;
    color: var(--docu-text-2);
    font-size: 11px;
    line-height: 1.75;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}

.pdf-paper-body mark {
    padding: 2px 0;
    background: #FDF6DC;
    color: var(--docu-text);
    box-decoration-break: clone;
    -webkit-box-decoration-break: clone;
}

.pdf-paper-footer {
    overflow-wrap: anywhere;
    margin-top: 22px;
    padding-top: 16px;
    border-top: 1px solid #E8E8EE;
    color: var(--docu-purple-ink);
    font-size: 8.5px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.preview-footer {
    margin-top: 22px;
    color: var(--docu-muted);
    font-size: 11.5px;
}

/* ---------- responsive ---------- */

@media (max-width: 1100px) {
    .source-grid { grid-template-columns: 1fr; }
    .chat-page-header, .st-key-chat_composer { padding-left: 20px; padding-right: 20px; }
    .st-key-chat_scroll { padding-left: 22px; padding-right: 22px; }
}

@media (max-width: 640px) {
    [data-testid="stLayoutWrapper"]:has(> .st-key-chat_pane),
    [data-testid="stLayoutWrapper"]:has(> .st-key-preview_panel),
    .st-key-chat_pane,
    .st-key-preview_panel { height: auto; }
    .st-key-chat_scroll { height: auto; overflow: visible; }
    .st-key-preview_panel { border-left: 0; border-top: 1px solid var(--docu-border); }
    .upload-shell { padding-top: 64px; padding-left: 16px; padding-right: 16px; }
    .upload-title { font-size: 25px; }
    .chat-page-header { padding: 60px 16px 16px 16px; }
    .st-key-chat_scroll { padding: 20px 16px; }
    .st-key-chat_composer { padding: 14px 16px; }
    .st-key-preview_panel { padding: 16px; }
    .pdf-paper { min-height: 0; }
    .user-bubble { max-width: 92%; }
    .composer-footer { flex-direction: column; align-items: flex-start; }
}
""".replace("__UPLOAD_ARROW__", _UPLOAD_ARROW).replace(
    "__SIDEBAR_ICON__",
    "data:image/svg+xml," + quote(_ICON_SVGS["sidebar"]),
) + _icon_css()


def apply_docu_theme() -> None:
    st.html(f"<style>{THEME_CSS}</style>")
