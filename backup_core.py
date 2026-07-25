import os
import re
import zipfile
from datetime import datetime

IGNORE_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}


def today_str():
    return datetime.now().strftime("%d.%m.%y")


def backup_name(folder_name, date_str=None):
    date_str = date_str or today_str()
    return f"{folder_name} (FULL BACKUP {date_str}).zip"


def backup_pattern(folder_name):
    escaped = re.escape(folder_name)
    return re.compile(rf"^{escaped} \(FULL BACKUP \d{{2}}\.\d{{2}}\.\d{{2}}\)\.zip$")


def find_existing_backups(folder_name, destination):
    pattern = backup_pattern(folder_name)
    if not os.path.isdir(destination):
        return []
    return [
        os.path.join(destination, f)
        for f in os.listdir(destination)
        if pattern.match(f)
    ]


def create_backup_zip(source, destination, log=None):
    log = log or (lambda msg: None)
    if not os.path.isdir(source):
        raise FileNotFoundError(f"Source folder not found: {source}")
    if not os.path.isdir(destination):
        raise FileNotFoundError(f"Destination not found: {destination}")

    folder_name = os.path.basename(os.path.normpath(source))
    zip_filename = backup_name(folder_name)
    zip_path = os.path.join(destination, zip_filename)
    tmp_path = zip_path + ".part"

    file_count = 0
    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source):
            for name in files:
                if name in IGNORE_NAMES:
                    continue
                full_path = os.path.join(root, name)
                rel_path = os.path.join(folder_name, os.path.relpath(full_path, source))
                try:
                    zf.write(full_path, rel_path)
                    file_count += 1
                except (OSError, PermissionError) as e:
                    log(f"  skipped {full_path}: {e}")

    os.replace(tmp_path, zip_path)
    log(f"  archived {file_count} files -> {zip_filename}")
    return zip_path, file_count


def cleanup_old_backups(folder_name, destination, keep_path, log=None):
    log = log or (lambda msg: None)
    removed = []
    for path in find_existing_backups(folder_name, destination):
        if os.path.abspath(path) == os.path.abspath(keep_path):
            continue
        try:
            os.remove(path)
            removed.append(path)
            log(f"  removed old backup: {os.path.basename(path)}")
        except OSError as e:
            log(f"  could not remove {path}: {e}")
    return removed 


def run_backup_job(sources, destination, log=None):
    log = log or (lambda msg: None)
    results = []
    for source in sources:
        folder_name = os.path.basename(os.path.normpath(source))
        log(f"Backing up '{folder_name}'...")
        try:
            zip_path, file_count = create_backup_zip(source, destination, log=log)
            cleanup_old_backups(folder_name, destination, keep_path=zip_path, log=log)
            results.append({"source": source, "status": "ok", "zip_path": zip_path, "files": file_count})
            log(f"'{folder_name}' done.\n")
        except Exception as e:
            log(f"'{folder_name}' FAILED: {e}\n")
            results.append({"source": source, "status": "error", "error": str(e)})
    return results