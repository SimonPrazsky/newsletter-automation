#!/usr/bin/env python3
"""VKH Praha Newsletter Builder — main.py
Two-pane editor: left = controls, right = live preview / raw HTML.
State persisted in events.json and config.json.
"""

from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import HTMLResponse
import json, os, uuid

# ── Constants ─────────────────────────────────────────────────────────────────
EVENTS_FILE    = "events.json"
CONFIG_FILE    = "config.json"
SECTIONS       = ["vtydnu", "dale", "odjinud"]
SECTION_LABELS = {"vtydnu": "V týdnu", "dale": "Dále", "odjinud": "Od jinud"}
STYLE_LABELS   = {"regular": "Běžná", "ticket": "Lístek", "mass": "Mše"}
DEFAULT_TC     = "#a76a65"
HAND_URL       = "https://vkhpraha.cz/wp-content/uploads/2025/10/hand.png"
VKH_LOGO_URL   = "https://vkhpraha.cz/wp-content/uploads/2025/10/vkh-red.png"


# ── Storage ───────────────────────────────────────────────────────────────────
def load_events():
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {s: [] for s in SECTIONS}

def save_events(data):
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"date_range": "", "highlight_title": "", "highlight_content": ""}

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def find_event(events, eid):
    """Return (section_key, event_dict) or (None, None)."""
    for sec in SECTIONS:
        for ev in events.get(sec, []):
            if ev["id"] == eid:
                return sec, ev
    return None, None


# ── Newsletter HTML Generator ─────────────────────────────────────────────────
def _hand():
    return (f'<img src="{HAND_URL}" alt="" style="display:inline-block;'
            f'width:28px;height:auto;border:0;vertical-align:middle;margin-left:8px;">')

def _double_rule():
    return """\
<tr><td colspan="2" style="padding:0 20px 12px 20px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
    <tr><td style="height:3px;background:#222;line-height:3px;font-size:3px;">&nbsp;</td></tr>
    <tr><td style="height:6px;line-height:6px;font-size:6px;">&nbsp;</td></tr>
    <tr><td style="height:1px;background:#999;line-height:1px;font-size:1px;">&nbsp;</td></tr>
  </table>
</td></tr>"""

def _thin_rule():
    return """\
<tr><td colspan="2" style="padding:0;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
    <tr><td style="height:1px;background:#222;line-height:1px;font-size:1px;">&nbsp;</td></tr>
  </table>
</td></tr>"""

def _section_heading(label):
    return f"""\
<tr><td colspan="2" style="padding:10px 20px 0 20px;text-align:center;">
  <div style="font-family:Georgia,'Times New Roman',serif;font-size:18px;color:#111;font-weight:600;text-transform:uppercase;">{label}:</div>
</td></tr>"""

def _nl_title_link(ev):
    title = ev.get("title", "")
    url   = ev.get("url", "")
    base  = ("font-family:Georgia,'Times New Roman',serif;"
             "font-size:14px;text-transform:uppercase;"
             "letter-spacing:1px;color:#444;font-weight:700;")
    if url:
        return f'<a href="{url}" style="{base}">{title}</a>'
    return f'<span style="{base}">{title}</span>'

def _nl_regular_vtydnu(ev):
    date      = ev.get("date", "")
    day       = ev.get("day_name", "")
    desc      = ev.get("description", "")
    hand      = _hand() if ev.get("hand") else ""

    date_header = ""
    if date or day:
        parts = []
        if date:
            parts.append(
                f'<span style="display:inline-block;margin:0 4px;'
                f"font-family:Georgia,'Times New Roman',serif;"
                f'font-size:28px;line-height:1.05;color:#111;font-weight:700;">{date}</span>'
            )
        if day:
            parts.append(
                f'<span style="display:inline-block;margin:0 4px;'
                f"font-family:Georgia,'Times New Roman',serif;"
                f'font-size:14px;line-height:1.05;color:#111;'
                f'font-weight:700;text-transform:uppercase;">{day}</span>'
            )
        date_header = f'<div style="padding:0 0 5px 0;">{"".join(parts)}</div>'

    desc_html = f"<br>{desc}" if desc else ""
    return (
        f'{date_header}'
        f'<div style="border:2px solid #7D211A;border-radius:30px;'
        f'padding:13px 13px 13px 25px;background:#fff;font-size:14px;'
        f'line-height:1.3;box-sizing:border-box;margin:0 0 10px 0;">'
        f'{_nl_title_link(ev)}{hand}{desc_html}'
        f'</div>'
    )

