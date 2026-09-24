from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import json

app = Flask(__name__)
app.secret_key = "zoo-logic-ai-agents"

# Carpeta donde se guardarán los PDFs
UPLOAD_FOLDER = "knowledge/dragonfish"
METADATA_FILE = "knowledge/dragonfish/metadata.json"

ALLOWED_EXTENSIONS = {"pdf"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def cargar_metadata():
    if not os.path.exists(METADATA_FILE):
        return []

    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except Exception:
        return []


def guardar_metadata(metadata):
    with open(METADATA_FILE, "w", encoding="utf-8") as archivo:
        json.dump(metadata, archivo, ensure_ascii=False, indent=4)


@app.route("/")
def home():
    return render_template("index.html", section=None)


@app.route("/agentes")
def agentes():
    return render_template("index.html", section="agentes")


@app.route("/agentes/configurar")
def agentes_configurar():
    return render_template("index.html", section="agente_config")


@app.route("/knowledge")
def knowledge():

    documentos = cargar_metadata()

    return render_template(
        "index.html",
        section="knowledge",
        documentos=documentos
    )


@app.route("/knowledge/upload", methods=["POST"])
def knowledge_upload():

    if "archivo" not in request.files:
        flash("No se seleccionó ningún archivo.")
        return redirect(url_for("knowledge"))

    archivo = request.files["archivo"]

    if archivo.filename == "":
        flash("No se seleccionó ningún archivo.")
        return redirect(url_for("knowledge"))

    if not allowed_file(archivo.filename):
        flash("Solo se permiten archivos PDF.")
        return redirect(url_for("knowledge"))

    # Nombre seguro del archivo
    nombre_archivo = secure_filename(archivo.filename)

    carpeta = app.config["UPLOAD_FOLDER"]
    ruta = os.path.join(carpeta, nombre_archivo)

    # Guardar PDF
    archivo.save(ruta)

    # Obtener metadata del formulario
    documento = {
        "archivo": nombre_archivo,
        "nombre": request.form.get("nombre_documento", "").strip(),
        "producto": request.form.get("producto", "").strip(),
        "categoria": request.form.get("categoria", "").strip(),
        "subcategoria": request.form.get("subcategoria", "").strip(),
        "nivel": request.form.get("nivel", "").strip(),
        "estado": request.form.get("estado", "").strip(),
        "fuente": request.form.get("fuente", "").strip(),
        "descripcion": request.form.get("descripcion", "").strip()
    }

    # Si ya existía un documento con ese nombre, lo reemplazamos
    documentos = cargar_metadata()

    documentos = [
        d for d in documentos
        if d.get("archivo") != nombre_archivo
    ]

    documentos.append(documento)

    guardar_metadata(documentos)

    flash(f"Documento '{nombre_archivo}' cargado correctamente.")

    return redirect(url_for("knowledge"))


@app.route("/conexiones")
def conexiones():
    return render_template("index.html", section="conexiones")


@app.route("/metricas")
def metricas():
    return render_template("index.html", section="metricas")


@app.route("/playground")
def playground():
    return render_template("index.html", section="playground")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
