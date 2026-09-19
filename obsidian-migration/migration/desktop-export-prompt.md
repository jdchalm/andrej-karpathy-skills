# Desktop-control export (Path B)

Give this to Cowork, or Claude Code with computer use, on the machine that has the OneNote desktop app signed in. It exports one section at a time to `.docx`, then converts with Pandoc. It does not touch the vault.

Prerequisites on the machine: OneNote desktop (not the Store app; the Store app has no Export menu), Pandoc installed, and an empty `quarantine/` folder path decided.

## Prompt

```
You are exporting OneNote sections to Markdown for a migration. You only
export; you never edit or delete OneNote content, and you never open any
folder under the Obsidian vault.

Sections to export (notebook/section), one at a time, in this order:
  <fill in from scan-config.json, "mine" and "private" only>

Output root: <absolute path to quarantine/>

For each section:
1. In OneNote, open the notebook and click the section tab.
2. File → Export → Section → Word Document (*.docx).
   Save as <output root>/<notebook>/<section>.docx. Create folders if needed.
3. Confirm the file exists and is larger than 0 bytes before moving on.
4. Run in a terminal:
     pandoc "<section>.docx" -t gfm --wrap=none --extract-media=media \
       -o "<section>.md"
5. Report: section name, page count as shown in OneNote, file size.

Stop and ask me if:
- Export is greyed out or the dialog asks to sign in.
- A section has more than 100 pages (export it in halves by moving the tab, or fall back to Graph).
- Any dialog mentions sharing, publishing, or sending.

When all sections are done, print the list of .md files produced. Do not
run any scan or move anything into the vault.
```

## Splitting the section file into pages

Pandoc produces one `.md` per section. OneNote puts each page title as a top-level heading, so split on `^# `:

```
python split_section.py quarantine/<notebook>/<section>.md
```

`split_section.py` is not included; it is a ten-line script and the heading rule varies by OneNote version. Write it after looking at the first exported file.

## Why Path A is preferred

Desktop control is fine for a few sections. It is fragile for many: each export is a modal dialog, OneNote occasionally drops images, and there is no way to select pages within a section. Graph gives per-page HTML with metadata and no UI to babysit.
