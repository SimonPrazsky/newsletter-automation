"""
VKH Newsletter Builder
======================
A locally-hosted FastHTML web application for composing the weekly VKH Praha
newsletter.  The app lets you:

  • Add / edit / delete event rows (V týdnu, Dále, Od jinud sections).
  • Reorder events via drag-and-drop (SortableJS).
  • Configure the newsletter header and the optional highlight / ticket box.
  • Preview the generated newsletter HTML in an embedded iframe.
  • Copy the finished HTML to the clipboard in one click.

All state is persisted to `events.json` and `config.json` in the project
directory so that your work survives server restarts.

Run with:
    python main.py
Then open http://localhost:5001 in your browser.
"""

from __future__ import annotations

import html as htmlesc
import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from fasthtml.common import *
from starlette.responses import HTMLResponse, PlainTextResponse

# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────

SECTIONS = {
    "week": "V týdnu",
    "later": "Dále",
    "external": "Od jinud",
}


@dataclass
class Event:
    id: str = ""
    section: str = "week"   # week | later | external
    date: str = ""           # e.g. "2.3."
    day_name: str = ""       # e.g. "Pondělí"  (used for week events)
    title: str = ""
    url: str = "#"
    description: str = ""   # Raw HTML allowed (links etc.)
    has_hand: bool = False   # Show the pointing-hand emoji image


@dataclass
class Config:
    date_range: str = "od 2. 3. – 8. 3. 2026"
    show_highlight: bool = True
    highlight_color: str = "#a76a65"
    highlight_title: str = "PLES VKH PRAHA"
    highlight_date: str = "9. 4. 2026"
    highlight_venue: str = "Na Maninách, Holešovice"
    highlight_time: str = "19 hodin"
    highlight_url: str = "https://tickets.alabanda.cz/"
    highlight_ticket_text: str = "Nákup lístku zde"


# ─────────────────────────────────────────────────────────────────────────────
# Persistent storage
# ─────────────────────────────────────────────────────────────────────────────

EVENTS_FILE = Path("events.json")
CONFIG_FILE = Path("config.json")

events: list[Event] = []
config = Config()


def _load_state() -> None:
    global events, config
    if EVENTS_FILE.exists():
        try:
            events = [Event(**e) for e in json.loads(EVENTS_FILE.read_text("utf-8"))]
        except Exception:
            events = []
    if CONFIG_FILE.exists():
        try:
            config = Config(**json.loads(CONFIG_FILE.read_text("utf-8")))
        except Exception:
            config = Config()