def _nl_ticket(ev):
    date   = ev.get("date", "")
    desc   = ev.get("description", "")
    tc     = ev.get("ticket_color") or DEFAULT_TC
    hand   = _hand() if ev.get("hand") else ""
    url    = ev.get("url", "")
    title  = ev.get("title", "")

    if url:
        name = (f'<a href="{url}" style="font-family:Georgia,\'Times New Roman\',serif;'
                f'font-size:16px;font-weight:700;text-transform:uppercase;'
                f'color:#fff;letter-spacing:1px;">{title}</a>')
    else:
        name = (f'<span style="font-family:Georgia,\'Times New Roman\',serif;'
                f'font-size:16px;font-weight:700;text-transform:uppercase;'
                f'color:#fff;">{title}</span>')

    date_right = (f'<span style="float:right;font-family:Georgia,serif;'
                  f'font-weight:700;color:#fff;">{date}</span>') if date else ""
    desc_html  = (f'<div style="font-family:Arial,sans-serif;font-size:14px;'
                  f'color:#fff;line-height:1.3;">{desc}{hand}</div>') if (desc or hand) else ""

    return f"""\
<div style="width:100%;margin:10px 0;background:{tc};border-radius:8px;box-sizing:border-box;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
         style="border-collapse:collapse;background:{tc};border-radius:8px;">
    <tr>
      <td width="12" style="width:12px;padding:0;">
        <div style="width:12px;height:12px;background:#fff;border-radius:50%;margin-left:-6px;"></div>
      </td>
      <td style="padding:15px 20px;">
        <div style="border-bottom:1px dashed rgba(255,255,255,0.6);padding-bottom:10px;margin-bottom:10px;">
          {date_right}{name}
        </div>
        {desc_html}
      </td>
      <td width="12" style="width:12px;padding:0;">
        <div style="width:12px;height:12px;background:#fff;border-radius:50%;margin-right:-6px;"></div>
      </td>
    </tr>
  </table>
</div>"""

def _nl_mass(ev):
    title  = ev.get("title", "Studentská mše svatá")
    time_  = ev.get("time", "")
    desc   = ev.get("description", "")

    time_span = (f'<span style="color:#7D211A;font-family:Georgia,serif;'
                 f'font-size:18px;font-weight:700;margin-left:16px;">{time_}</span>') if time_ else ""
    desc_html = (f'<tr><td colspan="2" style="padding:4px 0 8px 0;'
                 f'font-family:Arial,sans-serif;font-size:14px;color:#333;'
                 f'line-height:1.4;">{desc}</td></tr>') if desc else ""

    return f"""\
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
       style="border-collapse:collapse;margin:8px 0;">
  <tr><td colspan="2" style="padding:0 0 4px 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
      <tr><td style="height:3px;background:#222;line-height:3px;font-size:3px;">&nbsp;</td></tr>
      <tr><td style="height:5px;line-height:5px;font-size:5px;">&nbsp;</td></tr>
      <tr><td style="height:1px;background:#999;line-height:1px;font-size:1px;">&nbsp;</td></tr>
    </table>
  </td></tr>
  <tr><td colspan="2" style="text-align:right;padding:4px 0 6px 0;">
    <span style="font-family:Georgia,'Times New Roman',serif;font-size:28px;font-weight:700;color:#111;">{title}</span>
    {time_span}
  </td></tr>
  <tr><td colspan="2" style="padding:0 0 6px 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
      <tr><td style="height:1px;background:#222;line-height:1px;font-size:1px;">&nbsp;</td></tr>
    </table>
  </td></tr>
  {desc_html}
</table>"""

def _nl_dale_row(ev):
    date   = ev.get("date", "")
    desc   = ev.get("description", "")
    hand   = _hand() if ev.get("hand") else ""
    style  = ev.get("style", "regular")

    if style == "ticket":
        return f'<tr><td style="padding:0 0 12px 0;">{_nl_ticket(ev)}</td></tr>'

    date_div  = (f'<div style="font-family:Arial,sans-serif;font-size:13px;'
                 f'color:#666;margin-bottom:3px;">{date}</div>') if date else ""
    desc_html = f"<br>{desc}" if desc else ""

    return (
        f'<tr><td style="background:#f0f0f0;border-radius:30px;'
        f'padding:13px 13px 13px 25px;font-size:14px;line-height:1.3;'
        f'margin:0 0 12px 0;display:block;box-sizing:border-box;">'
        f'{date_div}{_nl_title_link(ev)}{hand}{desc_html}'
        f'</td></tr>'
    )

