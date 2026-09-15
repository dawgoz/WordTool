# Order Document Filler (Word → PDF)

Cross-platform (Windows + macOS) desktop-style tool that lets a user:

1. Upload a Word (`.docx`) template that contains placeholder tags.
2. Enter **date**, **order number**, and **order price**.
3. Automatically convert the price to Lithuanian words (with correctly declined *euras / eurai / eurų* and *centas / centai / centų*).
4. Click **Proceed and generate** to download the filled `.docx` and a generated `.pdf`.

The UI runs in the browser via **Streamlit**, so the exact same code works identically on Windows and macOS.

---

## 1. Install

Requires **Python 3.10+**.

```powershell
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### PDF conversion prerequisite

`docx2pdf` uses the local installation of Microsoft Word:

- **Windows** – Microsoft Word must be installed (any recent version). No extra setup needed.
- **macOS – recommended:** install **LibreOffice** and let the app use it. This avoids all macOS permission dialogs.
  ```bash
  brew install --cask libreoffice
  # or download the installer from https://www.libreoffice.org/download/
  ```
  The app auto-detects LibreOffice at `/Applications/LibreOffice.app/Contents/MacOS/soffice` and prefers it over Word on macOS.
- **macOS – if you must use Microsoft Word:** the first time you generate a PDF, macOS will display several permission prompts (Automation → Microsoft Word, Files and Folders access). You **must click Allow** on each one. If you accidentally clicked Deny, re-enable them in **System Settings → Privacy & Security → Automation** (allow WordTool to control Microsoft Word) and **→ Files and Folders**. Unsigned builds may re-prompt after each rebuild; installing LibreOffice removes this issue entirely.

If neither Word nor LibreOffice is available, PDF generation will fail with a descriptive error.

## 2. Run

```bash
streamlit run app.py
```

Your browser opens at <http://localhost:8501>. Upload a template, fill in the fields, click **Proceed and generate**, then download the DOCX and PDF.

## 3. Template tags

Use these Jinja-style placeholders anywhere in your `.docx`:

| Tag | Meaning | Example |
| --- | --- | --- |
| `{{ date }}` | Order date | `2026-09-11` |
| `{{ order_number }}` | Order number | `ORD-1042` |
| `{{ order_price }}` | Numeric price | `1234.56` |
| `{{ order_price_eur }}` | Numeric price with euro sign | `1234,56` |
| `{{ order_price_words }}` | Lithuanian words + numeric cents | `vienas tūkstantis du šimtai trisdešimt keturi eurai 56 ct` |
| `{{ order_price_words_full }}` | Cents also spelled out | `... eurai penkiasdešimt šeši centai` |

You can freely place tags in headings, paragraphs, tables, headers, and footers.

### Generate a sample template

```bash
python make_sample_template.py
```

Creates `templates/sample_template.docx` you can use to try the app.

## 4. Project structure

```
WordTool/
├── app.py                    # Streamlit UI
├── lt_numbers.py             # Lithuanian number-to-words helpers
├── pdf_convert.py            # docx → pdf (docx2pdf + LibreOffice fallback)
├── make_sample_template.py   # Generates a demo template
├── requirements.txt
├── templates/                # (generated) sample template lives here
├── Dockerfile                # Container image for Render / any Docker host
├── render.yaml               # Render Blueprint (see section 7)
├── .dockerignore
└── .streamlit/config.toml    # Server-side Streamlit config (upload cap etc.)
```

## 5. Build a native executable

You can package the app as a self-contained executable so end users don't have to install Python. Because PyInstaller cannot cross-compile, **build on the platform you're targeting**: build on Windows to produce a `.exe`, and on macOS to produce a `.app`.

### 5.1 Windows (`WordTool.exe`)

```powershell
# from the project root
powershell -ExecutionPolicy Bypass -File .\build_windows.ps1
```

Output: `dist\WordTool\WordTool.exe`. Ship the **entire `dist\WordTool\` folder** — the `.exe` needs the sibling `_internal\` directory. Zip that folder to distribute.

### 5.2 macOS (`WordTool.app`)

```bash
chmod +x build_macos.sh
./build_macos.sh
```

Output: `dist/WordTool.app`. Ship the `.app` bundle (drag to `/Applications`).

On unsigned builds, first launch requires **right-click → Open** to bypass Gatekeeper, or run:

```bash
xattr -dr com.apple.quarantine dist/WordTool.app
```

For distribution to other users you'll want to sign and notarize the bundle with an Apple Developer ID.

### 5.3 What the executable does

- Starts the Streamlit server locally on `http://localhost:8501`.
- Opens the default browser automatically.
- Keeps a small console window open so you can see errors (change `console=True` to `False` in [WordTool.spec](WordTool.spec) for a polished release build).

### 5.4 Notes on size and prerequisites

