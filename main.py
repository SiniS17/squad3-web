import os
import json
import uuid
import datetime
from flask import Flask, render_template, request, jsonify, redirect, session, Response
from werkzeug.utils import secure_filename

# Load variables from a local .env file (if present) into os.environ.
# In production (Replit/Render/etc.) real env vars are already set, so
# this is a no-op there — it only matters for local development.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)
app.secret_key = "VAECOsquad3_A320"

# ─────────────────────────────────────────────────────────────────────────────
# Config  (edit config.json to change tab names / folder names / SA email)
# ─────────────────────────────────────────────────────────────────────────────

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def _load_config():
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

CONFIG = _load_config()

def cfg(key, default=""):
    return CONFIG.get(key, default)


# ─────────────────────────────────────────────────────────────────────────────
# Google credential helpers
# ─────────────────────────────────────────────────────────────────────────────

def _is_google_configured():
    return bool(
        os.environ.get("GOOGLE_SHEET_ID", "").strip() and
        os.environ.get("GOOGLE_PRIVATE_KEY", "").strip() and
        cfg("google_service_account_email") and
        "your-service-account" not in cfg("google_service_account_email")
    )


def _build_credentials(scopes):
    """Build service-account credentials from GOOGLE_PRIVATE_KEY + config email."""
    private_key = os.environ.get("GOOGLE_PRIVATE_KEY", "")
    # Strip surrounding quotes that Replit sometimes adds
    private_key = private_key.strip().strip('"').strip("'")
    # Convert literal \n sequences to real newlines
    private_key = private_key.replace("\\n", "\n")
    sa_email    = cfg("google_service_account_email", "")

    info = {
        "type":                        "service_account",
        "project_id":                  "vaeco-squad3",
        "private_key_id":              "",
        "private_key":                 private_key,
        "client_email":                sa_email,
        "client_id":                   "",
        "auth_uri":                    "https://accounts.google.com/o/oauth2/auth",
        "token_uri":                   "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url":        "",
    }
    from google.oauth2 import service_account
    return service_account.Credentials.from_service_account_info(info, scopes=scopes)


def _sheets_service():
    from googleapiclient.discovery import build
    creds = _build_credentials(["https://www.googleapis.com/auth/spreadsheets.readonly"])
    return build("sheets", "v4", credentials=creds)


def _drive_service():
    from googleapiclient.discovery import build
    creds = _build_credentials(["https://www.googleapis.com/auth/drive.readonly"])
    return build("drive", "v3", credentials=creds)


# ─────────────────────────────────────────────────────────────────────────────
# Drive folder navigation helpers
#
#  Folder layout (inside GOOGLE_DRIVE_FOLDER_ID):
#    Hình ảnh/
#      ├── Hotspot/      ← hotspot card images
#      └── Album đội/    ← home-page thumbnails + album page photos
# ─────────────────────────────────────────────────────────────────────────────

_folder_id_cache = {}   # simple in-process cache: path-tuple → folder_id

