from flask import Flask, request, send_from_directory, send_file, abort, render_template, render_template_string
import os, io, zipfile

BASE = "files"
app = Flask(__name__)
os.makedirs(BASE, exist_ok=True)

# ファイル名重複回避
def safe_filename(folder, filename):
    path = os.path.join(folder, filename)
    if not os.path.exists(path):
        return filename
    name, ext = os.path.splitext(filename)
    i = 1
    while True:
        new_name = f"{name}({i}){ext}"
        path = os.path.join(folder, new_name)
        if not os.path.exists(path):
            return new_name
        i += 1

# キー重複回避
def get_unique_key(base, key):
    path = os.path.join(base, key)
    if not os.path.exists(path):
        return key
    i = 1
    while True:
        new_key = f"{key}({i})"
        path = os.path.join(base, new_key)
        if not os.path.exists(path):
            return new_key
        i += 1

# ==== アップロード ====
@app.route("/<key>/upload", methods=["GET", "POST"])
def upload(key):
    key = get_unique_key(BASE, key)
    folder_path = os.path.join(BASE, key)
    os.makedirs(folder_path, exist_ok=True)

    if request.method == "POST":
        f = request.files.get("file")
        if not f:
            return "No file", 400

        filename = safe_filename(folder_path, f.filename)
        f.save(os.path.join(folder_path, filename))
        return f"Saved as {filename} in folder {key}"

    return render_template_string("""
        <h2>Upload to {{folder}}</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file">
            <button type="submit">Upload</button>
        </form>
    """, folder=key)

# ==== 単体ファイルDL ====
@app.route("/<key>/file/<filename>")
def download_file(key, filename):
    folder_path = os.path.join(BASE, key)
    path = os.path.join(folder_path, filename)
    if not os.path.exists(path):
        abort(404)
    return send_from_directory(folder_path, filename, as_attachment=True)

# ==== フォルダZIP DL ====
@app.route("/<key>/folder/<foldername>")
def download_folder(key, foldername):
    folder_path = os.path.join(BASE, foldername)
    if not os.path.isdir(folder_path):
        abort(404)

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(folder_path):
            for f in files:
                full = os.path.join(root, f)
                arc = os.path.relpath(full, folder_path)
                z.write(full, arc)
    mem.seek(0)

    return send_file(mem, as_attachment=True, download_name=f"{foldername}.zip", mimetype="application/zip")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