def generate_newsletter(events, config):
    date_range = config.get("date_range", "")
    hl_title   = config.get("highlight_title", "")
    hl_content = config.get("highlight_content", "")

    # Highlight block
    hl_block = ""
    if hl_title or hl_content:
        hl_inner = ""
        if hl_title:
            hl_inner += (f'<div style="font-family:Georgia,serif;font-size:16px;'
                         f'font-weight:700;margin-bottom:8px;">{hl_title}</div>')
        hl_inner += hl_content
        hl_block = f"""\
<tr><td colspan="2" style="padding:0 20px 20px 20px;">
  <div style="background:#fffde7;border:1px solid #f9ca24;border-radius:6px;
              padding:14px 18px;font-family:Arial,sans-serif;font-size:14px;
              color:#333;line-height:1.4;">{hl_inner}</div>
</td></tr>"""

    # V týdnu
    vtydnu_html = ""
    vtydnu_evs = events.get("vtydnu", [])
    if vtydnu_evs:
        rows = []
        for ev in vtydnu_evs:
            s = ev.get("style", "regular")
            if s == "ticket":
                rows.append(_nl_ticket(ev))
            elif s == "mass":
                rows.append(_nl_mass(ev))
            else:
                rows.append(_nl_regular_vtydnu(ev))
        vtydnu_html = (
            f'{_section_heading("V týdnu")}\n{_double_rule()}\n'
            f'<tr><td colspan="2" style="padding:0 20px 8px 20px;">'
            f'{"".join(rows)}</td></tr>'
        )

    # Dále
    dale_html = ""
    dale_evs = events.get("dale", [])
    if dale_evs:
        rows = "\n".join(_nl_dale_row(ev) for ev in dale_evs)
        dale_html = (
            f'{_section_heading("Dále")}\n{_double_rule()}\n'
            f'<tr><td colspan="2" style="padding:0 20px 8px 20px;">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"'
            f' border="0" style="border-collapse:collapse;">{rows}</table>'
            f'</td></tr>'
        )

    # Od jinud
    odjinud_html = ""
    odjinud_evs = events.get("odjinud", [])
    if odjinud_evs:
        rows = "\n".join(_nl_dale_row(ev) for ev in odjinud_evs)
        odjinud_html = (
            f'{_section_heading("Od jinud")}\n{_double_rule()}\n'
            f'<tr><td colspan="2" style="padding:0 20px 8px 20px;">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"'
            f' border="0" style="border-collapse:collapse;">{rows}</table>'
            f'</td></tr>'
        )

    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>VKH Newsletter</title>
  <style>
    body{{margin:0;padding:0;background:#fff;font-family:Arial,Helvetica,sans-serif;
          font-size:14px;color:#666;letter-spacing:.6px;
          -webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;}}
    .container{{width:600px;max-width:600px;margin:0 auto;background:#fff;}}
    @media only screen and (max-width:500px){{
      .container{{width:100%!important;max-width:100%!important;}}
    }}
  </style>
</head>
<body style="margin:0;padding:0;background:#fff;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#fff">
  <tr><td align="center" style="font-family:Arial,Helvetica,sans-serif;">
    <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
           class="container"
           style="width:600px;max-width:100%;margin:0 auto;border-collapse:collapse;background:#fff;">
      <!-- Masthead -->
      <tr>
        <td style="padding:10px 0 4px 0;">
          <img src="{VKH_LOGO_URL}" alt="VKH"
               style="display:block;width:30px;max-width:100%;height:auto;border:0;">
        </td>
        <td style="padding:10px 10px 0 0;text-align:right;
                   font-family:Georgia,'Times New Roman',serif;font-size:13px;color:#444;">
          <div style="color:#111;font-weight:700;">týdenní dávka nových akcí</div>
        </td>
      </tr>
      {_thin_rule()}
      <!-- Title -->
      <tr><td colspan="2" style="padding:18px 20px 6px 20px;text-align:center;">
        <div style="font-family:Georgia,'Times New Roman',serif;font-size:42px;
                    line-height:1.05;color:#111;font-weight:700;">VKH Newsletter</div>
      </td></tr>
      <!-- Date range -->
      <tr><td colspan="2" style="padding:0 20px 12px 20px;text-align:center;">
        <div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;
                    color:#666;letter-spacing:.6px;">{date_range}</div>
      </td></tr>
      {_double_rule()}
      {hl_block}
      {vtydnu_html}
      {dale_html}
      {odjinud_html}
      <!-- Footer -->
      <tr><td colspan="2" style="padding:24px 0 16px 0;text-align:center;
                                  font-family:Arial,sans-serif;font-size:11px;color:#bbb;">
        VKH Praha · newsletter
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""


# ── App CSS ───────────────────────────────────────────────────────────────────
APP_CSS = """
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:system-ui,-apple-system,sans-serif;font-size:14px;background:#f5f5f5;overflow:hidden;}

/* Two-pane layout */
.app{display:grid;grid-template-columns:430px 1fr;height:100vh;overflow:hidden;}

/* Left pane */
.left-pane{display:flex;flex-direction:column;overflow:hidden;background:#fff;border-right:2px solid #e0e0e0;}
.left-header{flex-shrink:0;background:#7D211A;color:#fff;padding:11px 16px;
             font-size:15px;font-weight:700;letter-spacing:.5px;
             display:flex;align-items:center;gap:8px;}
.left-header .subtext{font-size:11px;font-weight:400;opacity:.7;margin-left:auto;}
.left-scroll{flex:1;overflow-y:auto;padding:14px 16px 32px;}

/* Right pane */
.right-pane{display:flex;flex-direction:column;overflow:hidden;}
.right-header{flex-shrink:0;background:#fff;border-bottom:1px solid #ddd;
              padding:8px 14px;display:flex;align-items:center;gap:8px;}
.right-content{flex:1;overflow:hidden;position:relative;}
#preview-frame{width:100%;height:100%;border:none;display:block;}
#html-pane{display:none;width:100%;height:100%;padding:12px;}
#html-code{width:100%;height:100%;font-family:'Courier New',monospace;font-size:12px;
           border:1px solid #ddd;border-radius:4px;padding:10px;resize:none;
           background:#fafafa;color:#222;}

/* Tabs */
.tab-btn{padding:5px 16px;border:1px solid #ccc;border-radius:4px;
         background:#f5f5f5;cursor:pointer;font-size:13px;font-family:inherit;}
.tab-btn.active{background:#7D211A;color:#fff;border-color:#7D211A;}
.tab-btn:not(.active):hover{background:#e8e8e8;}
.ml-auto{margin-left:auto;}

/* Config block */
.config-block{background:#fafafa;border:1px solid #e0e0e0;border-radius:6px;
              padding:12px;margin-bottom:18px;}
.config-block h3{font-size:11px;text-transform:uppercase;color:#999;
                 letter-spacing:.5px;margin-bottom:10px;font-weight:700;}

/* Fields */
.field{margin-bottom:8px;}
.field label{display:block;font-size:11px;color:#555;margin-bottom:3px;font-weight:600;}
.field input[type=text],.field input[type=url],.field select,.field textarea{
  width:100%;padding:5px 8px;border:1px solid #ccc;border-radius:4px;
  font-size:13px;font-family:inherit;color:#222;}
.field textarea{resize:vertical;min-height:52px;}
.field-row{display:flex;gap:8px;}
.field-row>.field{flex:1;min-width:0;}
.field input[type=color]{width:44px;height:30px;padding:2px;border:1px solid #ccc;
                         border-radius:4px;cursor:pointer;flex-shrink:0;}
.checkbox-field{display:flex;align-items:center;gap:6px;padding:4px 0;}
.checkbox-field label{font-size:13px;color:#333;font-weight:400;margin-bottom:0;cursor:pointer;}
.save-msg{font-size:11px;color:#1a7a1a;margin-left:6px;}

/* Section blocks */
.section-block{margin-bottom:20px;}
.section-head{display:flex;align-items:center;justify-content:space-between;
              background:#7D211A;color:#fff;padding:7px 10px;border-radius:4px 4px 0 0;}
.section-head .section-label{font-weight:700;font-size:14px;}
.event-list{list-style:none;padding:0;border:1px solid #ddd;border-top:none;
            border-radius:0 0 4px 4px;min-height:30px;background:#fff;}
.event-list:empty::before{content:'Žádné akce — klikni + Přidat';display:block;
                           padding:10px 12px;color:#bbb;font-size:12px;font-style:italic;}

/* Event rows */
.event-item{display:flex;align-items:center;gap:6px;padding:7px 10px;
            border-bottom:1px solid #f0f0f0;background:#fff;}
.event-item:last-child{border-bottom:none;}
.sortable-ghost{opacity:.35;background:#e8f0ff!important;}
.sortable-chosen{box-shadow:0 2px 8px rgba(0,0,0,.12);}
.drag-handle{color:#ccc;cursor:grab;font-size:14px;flex-shrink:0;line-height:1;}
.drag-handle:active{cursor:grabbing;}
.event-info{flex:1;min-width:0;}
.event-title-line{font-size:13px;font-weight:500;white-space:nowrap;
                  overflow:hidden;text-overflow:ellipsis;color:#222;}
.event-meta-line{font-size:11px;color:#999;white-space:nowrap;
                 overflow:hidden;text-overflow:ellipsis;}
.badge{font-size:10px;padding:2px 7px;border-radius:10px;
       background:#eee;color:#666;white-space:nowrap;flex-shrink:0;}
.badge-ticket{background:#fff3cd;color:#856404;}
.badge-mass{background:#ede9ff;color:#6f42c1;}
.event-actions{display:flex;gap:3px;flex-shrink:0;}

/* Buttons */
.btn{padding:4px 11px;border:1px solid #ccc;border-radius:4px;background:#f5f5f5;
     cursor:pointer;font-size:12px;font-family:inherit;color:#333;}
.btn:hover{background:#e8e8e8;}
.btn-primary{background:#7D211A;color:#fff;border-color:#7D211A;}
.btn-primary:hover{background:#5f1815;}
.btn-danger{color:#c00;border-color:#fcc;background:#fff5f5;}
.btn-danger:hover{background:#ffe5e5;}
.btn-sm{padding:2px 8px;font-size:11px;}

/* Event add/edit form shell */
.form-shell{border:1px solid #ddd;border-top:none;padding:10px;
            background:#f7f8ff;border-radius:0 0 4px 4px;}
.form-shell.inline-edit{border-top:1px solid #c0cfff;border-radius:4px;margin:2px 0;}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px 10px;}
.form-grid .span2{grid-column:span 2;}
.form-actions{display:flex;gap:6px;justify-content:flex-end;margin-top:10px;}
"""


# ── FastHTML App ──────────────────────────────────────────────────────────────
app, rt = fast_app(
    hdrs=(
        Style(APP_CSS),
        Script(src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"),
    )
)


# ── UI Components ─────────────────────────────────────────────────────────────
def event_form(section, ev=None):
    """Add or edit form for an event."""
    is_edit  = ev is not None
    v        = ev or {}
    eid      = v.get("id", "new")
    ev_style = v.get("style", "regular")
    tc_id    = f"tc-row-{eid}"

    if is_edit:
        action_attrs = {"hx_put": f"/events/{eid}"}
        shell_cls    = "form-shell inline-edit"
    else:
        action_attrs = {"hx_post": "/events"}
        shell_cls    = "form-shell"

    return Form(
        Input(type="hidden", name="section", value=section),
        Div(
            # Title (full width)
            Div(
                Label("Název *"),
                Input(type="text", name="title", value=v.get("title", ""),
                      placeholder="Název akce", required=True),
                cls="field span2",
            ),
            # URL (full width)
            Div(
                Label("URL titulku"),
                Input(type="url", name="url", value=v.get("url", ""),
                      placeholder="https://vkhpraha.cz/..."),
                cls="field span2",
            ),
            # Date + day name
            Div(
                Label("Datum"),
                Input(type="text", name="date", value=v.get("date", ""),
                      placeholder="2.3."),
                cls="field",
            ),
            Div(
                Label("Den (V týdnu)"),
                Input(type="text", name="day_name", value=v.get("day_name", ""),
                      placeholder="Pondělí"),
                cls="field",
            ),
            # Time + style
            Div(
                Label("Čas (styl Mše)"),
                Input(type="text", name="time", value=v.get("time", ""),
                      placeholder="19:00"),
                cls="field",
            ),
            Div(
                Label("Styl"),
                Select(
                    Option("Běžná",  value="regular", selected=(ev_style == "regular")),
                    Option("Lístek", value="ticket",  selected=(ev_style == "ticket")),
                    Option("Mše",    value="mass",    selected=(ev_style == "mass")),
                    name="style",
                    onchange=(
                        f"document.getElementById('{tc_id}').style.display="
                        f"this.value==='ticket'?'flex':'none'"
                    ),
                ),
                cls="field",
            ),
            # Ticket colour (shown only for ticket style)
            Div(
                Label("Barva lístku"),
                Input(type="color", name="ticket_color",
                      value=v.get("ticket_color", DEFAULT_TC)),
                cls="field field-row",
                id=tc_id,
                style=f"display:{'flex' if ev_style == 'ticket' else 'none'}",
            ),
            Div(cls="field"),  # grid spacer
            # Hand checkbox
            Div(
                Input(type="checkbox", name="hand", id=f"hand-{eid}",
                      value="on", **({"checked": True} if v.get("hand") else {})),
                Label("Ikona ruky ☞", for_=f"hand-{eid}"),
                cls="checkbox-field span2",
            ),
            # Description (full width)
            Div(
                Label("Popis (HTML povoleno)"),
                Textarea(v.get("description", ""), name="description",
                         placeholder="Popis, místo, odkaz…"),
                cls="field span2",
            ),
            cls="form-grid",
        ),
        Div(
            Button("Uložit" if is_edit else "Přidat", type="submit", cls="btn btn-primary"),
            Button("Zrušit", type="button", cls="btn",
                   hx_get=f"/section/{section}",
                   hx_target=f"#section-{section}",
                   hx_swap="outerHTML"),
            cls="form-actions",
        ),
        cls=shell_cls,
        hx_target=f"#section-{section}",
        hx_swap="outerHTML",
        **action_attrs,
    )

def event_item_row(ev, section):
    """Single draggable event row for the editor list."""
    style     = ev.get("style", "regular")
    hand_lbl  = "☞ " if ev.get("hand") else ""
    badge_cls = f"badge badge-{style}" if style != "regular" else "badge"
    meta      = ev.get("date", "") or ev.get("time", "")

    return Li(
        Span("⠿", cls="drag-handle"),
        Div(
            Div(hand_lbl + ev.get("title", "(bez názvu)"), cls="event-title-line"),
            Div(meta, cls="event-meta-line") if meta else "",
            cls="event-info",
        ),
        Span(STYLE_LABELS.get(style, style), cls=badge_cls),
        Div(
            Button("upravit", cls="btn btn-sm",
                   hx_get=f"/events/{ev['id']}/edit",
                   hx_target=f"#section-{section}",
                   hx_swap="outerHTML"),
            Button("smazat", cls="btn btn-sm btn-danger",
                   hx_delete=f"/events/{ev['id']}",
                   hx_target=f"#section-{section}",
                   hx_swap="outerHTML",
                   hx_confirm="Opravdu smazat tuto akci?"),
            cls="event-actions",
        ),
        cls="event-item",
        id=f"ev-{ev['id']}",
        data_id=ev["id"],
    )

def section_block(section, events_data, show_add=False, edit_id=None):
    """Full renderable section block (id=section-{section})."""
    evs = events_data.get(section, [])

    items = []
    for ev in evs:
        if ev["id"] == edit_id:
            items.append(Li(
                event_form(section, ev),
                cls="event-item",
                style="padding:0;display:block;background:transparent;",
            ))
        else:
            items.append(event_item_row(ev, section))

    # Sortable init — runs after each HTMX swap
    sort_js = Script(f"""
(function(){{
  var el=document.getElementById('sortable-{section}');
  if(!el||!window.Sortable)return;
  if(el._si){{el._si.destroy();el._si=null;}}
  el._si=Sortable.create(el,{{
    handle:'.drag-handle',
    animation:150,
    ghostClass:'sortable-ghost',
    chosenClass:'sortable-chosen',
    onEnd:function(){{
      var ids=Array.from(el.querySelectorAll('[data-id]'))
               .map(function(x){{return x.dataset.id;}});
      fetch('/reorder/{section}',{{
        method:'POST',
        headers:{{'Content-Type':'application/json'}},
        body:JSON.stringify({{order:ids}})
      }}).then(function(){{
        var f=document.getElementById('preview-frame');
        if(f&&f.style.display!=='none')f.src='/preview?t='+Date.now();
      }});
    }}
  }});
}})();
""")

    return Div(
        Div(
            Span(SECTION_LABELS[section], cls="section-label"),
            Button(
                "+ Přidat", cls="btn btn-sm",
                style="background:rgba(255,255,255,.15);border-color:rgba(255,255,255,.4);color:#fff;",
                hx_get=f"/section/{section}/add-form",
                hx_target=f"#section-{section}",
                hx_swap="outerHTML",
            ),
            cls="section-head",
        ),
        Ul(*items, id=f"sortable-{section}", cls="event-list"),
        event_form(section) if show_add else "",
        sort_js,
        id=f"section-{section}",
        cls="section-block",
    )

def config_panel(cfg):
    return Div(
        H3("Nastavení newsletteru"),
        Form(
            Div(
                Label("Datum (rozsah týdne)"),
                Input(type="text", name="date_range",
                      value=cfg.get("date_range", ""),
                      placeholder="od 2. 3. – 8. 3. 2026"),
                cls="field",
            ),
            Div(
                Label("Zvýrazněný box – nadpis (volitelné)"),
                Input(type="text", name="highlight_title",
                      value=cfg.get("highlight_title", ""),
                      placeholder="Ples VKH Praha"),
                cls="field",
            ),
            Div(
                Label("Zvýrazněný box – obsah HTML (volitelné)"),
                Textarea(cfg.get("highlight_content", ""),
                         name="highlight_content",
                         placeholder="<b>9. 4.</b> Na Maninách, 19:00…"),
                cls="field",
            ),
            Div(
                Button("Uložit nastavení", type="submit",
                       cls="btn btn-primary btn-sm"),
                Span("", id="cfg-saved", cls="save-msg"),
                style="display:flex;align-items:center;margin-top:8px;",
            ),
            hx_post="/config",
            hx_target="#cfg-saved",
            hx_swap="innerHTML",
        ),
        cls="config-block",
    )


# ── Routes ────────────────────────────────────────────────────────────────────

# ---------- Main page ----------
@rt("/")
def get():
    events = load_events()
    cfg    = load_config()

    left_pane = Div(
        Div("VKH Newsletter Builder",
            Span("editor", cls="subtext"),
            cls="left-header"),
        Div(
            config_panel(cfg),
            *[section_block(s, events) for s in SECTIONS],
            cls="left-scroll",
        ),
        cls="left-pane",
    )

    right_pane = Div(
        Div(
            Button("Náhled",  cls="tab-btn active", id="tab-preview",
                   onclick="showTab('preview')"),
            Button("HTML",    cls="tab-btn",         id="tab-html",
                   onclick="showTab('html')"),
            Button("↻ Obnovit", cls="btn ml-auto",
                   onclick="refreshPreview()"),
            cls="right-header",
        ),
        Div(
            Iframe(src="/preview", id="preview-frame"),
            Div(
                Textarea("", id="html-code", readonly=True,
                         placeholder="Klikni na záložku HTML pro zobrazení kódu…"),
                id="html-pane",
            ),
            cls="right-content",
        ),
        cls="right-pane",
    )

    page_js = Script("""
function showTab(t) {
  var frame   = document.getElementById('preview-frame');
  var htmlPane = document.getElementById('html-pane');
  var btnP = document.getElementById('tab-preview');
  var btnH = document.getElementById('tab-html');
  if (t === 'preview') {
    frame.style.display    = 'block';
    htmlPane.style.display = 'none';
    btnP.classList.add('active');
    btnH.classList.remove('active');
    refreshPreview();
  } else {
    frame.style.display    = 'none';
    htmlPane.style.display = 'block';
    btnP.classList.remove('active');
    btnH.classList.add('active');
    loadHtml();
  }
}

function refreshPreview() {
  var f = document.getElementById('preview-frame');
  if (f) f.src = '/preview?t=' + Date.now();
}

function loadHtml() {
  fetch('/html').then(function(r){ return r.text(); }).then(function(html){
    document.getElementById('html-code').value = html;
  });
}

// After any mutating HTMX request, refresh the active pane
document.addEventListener('htmx:afterRequest', function(e) {
  var verb = (e.detail.requestConfig && e.detail.requestConfig.verb || '').toUpperCase();
  if (verb !== 'GET') {
    var htmlVisible = document.getElementById('html-pane').style.display !== 'none';
    if (htmlVisible) { loadHtml(); } else { refreshPreview(); }
  }
});
""")

    return (
        Title("VKH Newsletter Builder"),
        Div(left_pane, right_pane, cls="app"),
        page_js,
    )


# ---------- Preview / HTML ----------
@rt("/preview")
def get():
    return HTMLResponse(generate_newsletter(load_events(), load_config()))

@rt("/html")
def get():
    return HTMLResponse(
        generate_newsletter(load_events(), load_config()),
        media_type="text/plain; charset=utf-8",
    )


# ---------- Config ----------
@rt("/config")
async def post(req: Request):
    form = await req.form()
    save_config({
        "date_range":        form.get("date_range", ""),
        "highlight_title":   form.get("highlight_title", ""),
        "highlight_content": form.get("highlight_content", ""),
    })
    return "✓ Uloženo"


# ---------- Section helpers (cancel / add-form) ----------
@rt("/section/{section}")
def get(section: str):
    if section not in SECTIONS:
        return ""
    return section_block(section, load_events())

@rt("/section/{section}/add-form")
def get(section: str):
    if section not in SECTIONS:
        return ""
    return section_block(section, load_events(), show_add=True)


# ---------- Events create ----------
@rt("/events")
async def post(req: Request):
    form    = await req.form()
    section = form.get("section", "vtydnu")
    if section not in SECTIONS:
        section = "vtydnu"

    ev = {
        "id":           str(uuid.uuid4()),
        "section":      section,
        "title":        form.get("title", "").strip(),
        "url":          form.get("url", "").strip(),
        "date":         form.get("date", "").strip(),
        "day_name":     form.get("day_name", "").strip(),
        "time":         form.get("time", "").strip(),
        "description":  form.get("description", "").strip(),
        "style":        form.get("style", "regular"),
        "hand":         form.get("hand") == "on",
        "ticket_color": form.get("ticket_color", DEFAULT_TC),
    }

    events = load_events()
    events[section].append(ev)
    save_events(events)
    return section_block(section, events)


# ---------- Events edit form ----------
@rt("/events/{eid}/edit")
def get(eid: str):
    events = load_events()
    sec, _ = find_event(events, eid)
    if sec is None:
        return ""
    return section_block(sec, events, edit_id=eid)


# ---------- Events update ----------
@rt("/events/{eid}")
async def put(req: Request, eid: str):
    form    = await req.form()
    events  = load_events()
    sec, ev = find_event(events, eid)
    if ev is None:
        return ""

    ev["title"]        = form.get("title",        ev["title"]).strip()
    ev["url"]          = form.get("url",           ev.get("url", "")).strip()
    ev["date"]         = form.get("date",          ev.get("date", "")).strip()
    ev["day_name"]     = form.get("day_name",      ev.get("day_name", "")).strip()
    ev["time"]         = form.get("time",          ev.get("time", "")).strip()
    ev["description"]  = form.get("description",   ev.get("description", "")).strip()
    ev["style"]        = form.get("style",         ev.get("style", "regular"))
    ev["hand"]         = form.get("hand") == "on"
    ev["ticket_color"] = form.get("ticket_color",  ev.get("ticket_color", DEFAULT_TC))

    save_events(events)
    return section_block(sec, events)


# ---------- Events delete ----------
@rt("/events/{eid}")
def delete(eid: str):
    events = load_events()
    sec, _ = find_event(events, eid)
    if sec is None:
        return ""
    events[sec] = [e for e in events[sec] if e["id"] != eid]
    save_events(events)
    return section_block(sec, events)


# ---------- Reorder (JSON body from SortableJS) ----------
@rt("/reorder/{section}")
async def post(req: Request, section: str):
    if section not in SECTIONS:
        return ""
    data   = await req.json()
    order  = data.get("order", [])
    events = load_events()
    by_id  = {e["id"]: e for e in events.get(section, [])}
    events[section] = [by_id[i] for i in order if i in by_id]
    save_events(events)
    return ""


# ── Entry point ───────────────────────────────────────────────────────────────
serve(port=5001)