def _find_child_folder(drive_svc, parent_id, name):
    """Return the Drive folder ID for a direct child folder by name."""
    cache_key = (parent_id, name)
    if cache_key in _folder_id_cache:
        return _folder_id_cache[cache_key]
    q = (
        f"name='{name}' and '{parent_id}' in parents "
        "and mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    res   = drive_svc.files().list(q=q, fields="files(id,name)", pageSize=1).execute()
    files = res.get("files", [])
    fid   = files[0]["id"] if files else None
    _folder_id_cache[cache_key] = fid
    return fid


def _resolve_folder(drive_svc, *path_parts):
    """
    Walk GOOGLE_DRIVE_FOLDER_ID → path_parts[0] → path_parts[1] → …
    Empty strings in path_parts are skipped (allows drive_images_root = "").
    Returns the final folder ID, or None if any step is missing.
    """
    fid = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
    if not fid:
        return None
    for part in path_parts:
        if not part:          # skip empty intermediate path segments
            continue
        fid = _find_child_folder(drive_svc, fid, part)
        if not fid:
            return None
    return fid


def _list_images_in_folder(drive_svc, folder_id, page_size=100):
    """Return list of {id, name} image files in a Drive folder."""
    q   = f"'{folder_id}' in parents and trashed=false and mimeType contains 'image/'"
    res = drive_svc.files().list(
        q=q, fields="files(id,name)", orderBy="name", pageSize=page_size
    ).execute()
    return res.get("files", [])


def get_album_images_from_drive():
    """
    Return list of {id, name, url} from DRIVE_ALBUM_FOLDER_ID directly.
    Falls back to None if not configured.
    """
    if not _is_google_configured():
        return None
    folder_id = os.environ.get("DRIVE_ALBUM_FOLDER_ID", "").strip()
    if not folder_id:
        return None
    try:
        svc   = _drive_service()
        files = _list_images_in_folder(svc, folder_id)
        return [
            {"id": f["id"], "name": f["name"],
             "url": f"/proxy-drive-image?file_id={f['id']}"}
            for f in files
        ]
    except Exception:
        return None


def find_hotspot_image_id(filename):
    """
    Search for a hotspot image by name inside DRIVE_HOTSPOT_FOLDER_ID.
    Matches by exact filename or by name stem (ignoring extension).
    Returns the Drive file_id or None.
    """
    if not _is_google_configured() or not filename:
        return None
    folder_id = os.environ.get("DRIVE_HOTSPOT_FOLDER_ID", "").strip()
    if not folder_id:
        return None

    stem = os.path.splitext(filename)[0].lower()
    try:
        q   = f"'{folder_id}' in parents and trashed=false and mimeType contains 'image/'"
        res = _drive_service().files().list(
            q=q, fields="files(id,name)", pageSize=200
        ).execute()
        for f in res.get("files", []):
            fname_stem = os.path.splitext(f["name"])[0].lower()
            if fname_stem == stem or f["name"].lower() == filename.lower():
                return f["id"]
        return None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Hotspot  (tab: config→hotspot_tab | images: Hình ảnh/Hotspot)
# ─────────────────────────────────────────────────────────────────────────────

MOCK_HOTSPOT_DATA = [
    {"noi_dung": "Kiểm tra nose radome seal for damages, cracks or debonding",       "dung": "", "sai": "", "zone": "100"},
    {"noi_dung": "Kiểm tra windshield window for scratches, delamination, burn marks","dung": "", "sai": "", "zone": "100"},
    {"noi_dung": "Kiểm tra static wicks condition – missing, damaged, loose",         "dung": "", "sai": "", "zone": "200"},
    {"noi_dung": "Kiểm tra slat track fairing for cracks or missing fasteners",       "dung": "", "sai": "", "zone": "500"},
    {"noi_dung": "Kiểm tra NLG door actuator attachment bolts for security",          "dung": "", "sai": "", "zone": "600"},
    {"noi_dung": "Kiểm tra MLG shock absorber for fluid leaks and strut extension",   "dung": "", "sai": "", "zone": "700"},
]

# ── 5-minute in-memory cache ──────────────────────────────────────────────────
import time as _time
_cache = {}   # key → (timestamp, data, error)
CACHE_TTL = 300   # seconds

def _cache_get(key):
    if key in _cache:
        ts, data, error = _cache[key]
        if _time.time() - ts < CACHE_TTL:
            return data, error
    return None, None   # miss

def _cache_set(key, data, error):
    _cache[key] = (_time.time(), data, error)


def fetch_hotspot_from_sheets():
    cached_data, cached_err = _cache_get("hotspot")
    if cached_data is not None:
        return cached_data, cached_err

    if not _is_google_configured():
        return None, "Google chưa được cấu hình"
    try:
        sheet_id = os.environ.get("GOOGLE_SHEET_ID")
        tab      = cfg("hotspot_tab", "Hotspot")
        svc      = _sheets_service()
        result   = svc.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"'{tab}'!A1:D"
        ).execute()
        rows = result.get("values", [])
        if not rows:
            _cache_set("hotspot", [], None)
            return [], None
        data = []
        for row in rows[1:]:
            while len(row) < 4:
                row.append("")
            data.append({
                "noi_dung": row[0].strip(),
                "dung":     row[1].strip(),
                "sai":      row[2].strip(),
                "zone":     row[3].strip(),
            })
        _cache_set("hotspot", data, None)
        return data, None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# Tools  (tab: config→tools_tab)
