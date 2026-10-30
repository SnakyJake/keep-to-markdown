#!/usr/bin/env python3
"""Convert Google Keep Takeout JSON notes into Nextcloud Notes Markdown.
Usage: python keep_to_nextcloud.py INPUT_DIR OUTPUT_DIR
No third-party dependencies. Source files are never changed.
"""
import argparse
import csv
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote


def safe_name(s):
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', str(s or '').strip()).strip(' .')
    return (s[:110].rstrip(' .') or 'Ohne Titel')


def date_string(ms):
    try:
        if ms is None: return ''
        return datetime.fromtimestamp(int(ms)/1000, timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    except (TypeError, ValueError, OverflowError): return ''


def repair_windows_arguments(argv):
    """Recover paths merged by Windows argv parsing after a quoted trailing slash.

    Example: "Takeout\\Google Notizen\\" MD may arrive as one argument:
    'Takeout\\Google Notizen" MD'.
    """
    if len(argv) != 1:
        return argv
    merged = argv[0]
    match = re.fullmatch(r'(.+)["\']\s+(["\']?)(.+?)\2', merged)
    if match:
        return [match.group(1), match.group(3)]
    return argv


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input', type=Path, help='Extracted Google Keep Takeout folder')
    ap.add_argument('output', type=Path, help='New output folder (must not exist)')
    args = ap.parse_args(repair_windows_arguments(sys.argv[1:]))
    src, dst = args.input.resolve(), args.output.resolve()
    if not src.is_dir(): ap.error('Input folder does not exist')
    if dst.exists(): ap.error('Output folder already exists; choose a new empty destination')
    if src == dst or src in dst.parents: ap.error('Output must be outside input folder')
    files = sorted(src.rglob('*.json'))
    notes = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding='utf-8-sig'))
            if isinstance(data, dict) and any(k in data for k in ('textContent','listContent','attachments','title','createdTimestampUsec','createdTimestampMs')):
                notes.append((f,data))
        except (OSError, UnicodeError, json.JSONDecodeError): pass
    if not notes: ap.error('No Google Keep note JSON files found')
    dst.mkdir(parents=True)
    report = []
    used = set()
    for idx, (f, data) in enumerate(notes, 1):
        title = str(data.get('title') or f.stem).strip() or 'Ohne Titel'
        labels = [str(x.get('name','')).strip() for x in data.get('labels',[]) if isinstance(x,dict) and x.get('name')]
        status = 'Papierkorb' if data.get('isTrashed') else 'Archiv' if data.get('isArchived') else 'Aktiv'
        category = safe_name(labels[0]) if labels else 'Ohne Kategorie'
        folder = dst / status / category
        folder.mkdir(parents=True, exist_ok=True)
        basename = safe_name(title)
        target = folder / (basename + '.md')
        n = 2
        while str(target).casefold() in used or target.exists():
            target = folder / f'{basename} ({n}).md'; n += 1
        used.add(str(target).casefold())
        lines = [f'# {title}', '']
        body = data.get('textContent')
        if isinstance(body, str) and body.strip(): lines.extend([body.strip(), ''])
        checklist = data.get('listContent')
        if isinstance(checklist,list):
            for item in checklist:
                if not isinstance(item,dict): continue
                text = str(item.get('text','')).replace('\n',' ').strip()
                lines.append(f"- [{'x' if item.get('isChecked') else ' '}] {text}")
            if checklist: lines.append('')
        attachments = data.get('attachments') or []
        copied = 0; missing = []
        if attachments: lines.extend(['## Anhänge',''])
        for att in attachments:
            if not isinstance(att,dict): continue
            filename = att.get('filePath') or att.get('name')
            if not filename: continue
            # Reject traversal and absolute paths; Takeout usually stores attachments next to JSON.
            clean = Path(str(filename).replace('\\','/')).name
            if clean in ('','.','..'): continue
            candidate = f.parent / clean
            if not candidate.is_file():
                missing.append(clean); continue
            attachment_dir = folder / '.attachments' / target.stem
            attachment_dir.mkdir(parents=True, exist_ok=True)
            dest = attachment_dir / safe_name(clean)
            if dest.exists():
                stem, suffix = dest.stem, dest.suffix
                j = 2
                while dest.exists(): dest = attachment_dir / f'{stem}-{j}{suffix}'; j += 1
            shutil.copy2(candidate, dest)
            rel = dest.relative_to(folder).as_posix()
            link = quote(rel, safe='/.-_~')
            mime = str(att.get('mimetype') or att.get('mimeType') or '')
            is_image = mime.startswith('image/') or dest.suffix.lower() in ('.jpg','.jpeg','.png','.gif','.webp','.bmp')
            lines.append(f"{'!' if is_image else ''}[{clean}]({link})")
            copied += 1
        if attachments: lines.append('')
        if labels: lines.extend(['**Google-Keep-Labels:** ' + ', '.join(labels), ''])
        created = date_string(data.get('createdTimestampMs'))
        edited = date_string(data.get('userEditedTimestampMs'))
        if created or edited:
            lines.extend(['---', ''])
            if created: lines.append('Erstellt: ' + created)
            if edited: lines.append('Zuletzt bearbeitet: ' + edited)
            lines.append('')
        target.write_text('\n'.join(lines).rstrip()+'\n',encoding='utf-8')
        try:
            timestamp = data.get('userEditedTimestampMs') or data.get('createdTimestampMs')
            if timestamp:
                seconds = int(timestamp)/1000
                os.utime(target,(seconds,seconds))
        except (ValueError,TypeError,OverflowError,OSError): pass
        report.append({'source':str(f.relative_to(src)),'output':str(target.relative_to(dst)),
                       'status':status,'labels':' | '.join(labels),'attachments_copied':copied,
                       'attachments_missing':' | '.join(missing)})
    with (dst/'import_report.csv').open('w',newline='',encoding='utf-8-sig') as fh:
        writer=csv.DictWriter(fh,fieldnames=report[0].keys(),delimiter=';')
        writer.writeheader();writer.writerows(report)
    print(f'Converted {len(report)} notes to {dst}')
    print(f'Missing attachments in {sum(bool(r["attachments_missing"]) for r in report)} notes')
    print('Report: '+str(dst/'import_report.csv'))
    print('Note: archived/trash folders are preserved as separate folders; Nextcloud Notes may show them as ordinary categories.')

if __name__=='__main__': main()
