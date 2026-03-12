# VKH Praha – Newsletter Builder

A local web app for building the weekly VKH Praha e-mail newsletter without editing raw HTML.

## Setup

```bash
pip install -r requirements.txt
python main.py
```

Then open **http://localhost:5001** in your browser.

## Features

| Feature | Detail |
|---|---|
| Three sections | *V týdnu*, *Dále*, *Od jinud* |
| Event styles | `regular`, `ticket` (coloured left border + button), `mass` (blue liturgy card) |
| Hand icon | Optional ☞ prefix on the event title |
| Ticket colour | Custom colour picker per event |
| Drag & drop | Reorder events within and across sections |
| Config panel | Date range, optional highlight/ticket box with custom colour |
| Live preview | Right pane auto-refreshes after every save/reorder |
| HTML view | Switch to the raw HTML tab, or click **Kopírovat HTML** to copy to clipboard |
| Persistence | All data saved to `events.json` and `config.json` |

## Data files

- `events.json` – list of all events (auto-created)
- `config.json` – newsletter-wide settings (auto-created)

Both files are plain JSON; you can edit them manually if needed.