# ─────────────────────────────────────────────────────────────────────────────

MOCK_TOOLS_DATA = [
    {"task": "Thay lốp NLG / MLG",           "part_number": "—", "tool": "Cờ lê tròng 2-1/4\"",      "so_luong": "1", "engine": "",      "zone": "100"},
    {"task": "Thay lốp NLG / MLG",           "part_number": "—", "tool": "Torque wrench 250 ft·lb",  "so_luong": "1", "engine": "",      "zone": "100"},
    {"task": "Thay lốp NLG / MLG",           "part_number": "—", "tool": "Breaker bar 3/4\"",        "so_luong": "1", "engine": "",      "zone": "100"},
    {"task": "Thay phanh (brake unit) MLG",   "part_number": "—", "tool": "Socket 1-1/4\"",           "so_luong": "1", "engine": "",      "zone": "100"},
    {"task": "Thay phanh (brake unit) MLG",   "part_number": "—", "tool": "Torque wrench 100 ft·lb", "so_luong": "1", "engine": "",      "zone": "100"},
    {"task": "Thay EDP (Engine Driven Pump)", "part_number": "—", "tool": "Cờ lê miệng 1-1/8\"",    "so_luong": "1", "engine": "CFM56", "zone": "400"},
    {"task": "Thay EDP (Engine Driven Pump)", "part_number": "—", "tool": "Càng cua 1-5/8\"",        "so_luong": "1", "engine": "CFM56", "zone": "400"},
    {"task": "Thay IDG",                      "part_number": "—", "tool": "Allen key 5/32\"",         "so_luong": "1", "engine": "IAE",   "zone": "400"},
    {"task": "Thay IDG",                      "part_number": "—", "tool": "Cờ lê 1-1/4\"",           "so_luong": "1", "engine": "IAE",   "zone": "400"},
    {"task": "Thay IDG",                      "part_number": "—", "tool": "Thanh đồng",               "so_luong": "1", "engine": "IAE",   "zone": "400"},
    {"task": "Kiểm tra / thay igniter plug",  "part_number": "—", "tool": "Socket dài 13/16\"",       "so_luong": "1", "engine": "CFM56", "zone": "400"},
    {"task": "Kiểm tra / thay igniter plug",  "part_number": "—", "tool": "Torque wrench 30 ft·lb",  "so_luong": "1", "engine": "CFM56", "zone": "400"},
    {"task": "Thay fuel filter element",      "part_number": "—", "tool": "Cờ lê dây (strap wrench)","so_luong": "1", "engine": "CFM56", "zone": "400"},
    {"task": "Thay rudder PCU",               "part_number": "—", "tool": "Socket 1-1/8\"",           "so_luong": "2", "engine": "",      "zone": "500"},
    {"task": "Thay elevator PCU",             "part_number": "—", "tool": "Deep socket 1-1/8\"",      "so_luong": "1", "engine": "",      "zone": "500"},
    {"task": "Đo Dimension A NLG & MLG",      "part_number": "—", "tool": "Thước dây (steel tape)",   "so_luong": "1", "engine": "",      "zone": "100"},
]


