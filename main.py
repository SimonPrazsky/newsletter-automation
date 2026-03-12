"""
VKH Praha – Newsletter Builder
Run:  python main.py
Then open: http://localhost:5001
"""

from fasthtml.common import *
from starlette.responses import Response
import json, uuid, datetime
from pathlib import Path

# ── persistence ───────────────────────────────────────────────────────────────
EVENTS_FILE  = Path("events.json")
CONFIG_FILE  = Path("config.json")
ARCHIVE_FILE = Path("archive.json")

CS_DAYS   = ["Pondělí","Úterý","Středa","Čtvrtek","Pátek","Sobota","Neděle"]
CS_MONTHS = ["ledna","února","března","dubna","května","června",
             "července","srpna","září","října","listopadu","prosince"]

DEFAULT_MSE_SUBEVENTS = [
    {"label": "Svátost smíření / duchovní rozhovor", "time": "17:30–18:45",
     "detail": "P. Petr Hruška SJ – místnost 71 | S. Simeona CJ – místnost u vrátnice"},
    {"label": "Růženec",              "time": "18:15", "detail": "Sraz v průjezdu Ječná 2 – místnost 27"},
    {"label": "PoStřeH", "time": "20:10", "detail": "Examen"},
]
DEFAULT_MSE_INFOBOXES = [
    {"title": "Bar",          "body": "Hledáme barmany do týmu. Přidej se k nám!"},
    {"title": "Ministrování", "body": "Přijď 12 minut přede mší do sakristie. Kdokoli se může přidat."},
    {"title": "#rytmig",      "body": "Sraz v 17:00 v průjezdu Ječná 2, zvonek Rytmig."},
]

# Title → weekday map for auto-dating recurring events when week is set
# (weekday 0=Mon)
RECURRING_WEEKDAY = {
    "tančírna v družinské":    1,
    "útes":                    1,
    "pomáháme lidem bez domova": 1,
    "ranní":                   1,
    "ranní modlitba s písmem": 2,
    "chill out":               2,
    "herní večer":             3,
    "křížová cesta na petříně":4,
    "rorátní mše":             4,
}

# Default Akce library – seed file if akce.json doesn't exist yet.
# Each entry: id, weekday(0=Mon), title, time, place, description, links,
#             auto_add (bool: add to newsletter automatically when week is set)
AKCE_FILE = Path("akce.json")
AKCE_DEFAULTS_FILE = Path("akce_defaults.json")

DEFAULT_AKCE = [
    {"id": "95381f1c-c867-49e8-9cbc-01e03609762a", "weekday": 0, "title": "Pondělní vysokoškolský klub", "time": "19:00", "place": "Družínský sál", "description": "", "auto_add": False, "links": [{"url": "www.vkhpraha.cz/povyk", "label": "www.vkhpraha.cz/povyk", "hand": False}], "title_url": "", "hand": False},
    {"id": "0b8fedc5-7ca5-4eb9-ba6a-f0e77b030b71", "weekday": 1, "title": "Pomáháme lidem bez domova", "time": "17:45", "place": "Místnost 27", "description": "Přijďte pomáhat s přípravou a rozdáváním jídla a pití pro bezdomovce. ", "auto_add": True, "links": [{"url": "https://bit.ly/SluzbaChudym", "label": "Přihlaš se zapsáním do tabulky", "hand": False}], "title_url": "", "hand": False},
    {"id": "5dcaafd3-a526-46fd-8c58-6879d0e08044", "weekday": 1, "title": "Útes", "time": "18:15", "place": "Průjezd Ječná 2", "description": "Přijď kdykoliv.", "auto_add": True, "links": [], "title_url": "", "hand": False},
    {"id": "f86c8a8c-78bf-4d84-bcc6-f825e976da46", "weekday": 1, "title": "Tančírna v Družinské", "time": "18:30", "place": "Družinský sál", "description": "Budeme rádi, když dáš vědět:", "auto_add": True, "links": [{"url": "https://forms.gle/GKS4a7MmbXWxMqDD8", "label": "Přihlásit se", "hand": False}], "title_url": "", "hand": False},
    {"id": "2cecc6d6-9ac2-4cd5-bffe-a9354f9e12ec", "weekday": 2, "title": "Chill out", "time": "16:30", "place": "Podkroví VKH", "description": "Máš před studentskou čas? Přijď chillovat do podkroví VKH. Jsi vítán kdykoliv od 16:30.", "auto_add": True, "links": [], "title_url": "", "hand": False},
    {"id": "24771325-30cb-4ae8-9ec3-a70b89c2a8fa", "weekday": 2, "title": "Ranní modlitba s Písmem", "time": "7:00", "place": "Ječná 2", "description": "Pravidelná modlitba nad Písmem pokračující společnou snídaní.", "auto_add": True, "links": [], "title_url": "", "hand": False},
    {"id": "65e4dbad-850e-42c9-8167-75cfc6c5f0f6", "weekday": 3, "title": "Herní večer", "time": "18:00", "place": "Podkroví VKH", "description": "Deskovky v podkroví (můžeš dorazit i později).", "auto_add": True, "links": [], "title_url": "", "hand": False},
    {"id": "0d0ce406-1d8e-4a30-9a4b-84aea97ddb88", "weekday": 4, "title": "Rorátní mše", "time": "6:15", "place": "Kostel sv. Ignáce, Ječná 2", "description": "Adventní rorátní mše svatá. Svíčky zajištěny, přijď o minutu dříve.", "auto_add": False, "links": []},
    {"id": "c7d548a7-23c2-45d0-8cbd-9714c85a80fe", "weekday": 4, "title": "Křížová cesta na Petříně", "time": "6:20", "place": "Pohořelec", "description": "Tradiční křížovou cestu v postní době. Sraz každý pátek v 6.20 na zastávce Pohořelec.", "auto_add": False, "links": [], "title_url": "", "hand": False},
    {"id": "b45c5a19-cff7-4450-86cd-c26406ffd2d7", "weekday": 5, "title": "Chodíme s jezuity", "time": "", "place": "", "description": "", "auto_add": False, "links": [], "title_url": "", "hand": False},
]

DEFAULT_CONFIG = {
    "week_monday": "",
    "date_range": "",
    "highlight_enabled": False,
    "highlight_title": "",
    "highlight_body": "",
    "highlight_color": "#a76a65",
    "mse_enabled": True,
    "mse_note": "",
    "mse_subevents": DEFAULT_MSE_SUBEVENTS,
    "mse_infoboxes": DEFAULT_MSE_INFOBOXES,
}

SECTIONS = ["V týdnu", "Dále", "Od jinud"]


# ── date helpers ──────────────────────────────────────────────────────────────

def monday_of_week(iso: str):
    try:
        d = datetime.date.fromisoformat(iso)
        return d - datetime.timedelta(days=d.weekday())
    except Exception:
        return None

def next_monday():
    today = datetime.date.today()
    if today.weekday() == 6:
        return today + datetime.timedelta(days=1)
    return today + datetime.timedelta(days=7 - today.weekday())

def fmt_d(d):   return f"{d.day}.{d.month}."
def fmt_wd(d):  return CS_DAYS[d.weekday()]

def fmt_range(mon):
    sun = mon + datetime.timedelta(6)
    y   = sun.year
    if mon.month == sun.month:
        return f"{mon.day}.–{sun.day}. {CS_MONTHS[sun.month-1]} {y}"
    return f"{mon.day}. {CS_MONTHS[mon.month-1]} – {sun.day}. {CS_MONTHS[sun.month-1]} {y}"


# ── persistence helpers ───────────────────────────────────────────────────────

def load_events():
    evs = json.loads(EVENTS_FILE.read_text("utf-8")) if EVENTS_FILE.exists() else []
    return [_migrate_links(e) for e in evs]

def save_events(ev):
    EVENTS_FILE.write_text(json.dumps(ev, ensure_ascii=False, indent=2), "utf-8")

def load_config():
    if CONFIG_FILE.exists():
        return {**DEFAULT_CONFIG, **json.loads(CONFIG_FILE.read_text("utf-8"))}
    return dict(DEFAULT_CONFIG)

def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), "utf-8")

def load_archive():
    return json.loads(ARCHIVE_FILE.read_text("utf-8")) if ARCHIVE_FILE.exists() else []

def save_archive(arc):
    ARCHIVE_FILE.write_text(json.dumps(arc, ensure_ascii=False, indent=2), "utf-8")

def load_akce():
    if AKCE_FILE.exists():
        saved = json.loads(AKCE_FILE.read_text("utf-8"))
        # Ensure every entry has the auto_add field (backwards compat)
        changed = False
        for ak in saved:
            if "auto_add" not in ak:
                # Find matching default by id or title to recover the intended value
                default = next((d for d in DEFAULT_AKCE if d["id"] == ak.get("id") or d["title"] == ak.get("title")), None)
                ak["auto_add"] = default["auto_add"] if default else False
                changed = True
        for ak in saved:
            _migrate_links(ak)
        if changed:
            save_akce(saved)
        return saved
    # seed from defaults
    save_akce(DEFAULT_AKCE)
    return list(DEFAULT_AKCE)

def _parse_links(form, prefix="link_"):
    links = []
    for i in range(20):
        url = (form.get(f"{prefix}{i}_url") or "").strip()
        if not url: continue
        links.append({
            "url":   url,
            "label": (form.get(f"{prefix}{i}_label") or "").strip() or url,
            "hand":  form.get(f"{prefix}{i}_hand") == "on",
        })
    return links


def _migrate_links(obj):
    """Upgrade old link/link_label fields to links list in-place."""
    if "links" not in obj:
        old_url = obj.pop("link", "")
        old_lbl = obj.pop("link_label", "")
        obj["links"] = [{"url": old_url, "label": old_lbl or old_url, "hand": False}] if old_url else []
    return obj


def sort_akce(akce):
    def _key(ak):
        t = ak.get("time", "") or "99:99"
        if t and ":" in t and len(t.split(":")[0]) == 1:
            t = "0" + t
        return (ak.get("weekday", 0), t)
    return sorted(akce, key=_key)

def save_akce(akce):
    AKCE_FILE.write_text(json.dumps(sort_akce(akce), ensure_ascii=False, indent=2), "utf-8")


def new_event(section, date_str="", weekday_str="", iso_str=""):
    return {"id": str(uuid.uuid4()), "section": section, "style": "regular",
            "hand": False, "ticket_color": "#a76a65",
            "title": "Nová událost", "date": date_str, "weekday": weekday_str,
            "iso_date": iso_str,
            "time": "", "place": "", "description": "", "links": []}


# ── app ───────────────────────────────────────────────────────────────────────
app, rt = fast_app(live=False)


# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
APP_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #F5F0EB; --surface: #FDFAF7; --border: #D6CDBF;
  --accent: #8B1A1A; --accent2: #C0392B; --text: #1A1209; --muted: #7A6E62;
  --panel-w: 440px; --radius: 6px; --shadow: 0 2px 12px rgba(0,0,0,.10);
}
body { font-family: 'Source Sans 3', sans-serif; background: var(--bg); color: var(--text); height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent2); text-decoration: underline; }