- Bundles are **large (~300–500 MB)** because Streamlit pulls in `pandas`, `pyarrow`, `numpy`, etc. This is unavoidable for a Streamlit desktop bundle.
- The bundle does **not** include Microsoft Word or LibreOffice. Target machines still need one of them installed for PDF conversion (see section 1).
- Rebuild each time you change Python source files.

## 6. Troubleshooting

- **“Could not convert DOCX to PDF.”** – Install Microsoft Word or LibreOffice, then restart the app.
- **`docx2pdf` hangs on Windows** – Close any open Word windows; the COM automation cannot share a busy Word instance.
- **Tags are not replaced** – Make sure they use double curly braces exactly like `{{ date }}` and were typed as plain text (not autocorrected into smart quotes or split across multiple runs). Re-type the tag in a single go if needed.
- **PyInstaller build fails with `ModuleNotFoundError` at runtime** – Add the missing module name to the `hiddenimports` list in [WordTool.spec](WordTool.spec) and rebuild.
- **macOS: "app is damaged and can't be opened"** – Run `xattr -dr com.apple.quarantine dist/WordTool.app` (see 5.2) or sign & notarize the bundle.
- **macOS: lots of permission dialogs when clicking generate** – This happens because `docx2pdf` drives Microsoft Word via AppleScript. Install LibreOffice (`brew install --cask libreoffice`) and the prompts go away — the app prefers LibreOffice on macOS. If you want to keep using Word, allow each prompt once, then re-check **System Settings → Privacy & Security → Automation** and → **Files and Folders** to make sure WordTool is ticked.
- **macOS: PDF conversion fails silently after granting permissions** – The unsigned bundle's identity changes on every build, so macOS may re-evaluate its permissions. Rebuild once, grant the prompts once, or (recommended) sign & notarize with an Apple Developer ID.

## 7. Deploy as a website on Render

The repo ships a container-ready configuration so you can host the Streamlit UI publicly on [Render](https://render.com/). PDF conversion on the server uses **LibreOffice** headless — no Microsoft Word needed.

Files that make this work:

- [Dockerfile](Dockerfile) – Python 3.12 image with `libreoffice-core`, `libreoffice-writer`, Unicode fonts, and the app.
- [.streamlit/config.toml](.streamlit/config.toml) – headless mode, 10 MB upload cap, CORS/XSRF settings tuned for a reverse proxy.
- [render.yaml](render.yaml) – Render Blueprint (Docker runtime, Frankfurt region, health check, optional `APP_PASSWORD`).
- [.dockerignore](.dockerignore) – keeps desktop build artefacts out of the image.

### 7.1 One-time deploy

1. Push this repo to GitHub (or GitLab / Bitbucket).
2. In Render, click **New +** → **Blueprint** and select the repo. Render reads [render.yaml](render.yaml) and creates the web service.
3. (Recommended) In the service **Environment** tab, add a secret `APP_PASSWORD` with any value. The app will then require that password before showing the form. Leave it unset if you want the site fully public.
4. First build takes a few minutes because it installs LibreOffice. Subsequent deploys are cached.

### 7.2 Local Docker smoke test

Before pushing, verify the container builds and serves locally:

```powershell
# Windows PowerShell
docker build -t wordtool .
docker run --rm -p 8501:8501 -e PORT=8501 wordtool
```

```bash
# macOS / Linux
docker build -t wordtool .
docker run --rm -p 8501:8501 -e PORT=8501 wordtool
```

Open <http://localhost:8501>. To test the password gate:

```bash
docker run --rm -p 8501:8501 -e PORT=8501 -e APP_PASSWORD=letmein wordtool
```

### 7.3 Security & GDPR notes for the hosted site

Read this before putting real customer data through the deployed site:

- **HTTPS is on by default** on Render — uploads and downloads are encrypted end-to-end.
- **Files are ephemeral.** [app.py](app.py) writes both the uploaded template and generated files into a `tempfile.TemporaryDirectory()` that is deleted at the end of the request. Nothing is persisted unless you attach a Render Disk (don't, unless you also add a retention policy).
- **Personal data (GDPR).** The order form collects name, address, phone, delivery address — all personal data under EU law. `render.yaml` pins the service to the **Frankfurt** region so data stays in the EU. Sign Render's DPA if you process third-party PII.
- **Public URL by default.** Add `APP_PASSWORD` (see 7.1) or put the service behind Cloudflare Access / a VPN if the tool is only for internal use.
- **Template uploads are trusted code.** `docxtpl` renders templates through Jinja2. Only allow trusted users to upload templates — a malicious `.docx` can execute Jinja expressions. If you need to accept templates from untrusted users, replace the `DocxTemplate` render with a sandboxed Jinja environment or ship a fixed built-in template instead of accepting uploads.
- **Upload size** is capped at 10 MB in [.streamlit/config.toml](.streamlit/config.toml) to reduce abuse.
- **No shell injection.** `soffice` is invoked via `subprocess.run([...])` with an argument list in [pdf_convert.py](pdf_convert.py) — user input never touches a shell.