def fetch_tools_from_sheets():
    cached_data, cached_err = _cache_get("tools")
    if cached_data is not None:
        return cached_data, cached_err

    if not _is_google_configured():
        return None, "Google chưa được cấu hình"
    try:
        sheet_id = os.environ.get("GOOGLE_SHEET_ID")
        tab      = cfg("tools_tab", "Tool chuẩn bị")
        svc      = _sheets_service()
        result   = svc.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"'{tab}'!A1:F"
        ).execute()
        rows = result.get("values", [])
        if not rows:
            _cache_set("tools", [], None)
            return [], None
        data = []
        for row in rows[1:]:
            while len(row) < 6:
                row.append("")
            data.append({
                "task":        row[0].strip(),
                "part_number": row[1].strip(),
                "tool":        row[2].strip(),
                "so_luong":    row[3].strip(),
                "engine":      row[4].strip(),
                "zone":        row[5].strip(),
            })
        _cache_set("tools", data, None)
        return data, None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    tab_images = cfg("tab_images", {})
    return render_template("index.html", tab_images=tab_images)


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    if username == "admin" and password == "a320hotspot":
        session["edit_mode"] = True
        return jsonify({"success": True})
    return jsonify({"success": False})


@app.route("/logout")
def logout():
    session.pop("edit_mode", None)
    return redirect("/hotspot")


@app.route("/rules")
def rules():
    return render_template("rules.html")


# ── Hotspot ───────────────────────────────────────────────────────────────────

@app.route("/hotspot")
def hotspot():
    edit_mode   = session.get("edit_mode", False)
    data, error = fetch_hotspot_from_sheets()
    using_mock  = data is None
    if using_mock:
        data = MOCK_HOTSPOT_DATA
    zones = sorted(set(r["zone"] for r in data if r["zone"]))
    return render_template(
        "hotspot.html",
        edit_mode=edit_mode,
        hotspot_data=data,
        zones=zones,
        using_mock=using_mock,
        google_error=error,
    )


@app.route("/proxy-drive-image")
def proxy_drive_image():
    """
    Serve a Drive image by file_id or filename, streamed directly on
    each request (in-memory cache only — no disk writes, view-only site).
    """
    import mimetypes

    file_id = request.args.get("file_id", "")
    filename = request.args.get("filename", "")

    # ── 1. Bundled local images (checked into the repo, not runtime uploads) ──
    if filename and not file_id:
        local_dirs = [
            os.path.join(os.path.dirname(__file__), "static", "images", "B787-hotspots"),
            os.path.join(os.path.dirname(__file__), "static", "images"),
        ]
        for local_dir in local_dirs:
            local_path = os.path.join(local_dir, filename)
            if os.path.isfile(local_path):
                ct = mimetypes.guess_type(local_path)[0] or "image/jpeg"
                with open(local_path, "rb") as f:
                    return Response(f.read(), content_type=ct)

    # ── 2. Resolve filename → Drive file_id ────────────────────────────────────
    if not file_id and filename:
        file_id = find_hotspot_image_id(filename) or ""
    if not file_id:
        return "", 404

    # ── 3. Stream from Drive (in-memory cache only) ────────────────────────────
    cached, _ = _cache_get(f"img:{file_id}")
    if cached is not None:
        data, ct = cached
        return Response(data, content_type=ct)

    try:
        import io
        from googleapiclient.http import MediaIoBaseDownload

        svc = _drive_service()
        meta = svc.files().get(fileId=file_id, fields="mimeType").execute()
        ct = meta.get("mimeType", "image/jpeg")

        dl_req = svc.files().get_media(fileId=file_id)
        buf = io.BytesIO()
        dl = MediaIoBaseDownload(buf, dl_req)
        done = False
        while not done:
            _, done = dl.next_chunk()
        data = buf.getvalue()

        _cache_set(f"img:{file_id}", (data, ct), None)
        return Response(data, content_type=ct)
    except Exception:
        return "", 404


# ── Tools ─────────────────────────────────────────────────────────────────────