def _save_events() -> None:
    EVENTS_FILE.write_text(
        json.dumps([asdict(e) for e in events], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _save_config() -> None:
    CONFIG_FILE.write_text(
        json.dumps(asdict(config), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


_load_state()


# ─────────────────────────────────────────────────────────────────────────────
# Newsletter HTML generator
# ─────────────────────────────────────────────────────────────────────────────

_HAND_IMG = (
    '<img src="https://vkhpraha.cz/wp-content/uploads/2025/10/hand.png" alt=""'
    ' style="display:inline-block;width:30px;height:auto;border:0;'
    'vertical-align:middle;margin-left:8px;">'
)


def _title_link(ev: Event) -> str:
    """Return the styled <a> title link, optionally followed by the hand image."""
    link = (
        f'<a href="{htmlesc.escape(ev.url)}" style="font-family:Georgia,'
        f"'Times New Roman',serif;font-size:14px;text-transform:uppercase;"
        f'letter-spacing:1px;color:#444;font-weight:700;">'
        f"{htmlesc.escape(ev.title)}</a>"
    )
    return link + (_HAND_IMG if ev.has_hand else "")


def _render_week_event(ev: Event) -> str:
    return (
        '<div style="border:2px solid #7D211A;border-radius:30px;'
        "padding:13px 13px 13px 25px;background:#ffffff;font-size:14px;"
        'line-height:1.3;width:400px;box-sizing:border-box;margin:0 0 10px 0;">\n'
        f"{_title_link(ev)}<br>\n{ev.description}\n</div>"
    )


def _render_dale_event(ev: Event) -> str:
    date_str = htmlesc.escape(ev.date)
    if ev.day_name:
        date_str += " " + htmlesc.escape(ev.day_name)
    return (
        '<td class="daybox-dale" style="padding:13px 13px 13px 25px;">\n'
        f"<div>{date_str}</div>\n"
        f"{_title_link(ev)}<br>\n{ev.description}\n</td>"
    )


def _render_date_header(date: str, day_name: str) -> str:
    return (
        '<div style="padding:0 0 5px 0;">'
        f'<span class="daytitle1" style="display:inline-block;margin:0 6px;">'
        f"{htmlesc.escape(date)}</span>"
        f'<span class="daytitle2" style="display:inline-block;margin:0 6px;">'
        f"{htmlesc.escape(day_name)}</span></div>"
    )


def _render_highlight(cfg: Config) -> str:
    if not cfg.show_highlight:
        return ""
    c = cfg.highlight_color
    return (
        f'<div style="width:400px;margin:10px 0;padding:0;background:{c};border-radius:8px;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"'
        f' style="border-collapse:collapse;background:{c};border-radius:6px;"><tr>'
        f'<td width="12" style="width:12px;padding:0;">'
        f'<div style="width:12px;height:12px;background:#fff;border-radius:50%;margin-left:-6px;"></div></td>'
        f'<td style="padding:15px 20px;">'
        f'<div style="border-bottom:1px dashed #fff;padding-bottom:10px;margin-bottom:10px;">'
        f'<span style="font-family:Georgia,serif;font-size:16px;font-weight:700;text-transform:uppercase;color:#fff;">'
        f"{htmlesc.escape(cfg.highlight_title)}</span>"
        f'<span style="float:right;font-family:Georgia,serif;font-weight:700;color:#fff;">'
        f"{htmlesc.escape(cfg.highlight_date)}</span></div>"
        f'<div style="font-family:Arial,sans-serif;font-size:14px;color:#fff;line-height:1.3;">'
        f"{htmlesc.escape(cfg.highlight_venue)}<br>začíná v {htmlesc.escape(cfg.highlight_time)}<br>"
        f'<a href="{htmlesc.escape(cfg.highlight_url)}" style="color:#fff;font-weight:700;text-decoration:underline;">'
        f"{htmlesc.escape(cfg.highlight_ticket_text)}</a>{_HAND_IMG}"
        f"</div></td>"
        f'<td width="12" style="width:12px;padding:0;">'
        f'<div style="width:12px;height:12px;background:#fff;border-radius:50%;margin-right:-6px;"></div></td>'
        f"</tr></table></div>"
    )


def generate_newsletter(cfg: Config, evs: list[Event]) -> str:
    """Generate the full newsletter HTML string from current config and events."""
    week_evs = [e for e in evs if e.section == "week"]
    later_evs = [e for e in evs if e.section == "later"]
    ext_evs = [e for e in evs if e.section == "external"]

    # Week events: emit a date header for each distinct (date, day_name) group,
    # respecting the user-defined order of events.
    seen_dates: set[tuple[str, str]] = set()
    week_parts: list[str] = []
    for ev in week_evs:
        key = (ev.date, ev.day_name)
        if ev.date and key not in seen_dates:
            seen_dates.add(key)
            week_parts.append(_render_date_header(ev.date, ev.day_name))
        week_parts.append(_render_week_event(ev))
    week_html = "\n".join(week_parts)

    def _section_table(label: str, evs_list: list[Event]) -> str:
        if not evs_list:
            return ""
        rows = "\n".join(f"<tr>\n{_render_dale_event(e)}\n</tr>" for e in evs_list)
        return (
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0"'
            ' style="width:600px;max-width:100%;border-collapse:collapse;margin:10px 0 10px 30px;">\n'
            "  <tr><td>"
            '<div style="font-family:Georgia,serif;font-size:18px;color:#111;'
            "font-weight:600;text-transform:uppercase;text-align:center;margin:0 0 13px 0;\">"
            f"{label}</div></td></tr>\n  {rows}\n</table>"
        )

    later_html = _section_table("Dále:", later_evs)
    ext_html = _section_table("Od jinud:", ext_evs)

    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <title>VKH Newsletter</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <style>
    body{{margin:0;padding:0;background:#fff;font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#666;letter-spacing:.6px;font-weight:400;}}
    .daytitle1{{display:inline-block;padding:2px 4px;text-transform:uppercase;font-family:Georgia,'Times New Roman',serif;font-size:30px;line-height:1.05;color:#111;font-weight:700;}}
    .daytitle2{{padding-left:4px;display:inline-block;text-transform:uppercase;font-family:Georgia,'Times New Roman',serif;font-size:14px;line-height:1.05;color:#111;font-weight:700;}}
    .daybox-dale{{background:#f0f0f0;border-radius:30px;padding:10px;font-size:14px;line-height:1.4;width:400px;max-width:100%;margin:0 0 12px 0;display:block;box-sizing:border-box;}}
    .daybox-dale a{{font-family:Georgia,'Times New Roman',serif;font-size:14px;text-transform:uppercase;letter-spacing:1px;color:#444;font-weight:700;}}
    @media only screen and (max-width:500px){{
      .daytitle1,.daytitle2{{display:inline-block;font-size:16px;}}
    }}
  </style>
</head>
<body style="margin:0;padding:0;background:#fff;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#fff">
<tr><td align="center">

<!-- ── Newsletter header ───────────────────────────────────────────────── -->
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
       style="width:600px;max-width:100%;margin:0 auto;border-collapse:collapse;background:#fff;">
  <tr>
    <td style="padding:10px 0 4px 0;">
      <img src="https://vkhpraha.cz/wp-content/uploads/2025/10/vkh-red.png" alt="VKH"
           style="display:block;width:30px;max-width:100%;height:auto;border:0;">
    </td>
    <td style="padding:10px 10px 0 0;text-align:right;font-family:Georgia,serif;font-size:13px;color:#444;">
      <div style="color:#111;font-weight:700;">týdenní dávka nových akcí</div>
    </td>
  </tr>
  <tr>
    <td colspan="2" style="padding:0;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
        <tr><td style="height:1px;background:#222;line-height:1px;font-size:1px;">&nbsp;</td></tr>
      </table>
    </td>
  </tr>
  <tr>
    <td colspan="2" style="padding:18px 20px 6px 20px;text-align:center;">
      <div style="font-family:Georgia,serif;font-size:42px;line-height:1.05;color:#111;font-weight:700;">VKH Newsletter</div>
    </td>
  </tr>
  <tr>
    <td colspan="2" style="padding:0 20px 12px 20px;text-align:center;">
      <div style="font-family:Arial,sans-serif;font-size:14px;color:#666;letter-spacing:.6px;">{htmlesc.escape(cfg.date_range)}</div>
    </td>
  </tr>
  <tr>
    <td colspan="2" style="padding:0 20px 12px 20px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
        <tr><td style="height:3px;background:#222;line-height:3px;font-size:3px;">&nbsp;</td></tr>
        <tr><td style="height:6px;line-height:6px;font-size:6px;">&nbsp;</td></tr>
        <tr><td style="height:1px;background:#999;line-height:1px;font-size:1px;">&nbsp;</td></tr>
      </table>
    </td>
  </tr>
  <tr>
    <td colspan="2" style="padding:10px 20px 0 20px;text-align:center;">
      <div style="font-family:Georgia,serif;font-size:18px;color:#111;font-weight:600;text-transform:uppercase;">V týdnu:</div>
    </td>
  </tr>
</table>

<!-- ── Two-column: logo right + events left ────────────────────────────── -->
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
       style="width:600px;max-width:100%;margin:0;border-collapse:collapse;direction:rtl;">
  <tr>
    <td valign="top" width="200" style="width:200px;padding:0 0 0 10px;box-sizing:border-box;vertical-align:top;text-align:center;">
      <img src="https://vkhpraha.cz/wp-content/uploads/2025/10/universal2_bile_pozadi.png" alt="VKH"
           style="display:block;width:200px;max-width:100%;height:auto;border:0;">
    </td>
    <td valign="top" width="400" style="width:400px;box-sizing:border-box;vertical-align:top;text-align:left;direction:ltr;">
{_render_highlight(cfg)}
{week_html}
    </td>
  </tr>
</table>

{later_html}
{ext_html}

</td></tr>
</table>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# App-level CSS / JS assets
# ─────────────────────────────────────────────────────────────────────────────

_CSS = Style("""
/* ── Reset & Layout ───────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }
html, body { margin: 0; padding: 0; height: 100%; font-family: Arial, sans-serif;
             font-size: 14px; background: #f4f4f4; color: #222; }
.app { display: flex; height: 100vh; overflow: hidden; }

/* ── Sidebar ──────────────────────────────────────────────────────── */
.sidebar { width: 400px; min-width: 300px; background: #fff;
           border-right: 2px solid #e0e0e0;
           display: flex; flex-direction: column; overflow-y: auto; }
.sb-header { background: #7D211A; color: #fff; padding: 14px 18px; flex-shrink: 0; }
.sb-header h1 { margin: 0; font-family: Georgia, serif; font-size: 17px; }
.sb-header p  { margin: 4px 0 0; font-size: 12px; opacity: .75; }
.sb-section { padding: 12px 16px; border-bottom: 1px solid #eee; }
.sb-section-title { font-size: 11px; font-weight: 700; text-transform: uppercase;
                    letter-spacing: .8px; color: #999; margin: 0 0 10px; }

/* ── Collapsible details ──────────────────────────────────────────── */
.collapsible { border: 1px solid #eee; border-radius: 6px; overflow: hidden; }
.collapsible > summary {
  padding: 9px 14px; font-size: 13px; font-weight: 700; color: #444;
  cursor: pointer; user-select: none; background: #fafafa; list-style: none;
  display: flex; align-items: center; gap: 6px; }
.collapsible > summary::-webkit-details-marker { display: none; }
.collapsible > summary::before { content: "▶"; font-size: 9px; transition: transform .15s; }
.collapsible[open] > summary::before { content: "▼"; }
.collapsible-body { padding: 12px 14px; }

/* ── Forms ────────────────────────────────────────────────────────── */
.field { margin-bottom: 10px; }
.field label { display: block; font-size: 12px; font-weight: 600; color: #555; margin-bottom: 3px; }
.field input, .field textarea, .field select {
  width: 100%; padding: 6px 9px; border: 1px solid #ddd; border-radius: 5px;
  font-size: 13px; font-family: inherit; outline: none; }
.field input:focus, .field textarea:focus, .field select:focus { border-color: #7D211A; box-shadow: 0 0 0 2px rgba(125,33,26,.12); }
.field textarea { resize: vertical; min-height: 64px; }
.field-row { display: flex; gap: 8px; }
.field-row .field { flex: 1; }
.field-check { display: flex; align-items: center; gap: 7px; font-size: 13px; margin-bottom: 10px; }
.field-check input { width: auto; }
.field-note { font-size: 11px; color: #888; margin-top: 2px; }

/* ── Buttons ──────────────────────────────────────────────────────── */
.btn { display: inline-block; padding: 7px 15px; border: none; border-radius: 5px;
       font-size: 13px; font-weight: 600; cursor: pointer; font-family: inherit; }
.btn-red   { background: #7D211A; color: #fff; }
.btn-gray  { background: #eee; color: #333; }
.btn-green { background: #2a7d3d; color: #fff; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
.btn:hover { opacity: .85; }
.btn-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; }

/* ── Event cards ──────────────────────────────────────────────────── */
.events-wrap { padding: 8px 10px; }
.event-card {
  background: #fff; border: 1px solid #e0e0e0; border-left: 4px solid #7D211A;
  border-radius: 5px; padding: 8px 10px 8px 8px; margin-bottom: 6px;
  display: flex; align-items: flex-start; gap: 8px; }
.event-card[data-section="later"]   { border-left-color: #888; }
.event-card[data-section="external"] { border-left-color: #3a5f9d; }
.handle { cursor: grab; color: #ccc; font-size: 18px; line-height: 1;
          flex-shrink: 0; padding-top: 2px; user-select: none; }
.handle:active { cursor: grabbing; }
.card-body { flex: 1; min-width: 0; }
.card-title { font-weight: 700; font-size: 13px; color: #111;
              white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.card-meta  { font-size: 11px; color: #888; margin-top: 2px; }
.card-actions { flex-shrink: 0; display: flex; gap: 3px; }
.card-actions button {
  background: none; border: none; cursor: pointer; padding: 3px 6px;
  font-size: 14px; color: #aaa; border-radius: 4px; }
.card-actions button:hover { color: #7D211A; background: #f0e8e8; }
.badge { font-size: 10px; padding: 1px 7px; border-radius: 10px; font-weight: 700;
         display: inline-block; margin-bottom: 3px; }
.badge-week     { background: #f0e8e8; color: #7D211A; }
.badge-later    { background: #eee; color: #555; }
.badge-external { background: #ddeaff; color: #3a5f9d; }
.sortable-ghost { opacity: .35; }
.empty-msg { color: #aaa; font-size: 13px; font-style: italic; padding: 10px 4px; }

/* ── Preview pane ─────────────────────────────────────────────────── */
.preview { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
.preview-toolbar {
  background: #fff; border-bottom: 1px solid #e0e0e0;
  padding: 10px 16px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.preview-toolbar h2 { margin: 0; font-size: 14px; color: #333; flex: 1; }
.tab-btns { display: flex; border: 1px solid #ddd; border-radius: 5px; overflow: hidden; }
.tab-btn  { padding: 5px 13px; border: none; cursor: pointer; font-size: 12px;
            font-weight: 600; background: #f5f5f5; color: #666; }
.tab-btn.active { background: #7D211A; color: #fff; }
.preview-content { flex: 1; display: flex; overflow: hidden; }
#preview-frame {
  flex: 1; border: none; width: 100%;
  background: repeating-linear-gradient(45deg,#f9f9f9,#f9f9f9 10px,#f4f4f4 10px,#f4f4f4 20px); }
#html-code {
  flex: 1; padding: 16px; font-family: 'Courier New', monospace; font-size: 12px;
  resize: none; border: none; outline: none; background: #1a1a1a; color: #ccc;
  display: none; tab-size: 2; }

/* ── Misc ─────────────────────────────────────────────────────────── */
.notice-ok  { color: #2a7d3d; font-size: 12px; font-weight: 600; }
.notice-err { color: #c0392b; font-size: 12px; font-weight: 600; }
""")

_JS = Script("""
/* ─── Tab switching ─────────────────────────────────────────────── */
function showTab(name) {
  const frame = document.getElementById('preview-frame');
  const code  = document.getElementById('html-code');
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelector('.tab-btn[data-tab="' + name + '"]').classList.add('active');
  if (name === 'preview') {
    frame.style.display = '';
    code.style.display  = 'none';
  } else {
    frame.style.display = 'none';
    code.style.display  = '';
    refreshHtml();
  }
}

/* ─── Preview / HTML refresh ────────────────────────────────────── */
function refreshPreview() {
  const frame = document.getElementById('preview-frame');
  frame.src = '/preview?' + Date.now();
}

function refreshHtml() {
  fetch('/html').then(r => r.text()).then(t => {
    document.getElementById('html-code').value = t;
  });
}

function refreshAll() {
  refreshPreview();
  const code = document.getElementById('html-code');
  if (code && code.style.display !== 'none') refreshHtml();
}

/* ─── Copy HTML to clipboard ────────────────────────────────────── */
function copyHtml() {
  fetch('/html').then(r => r.text()).then(t => {
    navigator.clipboard.writeText(t).then(() => {
      const btn = document.getElementById('copy-btn');
      const orig = btn.textContent;
      btn.textContent = '✓ Zkopírováno!';
      setTimeout(() => { btn.textContent = orig; }, 2500);
    });
  });
}

/* ─── Download HTML ─────────────────────────────────────────────── */
function downloadHtml() {
  fetch('/html').then(r => r.text()).then(t => {
    const a = document.createElement('a');
    a.href = 'data:text/html;charset=utf-8,' + encodeURIComponent(t);
    a.download = 'newsletter.html';
    a.click();
  });
}

/* ─── Drag-and-drop via SortableJS ──────────────────────────────── */
function initSortable() {
  if (typeof Sortable === 'undefined') return;  // CDN may be unavailable
  const list = document.getElementById('event-list');
  if (!list || list._sortable) return;
  try {
    list._sortable = Sortable.create(list, {
      handle: '.handle',
      ghostClass: 'sortable-ghost',
      animation: 150,
      onEnd: function() {
        const ids = Array.from(list.querySelectorAll('.event-card'))
                         .map(c => c.dataset.id).join(',');
        htmx.ajax('POST', '/events/reorder', {values: {ids: ids}, swap: 'none'});
        setTimeout(refreshAll, 100);
      }
    });
  } catch(e) { console.warn('SortableJS init failed:', e); }
}

/* ─── Add / edit form helpers ───────────────────────────────────── */
function showAddForm() {
  document.getElementById('add-form-wrap').style.display = 'block';
  document.getElementById('add-form-btn').style.display  = 'none';
}
function hideAddForm() {
  document.getElementById('add-form-wrap').style.display = 'none';
  document.getElementById('add-form-btn').style.display  = 'block';
  document.getElementById('add-form').reset();
}
function hideEditForm() {
  document.getElementById('edit-form-wrap').innerHTML = '';
}

/* ─── HTMX lifecycle hooks ──────────────────────────────────────── */
document.addEventListener('htmx:afterSettle', function(evt) {
  const tid = evt.detail && evt.detail.target && evt.detail.target.id;
  if (tid === 'event-list') {
    list = document.getElementById('event-list');
    if (list) list._sortable = null;  // reset so initSortable re-creates it
    initSortable();
    refreshAll();
    hideEditForm();
  }
  if (tid === 'config-msg') refreshAll();
});

document.addEventListener('DOMContentLoaded', function() {
  refreshPreview();   // Load preview first — independent of SortableJS
  initSortable();
});
""")

_SORTABLE = Script(src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.6/Sortable.min.js")

# ─────────────────────────────────────────────────────────────────────────────
# UI components
# ─────────────────────────────────────────────────────────────────────────────

def _badge(section: str) -> FT:
    labels = {"week": "V týdnu", "later": "Dále", "external": "Od jinud"}
    return Span(labels.get(section, section), cls=f"badge badge-{section}")


def _event_card(ev: Event) -> FT:
    meta = ev.date + (" " + ev.day_name if ev.day_name else "")
    return Div(
        Span("⠿", cls="handle", title="Přetáhněte pro seřazení"),
        Div(
            _badge(ev.section),
            Div(meta.strip(), cls="card-meta"),
            Div(ev.title or "(bez názvu)", cls="card-title"),
            Div(
                (ev.url[:55] + "…") if len(ev.url) > 55 else ev.url,
                cls="card-meta",
            ),
            cls="card-body",
        ),
        Div(
            Button(
                "✎",
                title="Upravit",
                hx_get=f"/events/{ev.id}/edit",
                hx_target="#edit-form-wrap",
                hx_swap="innerHTML",
            ),
            Button(
                "✕",
                title="Smazat",
                hx_delete=f"/events/{ev.id}",
                hx_target="#event-list",
                hx_swap="outerHTML",
                hx_confirm="Opravdu smazat tuto akci?",
            ),
            cls="card-actions",
        ),
        cls="event-card",
        data_id=ev.id,
        data_section=ev.section,
        id=f"card-{ev.id}",
    )


def _event_list() -> FT:
    cards = [_event_card(ev) for ev in events]
    if not cards:
        cards = [P("Zatím žádné akce. Přidejte první!", cls="empty-msg")]
    return Div(*cards, id="event-list", cls="events-wrap")


def _event_form(ev: Event | None = None, *, action: str = "/events") -> FT:
    """Render an add or edit form pre-filled with ev's data (or blanks)."""
    e = ev or Event()
    is_edit = bool(e.id)
    return Form(
        Input(type="hidden", name="id", value=e.id),
        Div(
            Label("Sekce"),
            Select(
                Option("V týdnu",   value="week",     selected=(e.section == "week")),
                Option("Dále",      value="later",    selected=(e.section == "later")),
                Option("Od jinud",  value="external", selected=(e.section == "external")),
                name="section",
            ),
            cls="field",
        ),
        Div(
            Div(Label("Datum"), Input(name="date", value=e.date, placeholder="2.3."), cls="field"),
            Div(Label("Den"),   Input(name="day_name", value=e.day_name, placeholder="Pondělí"), cls="field"),
            cls="field-row",
        ),
        Div(Label("Název akce *"), Input(name="title", value=e.title, placeholder="Název akce", required=True), cls="field"),
        Div(Label("URL"),          Input(name="url",   value=e.url,   placeholder="https://…"), cls="field"),
        Div(
            Label("Popis (HTML je povoleno – lze přidat <a href=…> odkazů)"),
            Textarea(e.description, name="description",
                     placeholder="Krátký popis akce…"),
            P("Tip: HTML tagy jako <a href=\"…\">text</a> jsou povoleny.", cls="field-note"),
            cls="field",
        ),
        Div(
            Input(type="checkbox", name="has_hand", value="1",
                  id=f"has_hand_{e.id or 'new'}", checked=e.has_hand),
            Label("Přidat ikonu ručičky 👆", **{"for": f"has_hand_{e.id or 'new'}"}),
            cls="field-check",
        ),
        Div(
            Button("Uložit" if is_edit else "Přidat akci", type="submit", cls="btn btn-red btn-sm"),
            Button("Zrušit", type="button", cls="btn btn-gray btn-sm",
                   onclick="hideEditForm();" if is_edit else "hideAddForm();"),
            cls="btn-row",
        ),
        id="add-form" if not is_edit else f"edit-form-{e.id}",
        **({"hx_put": action} if is_edit else {"hx_post": action}),
        hx_target="#event-list",
        hx_swap="outerHTML",
    )


def _config_form() -> FT:
    return Details(
        Summary("⚙ Nastavení newsletteru"),
        Div(
            Form(
                Div(Label("Rozsah dat (zobrazuje se v hlavičce)"),
                    Input(name="date_range", value=config.date_range,
                          placeholder="od 2. 3. – 8. 3. 2026"),
                    cls="field"),
                Div(
                    Input(type="checkbox", name="show_highlight", value="1",
                          id="show_highlight", checked=config.show_highlight),
                    Label("Zobrazit highlight / ticketový box", **{"for": "show_highlight"}),
                    cls="field-check",
                ),
                Div(
                    Div(Label("Název události"),
                        Input(name="highlight_title", value=config.highlight_title),
                        cls="field"),
                    Div(Label("Datum"),
                        Input(name="highlight_date", value=config.highlight_date,
                              placeholder="9. 4. 2026"),
                        cls="field"),
                    cls="field-row",
                ),
                Div(
                    Div(Label("Místo konání"),
                        Input(name="highlight_venue", value=config.highlight_venue),
                        cls="field"),
                    Div(Label("Čas"),
                        Input(name="highlight_time", value=config.highlight_time),
                        cls="field"),
                    cls="field-row",
                ),
                Div(Label("URL lístků"),
                    Input(name="highlight_url", value=config.highlight_url,
                          placeholder="https://…"),
                    cls="field"),
                Div(
                    Div(Label("Text odkazu"),
                        Input(name="highlight_ticket_text",
                              value=config.highlight_ticket_text),
                        cls="field"),
                    Div(Label("Barva pozadí"),
                        Input(type="color", name="highlight_color",
                              value=config.highlight_color,
                              style="height:38px;padding:2px 4px;"),
                        cls="field"),
                    cls="field-row",
                ),
                Div(
                    Button("Uložit nastavení", type="submit", cls="btn btn-red btn-sm"),
                    Span(id="config-msg", style="margin-left:8px;"),
                    cls="btn-row",
                ),
                hx_post="/config",
                hx_target="#config-msg",
                hx_swap="innerHTML",
            ),
            cls="collapsible-body",
        ),
        cls="collapsible",
    )


def _main_page() -> FT:
    return Html(
        Head(
            Title("VKH Newsletter Builder"),
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            _SORTABLE,
            _CSS,
        ),
        Body(
            Div(
                # ── Sidebar ──────────────────────────────────────────────────
                Div(
                    # Header
                    Div(
                        H1("VKH Newsletter Builder"),
                        P("Sestavte newsletter, zkopírujte HTML."),
                        cls="sb-header",
                    ),
                    # Config
                    Div(_config_form(), cls="sb-section"),
                    # Add-event area
                    Div(
                        P("Akce", cls="sb-section-title"),
                        Button(
                            "+ Přidat novou akci",
                            cls="btn btn-red btn-sm",
                            id="add-form-btn",
                            onclick="showAddForm()",
                            style="width:100%;",
                        ),
                        Div(
                            _event_form(),
                            id="add-form-wrap",
                            style="display:none; margin-top:10px;",
                        ),
                        cls="sb-section",
                    ),
                    # Edit form container (populated via HTMX)
                    Div(id="edit-form-wrap", cls="sb-section",
                        style="display:contents;"),
                    # Event list
                    Div(_event_list(), cls="sb-section"),
                    cls="sidebar",
                ),
                # ── Preview pane ──────────────────────────────────────────────
                Div(
                    Div(
                        H2("Náhled newsletteru"),
                        Div(
                            Button("Náhled", cls="tab-btn active",
                                   data_tab="preview", onclick="showTab('preview')"),
                            Button("HTML kód", cls="tab-btn",
                                   data_tab="html", onclick="showTab('html')"),
                            cls="tab-btns",
                        ),
                        Button("⟳ Obnovit", cls="btn btn-gray btn-sm",
                               onclick="refreshAll()"),
                        Button("📋 Kopírovat HTML", cls="btn btn-red btn-sm",
                               id="copy-btn", onclick="copyHtml()"),
                        Button("⬇ Stáhnout HTML", cls="btn btn-green btn-sm",
                               onclick="downloadHtml()"),
                        cls="preview-toolbar",
                    ),
                    Div(
                        Iframe(id="preview-frame"),
                        Textarea(id="html-code", readonly=True),
                        cls="preview-content",
                    ),
                    cls="preview",
                ),
                cls="app",
            ),
            _JS,
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# FastHTML app & routes
# ─────────────────────────────────────────────────────────────────────────────

app, rt = fast_app(pico=False, live=False)


@rt("/")
def get() -> FT:
    return _main_page()


# ── Events: add ──────────────────────────────────────────────────────────────

@rt("/events")
async def post(req: Request) -> FT:  # noqa: F811
    form = await req.form()
    ev = Event(
        id=str(uuid.uuid4()),
        section=form.get("section", "week"),
        date=(form.get("date") or "").strip(),
        day_name=(form.get("day_name") or "").strip(),
        title=(form.get("title") or "").strip(),
        url=(form.get("url") or "#").strip(),
        description=(form.get("description") or "").strip(),
        has_hand=form.get("has_hand") == "1",
    )
    events.append(ev)
    _save_events()
    return _event_list()


# ── Events: edit form ────────────────────────────────────────────────────────

@rt("/events/{eid}/edit")
def get_edit(eid: str) -> FT:  # noqa: F811
    ev = next((e for e in events if e.id == eid), None)
    if ev is None:
        return P("Akce nenalezena.", cls="notice-err")
    return _event_form(ev, action=f"/events/{eid}")


# ── Events: save edit ────────────────────────────────────────────────────────

@rt("/events/{eid}")
async def put(eid: str, req: Request) -> FT:  # noqa: F811
    form = await req.form()
    for ev in events:
        if ev.id == eid:
            ev.section = form.get("section", ev.section)
            ev.date = (form.get("date") or "").strip()
            ev.day_name = (form.get("day_name") or "").strip()
            ev.title = (form.get("title") or "").strip()
            ev.url = (form.get("url") or "#").strip()
            ev.description = (form.get("description") or "").strip()
            ev.has_hand = form.get("has_hand") == "1"
            break
    _save_events()
    return _event_list()


# ── Events: delete ───────────────────────────────────────────────────────────

@rt("/events/{eid}")
def delete(eid: str) -> FT:  # noqa: F811
    global events
    events = [e for e in events if e.id != eid]
    _save_events()
    return _event_list()


# ── Events: reorder ──────────────────────────────────────────────────────────

@rt("/events/reorder")
async def post_reorder(req: Request):  # noqa: F811
    form = await req.form()
    ids = [i for i in (form.get("ids") or "").split(",") if i]
    id_map = {e.id: e for e in events}
    reordered = [id_map[i] for i in ids if i in id_map]
    # Append any events that were not in the submitted list (safety net)
    known = {e.id for e in reordered}
    reordered += [e for e in events if e.id not in known]
    events.clear()
    events.extend(reordered)
    _save_events()
    return ""


# ── Config: save ─────────────────────────────────────────────────────────────

@rt("/config")
async def post_config(req: Request) -> FT:  # noqa: F811
    form = await req.form()
    config.date_range = (form.get("date_range") or "").strip()
    config.show_highlight = form.get("show_highlight") == "1"
    config.highlight_color = form.get("highlight_color") or "#a76a65"
    config.highlight_title = (form.get("highlight_title") or "").strip()
    config.highlight_date = (form.get("highlight_date") or "").strip()
    config.highlight_venue = (form.get("highlight_venue") or "").strip()
    config.highlight_time = (form.get("highlight_time") or "").strip()
    config.highlight_url = (form.get("highlight_url") or "#").strip()
    config.highlight_ticket_text = (form.get("highlight_ticket_text") or "").strip()
    _save_config()
    return Span("✓ Uloženo", cls="notice-ok")


# ── Preview & HTML output ────────────────────────────────────────────────────

@rt("/preview")
def get_preview() -> HTMLResponse:
    html = generate_newsletter(config, events)
    return HTMLResponse(html)


@rt("/html")
def get_html() -> PlainTextResponse:
    html = generate_newsletter(config, events)
    return PlainTextResponse(html)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    print("VKH Newsletter Builder spuštěn na http://localhost:5001")
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)
