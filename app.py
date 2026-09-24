from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from pypdf import PdfReader
import os
import json

app = Flask(__name__)
app.secret_key = "zoo-logic-ai-agents"

# ============================================================
# CONFIGURACIÓN
# ============================================================

# Carpeta donde se guardan los PDFs
UPLOAD_FOLDER = "knowledge/dragonfish"

# Archivo donde guardamos los datos de cada documento
METADATA_FILE = "knowledge/dragonfish/metadata.json"

# Extensiones permitidas
ALLOWED_EXTENSIONS = {"pdf"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Tamaño máximo del archivo: 20 MB
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

# Crear carpeta si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def allowed_file(filename):
    """
    Verifica que el archivo tenga extensión PDF.
    """
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def cargar_metadata():
    """
    Lee el archivo metadata.json.
    Si todavía no existe, devuelve una lista vacía.
    """

    if not os.path.exists(METADATA_FILE):
        return []

    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as archivo:
            return json.load(archivo)

    except Exception:
        return []


def guardar_metadata(metadata):
    """
    Guarda toda la metadata en metadata.json.
    """

    with open(METADATA_FILE, "w", encoding="utf-8") as archivo:
        json.dump(
            metadata,
            archivo,
            ensure_ascii=False,
            indent=4
        )


def extraer_texto_pdf(ruta_pdf):
    """
    Extrae el texto de todas las páginas de un PDF.
    """

    texto = []

    reader = PdfReader(ruta_pdf)

    for pagina in reader.pages:

        contenido = pagina.extract_text()

        if contenido:
            texto.append(contenido)

    return "\n\n".join(texto)


# ============================================================
# INICIO
# ============================================================

@app.route("/")
def home():
    return render_template(
        "index.html",
        section=None
    )


# ============================================================
# AGENTES
# ============================================================

@app.route("/agentes")
def agentes():
    return render_template(
        "index.html",
        section="agentes"
    )


@app.route("/agentes/configurar")
def agentes_configurar():
    return render_template(
        "index.html",
        section="agente_config"
    )


# ============================================================
# KNOWLEDGE BASE
# ============================================================

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

    # --------------------------------------------------------
    # Verificar que haya archivo
    # --------------------------------------------------------

    if "archivo" not in request.files:

        flash("No se seleccionó ningún archivo.")

        return redirect(
            url_for("knowledge")
        )

    archivo = request.files["archivo"]

    # --------------------------------------------------------
    # Verificar nombre
    # --------------------------------------------------------

    if archivo.filename == "":

        flash("No se seleccionó ningún archivo.")

        return redirect(
            url_for("knowledge")
        )

    # --------------------------------------------------------
    # Verificar extensión
    # --------------------------------------------------------

    if not allowed_file(archivo.filename):

        flash("Solo se permiten archivos PDF.")

        return redirect(
            url_for("knowledge")
        )

    # --------------------------------------------------------
    # Generar nombre seguro
    # --------------------------------------------------------

    nombre_archivo = secure_filename(
        archivo.filename
    )

    carpeta = app.config["UPLOAD_FOLDER"]

    ruta = os.path.join(
        carpeta,
        nombre_archivo
    )

    # --------------------------------------------------------
    # Guardar PDF
    # --------------------------------------------------------

    archivo.save(ruta)

    # --------------------------------------------------------
    # Extraer texto del PDF
    # --------------------------------------------------------

    try:

        texto_extraido = extraer_texto_pdf(
            ruta
        )

    except Exception as e:

        flash(
            f"El PDF se cargó, pero no se pudo leer: {str(e)}"
        )

        return redirect(
            url_for("knowledge")
        )

    # --------------------------------------------------------
    # Obtener metadata del formulario
    # --------------------------------------------------------

    documento = {

        "archivo": nombre_archivo,

        "nombre": request.form.get(
            "nombre_documento",
            ""
        ).strip(),

        "producto": request.form.get(
            "producto",
            ""
        ).strip(),

        "categoria": request.form.get(
            "categoria",
            ""
        ).strip(),

        "subcategoria": request.form.get(
            "subcategoria",
            ""
        ).strip(),

        "nivel": request.form.get(
            "nivel",
            ""
        ).strip(),

        "estado": request.form.get(
            "estado",
            ""
        ).strip(),

        "fuente": request.form.get(
            "fuente",
            ""
        ).strip(),

        "descripcion": request.form.get(
            "descripcion",
            ""
        ).strip(),

        # Texto extraído del PDF
        "texto_extraido": texto_extraido
    }

    # --------------------------------------------------------
    # Cargar documentos existentes
    # --------------------------------------------------------

    documentos = cargar_metadata()

    # --------------------------------------------------------
    # Si ya existe el mismo archivo,
    # reemplazar su metadata
    # --------------------------------------------------------

    documentos = [
        d
        for d in documentos
        if d.get("archivo") != nombre_archivo
    ]

    # --------------------------------------------------------
    # Agregar nuevo documento
    # --------------------------------------------------------

    documentos.append(
        documento
    )

    # --------------------------------------------------------
    # Guardar metadata
    # --------------------------------------------------------

    guardar_metadata(
        documentos
    )

    # --------------------------------------------------------
    # Mensaje de confirmación
    # --------------------------------------------------------

    flash(
        f"Documento '{nombre_archivo}' cargado correctamente."
    )

    return redirect(
        url_for("knowledge")
    )


# ============================================================
# CONEXIONES
# ============================================================

@app.route("/conexiones")
def conexiones():
    return render_template(
        "index.html",
        section="conexiones"
    )


# ============================================================
# MÉTRICAS
# ============================================================

@app.route("/metricas")
def metricas():
    return render_template(
        "index.html",
        section="metricas"
    )


# ============================================================
# PLAYGROUND
# ============================================================

@app.route("/playground")
def playground():
    return render_template(
        "index.html",
        section="playground"
    )


# ============================================================
# EJECUCIÓN LOCAL
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )
