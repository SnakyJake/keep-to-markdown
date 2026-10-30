# Google Keep Takeout → Markdown Notes

Ein kleines Python-Skript, das Notizen aus einem **Google-Keep-Takeout** in Markdown-Dateien für **Markdown Notes** (beispielsweise Nextcloud) umwandelt. Es arbeitet lokal, benötigt keine zusätzlichen Python-Pakete und verändert die Quelldateien nicht.

## Funktionen

- Konvertiert Google-Keep-Notizen aus `*.json` in `*.md`.
- Übernimmt Notiztitel, Text und Checklisten (`- [ ]` / `- [x]`).
- Ordnet Notizen nach **Status** (`Aktiv`, `Archiv`, `Papierkorb`) und nach dem **ersten Label** in Unterordner ein.
- Schreibt sämtliche Labels zusätzlich in die Markdown-Datei.
- Kopiert referenzierte Anhänge aus dem Verzeichnis der jeweiligen JSON-Datei und verlinkt sie relativ; Bilder werden als Markdown-Bilder eingebunden.
- Übernimmt Erstellungs- und Änderungszeitpunkte, **sofern** sie als `createdTimestampMs` bzw. `userEditedTimestampMs` vorliegen; setzt nach Möglichkeit das Änderungsdatum der erzeugten Datei.
- Vermeidet gleiche Markdown-Dateinamen innerhalb eines Zielordners durch Nummerierung.
- Erstellt einen `import_report.csv` mit Dateizuordnungen und fehlenden Anhängen.

## Voraussetzungen

- Python 3 (nur Standardbibliothek)
- Ein entpackter Google-Keep-Export aus [Google Takeout](https://takeout.google.com/)
- Optional: Nextcloud mit der [Notes-App](https://apps.nextcloud.com/apps/notes)

## Installation

Repository klonen oder `keep_to_md.py` herunterladen. Es ist keine `pip install`-Anweisung nötig.

## Verwendung

```bash
python keep_to_md.py INPUT_DIR OUTPUT_DIR
```

Beispiel unter Windows PowerShell:

```powershell
python .\keep_to_md.py `
  "C:\Google Download\Takeout\Notes\" `
  "C:\Google Download\Nextcloud-Notizen"
```

Beispiel unter Linux/macOS:

```bash
python3 keep_to_md.py ~/Downloads/Takeout/Keep ~/Nextcloud-Notizen
```

**Wichtig:** Das Ausgabeverzeichnis darf **noch nicht existieren** und muss außerhalb des Eingabeverzeichnisses liegen. Das Skript durchsucht das Eingabeverzeichnis rekursiv nach passenden JSON-Notizen.

## Ergebnis

```text
Nextcloud-Notizen/
├── Aktiv/
│   ├── Einkauf/
│   │   ├── Einkaufsliste.md
│   │   └── .attachments/
│   │       └── Einkaufsliste/
│   │           └── bild.jpg
│   └── Ohne Kategorie/
│       └── Eine Notiz.md
├── Archiv/
│   └── Ohne Kategorie/
│       └── Alte Notiz.md
├── Papierkorb/
│   └── Ohne Kategorie/
│       └── Gelöschte Notiz.md
└── import_report.csv
```

Die Ordner und Dateien werden nur erstellt, wenn entsprechende Notizen vorhanden sind. Versteckte `.attachments`-Ordner müssen beim Kopieren mitgenommen werden.

### Beispiel einer konvertierten Notiz

```markdown
# Einkaufsliste

- [x] Milch
- [ ] Brot

**Google-Keep-Labels:** Einkauf, Privat

---

Erstellt: 2024-01-01 12:00:00 UTC
Zuletzt bearbeitet: 2024-01-02 12:00:00 UTC
```

## Nach Nextcloud importieren

1. Zuerst einige erzeugte `.md`-Dateien samt zugehörigen `.attachments`-Ordnern testweise hochladen.
2. Die Dateien in das in **Nextcloud Notes** konfigurierte Notizenverzeichnis kopieren, beispielsweise über den Nextcloud-Desktop-Client oder WebDAV.
3. In Nextcloud Notes prüfen, ob Notizen, Checklisten, Kategorien und Bildlinks wie erwartet angezeigt werden.
4. Erst danach die übrigen Dateien übernehmen.

**Hinweis:** `Aktiv`, `Archiv` und `Papierkorb` sind hier lediglich Ordner. Sie bilden **nicht** automatisch die Google-Keep-Archiv- oder Papierkorbfunktion in Nextcloud nach. Die Darstellung relativer Bildlinks kann je nach Nextcloud-Client variieren.

## Importbericht

Die Datei `import_report.csv` ist UTF-8 mit BOM und semikolongetrennt (praktisch für Excel). Sie enthält:

| Spalte | Bedeutung |
| --- | --- |
| `source` | Pfad der ursprünglichen JSON-Datei |
| `output` | Pfad der erzeugten Markdown-Datei |
| `status` | Aktiv, Archiv oder Papierkorb |
| `labels` | Google-Keep-Labels |
| `attachments_copied` | Anzahl kopierter Anhänge |
| `attachments_missing` | Nicht gefundene Anhänge |

## Einschränkungen

- Das Skript verwendet die **JSON-Dateien** als Datenquelle; HTML-Dateien werden nicht verarbeitet. Rich-Text-Formatierungen aus HTML können daher verloren gehen.
- Anhänge werden nur gefunden, wenn die im JSON referenzierte Datei im selben Verzeichnis wie die JSON-Datei liegt.
- Das erste Label bestimmt den Ordner; weitere Labels stehen im Notiztext, werden aber nicht zu mehreren Nextcloud-Kategorien.
- Zeitstempel im alternativen Format `*TimestampUsec` werden derzeit nicht ausgewertet.
- Erinnerungen, Farben, angeheftete Notizen, Kollaboration und andere Keep-spezifische Eigenschaften werden nicht vollständig übernommen.
- Die Notizen erhalten eine Markdown-Überschrift und gegebenenfalls einen Metadatenabschnitt; das ist keine 1:1-Reproduktion des Originals.
- Der Konverter führt keine direkte Synchronisierung mit Google Keep oder Nextcloud durch.
- Die Verarbeitung ist nicht transaktional: Falls ein Lauf abbricht, sollte das unvollständige **Ausgabeverzeichnis** vor einem erneuten Start geprüft bzw. entfernt werden. Das Original bleibt unangetastet.

## Datenschutz

Die Konvertierung erfolgt vollständig lokal. Das Skript sendet keine Daten an externe Dienste. Notiztexte und Anhänge können sensible Informationen enthalten; prüfe den Ausgabeordner, bevor du ihn teilst oder in ein öffentliches Repository hochlädst.

## Lizenz

**Noch festzulegen.** Vor der Veröffentlichung auf GitHub eine passende `LICENSE`-Datei hinzufügen, wenn andere das Skript unter klaren Bedingungen verwenden und weiterentwickeln dürfen.