/* topbar */
.topbar { display:flex; align-items:center; gap:16px; padding:0 24px; height:54px; background:var(--accent); color:#fff; flex-shrink:0; box-shadow:0 2px 8px rgba(0,0,0,.25); }
.topbar h1 { font-family:'Playfair Display',serif; font-size:1.25rem; letter-spacing:.03em; flex:1; }
.topbar .badge { font-size:.7rem; background:rgba(255,255,255,.18); padding:2px 8px; border-radius:20px; letter-spacing:.06em; text-transform:uppercase; }
.topbar .week-label { font-size:.8rem; opacity:.85; }

/* layout */
.workspace { display:flex; flex:1; overflow:hidden; }
.panel { width:var(--panel-w); flex-shrink:0; background:var(--surface); border-right:1px solid var(--border); display:flex; flex-direction:column; overflow:hidden; }
.panel-tabs { display:flex; border-bottom:1px solid var(--border); flex-shrink:0; }
.panel-tab { flex:1; padding:10px 6px; font-size:.78rem; font-weight:600; letter-spacing:.05em; text-transform:uppercase; background:none; border:none; cursor:pointer; color:var(--muted); border-bottom:2px solid transparent; transition:color .15s,border-color .15s; }
.panel-tab:hover { color:var(--accent); }
.panel-tab.active { color:var(--accent); border-bottom-color:var(--accent); }
.panel-body { flex:1; overflow-y:auto; padding:16px; }

/* week picker */
.week-picker-bar { background:#fff8f4; border:1px solid var(--border); border-radius:var(--radius); padding:12px 14px; margin-bottom:16px; }
.week-picker-bar > label { font-size:.72rem; font-weight:600; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); display:block; margin-bottom:4px; }
.week-row { display:flex; gap:8px; align-items:center; }
.week-row input[type=date] { flex:1; padding:6px 8px; border:1px solid var(--border); border-radius:var(--radius); font-size:.82rem; font-family:inherit; }
.week-row input[type=date]:focus { outline:none; border-color:var(--accent); }
.link-row input[type=text],.link-row input:not([type]) { font-size:.78rem; }
.btn-link-add { cursor:pointer; font-size:.75rem; color:var(--accent); text-decoration:underline; }
.btn-week { background:var(--accent); color:#fff; border:none; border-radius:var(--radius); padding:6px 12px; font-size:.78rem; font-weight:600; cursor:pointer; white-space:nowrap; min-width:110px; }
.btn-week:hover { background:var(--accent2); }
.week-info { font-size:.78rem; color:var(--muted); margin-top:6px; }

/* section blocks */
.section-block { margin-bottom:24px; }
.section-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }
.section-label { font-family:'Playfair Display',serif; font-size:.95rem; color:var(--accent); }
.btn-add { background:var(--accent); color:#fff; border:none; border-radius:var(--radius); padding:6px 10px; font-size:.78rem; cursor:pointer; }
.btn-add:hover { background:var(--accent2); }

/* event card */
.event-card { background:#fff; border:1px solid var(--border); border-radius:var(--radius); margin-bottom:8px; overflow:hidden; box-shadow:var(--shadow); }
.event-card-header { display:flex; align-items:center; gap:8px; padding:8px 10px; cursor:grab; background:var(--bg); border-bottom:1px solid var(--border); user-select:none; }
.drag-handle { color:var(--muted); font-size:1rem; flex-shrink:0; }
.event-title-preview { flex:1; font-size:.82rem; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.style-badge { font-size:.65rem; padding:1px 6px; border-radius:10px; background:var(--border); color:var(--muted); text-transform:uppercase; letter-spacing:.04em; flex-shrink:0; }
.style-badge.ticket { background:#fde8e8; color:#8B1A1A; }
.event-card-body { padding:10px; display:none; }
.event-card.open .event-card-body { display:block; }
.toggle-icon { font-size:.7rem; color:var(--muted); flex-shrink:0; }

/* fields */
.field { margin-bottom:10px; }
.field label { display:block; font-size:.72rem; font-weight:600; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin-bottom:3px; }
.field input,.field textarea,.field select { width:100%; padding:6px 8px; border:1px solid var(--border); border-radius:var(--radius); font-size:.82rem; font-family:inherit; background:var(--surface); color:var(--text); }
.field input:focus,.field textarea:focus,.field select:focus { outline:none; border-color:var(--accent); }
.field textarea { resize:vertical; min-height:54px; }
.field-row { display:flex; gap:8px; }
.field-row .field { flex:1; }
.field-check { display:flex; align-items:center; gap:6px; font-size:.82rem; margin-bottom:10px; }
.field-check input[type=checkbox] { accent-color:var(--accent); }
.color-row { display:flex; align-items:center; gap:8px; margin-bottom:10px; }
.color-row label { font-size:.72rem; font-weight:600; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }
.color-row input[type=color] { width:36px; height:28px; border:1px solid var(--border); border-radius:4px; cursor:pointer; padding:2px; }

/* date display in card */
.date-display { font-size:.8rem; color:var(--accent); font-weight:600; display:block; margin-top:4px; }

/* templates bar */
.templates-bar { background:#fff8f4; border:1px solid var(--border); border-radius:var(--radius); padding:10px 12px; margin-bottom:16px; }
.chip-row { display:flex; flex-wrap:wrap; gap:6px; }
.chip-add { background:#fff; border:1px solid var(--border); border-radius:20px; padding:4px 12px; font-size:.75rem; cursor:pointer; color:var(--text); transition:background .15s,border-color .15s; white-space:nowrap; }
.chip-add:hover { background:var(--accent); color:#fff; border-color:var(--accent); }

/* card actions */
.card-actions { display:flex; gap:6px; margin-top:12px; padding-top:10px; border-top:1px solid var(--border); }
.btn-save { flex:1; background:var(--accent); color:#fff; border:none; border-radius:var(--radius); padding:6px; font-size:.78rem; font-weight:600; cursor:pointer; }
.btn-save:hover { background:var(--accent2); }
.btn-delete { background:none; border:1px solid #e0c8c8; color:var(--accent2); border-radius:var(--radius); padding:6px 10px; font-size:.78rem; cursor:pointer; }
.btn-delete:hover { background:#fde8e8; }
.sortable-ghost { opacity:.35; }

/* config */
.config-section { background:#fff; border:1px solid var(--border); border-radius:var(--radius); padding:14px; margin-bottom:16px; box-shadow:var(--shadow); }
.config-section h3 { font-family:'Playfair Display',serif; font-size:.9rem; color:var(--accent); margin-bottom:12px; }
.btn-config-save { background:var(--accent); color:#fff; border:none; border-radius:var(--radius); padding:7px 18px; font-size:.8rem; font-weight:600; cursor:pointer; width:100%; margin-top:4px; }
.btn-config-save:hover { background:var(--accent2); }
.btn-danger { background:none; border:1px solid #e0c8c8; color:var(--accent2); border-radius:var(--radius); padding:6px 14px; font-size:.78rem; font-weight:600; cursor:pointer; width:100%; margin-top:4px; }
.btn-danger:hover { background:#fde8e8; }

/* archive */
.archive-section { background:#fff; border:1px solid var(--border); border-radius:var(--radius); padding:14px; margin-bottom:16px; }
.archive-section h3 { font-family:'Playfair Display',serif; font-size:.9rem; color:var(--accent); margin-bottom:10px; }
.archive-item { display:flex; align-items:center; justify-content:space-between; padding:6px 0; border-bottom:1px solid var(--border); font-size:.8rem; }
.archive-item:last-child { border-bottom:none; }
.archive-item a { color:var(--accent); font-weight:600; text-decoration:none; }

/* mše */
.mse-section { margin-bottom:14px; }
.mse-label-row { display:flex; align-items:center; gap:8px; margin-bottom:8px; font-size:.72rem; font-weight:600; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }
.subevent-card { background:var(--bg); border:1px solid var(--border); border-radius:var(--radius); padding:10px; margin-bottom:6px; }
.infobox-card  { background:var(--bg); border:1px solid var(--border); border-radius:var(--radius); padding:10px; margin-bottom:6px; display:flex; gap:8px; align-items:flex-start; }
.infobox-card .field { margin-bottom:0; flex:1; }
.subevent-remove { background:none; border:1px solid #e0c8c8; color:var(--accent2); border-radius:var(--radius); padding:3px 8px; font-size:.72rem; cursor:pointer; margin-top:4px; }
.subevent-remove:hover { background:#fde8e8; }

/* right pane */
.preview-pane { flex:1; display:flex; flex-direction:column; overflow:hidden; background:#E8E0D5; }
.preview-tabs { display:flex; align-items:center; padding:0 16px; height:44px; background:var(--surface); border-bottom:1px solid var(--border); flex-shrink:0; }
.preview-tab { padding:0 18px; height:100%; display:flex; align-items:center; font-size:.78rem; font-weight:600; letter-spacing:.05em; text-transform:uppercase; background:none; border:none; border-bottom:2px solid transparent; cursor:pointer; color:var(--muted); }
.preview-tab:hover { color:var(--accent); }
.preview-tab.active { color:var(--accent); border-bottom-color:var(--accent); }
.preview-actions { margin-left:auto; display:flex; gap:8px; }
.btn-copy { background:var(--accent); color:#fff; border:none; border-radius:var(--radius); padding:5px 14px; font-size:.75rem; font-weight:600; cursor:pointer; }
.btn-copy:hover { background:var(--accent2); }
.btn-download { text-decoration:none; display:inline-flex; align-items:center; }
.preview-content { flex:1; overflow:auto; padding:24px; display:flex; justify-content:center; min-width:0; }
.preview-frame-wrap { background:#fff; box-shadow:0 4px 32px rgba(0,0,0,.15); border-radius:4px; overflow:visible; width:640px; flex-shrink:0; height:fit-content; }
#preview-frame { width:640px; flex-shrink:0; border:none; display:block; min-height:200px; }
.code-content { flex:1; overflow:auto; padding:16px; }
.code-content pre { background:#1A1209; color:#EDE0CF; border-radius:var(--radius); padding:16px; font-size:.75rem; line-height:1.6; overflow-x:auto; white-space:pre-wrap; word-break:break-all; }

/* akce edit link */
.akce-edit-link { font-size:.72rem; color:var(--accent); text-decoration:none; }
.akce-edit-link:hover { text-decoration:underline; }

/* toast */
#toast { position:fixed; bottom:24px; right:24px; background:var(--accent); color:#fff; padding:10px 20px; border-radius:var(--radius); font-size:.82rem; font-weight:600; opacity:0; transform:translateY(10px); transition:opacity .2s,transform .2s; pointer-events:none; z-index:9999; }
#toast.show { opacity:1; transform:translateY(0); }
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-thumb { background:var(--border); border-radius:3px; }
"""


# ══════════════════════════════════════════════════════════════════════════════
# UI helpers
# ══════════════════════════════════════════════════════════════════════════════

def _link_row(prefix, i, lnk=None):
    """One link row: URL input, label input, hand checkbox, remove button."""
    url   = (lnk or {}).get("url","")
    label = (lnk or {}).get("label","")
    hand  = (lnk or {}).get("hand", False)
    return Div(
        Input(placeholder="URL", value=url,   name=f"{prefix}{i}_url",   style="flex:3;min-width:0;"),
        Input(placeholder="Popisek", value=label, name=f"{prefix}{i}_label", style="flex:2;min-width:0;"),
        Label(
            Input(type="checkbox", name=f"{prefix}{i}_hand", checked=hand, style="margin:0;"),
            " 🖐",
            style="display:flex;align-items:center;gap:2px;cursor:pointer;flex-shrink:0;",
            title="Ikona ruky",
        ),
        Span("✕", cls="btn-link-remove",
             onclick="removeLinkRow(this)",
             style="cursor:pointer;color:#a00;font-size:.85rem;padding:2px 6px;flex-shrink:0;"),
        cls="link-row", style="display:flex;gap:4px;align-items:center;margin-bottom:4px;",
        **{"data-prefix": prefix},
    )


def _links_ui(eid_or_aid, links, prefix):
    rows = [_link_row(prefix, i, lnk) for i, lnk in enumerate(links)]
    return Div(
        Div(Span("Odkazy", style="font-size:.78rem;font-weight:600;color:#555;"),
            Span("+ přidat odkaz", cls="btn-link-add",
                 onclick=f"addLinkRow(this, '{prefix}')",
                 style="margin-left:8px;cursor:pointer;font-size:.75rem;color:var(--accent);text-decoration:underline;"),
            style="display:flex;align-items:center;margin-bottom:4px;"),
        Div(*rows, cls="links-list", id=f"links-{eid_or_aid}",
            **{"data-count": str(len(links))}),
        cls="field",
    )


def event_card_html(ev, open_=False):
    eid   = ev["id"]
    sec   = ev["section"]
    style = ev.get("style","regular")
    badge_cls = "style-badge ticket" if style == "ticket" else "style-badge"
    open_cls  = "event-card open" if open_ else "event-card"
    date_lbl  = f'{ev.get("date","")} {ev.get("weekday","")}'.strip()

    # For V týdnu: show a date picker that converts to Czech format on change.
    # iso_date is stored separately to drive the native date input value.
    iso_date = ev.get("iso_date", "")

    body = Div(
        Div(Label("Styl"),
            Select(
                Option("Regular", value="regular", selected=(style=="regular")),
                Option("Ticket",  value="ticket",  selected=(style=="ticket")),
                name="style", id=f"style-{eid}", onchange=f"updateStyleBadge('{eid}')"),
            cls="field"),
        Div(Label("Barva ticketu"),
            Input(type="color", name="ticket_color", value=ev.get("ticket_color","#a76a65")),
            cls="color-row"),
        Div(Label("Název"),
            Input(name="title", value=ev["title"],
                  oninput=f"document.getElementById('title-preview-{eid}').textContent=this.value||'—'"),
            cls="field"),
        Div(
            Div(Label("Odkaz na název (volitelné)"),
                Input(name="title_url", value=ev.get("title_url",""), placeholder="https://..."),
                cls="field", style="flex:1;"),
            Div(Input(type="checkbox", name="hand", id=f"hand-{eid}", checked=ev.get("hand",False)),
                Label("🖐", **{"for":f"hand-{eid}"}), cls="field-check", style="flex-shrink:0;padding-top:18px;"),
            style="display:flex;gap:8px;align-items:flex-start;",
        ),
        # Date section – date picker for all sections, but V týdnu also stores weekday
        *(
            [Div(
                Label("Datum"),
                Input(type="date", id=f"iso-date-{eid}", value=iso_date,
                      onchange=f"eventDateChanged('{eid}', this.value)"),
                Span(date_lbl or "—", cls="date-display", id=f"date-display-{eid}",
                     style="margin-top:4px;"),
                Input(type="hidden", name="date",     value=ev.get("date",""),    id=f"date-{eid}"),
                Input(type="hidden", name="weekday",  value=ev.get("weekday",""), id=f"weekday-{eid}"),
                Input(type="hidden", name="iso_date", value=iso_date,             id=f"iso-hidden-{eid}"),
                cls="field",
            )] if sec == "V týdnu" else
            [Div(Label("Datum"), Input(name="date", value=ev.get("date","")), cls="field")]
        ),
        Div(Label("Čas"),   Input(name="time",  value=ev.get("time","")),  cls="field"),
        Div(Label("Místo"), Input(name="place", value=ev.get("place","")), cls="field"),
        Div(Label("Popis (lze použít <a href='url'>text</a>)"), Textarea(ev.get("description",""), name="description"), cls="field"),
        _links_ui(eid, ev.get("links", []), prefix="link_"),
        Div(
            Button("Uložit", type="button", cls="btn-save", onclick=f"saveEvent('{eid}')"),
            Button("Smazat", type="button", cls="btn-delete",
                   onclick=f"deleteEvent('{eid}')"),
            cls="card-actions"),
        cls="event-card-body", id=f"body-{eid}",
    )

    header = Div(
        Span("⠿", cls="drag-handle"),
        Span(ev["title"] or "—", cls="event-title-preview", id=f"title-preview-{eid}"),
        Span(date_lbl, style="font-size:.7rem;color:var(--muted);flex-shrink:0;") if date_lbl else "",
        Span(style, cls=badge_cls, id=f"style-badge-{eid}"),
        Span("▾", cls="toggle-icon"),
        cls="event-card-header", onclick=f"toggleCard('{eid}')",
    )

    return Div(header, body, cls=open_cls, id=f"card-{eid}", data_id=eid)


def section_block_html(section, events):
    sec_id = (section.replace(" ","_").replace("í","i").replace("á","a")
              .replace("é","e").replace("ů","u").replace("ž","z"))
    cards = [event_card_html(e) for e in events if e["section"] == section]
    return Div(
        Div(Span(section, cls="section-label"),
            Button("+ Přidat", cls="btn-add",
                   hx_post=f"/event/add/{section}",
                   hx_target=f"#sortable-{sec_id}",
                   hx_swap="beforeend",
                   hx_on__after_request="refreshPreview()"),
            cls="section-header"),
        Div(*cards, cls="sortable-list", id=f"sortable-{sec_id}", data_section=section),
        cls="section-block",
    )


def build_akce_bar(mon=None):
    if mon is None:
        cfg = load_config()
        mon = monday_of_week(cfg.get("week_monday","")) or next_monday()
    akce_list = load_akce()
    chips = []
    for ak in akce_list:
        wday = ak.get("weekday", 0)
        day  = mon + datetime.timedelta(days=wday)
        lbl  = f"{ak['title']} · {fmt_wd(day)} {fmt_d(day)}"
        chips.append(
            Button(f"+ {lbl}", type="button", cls="chip-add",
                   onclick=f"addFromAkce({json.dumps(ak['id'])})")
        )
    return Div(
        Div(
            Span("Akce", style="font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);"),
            A("Upravit akce →", href="#", cls="akce-edit-link", onclick="switchTab('akce'); return false;"),
            style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;",
        ),
        Div(*chips, cls="chip-row") if chips else P("Zatím žádné akce.", style="font-size:.8rem;color:var(--muted);"),
        cls="templates-bar", id="akce-bar",
    )


def events_panel(events, cfg):
    mon_str = cfg.get("week_monday","")
    mon = monday_of_week(mon_str) or next_monday()
    sun = mon + datetime.timedelta(6)

    picker = Div(
        Label("Týden newsletteru"),
        Div(
            Input(type="date", id="week-monday-input", value=mon.isoformat()),
            Button("Použít týden", cls="btn-week", type="button", onclick="applyWeek()"),
            cls="week-row",
        ),
        P(f"Pondělí {fmt_d(mon)} – Neděle {fmt_d(sun)} · {fmt_range(mon)}",
          cls="week-info", id="week-info-label"),
        Button("⇅ Seřadit", cls="btn-week", type="button",
               style="margin-top:6px;background:var(--accent2);",
               hx_post="/event/sort",
               hx_target="#events-panel",
               hx_swap="outerHTML",
               ),
        cls="week-picker-bar",
    )

    # ── Akce panel (user-managed library → quick-add chips) ──
    akce_bar = build_akce_bar(mon)
    return Div(picker, akce_bar, *[section_block_html(s, events) for s in SECTIONS], id="events-panel")


def subevent_row_html(idx, se):
    return Div(
        Div(
            Div(Label("Název"), Input(name=f"se_label_{idx}", value=se.get("label","")), cls="field"),
            Div(Label("Čas"),   Input(name=f"se_time_{idx}",  value=se.get("time","")),  cls="field"),
            cls="field-row",
        ),
        Div(Label("Detail (pod čarou)"), Input(name=f"se_detail_{idx}", value=se.get("detail","")), cls="field"),
        Button("✕ Odebrat", type="button", cls="subevent-remove", onclick=f"removeSubevent({idx})"),
        cls="subevent-card", data_idx=str(idx),
    )


def infobox_row_html(idx, ib):
    return Div(
        Div(Label("Název"), Input(name=f"ib_title_{idx}", value=ib.get("title","")), cls="field"),
        Div(Label("Text"),  Input(name=f"ib_body_{idx}",  value=ib.get("body","")),  cls="field"),
        Button("✕", type="button", cls="subevent-remove", onclick=f"removeInfobox({idx})"),
        cls="infobox-card", data_idx=str(idx),
    )


def akce_card_html(ak, open_=False):
    aid     = ak["id"]
    wday    = ak.get("weekday", 0)
    auto    = ak.get("auto_add", False)
    open_cls = "event-card open" if open_ else "event-card"
    day_name = CS_DAYS[wday]

    header = Div(
        Span("⠿", cls="drag-handle"),
        Span(ak["title"] or "—", cls="event-title-preview", id=f"atitle-{aid}"),
        Span(day_name, style="font-size:.7rem;color:var(--muted);flex-shrink:0;"),
        Span("✓ auto" if auto else "manual", cls="style-badge" + (" ticket" if auto else ""),
             id=f"abadge-{aid}"),
        Span("▾", cls="toggle-icon"),
        cls="event-card-header", onclick=f"toggleCard('a{aid}')",
    )
    body = Div(
        # auto_add checkbox
        Div(
            Input(type="checkbox", id=f"auto-{aid}", checked=auto),
            Label("Přidat automaticky při novém týdnu", **{"for": f"auto-{aid}"}),
            cls="field-check",
        ),
        Div(
            Div(Label("Den v týdnu"),
                Select(*[Option(d, value=str(i), selected=(i==wday))
                         for i, d in enumerate(CS_DAYS)],
                       id=f"awday-{aid}"),
                cls="field"),
            Div(Label("Čas"), Input(name=f"atime-{aid}", id=f"atime-{aid}",
                                    value=ak.get("time","")), cls="field"),
            cls="field-row",
        ),
        Div(Label("Název"), Input(name=f"atitle-inp-{aid}", id=f"atitle-inp-{aid}",
                                   value=ak["title"],
                                   oninput=f"document.getElementById('atitle-{aid}').textContent=this.value||'—'"),
            cls="field"),
        Div(
            Div(Label("Odkaz na název (volitelné)"),
                Input(name=f"atitle_url-{aid}", value=ak.get("title_url",""), placeholder="https://..."),
                cls="field", style="flex:1;"),
            Div(Input(type="checkbox", name=f"ahand-{aid}", id=f"ahand-{aid}", checked=ak.get("hand",False)),
                Label("🖐", **{"for":f"ahand-{aid}"}), cls="field-check", style="flex-shrink:0;padding-top:18px;"),
            style="display:flex;gap:8px;align-items:flex-start;",
        ),
        Div(Label("Místo"), Input(name=f"aplace-{aid}", id=f"aplace-{aid}",
                                   value=ak.get("place","")), cls="field"),
        Div(Label("Popis"), Textarea(ak.get("description",""), name=f"adesc-{aid}",
                                     id=f"adesc-{aid}"), cls="field"),
        _links_ui(aid, ak.get("links", []), prefix=f"alink-{aid}-"),
        Div(
            Button("Uložit", type="button", cls="btn-save", onclick=f"saveAkce('{aid}')"),
            Button("Smazat", type="button", cls="btn-delete", onclick=f"deleteAkce('{aid}')"),
            cls="card-actions",
        ),
        cls="event-card-body", id=f"abody-a{aid}",
    )
    return Div(header, body, cls=open_cls, id=f"card-a{aid}", data_id=f"a{aid}")


def akce_panel(akce_list):
    cards = [akce_card_html(ak) for ak in akce_list]
    return Div(
        Div(
            Span("Akce", cls="section-label"),
            Div(
                Button("+ Nová akce", cls="btn-add", type="button", onclick="newAkce()",
                       style="margin-right:4px;min-width:110px;"),
                Button("💾 Uložit výchozí", cls="btn-week", type="button", onclick="saveAkceDefaults()",
                       title="Uložit aktuální seznam jako výchozí", style="margin-right:4px;min-width:110px;font-weight:normal;"),
                Button("↺ Výchozí", cls="btn-delete", type="button", onclick="resetAkceDefaults()",
                       title="Obnovit výchozí akce", style="min-width:110px;"),
            ),
            style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;",
        ),
        P("Akce označené ✓ auto se automaticky přidají do newsletteru při nastavení týdne nebo archivaci.",
          style="font-size:.78rem;color:var(--muted);margin-bottom:12px;"),
        Div(*cards, id="akce-list"),
        id="akce-panel",
    )


def config_panel(cfg, archive):
    se_cards = [subevent_row_html(i, se) for i, se in enumerate(cfg.get("mse_subevents", DEFAULT_MSE_SUBEVENTS))]
    ib_cards = [infobox_row_html(i, ib)  for i, ib in enumerate(cfg.get("mse_infoboxes", DEFAULT_MSE_INFOBOXES))]

    arc_items = [
        Div(Span(a.get("date_range", a["id"]), style="flex:1;font-size:.8rem;"),
            A("Zobrazit", href=f"/archive/{a['id']}", target="_blank",
              style="font-size:.78rem;color:var(--accent);text-decoration:none;margin-right:8px;"),
            Button("Načíst", cls="btn-add",
                   style="font-size:.72rem;padding:2px 8px;margin-right:4px;",
                   onclick=f"loadArchive('{a['id']}')"),
            Button("Smazat", cls="btn-delete",
                   style="font-size:.72rem;padding:2px 8px;",
                   onclick=f"deleteArchive(this,'{a['id']}')"),
            cls="archive-item", **{"data-arc-id": a['id']})
        for a in reversed(load_archive()[-20:])
    ]

    return Div(
        # newsletter settings
        Div(H3("Nastavení newsletteru"),
            Div(Label("Rozsah dat"),
                Input(name="date_range", id="date-range-input",
                      value=cfg.get("date_range",""),
                      placeholder="Vyplní se automaticky"),
                cls="field"),
            cls="config-section"),

        # highlight box
        Div(H3("Zvýrazněný box (volitelné)"),
            Div(Input(type="checkbox", name="highlight_enabled", id="highlight_enabled",
                      checked=cfg.get("highlight_enabled",False)),
                Label("Zobrazit box", **{"for":"highlight_enabled"}), cls="field-check"),
            Div(Label("Nadpis boxu"), Input(name="highlight_title", value=cfg.get("highlight_title","")), cls="field"),
            Div(Label("Obsah boxu"),  Textarea(cfg.get("highlight_body",""), name="highlight_body"), cls="field"),
            Div(Label("Odkaz (URL)"), Input(name="highlight_link",  value=cfg.get("highlight_link","")),  cls="field"),
            Div(Label("Popisek odkazu"), Input(name="highlight_link_label", value=cfg.get("highlight_link_label","Více informací")), cls="field"),
            Div(Label("Barva boxu"),  Input(type="color", name="highlight_color",
                      value=cfg.get("highlight_color","#a76a65")), cls="color-row"),
            cls="config-section"),

        # studentská mše
        Div(H3("Studentská mše svatá"),
            Div(Input(type="checkbox", name="mse_enabled", id="mse_enabled",
                      checked=cfg.get("mse_enabled",True)),
                Label("Zobrazit sekci", **{"for":"mse_enabled"}), cls="field-check"),
            Div(Label("Poznámka (host, sbírka…)"),
                Textarea(cfg.get("mse_note",""), name="mse_note"), cls="field"),
            # sub-events
            Div(Div(Span("Dílčí události"), Button("+ Přidat", type="button", cls="btn-add", onclick="addSubevent()"), cls="mse-label-row"),
                Div(*se_cards, id="subevent-list"), cls="mse-section"),
            # info boxes
            Div(Div(Span("Info boxy (3 sloupce)"), Button("+ Přidat", type="button", cls="btn-add", onclick="addInfobox()"), cls="mse-label-row"),
                Div(*ib_cards, id="infobox-list"), cls="mse-section"),
            cls="config-section"),

        Button("Uložit nastavení", cls="btn-config-save", type="button", onclick="saveConfig()"),

        # archive + new
        Div(H3("Nový newsletter"),
            P("Archivuje aktuální a posune týden o +7 dní.", style="font-size:.8rem;color:var(--muted);margin-bottom:10px;"),
            Button("📦 Archivovat a nový", cls="btn-danger", type="button", onclick="archiveAndNew()"),
            cls="config-section", style="margin-top:16px;"),

        Div(H3("Archiv"), *(arc_items or [P("Zatím prázdný.", style="font-size:.8rem;color:var(--muted);")]),
            cls="archive-section") if True else Div(),

        id="config-panel",
    )


# ══════════════════════════════════════════════════════════════════════════════
# Routes
# ══════════════════════════════════════════════════════════════════════════════

@rt("/")
def get():
    events  = load_events()
    cfg     = load_config()
    archive = load_archive()
    return Html(
        Head(
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Title("VKH Praha – Newsletter Builder"),
            Link(rel="preconnect", href="https://fonts.googleapis.com"),
            Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
            Link(rel="stylesheet",
                 href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Source+Sans+3:wght@300;400;600&display=swap"),
            Script(src="https://unpkg.com/htmx.org@1.9.12"),
            Script(src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.2/Sortable.min.js"),
            Style(APP_CSS),
        ),
        Body(
            Div(H1("VKH Praha"), Span("Newsletter Builder", cls="badge"),
                Span(cfg.get("date_range","—"), cls="week-label", id="topbar-week"),
                cls="topbar"),
            Div(
                Div(
                    Div(Button("Události",  cls="panel-tab active", id="tab-events", onclick="switchTab('events')"),
                        Button("Akce",      cls="panel-tab",         id="tab-akce",   onclick="switchTab('akce')"),
                        Button("Nastavení", cls="panel-tab",         id="tab-config", onclick="switchTab('config')"),
                        cls="panel-tabs"),
                    Div(Div(events_panel(events, cfg), id="tab-events-body"),
                        Div(akce_panel(load_akce()),   id="tab-akce-body",   style="display:none"),
                        Div(config_panel(cfg, archive),id="tab-config-body", style="display:none"),
                        cls="panel-body"),
                    cls="panel"),
                Div(
                    Div(Button("Náhled",   cls="preview-tab active", id="ptab-preview", onclick="switchPreviewTab('preview')"),
                        Button("HTML kód", cls="preview-tab",         id="ptab-code",    onclick="switchPreviewTab('code')"),
                        Div(Button("Kopírovat HTML", cls="btn-copy", onclick="copyHtml()"),
                            A("⬇ Stáhnout", href="/download", cls="btn-copy btn-download"),
                            cls="preview-actions"),
                        cls="preview-tabs"),
                    Div(Div(Iframe(src="/preview", id="preview-frame", scrolling="yes"), cls="preview-frame-wrap"),
                        cls="preview-content", id="preview-pane"),
                    Div(Pre("", id="code-pre"), cls="code-content", id="code-pane", style="display:none"),
                    cls="preview-pane"),
                cls="workspace"),
            Div(id="toast"),
            Script(FRONTEND_JS),
        ),
    )


def event_from_akce(ak: dict, mon) -> dict:
    """Build a fully-populated event dict from an akce entry for a given Monday."""
    wday = ak.get("weekday", 0)
    day  = mon + datetime.timedelta(days=wday)
    ev   = new_event("V týdnu", fmt_d(day), fmt_wd(day), day.isoformat())
    ev["title"]       = ak.get("title", "")
    ev["title_url"]   = ak.get("title_url", "")
    ev["hand"]        = ak.get("hand", False)
    ev["time"]        = ak.get("time", "")
    ev["place"]       = ak.get("place", "")
    ev["description"] = ak.get("description", "")
    ev["links"]       = ak.get("links", [])
    return ev


@rt("/event/add/{section}")
def post(section: str):
    events = load_events()
    cfg    = load_config()
    mon    = monday_of_week(cfg.get("week_monday","")) or next_monday()
    date_str, wd_str, iso_str = "", "", ""
    if section == "V týdnu":
        date_str = fmt_d(mon)
        wd_str   = fmt_wd(mon)
        iso_str  = mon.isoformat()
    ev = new_event(section, date_str, wd_str, iso_str)
    events.append(ev)
    save_events(events)
    return event_card_html(ev, open_=True)


@rt("/event/add-from-akce/{aid}")
def post(aid: str):
    """Server-side: create a fully populated event from an akce entry and return its card HTML."""
    akce_list = load_akce()
    cfg       = load_config()
    mon       = monday_of_week(cfg.get("week_monday","")) or next_monday()
    ak = next((a for a in akce_list if a["id"] == aid), None)
    if not ak:
        return JSONResponse({"ok": False})
    events = load_events()
    ev = event_from_akce(ak, mon)
    events.append(ev)
    save_events(events)
    return event_card_html(ev, open_=True)


@rt("/event/{eid}")
def delete(eid: str):
    save_events([e for e in load_events() if e["id"] != eid])
    return ""


@rt("/event/save/{eid}")
async def post(eid: str, req: Request):
    form = await req.form()
    events = load_events()
    for ev in events:
        if ev["id"] == eid:
            ev.update({
                "style":       form.get("style","regular"),
                "hand":        form.get("hand") == "on",
                "ticket_color":form.get("ticket_color","#a76a65"),
                "title":       form.get("title",""),
                "title_url":   form.get("title_url",""),
                "date":        form.get("date",""),
                "weekday":     form.get("weekday",""),
                "iso_date":    form.get("iso_date",""),
                "time":        form.get("time",""),
                "place":       form.get("place",""),
                "description": form.get("description",""),
                "links":       _parse_links(form),
            })
            break
    save_events(events)
    return JSONResponse({"ok": True})


def sort_key(ev):
    """Return a sortable key for an event: (date, time). iso_date preferred, else parse Czech date string."""
    iso = ev.get("iso_date", "")
    base_date = None
    if iso:
        try:
            base_date = datetime.date.fromisoformat(iso)
        except Exception:
            pass
    if base_date is None:
        # Fallback: parse "3.3." or "3.3" against current year
        raw = ev.get("date", "").strip().rstrip(".")
        parts = raw.split(".")
        try:
            d, m = int(parts[0]), int(parts[1])
            base_date = datetime.date(datetime.date.today().year, m, d)
        except Exception:
            base_date = datetime.date(9999, 1, 1)  # unknown dates go last
    t = ev.get("time", "") or "99:99"
    if t and ":" in t and len(t.split(":")[0]) == 1:
        t = "0" + t
    return (base_date, t)


@rt("/event/sort")
def post():
    events = load_events()
    cfg    = load_config()
    # Sort each section independently by date
    vtydnu = sorted([e for e in events if e["section"] == "V týdnu"], key=sort_key)
    dale   = sorted([e for e in events if e["section"] == "Dále"],    key=sort_key)
    jinud  = sorted([e for e in events if e["section"] == "Od jinud"],key=sort_key)
    save_events(vtydnu + dale + jinud)
    # Return re-rendered events panel so DOM is in sync
    return events_panel(load_events(), cfg)


@rt("/event/reorder")
async def post(req: Request):
    body     = await req.json()
    events   = load_events()
    id_map   = {e["id"]: e for e in events}
    ordered  = []
    for grp in body:
        for eid in grp["ids"]:
            if eid in id_map:
                id_map[eid]["section"] = grp["section"]
                ordered.append(id_map[eid])
    seen = {e["id"] for e in ordered}
    ordered += [e for e in events if e["id"] not in seen]
    save_events(ordered)
    return JSONResponse({"ok": True})


@rt("/week/set")
async def post(req: Request):
    body    = await req.json()
    mon     = monday_of_week(body.get("monday",""))
    if not mon:
        return JSONResponse({"ok": False})
    cfg = load_config()
    cfg["week_monday"] = mon.isoformat()
    cfg["date_range"]  = fmt_range(mon)
    save_config(cfg)
    # 1. Auto-add Akce with auto_add=True that aren't already in the newsletter
    akce_list = load_akce()
    events    = load_events()
    existing_titles = {e["title"].strip().lower() for e in events if e["section"] == "V týdnu"}
    for ak in akce_list:
        if not ak.get("auto_add"):
            continue
        if ak["title"].strip().lower() in existing_titles:
            continue  # already present – just update its date below
        ev = event_from_akce(ak, mon)
        events.append(ev)
        existing_titles.add(ak["title"].strip().lower())

    # 2. Update dates on all existing V týdnu events that match Akce or RECURRING_WEEKDAY map
    akce_wday = {ak["title"].strip().lower(): ak.get("weekday", 0) for ak in akce_list}
    for ev in events:
        if ev["section"] != "V týdnu":
            continue
        key  = ev["title"].strip().lower()
        wday = akce_wday.get(key, RECURRING_WEEKDAY.get(key))
        if wday is not None:
            day = mon + datetime.timedelta(days=wday)
            ev["date"]     = fmt_d(day)
            ev["weekday"]  = fmt_wd(day)
            ev["iso_date"] = day.isoformat()
    save_events(events)
    sun = mon + datetime.timedelta(6)
    return JSONResponse({
        "ok": True,
        "date_range": cfg["date_range"],
        "week_label": f"Pondělí {fmt_d(mon)} – Neděle {fmt_d(sun)} · {fmt_range(mon)}",
    })


@rt("/event/setdate/{eid}")
async def post(eid: str, req: Request):
    """Accept an ISO date string, convert to Czech date + weekday name."""
    body     = await req.json()
    iso      = body.get("iso_date", "")
    day      = monday_of_week(iso)   # monday_of_week just parses any ISO date
    if day is None:
        return JSONResponse({"ok": False})
    # Re-parse as the exact date (monday_of_week shifts to Mon; we want the actual date)
    try:
        day = datetime.date.fromisoformat(iso)
    except Exception:
        return JSONResponse({"ok": False})
    events = load_events()
    for ev in events:
        if ev["id"] == eid:
            ev["date"]     = fmt_d(day)
            ev["weekday"]  = fmt_wd(day)
            ev["iso_date"] = iso
            break
    save_events(events)
    return JSONResponse({"date": fmt_d(day), "weekday": fmt_wd(day),
                         "label": f"{fmt_d(day)} {fmt_wd(day)}", "iso": iso})


@rt("/akce/chips")
def get():
    """Return a fresh akce-bar as raw HTML (no page wrapper)."""
    return HTMLResponse(to_xml(build_akce_bar()))


@rt("/akce/panel")
def get():
    """Return a fully re-rendered akce panel as raw HTML (no page wrapper)."""
    return HTMLResponse(to_xml(akce_panel(load_akce())))


@rt("/akce/save-defaults")
def post():
    """Save current akce list as the new defaults."""
    AKCE_DEFAULTS_FILE.write_text(
        json.dumps(load_akce(), ensure_ascii=False, indent=2), "utf-8")
    return JSONResponse({"ok": True})


@rt("/akce/reset-defaults")
def post():
    """Reset to custom defaults if saved, else fall back to built-in DEFAULT_AKCE."""
    if AKCE_DEFAULTS_FILE.exists():
        defaults = json.loads(AKCE_DEFAULTS_FILE.read_text("utf-8"))
    else:
        defaults = [dict(d) for d in DEFAULT_AKCE]
    save_akce(defaults)
    return JSONResponse({"ok": True})


@rt("/akce/new")
def post():
    akce = load_akce()
    new_ak = {"id": str(uuid.uuid4()), "weekday": 0, "title": "Nová akce",
              "time": "", "place": "", "description": "", "link": "", "auto_add": False}
    akce.append(new_ak)
    save_akce(akce)
    return JSONResponse({"ok": True, "ak": new_ak})


@rt("/akce/save/{aid}")
async def post(aid: str, req: Request):
    form  = await req.form()
    akce  = load_akce()
    for ak in akce:
        if ak["id"] == aid:
            ak["weekday"]     = int(form.get(f"awday-{aid}", ak["weekday"]))
            ak["title"]       = form.get(f"atitle-inp-{aid}", ak["title"])
            ak["title_url"]   = form.get(f"atitle_url-{aid}", "")
            ak["hand"]        = form.get(f"ahand-{aid}") == "on"
            ak["time"]        = form.get(f"atime-{aid}", "")
            ak["place"]       = form.get(f"aplace-{aid}", "")
            ak["description"] = form.get(f"adesc-{aid}", "")
            ak["links"]       = _parse_links(form, prefix=f"alink-{aid}-")
            ak["auto_add"]    = form.get(f"auto-{aid}") == "on"
            break
    save_akce(akce)
    return JSONResponse({"ok": True})


@rt("/akce/delete/{aid}")
def delete(aid: str):
    save_akce([a for a in load_akce() if a["id"] != aid])
    return JSONResponse({"ok": True})


@rt("/config/save")
async def post(req: Request):
    form = await req.form()
    cfg  = load_config()
    cfg.update({
        "date_range":        form.get("date_range", cfg.get("date_range","")),
        "highlight_enabled": form.get("highlight_enabled") == "on",
        "highlight_title":   form.get("highlight_title",""),
        "highlight_body":    form.get("highlight_body",""),
        "highlight_color":      form.get("highlight_color","#a76a65"),
        "highlight_link":       form.get("highlight_link",""),
        "highlight_link_label": form.get("highlight_link_label","Více informací"),
        "mse_enabled":       form.get("mse_enabled") == "on",
        "mse_note":          form.get("mse_note",""),
    })
    ses, i = [], 0
    while form.get(f"se_label_{i}") is not None:
        ses.append({"label": form.get(f"se_label_{i}",""), "time": form.get(f"se_time_{i}",""), "detail": form.get(f"se_detail_{i}","")})
        i += 1
    cfg["mse_subevents"] = ses
    ibs, j = [], 0
    while form.get(f"ib_title_{j}") is not None:
        ibs.append({"title": form.get(f"ib_title_{j}",""), "body": form.get(f"ib_body_{j}","")})
        j += 1
    cfg["mse_infoboxes"] = ibs
    save_config(cfg)
    return JSONResponse({"ok": True})


@rt("/newsletter/archive")
async def post(req: Request):
    events, cfg, arc = load_events(), load_config(), load_archive()
    arc.append({"id": str(uuid.uuid4()), "date_range": cfg.get("date_range",""), "events": events, "config": cfg})
    save_archive(arc)
    # advance week by 7 days, carry over mše template
    mon     = monday_of_week(cfg.get("week_monday",""))
    new_mon = (mon + datetime.timedelta(7)) if mon else next_monday()
    new_cfg = dict(DEFAULT_CONFIG)
    new_cfg.update({"week_monday": new_mon.isoformat(), "date_range": fmt_range(new_mon),
                    "mse_subevents": cfg.get("mse_subevents", DEFAULT_MSE_SUBEVENTS),
                    "mse_infoboxes": cfg.get("mse_infoboxes", DEFAULT_MSE_INFOBOXES)})
    save_config(new_cfg)
    # Auto-populate new newsletter with auto_add akce
    new_events = []
    for ak in load_akce():
        if ak.get("auto_add"):
            new_events.append(event_from_akce(ak, new_mon))
    save_events(new_events)
    return JSONResponse({"ok": True})


@rt("/archive/{arc_id}")
def get(arc_id: str):
    for a in load_archive():
        if a["id"] == arc_id:
            return HTMLResponse(build_newsletter_html(a["events"], a["config"]))
    return HTMLResponse("<h1>Nenalezeno</h1>", status_code=404)

@rt("/archive/{arc_id}/delete")
def post(arc_id: str):
    arc = [a for a in load_archive() if a["id"] != arc_id]
    save_archive(arc)
    return JSONResponse({"ok": True})

@rt("/archive/{arc_id}/load")
def post(arc_id: str):
    for a in load_archive():
        if a["id"] == arc_id:
            save_events(a["events"])
            save_config(a["config"])
            return JSONResponse({"ok": True})
    return JSONResponse({"ok": False}, status_code=404)


@rt("/preview")
def get():
    return HTMLResponse(build_newsletter_html(load_events(), load_config()))

@rt("/html")
def get():
    return HTMLResponse(build_newsletter_html(load_events(), load_config()),
                        headers={"Content-Type": "text/plain; charset=utf-8"})

@rt("/download")
def get():
    cfg  = load_config()
    raw  = cfg.get("date_range","newsletter")
    # Transliterate Czech chars so the filename stays ASCII (HTTP headers are latin-1)
    _tr = str.maketrans("áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ",
                        "acdeeinorstuuyzACDEEINORSTUUYZ")
    slug = raw.translate(_tr).replace(" ","_").replace(".","").replace("–","-").replace("—","-")
    html = build_newsletter_html(load_events(), cfg)
    return Response(html, media_type="text/html; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="newsletter_{slug}.html"'})


# ══════════════════════════════════════════════════════════════════════════════
# Newsletter HTML generator
# ══════════════════════════════════════════════════════════════════════════════

HAND_IMG   = ('<img src="https://vkhpraha.cz/wp-content/uploads/2025/10/hand.png" alt=""'
              ' style="display:inline-block;width:26px;height:auto;border:0;vertical-align:middle;margin-left:6px;">')
VKH_LOGO   = ('<img src="https://vkhpraha.cz/wp-content/uploads/2025/10/vkh-red.png" alt="VKH"'
              ' style="display:block;width:30px;height:auto;border:0;">')
DOUBLE_RULE = (
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">'
    '<tr><td style="height:3px;background:#222;line-height:3px;font-size:3px;">&nbsp;</td></tr>'
    '<tr><td style="height:6px;line-height:6px;font-size:6px;">&nbsp;</td></tr>'
    '<tr><td style="height:1px;background:#999;line-height:1px;font-size:1px;">&nbsp;</td></tr></table>')
THIN_RULE  = (
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">'
    '<tr><td style="height:1px;background:#222;line-height:1px;font-size:1px;">&nbsp;</td></tr></table>')


def build_newsletter_html(events: list, cfg: dict) -> str:
    date_range = cfg.get("date_range", "")

    _TS = "font-family:Georgia,'Times New Roman',serif;font-size:14px;text-transform:uppercase;letter-spacing:1px;color:#444;font-weight:700;text-decoration:none;"

    def a_title(title, url=""):
        if url:
            return f'<a href="{url}" style="{_TS}">{title}</a>'
        return f'<span style="{_TS}">{title}</span>'

    def render_links_html(links):
        parts = []
        for lnk in (links or []):
            url = lnk.get("url",""); label = lnk.get("label","") or url
            if not url: continue
            parts.append(f'<div style="margin-top:5px;font-size:13px;"><a href="{url}" style="color:#7D211A;font-weight:600;text-decoration:none;">{label}</a></div>')
        return "".join(parts)

    def render_regular(ev, show_date=True):
        title = ev.get("title",""); date = ev.get("date",""); wday = ev.get("weekday","")
        time_ = ev.get("time",""); place = ev.get("place",""); desc = ev.get("description","")
        links = ev.get("links",[]); hand = ev.get("hand",False); title_url = ev.get("title_url","")
        date_hdr = (
            f'<div style="padding:0 0 5px 0;">'
            f'<span style="display:inline-block;padding:2px 4px;text-transform:uppercase;font-family:Georgia,serif;font-size:30px;line-height:1.05;color:#111;font-weight:700;margin:0 6px;">{date}</span>'
            f'<span style="padding-left:4px;display:inline-block;text-transform:uppercase;font-family:Georgia,serif;font-size:14px;line-height:1.05;color:#111;font-weight:700;margin:0 6px;">{wday}</span>'
            f'</div>'
        ) if (date and show_date) else ""
        tp_parts = [x for x in [time_, place] if x]
        tp_line  = (f'<div style="font-size:13px;color:#888;padding:0 0 2px 0;">'
                    + "&nbsp;&middot;&nbsp;".join(tp_parts) + '</div>') if tp_parts else ""
        d_line  = f'<div style="font-size:14px;color:#666;line-height:1.4;padding:4px 0 0 0;">{desc}</div>' if desc else ""
        hand_h  = HAND_IMG if hand else ""
        lnks_h  = render_links_html(links)
        pill = (
            '<div style="border:2px solid #7D211A;border-radius:30px;padding:13px 13px 13px 25px;'
            'background:#ffffff;font-size:14px;line-height:1.3;width:400px;box-sizing:border-box;margin:0 0 10px 0;">'
            f'{a_title(title, title_url)}{hand_h}<br>{tp_line}{d_line}{lnks_h}</div>'
        )
        return date_hdr + pill

    def render_ticket(ev):
        title = ev.get("title",""); date = ev.get("date",""); time_ = ev.get("time","")
        place = ev.get("place",""); desc = ev.get("description","")
        links = ev.get("links",[]); tc = ev.get("ticket_color","#a76a65")
        hand  = ev.get("hand",False)
        dt    = " ".join(p for p in [date, time_] if p)
        dr    = f'<span style="float:right;font-family:Georgia,serif;font-weight:700;color:#fff;">{dt}</span>' if dt else ""
        pl    = f'<div style="font-size:13px;color:#fff;opacity:.85;padding:2px 0;">{place}</div>' if place else ""
        de    = f'<div style="font-size:14px;color:#fff;line-height:1.3;">{desc}</div>' if desc else ""
        lh    = render_links_html(links)
        hh    = HAND_IMG if hand else ""
        return (
            f'<div style="width:400px;margin:10px 0;padding:15px 20px;box-sizing:border-box;'
            f'background:radial-gradient(circle at 0% 50%,transparent 6px,{tc} 6px) left/50% 100% no-repeat,'
            f'radial-gradient(circle at 100% 50%,transparent 6px,{tc} 6px) right/50% 100% no-repeat;'
            f'border-radius:8px;">'
            f'<div style="border-bottom:1px dashed #fff;padding-bottom:10px;margin-bottom:10px;">'
            f'<span style="font-family:Georgia,serif;font-size:16px;font-weight:700;text-transform:uppercase;color:#fff;">{title}</span>'
            f'{dr}<div style="clear:both;"></div></div>{pl}{de}{lh}{hh}'
            f'</div>'
        )

    def render_dale(ev):
        title = ev.get("title",""); date = ev.get("date",""); time_ = ev.get("time","")
        place = ev.get("place",""); desc = ev.get("description","")
        links = ev.get("links",[]); hand  = ev.get("hand",False)
        dt    = " ".join(p for p in [date, time_] if p)
        dtl   = f'<div style="font-size:14px;color:#666;">{dt}</div>' if dt else ""
        pl    = f'<div style="font-size:13px;color:#888;">{place}</div>' if place else ""
        de    = f'<br>{desc}' if desc else ""
        hh    = HAND_IMG if hand else ""
        lh    = render_links_html(links)
        return (
            '<tr><td style="background:#f0f0f0;border-radius:30px;padding:13px 13px 13px 25px;'
            'font-size:14px;line-height:1.4;width:400px;max-width:100%;margin:0 0 12px 0;display:block;box-sizing:border-box;">'
            f'{dtl}{pl}{a_title(title)}{hh}{de}{lh}</td></tr>'
            '<tr><td style="height:10px;"></td></tr>'
        )

    def day_header_html(date, wday):
        """Day+weekday header as a plain div — lives inside the 400px left column."""
        if not date: return ""
        return (
            f'<div style="padding:4px 0 3px 8px;margin-top:4px;">'
            f'<span style="font-family:Georgia,serif;font-size:30px;line-height:1.05;color:#111;font-weight:700;">{date}</span>'
            f'&nbsp;<span style="font-family:Georgia,serif;font-size:14px;text-transform:uppercase;color:#111;font-weight:700;vertical-align:middle;">{wday}</span>'
            f'</div>'
        )

    def vtydnu_block(evs, mse_html="", highlight_html=""):
        if not evs and not mse_html and not highlight_html: return ""

        # Group events by day, preserving order
        groups = []
        seen_day = None
        for e in evs:
            day_key = (e.get("date",""), e.get("weekday",""))
            if day_key != seen_day:
                groups.append((e.get("date",""), e.get("weekday",""), []))
                seen_day = day_key
            groups[-1][2].append(e)

        # Find which group contains the last Wednesday event (for mše placement)
        # mše goes AFTER the two-column table, before Thursday+ events
        wed_group_idx = -1
        for gi, (date, wday, day_evs) in enumerate(groups):
            if wday.strip() == "Středa":
                wed_group_idx = gi

        # Split groups: those in the two-column section (up to and including Wednesday)
        # and those after (Thursday onwards, rendered full-width below mše)
        if mse_html and wed_group_idx >= 0:
            col_groups  = groups[:wed_group_idx + 1]
            post_groups = groups[wed_group_idx + 1:]
        else:
            col_groups  = groups
            post_groups = []

        # Build left-column content: highlight box + day headers + events (up to/incl Wednesday)
        left_parts = []
        if highlight_html:
            left_parts.append(highlight_html)
        for date, wday, day_evs in col_groups:
            left_parts.append(day_header_html(date, wday))
            for e in day_evs:
                if e.get("style") == "ticket":
                    left_parts.append(render_ticket(e))
                else:
                    left_parts.append(render_regular(e, show_date=False))

        left_content = "".join(left_parts)

        # Two-column table: events left (400px), image right (200px)
        result = (
            '<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"'
            ' style="width:600px;max-width:100%;margin:0;border-collapse:collapse;">'
            '<tr>'
            f'<td valign="top" width="400" style="width:400px;box-sizing:border-box;vertical-align:top;text-align:left;">'
            f'{left_content}</td>'
            '<td valign="top" width="200" style="width:200px;padding:0 0 0 10px;box-sizing:border-box;vertical-align:top;text-align:center;">'
            '<img src="https://vkhpraha.cz/wp-content/uploads/2025/10/universal2_bile_pozadi.png" alt="VKH"'
            ' style="display:block;width:200px;max-width:100%;height:auto;border:0;"></td>'
            '</tr></table>'
        )

        # Mše block full-width, outside the two-column table
        if mse_html:
            result += mse_html

        # Remaining days (Thursday+) below mše, same 400px left-column alignment as pre-Wednesday
        if post_groups:
            post_content = ""
            for date, wday, day_evs in post_groups:
                post_content += day_header_html(date, wday)
                for e in day_evs:
                    if e.get("style") == "ticket":
                        post_content += render_ticket(e)
                    else:
                        post_content += render_regular(e, show_date=False)
            result += (
                '<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"'
                ' style="width:600px;max-width:100%;margin:0;border-collapse:collapse;">'
                '<tr>'
                '<td valign="top" width="400" style="width:400px;box-sizing:border-box;vertical-align:top;text-align:left;">'
                f'{post_content}</td>'
                '<td width="200" style="width:200px;"></td>'
                '</tr></table>'
            )

        # If no Wednesday at all but mše enabled, append at end
        if mse_html and wed_group_idx == -1:
            result += mse_html

        return result

    def dale_block(name, evs):
        if not evs: return ""
        rows = "".join(render_dale(e) for e in evs)
        return (
            '<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"'
            ' style="max-width:100%;margin:10px 0 10px 30px;border-collapse:collapse;">'
            f'<tr><td><div style="font-family:Georgia,serif;font-size:18px;color:#111;font-weight:600;text-transform:uppercase;text-align:center;margin:0 0 13px 0;">{name}:</div></td></tr>'
            f'{rows}</table>'
        )

    def mse_block():
        if not cfg.get("mse_enabled", True): return ""
        mse_time  = cfg.get("mse_time","19:00")
        note      = cfg.get("mse_note","")
        subevents = cfg.get("mse_subevents", DEFAULT_MSE_SUBEVENTS)
        infoboxes = cfg.get("mse_infoboxes", DEFAULT_MSE_INFOBOXES)
        note_h = f'<div style="font-size:13px;color:#555;padding:0 0 8px 0;">{note}</div>' if note else ""
        se_html = ""
        for se in subevents:
            lbl = se.get("label",""); t = se.get("time",""); det = se.get("detail","")
            ttd = (f'<td style="text-align:right;font-family:Georgia,serif;font-size:18px;color:#7D211A;font-weight:700;white-space:nowrap;">{t}</td>' if t else "<td></td>")
            dd  = f'<div style="padding:0 0 8px 30px;font-size:13px;color:#555;line-height:1.4;">{det}</div>' if det else ""
            se_html += (
                '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">'
                f'<tr><td style="font-family:Georgia,serif;font-size:14px;color:#111;font-weight:bold;">{lbl}</td>{ttd}</tr>'
                f'</table>{dd}'
            )
        ib_cells = "".join(
            f'<td style="padding-right:8px;vertical-align:top;">'
            f'<div style="background:#f0f0f0;color:#111;padding:8px;border-radius:6px;font-family:Georgia,serif;font-size:13px;">'
            f'<b style="color:#111;">{ib.get("title","")}</b><br>{ib.get("body","")}</div></td>'
            for ib in infoboxes
        )
        ib_html = (
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">'
            f'<tr>{ib_cells}</tr></table>'
        ) if ib_cells else ""
        return (
            '<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"'
            ' style="width:600px;max-width:100%;margin:0;border-collapse:collapse;">'
            '<tr><td align="right" style="background:#fff;padding:12px 0 0 0;">'
            '<span style="font-family:Georgia,serif;padding:12px 15px 2px 0;font-size:30px;line-height:1.05;color:#111;font-weight:700;">'
            'Studentsk\u00e1 m\u0161e svat\u00e1</span>'
            f'<span style="color:#7D211A;font-family:Georgia,serif;padding:12px 0 2px 0;font-size:18px;font-weight:700;">{mse_time}</span>'
            '</td></tr></table>'
            '<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"'
            ' style="width:600px;max-width:100%;margin:0;border-collapse:collapse;">'
            f'<tr><td colspan="2" width="600">{THIN_RULE}</td></tr>'
            '<tr>'
            '<td valign="top" style="width:180px;padding:8px 10px 0 10px;box-sizing:border-box;vertical-align:top;">'
            '<img src="https://vkhpraha.cz/wp-content/uploads/2025/09/sv_ignac_bily.png" alt="Sv. Ignác"'
            ' style="display:block;width:180px;max-width:100%;height:auto;"></td>'
            '<td valign="top" style="width:420px;padding:8px 0 12px 0;box-sizing:border-box;vertical-align:top;text-align:left;">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">'
            f'<tr><td style="background:#fff;padding:4px 0 8px 4px;box-sizing:border-box;">{note_h}{se_html}{ib_html}</td></tr>'
            '</table></td></tr>'
            f'<tr><td colspan="2" style="padding:0 20px 5px 20px;">{DOUBLE_RULE}</td></tr>'
            '</table>'
        )

    def highlight_block():
        if not cfg.get("highlight_enabled"): return ""
        tc   = cfg.get("highlight_color","#a76a65")
        htit = cfg.get("highlight_title","")
        hbod = cfg.get("highlight_body","")
        hlnk = cfg.get("highlight_link","")
        hlbl = cfg.get("highlight_link_label","Více informací")
        td   = f'<div style="border-bottom:1px dashed #fff;padding-bottom:10px;margin-bottom:10px;font-family:Georgia,serif;font-size:16px;font-weight:700;text-transform:uppercase;color:#fff;">{htit}</div>' if htit else ""
        bd   = f'<div style="font-size:14px;color:#fff;line-height:1.4;">{hbod}</div>' if hbod else ""
        lh   = f'<div style="margin-top:8px;"><a href="{hlnk}" style="color:#fff;font-weight:700;text-decoration:underline;font-size:13px;">{hlbl}</a></div>' if hlnk else ""
        return (
            f'<div style="width:400px;margin:10px 0 16px 0;padding:15px 20px;box-sizing:border-box;'
            f'background:radial-gradient(circle at 0% 50%,transparent 6px,{tc} 6px) left/50% 100% no-repeat,'
            f'radial-gradient(circle at 100% 50%,transparent 6px,{tc} 6px) right/50% 100% no-repeat;'
            f'border-radius:8px;">'
            f'{td}{bd}{lh}'
            f'</div>'
        )

    vtydnu_evs = [e for e in events if e["section"] == "V týdnu"]
    dale_evs   = [e for e in events if e["section"] == "Dále"]
    jinud_evs  = [e for e in events if e["section"] == "Od jinud"]
    rule = (
        '<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"'
        ' style="max-width:100%;margin:0;border-collapse:collapse;">'
        f'<tr><td style="padding:0 20px 5px 20px;">{DOUBLE_RULE}</td></tr></table>'
    ) if (dale_evs or jinud_evs) else ""

    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="referrer" content="no-referrer">
  <title>VKH Newsletter</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <style>
    body{{margin:0;padding:0;background:#fff;font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#666;letter-spacing:0.6px;}}
    @media only screen and (max-width:500px){{.container{{width:100%!important;max-width:100%!important;}}}}
  </style>
</head>
<body style="margin:0;padding:0;background:#fff;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#fff">
<tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
       style="width:600px;max-width:100%;margin:0 auto;border-collapse:collapse;background:#fff;">
  <tr>
    <td style="padding:10px 0 4px 0;">{VKH_LOGO}</td>
    <td style="padding:10px 10px 0 0;text-align:right;font-family:Georgia,'Times New Roman',serif;font-size:13px;color:#444;">
      <div style="color:#111;font-weight:700;">t&#253;denn&#237; d&#225;vka nov&#253;ch akc&#237;</div>
    </td>
  </tr>
  <tr><td colspan="2">{THIN_RULE}</td></tr>
  <tr><td colspan="2" style="padding:18px 20px 6px 20px;text-align:center;">
    <div style="font-family:Georgia,'Times New Roman',serif;font-size:42px;line-height:1.05;color:#111;font-weight:700;">VKH Newsletter</div>
  </td></tr>
  <tr><td colspan="2" style="padding:0 20px 12px 20px;text-align:center;">
    <div style="font-family:Arial,sans-serif;font-size:14px;color:#666;letter-spacing:0.6px;">od {date_range}</div>
  </td></tr>
  <tr><td colspan="2" style="padding:0 20px 12px 20px;">{DOUBLE_RULE}</td></tr>
  <tr><td colspan="2" style="padding:10px 20px 0 20px;text-align:center;">
    <div style="font-family:Georgia,serif;font-size:18px;color:#111;font-weight:600;text-transform:uppercase;">V t&#253;dnu:</div>
  </td></tr>
</table>

{vtydnu_block(vtydnu_evs, mse_block(), highlight_block())}
{rule}
{dale_block("D&#225;le", dale_evs)}
{dale_block("Od jinud", jinud_evs)}

<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
       style="width:600px;max-width:100%;margin:0 auto;border-collapse:collapse;background:#fff;">
  <tr><td colspan="2" style="padding:0 20px 5px 20px;">{DOUBLE_RULE}</td></tr>
  <tr><td colspan="2" style="padding:14px 20px 6px 20px;text-align:center;">
    <span style="font-family:Georgia,'Times New Roman',serif;font-size:13px;color:#111;font-weight:700;">Vysoko&#353;kolsk&#233; katolick&#233; hnut&#237; Praha</span>
    &nbsp;
    <a href="https://vkhpraha.cz" style="font-family:Arial,sans-serif;font-size:12px;color:#7D211A;text-decoration:none;">vkhpraha.cz</a>
    &nbsp;|&nbsp;
    <a href="https://www.facebook.com/vkhpraha" style="font-family:Arial,sans-serif;font-size:12px;color:#7D211A;text-decoration:none;">facebook</a>
    &nbsp;|&nbsp;
    <a href="https://www.instagram.com/vkhpraha" style="font-family:Arial,sans-serif;font-size:12px;color:#7D211A;text-decoration:none;">instagram</a>
  </td></tr>
  <tr><td colspan="2" style="padding:0 20px;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
      <tr><td style="height:1px;background:#ddd;font-size:1px;">&nbsp;</td></tr>
    </table>
  </td></tr>
  <tr><td colspan="2" style="padding:8px 20px 4px 20px;font-family:Arial,sans-serif;font-size:11px;color:#999;line-height:1.5;text-align:center;">
    Tato zpr&#225;va poch&#225;z&#237; z emailov&#233; konference VKH Praha.
    Chcete-li se p&#345;idat nebo navrhnout p&#345;id&#225;n&#237; zn&#225;m&#233;ho, napi&#353;te na
    <a href="mailto:propagace@vkhpraha.cz" style="color:#7D211A;text-decoration:none;">propagace@vkhpraha.cz</a>.
  </td></tr>
  <tr><td colspan="2" style="padding:2px 20px 16px 20px;font-family:Arial,sans-serif;font-size:10px;color:#bbb;line-height:1.5;text-align:center;">
    Chcete-li zru&#353;it odb&#283;r, za&#353;lete e&#8209;mail na
    <a href="mailto:vkhpraha+unsubscribe@googlegroups.com" style="color:#aaa;text-decoration:none;">vkhpraha+unsubscribe@googlegroups.com</a>
    &nbsp;&#183;&nbsp;
    <a href="https://groups.google.com/d/forum/vkhpraha" style="color:#aaa;text-decoration:none;">Skupiny Google</a>
  </td></tr>
</table>

</td></tr>
</table>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
# Frontend JS  (raw string – no Python escaping issues)
# ══════════════════════════════════════════════════════════════════════════════
FRONTEND_JS = r"""
function switchTab(name) {
  ['events','akce','config'].forEach(function(t){
    document.getElementById('tab-'+t+'-body').style.display = t===name ? '' : 'none';
    document.getElementById('tab-'+t).classList.toggle('active', t===name);
  });
}
function switchPreviewTab(name) {
  document.getElementById('preview-pane').style.display = name==='preview' ? '' : 'none';
  document.getElementById('code-pane').style.display    = name==='code'    ? '' : 'none';
  document.getElementById('ptab-preview').classList.toggle('active', name==='preview');
  document.getElementById('ptab-code').classList.toggle('active',    name==='code');
  if (name==='code') loadCode();
}
function refreshPreview() {
  var f = document.getElementById('preview-frame');
  if (f) f.src = '/preview?_='+Date.now();
}
function loadCode() {
  fetch('/html').then(function(r){return r.text();}).then(function(t){
    document.getElementById('code-pre').textContent = t;
  });
}
function copyHtml() {
  fetch('/html').then(function(r){return r.text();}).then(function(t){
    navigator.clipboard.writeText(t).then(function(){ showToast('HTML zkopírováno ✓'); });
  });
}
function showToast(msg) {
  var t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  setTimeout(function(){ t.classList.remove('show'); }, 2400);
}
function toggleCard(eid) { document.getElementById('card-'+eid).classList.toggle('open'); }
function updateStyleBadge(eid) {
  var v = document.getElementById('style-'+eid).value;
  var b = document.getElementById('style-badge-'+eid);
  b.textContent = v;
  b.className = 'style-badge'+(v==='ticket' ? ' ticket' : '');
}
function saveEvent(eid) {
  var body = document.getElementById('body-'+eid);
  var data = new FormData();
  body.querySelectorAll('input,textarea,select').forEach(function(el){
    if (el.type==='checkbox'){ if(el.checked) data.append(el.name,'on'); }
    else data.append(el.name, el.value);
  });
  fetch('/event/save/'+eid, {method:'POST', body:data})
    .then(function(){ showToast('Uloženo ✓'); refreshPreview(); });
}
function deleteEvent(eid) {
  fetch('/event/'+eid, {method:'DELETE'})
    .then(function(){
      var card = document.getElementById('card-'+eid);
      if (card) card.remove();
      refreshPreview();
    });
}
function saveConfig() {
  var panel = document.getElementById('config-panel');
  var data  = new FormData();
  panel.querySelectorAll('input,textarea,select').forEach(function(el){
    if (el.type==='checkbox'){ if(el.checked) data.append(el.name,'on'); }
    else data.append(el.name, el.value);
  });
  fetch('/config/save', {method:'POST', body:data})
    .then(function(){ showToast('Nastavení uloženo ✓'); refreshPreview(); });
}
// ── week picker ───────────────────────────────────────────────────────────────
function applyWeek() {
  var val = document.getElementById('week-monday-input').value;
  if (!val) return;
  fetch('/week/set', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({monday:val})})
    .then(function(r){return r.json();})
    .then(function(d){
      if (!d.ok) return;
      document.getElementById('week-info-label').textContent = d.week_label;
      var dr = document.getElementById('date-range-input');
      if (dr) dr.value = d.date_range;
      var tw = document.getElementById('topbar-week');
      if (tw) tw.textContent = d.date_range;
      showToast('Týden nastaven ✓');
      refreshPreview();
    });
}
// ── date picker for V týdnu events ───────────────────────────────────────────
function eventDateChanged(eid, isoVal) {
  if (!isoVal) return;
  fetch('/event/setdate/'+eid, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({iso_date:isoVal})})
    .then(function(r){return r.json();})
    .then(function(d){
      var dateEl = document.getElementById('date-'+eid);
      var wdEl   = document.getElementById('weekday-'+eid);
      var isoEl  = document.getElementById('iso-hidden-'+eid);
      var disp   = document.getElementById('date-display-'+eid);
      if (dateEl) dateEl.value = d.date;
      if (wdEl)   wdEl.value   = d.weekday;
      if (isoEl)  isoEl.value  = d.iso;
      if (disp)   disp.textContent = d.label;
      // also update card header date label
      var hdr = document.querySelector('#card-'+eid+' .event-card-header span:nth-child(3)');
      if (hdr && hdr.style.color) hdr.textContent = d.label;
      refreshPreview();
    });
}
// ── add event from Akce library (server-side, fully pre-filled) ──────────────
function addFromAkce(aid) {
  // Add event, then sort — use htmx.ajax for the sort so the panel swap is handled correctly
  fetch('/event/add-from-akce/'+aid, {method:'POST'})
    .then(function(r){return r.text();})
    .then(function(){
      // Use htmx.ajax to POST /event/sort and swap #events-panel outerHTML
      // exactly like the Seřadit button does
      htmx.ajax('POST', '/event/sort', {
        target: '#events-panel',
        swap: 'outerHTML'
      }).then(function(){
        initSortables();
        refreshPreview();
        showToast('Přidáno a seřazeno ✓');
      });
    });
}

// ── Dynamic link rows ────────────────────────────────────────────────────────
function addLinkRow(btn, prefix) {
  var list = btn.parentElement.nextElementSibling;
  var idx  = parseInt(list.dataset.count || list.querySelectorAll('.link-row').length);
  var row  = document.createElement('div');
  row.className = 'link-row';
  row.style.cssText = 'display:flex;gap:4px;align-items:center;margin-bottom:4px;';
  row.innerHTML =
    '<input placeholder="URL" name="'+prefix+idx+'_url" style="flex:3;min-width:0;">' +
    '<input placeholder="Popisek" name="'+prefix+idx+'_label" style="flex:2;min-width:0;">' +
    '<label style="display:flex;align-items:center;gap:2px;cursor:pointer;flex-shrink:0;" title="Ikona ruky">' +
      '<input type="checkbox" name="'+prefix+idx+'_hand" style="margin:0;"> 🖐' +
    '</label>' +
    '<span style="cursor:pointer;color:#a00;font-size:.85rem;padding:2px 6px;flex-shrink:0;" onclick="removeLinkRow(this)">✕</span>';
  list.appendChild(row);
  list.dataset.count = idx + 1;
}
function removeLinkRow(btn) { btn.closest('.link-row').remove(); }

// ── Akce CRUD ─────────────────────────────────────────────────────────────────
function newAkce() {
  fetch('/akce/new', {method:'POST'})
    .then(function(r){return r.json();})
    .then(function(d){
      if (!d.ok) return;
      fetch('/akce/panel')
        .then(function(r){return r.text();})
        .then(function(html){
          var tmp = document.createElement('div'); tmp.innerHTML = html.trim();
          var newPanel = tmp.firstElementChild;
          var oldPanel = document.getElementById('akce-panel');
          if (oldPanel && newPanel) oldPanel.replaceWith(newPanel);
          // Open the newly created card by its id (from server response)
          var newCard = document.getElementById('card-a'+d.ak.id);
          if (newCard) {
            newCard.classList.add('open');
            newCard.scrollIntoView({behavior:'smooth', block:'nearest'});
          }
          showToast('Nová akce — vyplňte a uložte');
        });
    });
}

function saveAkce(aid) {
  var body = document.getElementById('abody-a'+aid);
  if (!body) return;
  var data = new FormData();
  body.querySelectorAll('input,textarea,select').forEach(function(el){
    if (el.type==='checkbox'){ if(el.checked) data.append(el.name||el.id,'on'); }
    else data.append(el.name||el.id, el.value);
  });
  // also grab auto checkbox by id
  var autoEl = document.getElementById('auto-'+aid);
  if (autoEl && autoEl.checked) data.set('auto-'+aid,'on');
  fetch('/akce/save/'+aid, {method:'POST', body:data})
    .then(function(r){return r.json();})
    .then(function(d){
      if(d.ok){
        showToast('Akce uložena ✓');
        function reloadAkce() {
          fetch('/akce/panel').then(function(r){return r.text();}).then(function(html){
            var tmp=document.createElement('div'); tmp.innerHTML=html.trim();
            var np=tmp.firstElementChild, op=document.getElementById('akce-panel');
            if(op&&np) op.replaceWith(np);
          });
          fetch('/akce/chips').then(function(r){return r.text();}).then(function(html){
            var tmp=document.createElement('div'); tmp.innerHTML=html.trim();
            var bar=document.getElementById('akce-bar');
            if(bar&&tmp.firstElementChild) bar.replaceWith(tmp.firstElementChild);
          });
        }
        reloadAkce();
      }
    });
}

function deleteAkce(aid) {
  if (!confirm('Smazat tuto akci z knihovny?')) return;
  fetch('/akce/delete/'+aid, {method:'DELETE'})
    .then(function(r){return r.json();})
    .then(function(d){
      if(d.ok){
        showToast('Akce smazána');
        fetch('/akce/panel').then(function(r){return r.text();}).then(function(html){
          var tmp=document.createElement('div'); tmp.innerHTML=html.trim();
          var np=tmp.firstElementChild, op=document.getElementById('akce-panel');
          if(op&&np) op.replaceWith(np);
        });
        fetch('/akce/chips').then(function(r){return r.text();}).then(function(html){
          var tmp=document.createElement('div'); tmp.innerHTML=html.trim();
          var bar=document.getElementById('akce-bar');
          if(bar&&tmp.firstElementChild) bar.replaceWith(tmp.firstElementChild);
        });
      }
    });
}
// ── reset akce to defaults ────────────────────────────────────────────────────
function saveAkceDefaults() {
  if (!confirm('Uložit aktuální akce jako nové výchozí? Přepíše stávající výchozí nastavení.')) return;
  fetch('/akce/save-defaults', {method:'POST'})
    .then(function(r){return r.json();})
    .then(function(d){ if(d.ok) showToast('Výchozí akce uloženy ✓'); });
}
function resetAkceDefaults() {
  if (!confirm('Obnovit výchozí akce? Vaše úpravy budou ztraceny.')) return;
  fetch('/akce/reset-defaults', {method:'POST'})
    .then(function(r){return r.json();})
    .then(function(d){
      if (!d.ok) return;
      showToast('Výchozí akce obnoveny ✓');
      fetch('/akce/panel').then(function(r){return r.text();}).then(function(html){
        var tmp=document.createElement('div'); tmp.innerHTML=html.trim();
        var np=tmp.firstElementChild, op=document.getElementById('akce-panel');
        if(op&&np) op.replaceWith(np);
      });
      fetch('/akce/chips').then(function(r){return r.text();}).then(function(html){
        var tmp=document.createElement('div'); tmp.innerHTML=html.trim();
        var bar=document.getElementById('akce-bar');
        if(bar&&tmp.firstElementChild) bar.replaceWith(tmp.firstElementChild);
      });
    });
}
// ── archive & new ─────────────────────────────────────────────────────────────
function archiveAndNew() {
  if (!confirm('Archivovat aktuální newsletter a začít nový?')) return;
  fetch('/newsletter/archive', {method:'POST'})
    .then(function(r){return r.json();})
    .then(function(d){ if(d.ok){ showToast('Archivováno ✓'); setTimeout(function(){ window.location.reload(); }, 800); }});
}
function deleteArchive(btn, arc_id) {
  if (!confirm('Smazat tento newsletter z archivu?')) return;
  fetch('/archive/'+arc_id+'/delete', {method:'POST'})
    .then(function(r){return r.json();})
    .then(function(d){
      if(d.ok){
        var item = btn.closest('.archive-item');
        if (item) item.remove();
        showToast('Newsletter smazán ✓');
      }
    });
}
function loadArchive(arc_id) {
  if (!confirm('Načíst tento newsletter? Přepíše aktuální události a nastavení.')) return;
  fetch('/archive/'+arc_id+'/load', {method:'POST'})
    .then(function(r){return r.json();})
    .then(function(d){ if(d.ok){ showToast('Načteno ✓'); setTimeout(function(){ window.location.reload(); }, 800); } });
}
// ── mše sub-events ────────────────────────────────────────────────────────────
function addSubevent() {
  var list = document.getElementById('subevent-list');
  var idx  = list.querySelectorAll('.subevent-card').length;
  var div  = document.createElement('div');
  div.className = 'subevent-card'; div.dataset.idx = idx;
  div.innerHTML =
    '<div class="field-row">' +
      '<div class="field"><label>Název</label><input name="se_label_'+idx+'" value=""></div>' +
      '<div class="field"><label>Čas</label><input name="se_time_'+idx+'" value=""></div>' +
    '</div>' +
    '<div class="field"><label>Detail</label><input name="se_detail_'+idx+'" value=""></div>' +
    '<button type="button" class="subevent-remove" onclick="removeSubevent('+idx+')">✕ Odebrat</button>';
  list.appendChild(div);
}
function removeSubevent(idx) {
  var list = document.getElementById('subevent-list');
  list.querySelectorAll('.subevent-card').forEach(function(c){ if(parseInt(c.dataset.idx)===idx) c.remove(); });
  reindex(list, '.subevent-card', ['se_label_','se_time_','se_detail_'], 'removeSubevent');
}
function addInfobox() {
  var list = document.getElementById('infobox-list');
  var idx  = list.querySelectorAll('.infobox-card').length;
  var div  = document.createElement('div');
  div.className = 'infobox-card'; div.dataset.idx = idx;
  div.innerHTML =
    '<div class="field" style="flex:1"><label>Název</label><input name="ib_title_'+idx+'" value=""></div>' +
    '<div class="field" style="flex:1"><label>Text</label><input name="ib_body_'+idx+'" value=""></div>' +
    '<button type="button" class="subevent-remove" onclick="removeInfobox('+idx+')">✕</button>';
  list.appendChild(div);
}
function removeInfobox(idx) {
  var list = document.getElementById('infobox-list');
  list.querySelectorAll('.infobox-card').forEach(function(c){ if(parseInt(c.dataset.idx)===idx) c.remove(); });
  reindex(list, '.infobox-card', ['ib_title_','ib_body_'], 'removeInfobox');
}
function reindex(list, cardSel, prefixes, removeFn) {
  list.querySelectorAll(cardSel).forEach(function(c, i){
    c.dataset.idx = i;
    c.querySelectorAll('input').forEach(function(inp){
      prefixes.forEach(function(pfx){
        if (inp.name.startsWith(pfx)) inp.name = pfx + i;
      });
    });
    var btn = c.querySelector('.subevent-remove');
    if (btn) btn.setAttribute('onclick', removeFn+'('+i+')');
  });
}
// ── SortableJS ────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function(){
  initSortables();
  document.body.addEventListener('htmx:afterSwap', function(evt){
    initSortables();
    var tid = evt.detail && evt.detail.target && evt.detail.target.id;
    // Sort replaced the whole panel
    if (tid === 'events-panel') { refreshPreview(); return; }
  });
  var frame = document.getElementById('preview-frame');
  if (frame) frame.addEventListener('load', function(){
    try { frame.style.height = frame.contentDocument.documentElement.scrollHeight+'px'; } catch(e){}
  });
});
function initSortables() {
  document.querySelectorAll('.sortable-list').forEach(function(el){
    if (el._sortable) return;
    el._sortable = new Sortable(el, {
      animation: 150,
      handle: '.event-card-header',
      ghostClass: 'sortable-ghost',
      group: 'newsletter',          // ← enables cross-section drag
      onEnd: function(evt) {
        // update the section badge on the dragged card if it moved sections
        var newList = evt.to;
        if (newList && newList.dataset.section) {
          var card = evt.item;
          // section is stored in data-section of the sortable list
        }
        persistOrder();
      }
    });
  });
}
function persistOrder() {
  var groups = [];
  document.querySelectorAll('.sortable-list').forEach(function(list){
    groups.push({section:list.dataset.section,
                 ids:Array.from(list.querySelectorAll('.event-card')).map(function(c){return c.dataset.id;})});
  });
  fetch('/event/reorder', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(groups)})
    .then(function(){ refreshPreview(); });
}
"""


# ── run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("Starting VKH Praha Newsletter Builder on http://localhost:5001")
    uvicorn.run(app, host="0.0.0.0", port=5001)
