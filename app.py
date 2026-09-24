from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "zoo-logic-ai-agents"

# Carpeta donde se guardarán los PDFs
UPLOAD_FOLDER = "knowledge/dragonfish"
ALLOWED_EXTENSIONS = {"pdf"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


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
    archivos = []

    carpeta = app.config["UPLOAD_FOLDER"]

    if os.path.exists(carpeta):
        for nombre in os.listdir(carpeta):
            ruta = os.path.join(carpeta, nombre)

            if os.path.isfile(ruta) and allowed_file(nombre):
                archivos.append(nombre)

    archivos.sort()

    return render_template(
        "index.html",
        section="knowledge",
        archivos=archivos
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

    nombre = secure_filename(archivo.filename)

    carpeta = app.config["UPLOAD_FOLDER"]
    ruta = os.path.join(carpeta, nombre)

    archivo.save(ruta)

    flash(f"Documento '{nombre}' cargado correctamente.")

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