@app.route("/tools")
def a320_tools():
    from tools_config import TOOLS_TABLE as tools_cfg
    data, error = fetch_tools_from_sheets()
    using_mock  = data is None
    if using_mock:
        data = MOCK_TOOLS_DATA
    tasks   = sorted(set(r["task"]   for r in data if r.get("task")))
    engines = sorted(set(r["engine"] for r in data if r.get("engine")))
    zones   = sorted(set(r["zone"]   for r in data if r.get("zone")))
    sheet_id  = os.environ.get("GOOGLE_SHEET_ID", "")
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}" if sheet_id else "#"
    return render_template(
        "a320_tools.html",
        tools_data=data,
        tasks=tasks,
        engines=engines,
        zones=zones,
        using_mock=using_mock,
        google_error=error,
        tools_cfg=tools_cfg,
        sheet_url=sheet_url,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Links
# ─────────────────────────────────────────────────────────────────────────────

MOCK_LINKS_DATA = [
    {"ten": "AMOS",                  "link": "https://amos.vna.vn"},
    {"ten": "MMS",                   "link": "https://mms.vna.vn"},
    {"ten": "VAECO Intranet",        "link": "https://intranet.vaeco.vn"},
    {"ten": "Airbus AMM A320",       "link": "https://www.airbus.com"},
    {"ten": "CFM Tech Data",         "link": "https://cfmaeroengines.com"},
    {"ten": "IAE Tech Data",         "link": "https://www.iae.com"},
]


def fetch_links_from_sheets():
    cached_data, cached_err = _cache_get("links")
    if cached_data is not None or cached_err is not None:
        return (None if cached_err else cached_data), cached_err
    try:
        sheet_id = os.environ.get("GOOGLE_SHEET_ID")
        tab      = cfg("links_tab", "Links")
        svc      = _sheets_service()
        result   = svc.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"'{tab}'!A1:B"
        ).execute()
        rows = result.get("values", [])
        if not rows:
            _cache_set("links", [], None)
            return [], None
        data = []
        for row in rows[1:]:
            while len(row) < 2:
                row.append("")
            ten  = row[0].strip()
            link = row[1].strip()
            if ten or link:
                data.append({"ten": ten, "link": link})
        _cache_set("links", data, None)
        return data, None
    except Exception as e:
        return None, str(e)


@app.route("/links")
def links_page():
    data, error = fetch_links_from_sheets()
    using_mock  = data is None
    if using_mock:
        data = MOCK_LINKS_DATA
    return render_template(
        "links.html",
        links_data=data,
        using_mock=using_mock,
        google_error=error,
    )


# ── Squad images API  (home-page thumbnails — Hình ảnh/Album đội) ─────────────

@app.route("/api/squad-images")
def api_squad_images():
    images = get_album_images_from_drive()
    if images is None:
        # Google not configured → static fallbacks
        images = [
            {"id": "s1", "name": "album",   "url": "/static/images/squad1.jpg"},
            {"id": "s2", "name": "hotspot", "url": "/static/images/pic02.jpg"},
            {"id": "s3", "name": "tools",   "url": "/static/images/pic03.jpg"},
            {"id": "s4", "name": "rules",   "url": "/static/images/pic01.jpg"},
        ]
    return jsonify({"images": images})


# ── Drive diagnostic API ──────────────────────────────────────────────────────

@app.route("/api/drive-debug")
def drive_debug():
    """List files visible in both Drive folders for troubleshooting."""
    result = {"hotspot": [], "album": [], "errors": {}}
    for key, label in [("DRIVE_HOTSPOT_FOLDER_ID", "hotspot"), ("DRIVE_ALBUM_FOLDER_ID", "album")]:
        folder_id = os.environ.get(key, "").strip()
        if not folder_id:
            result["errors"][label] = f"{key} not set"
            continue
        try:
            svc = _drive_service()
            q   = f"'{folder_id}' in parents and trashed=false"
            res = svc.files().list(q=q, fields="files(id,name,mimeType)", pageSize=50).execute()
            result[label] = [{"name": f["name"], "id": f["id"], "type": f["mimeType"]} for f in res.get("files", [])]
        except Exception as e:
            result["errors"][label] = str(e)
    return jsonify(result)


# ── Config debug API ──────────────────────────────────────────────────────────

@app.route("/api/config")
def api_config():
    safe = {k: v for k, v in CONFIG.items() if not k.startswith("_")}
    safe["google_configured"] = _is_google_configured()
    return jsonify(safe)


# ── Memories ──────────────────────────────────────────────────────────────────

