# Actual 2D game previews

- [Side-view campaign](./side-view.png)
- [Warden in Breach](./side-view-warden.png)

Both are captures of the actual orthographic renderer, not concept art.
Rebuild with [the preview tool](../../tools/preview.py):

```powershell
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe tools/preview.py
.\.venv\Scripts\python.exe tools/preview.py --level 10 --boss --output assets/previews/side-view-warden.png
```