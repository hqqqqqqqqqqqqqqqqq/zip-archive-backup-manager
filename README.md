# ZIP ARCHIVE BACKUP MANAGER V1.0.2

Zips selected folders and copies them to another folder or external drive, replacing the previous archive of each folder (rolling backup, not accumulating duplicates).

Archive name format: `<folder name> (FULL BACKUP dd.mm.yy).zip`

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

or double-click `run.bat`. Opens in your default browser at `127.0.0.1:5151`.

## Usage

1. **+ Add folder** — pick folders to back up
2. **+ Choose destination** — pick the target folder on your external drive
3. **Run backup** — zips and copies, replacing any previous archive of the same folder

Selections are saved to `config.json` and reloaded on next launch.

## Structure

- `app.py` — Flask server + API
- `backup_core.py` — zip/cleanup logic
- `dialog_helper.py` — isolated native folder picker
- `index.html` — UI
- `run.bat` — Windows launcher