@app.route("/memories")
def memories():
    edit_mode   = session.get("edit_mode", False)
    albums_file = "static/data/memories_albums.json"
    albums      = []
    if os.path.exists(albums_file):
        with open(albums_file, "r", encoding="utf-8") as f:
            albums = json.load(f)
    return render_template("memories.html", edit_mode=edit_mode, albums=albums)


@app.route("/memories/create-album", methods=["POST"])
def create_album():
    if not session.get("edit_mode"):
        return jsonify({"success": False}), 403
    data = request.get_json()
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"success": False}), 400
    albums_file = "static/data/memories_albums.json"
    albums      = []
    if os.path.exists(albums_file):
        with open(albums_file, "r", encoding="utf-8") as f:
            albums = json.load(f)
    album_id = str(uuid.uuid4())[:8]
    albums.append({
        "id":     album_id,
        "name":   name,
        "date":   datetime.date.today().strftime("%d/%m/%Y"),
        "photos": [],
    })
    os.makedirs("static/data", exist_ok=True)
    with open(albums_file, "w", encoding="utf-8") as f:
        json.dump(albums, f, ensure_ascii=False, indent=2)
    return jsonify({"success": True, "album_id": album_id})


@app.route("/memories/upload-photo", methods=["POST"])
def upload_photo():
    if not session.get("edit_mode"):
        return jsonify({"success": False}), 403
    album_id = request.form.get("album_id")
    file     = request.files.get("image")
    if not album_id or not file:
        return jsonify({"success": False}), 400
    upload_dir = f"static/uploads/memories/{album_id}"
    os.makedirs(upload_dir, exist_ok=True)
    ext      = os.path.splitext(secure_filename(file.filename))[1]
    photo_id = str(uuid.uuid4())[:8]
    filename = f"{photo_id}{ext}"
    file.save(os.path.join(upload_dir, filename))
    is_video = ext.lower() in (".mp4", ".mov", ".avi", ".webm", ".mkv")
    albums_file = "static/data/memories_albums.json"
    with open(albums_file, "r", encoding="utf-8") as f:
        albums = json.load(f)
    for album in albums:
        if album["id"] == album_id:
            album["photos"].append({
                "id":   photo_id,
                "url":  f"/static/uploads/memories/{album_id}/{filename}",
                "type": "video" if is_video else "image",
            })
            break
    with open(albums_file, "w", encoding="utf-8") as f:
        json.dump(albums, f, ensure_ascii=False, indent=2)
    return jsonify({"success": True})


@app.route("/memories/delete-photo", methods=["POST"])
def delete_photo():
    if not session.get("edit_mode"):
        return jsonify({"success": False}), 403
    data     = request.get_json()
    photo_id = data.get("photo_id")
    album_id = data.get("album_id")
    albums_file = "static/data/memories_albums.json"
    with open(albums_file, "r", encoding="utf-8") as f:
        albums = json.load(f)
    for album in albums:
        if album["id"] == album_id:
            for i, photo in enumerate(album["photos"]):
                if photo["id"] == photo_id:
                    try:
                        path = photo["url"].lstrip("/")
                        if os.path.exists(path):
                            os.remove(path)
                    except Exception:
                        pass
                    album["photos"].pop(i)
                    break
    with open(albums_file, "w", encoding="utf-8") as f:
        json.dump(albums, f, ensure_ascii=False, indent=2)
    return jsonify({"success": True})


@app.route("/memories/delete-album", methods=["POST"])
def delete_album():
    if not session.get("edit_mode"):
        return jsonify({"success": False}), 403
    import shutil
    data     = request.get_json()
    album_id = data.get("album_id")
    albums_file = "static/data/memories_albums.json"
    with open(albums_file, "r", encoding="utf-8") as f:
        albums = json.load(f)
    albums = [a for a in albums if a["id"] != album_id]
    upload_dir = f"static/uploads/memories/{album_id}"
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    with open(albums_file, "w", encoding="utf-8") as f:
        json.dump(albums, f, ensure_ascii=False, indent=2)
    return jsonify({"success": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)