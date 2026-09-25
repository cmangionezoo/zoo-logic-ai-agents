import os
import json
import base64

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from werkzeug.utils import secure_filename

from pypdf import PdfReader
import fitz

from openai import OpenAI


# ============================================================
# CONFIGURACIÓN
# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "zoo-logic-ai-agents"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

KNOWLEDGE_DIR = os.path.join(
    BASE_DIR,
    "knowledge"
)

DOCUMENTS_DIR = os.path.join(
    KNOWLEDGE_DIR,
    "documents"
)

IMAGES_DIR = os.path.join(
    KNOWLEDGE_DIR,
    "dragonfish",
    "images"
)

METADATA_FILE = os.path.join(
    KNOWLEDGE_DIR,
    "documents.json"
)


os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
os.makedirs(DOCUMENTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)


# ============================================================
# OPENAI
# ============================================================

OPENAI_API_KEY = os.environ.get(
    "OPENAI_API_KEY"
)

if OPENAI_API_KEY:

    client = OpenAI(
        api_key=OPENAI_API_KEY
    )

else:

    client = None


# ============================================================
# FUNCIONES DE METADATA
# ============================================================

def cargar_documentos():

    if not os.path.exists(METADATA_FILE):
        return []

    try:

        with open(
            METADATA_FILE,
            "r",
            encoding="utf-8"
        ) as archivo:

            datos = json.load(archivo)

            if isinstance(datos, list):
                return datos

            return []

    except Exception as e:

        print(
            f"Error leyendo metadata: {e}"
        )

        return []


def guardar_documentos(documentos):

    try:

        with open(
            METADATA_FILE,
            "w",
            encoding="utf-8"
        ) as archivo:

            json.dump(
                documentos,
                archivo,
                ensure_ascii=False,
                indent=4
            )

        return True

    except Exception as e:

        print(
            f"Error guardando metadata: {e}"
        )

        return False


# ============================================================
# EXTRACCIÓN DE TEXTO DEL PDF
# ============================================================

def extraer_texto_pdf(ruta_pdf):

    texto_completo = []

    lector = PdfReader(ruta_pdf)

    for numero, pagina in enumerate(
        lector.pages,
        start=1
    ):

        try:

            texto = pagina.extract_text()

            if texto:

                texto_completo.append(
                    f"\n--- PÁGINA {numero} ---\n"
                )

                texto_completo.append(
                    texto
                )

        except Exception as e:

            print(
                f"Error leyendo página {numero}: {e}"
            )

    return "\n".join(
        texto_completo
    )


# ============================================================
# ANALIZAR IMAGEN CON IA
# ============================================================

def analizar_imagen_con_ia(
    ruta_imagen,
    numero_pagina
):

    if not client:

        return (
            "Imagen extraída correctamente. "
            "No se pudo realizar el análisis visual "
            "porque OPENAI_API_KEY no está configurada."
        )

    try:

        with open(
            ruta_imagen,
            "rb"
        ) as archivo:

            imagen_bytes = archivo.read()

        imagen_base64 = base64.b64encode(
            imagen_bytes
        ).decode(
            "utf-8"
        )

        extension = os.path.splitext(
            ruta_imagen
        )[1].lower()

        mime_types = {

            ".png": "image/png",

            ".jpg": "image/jpeg",

            ".jpeg": "image/jpeg",

            ".webp": "image/webp"

        }

        mime_type = mime_types.get(
            extension,
            "image/png"
        )

        prompt = f"""
Analizá esta imagen extraída de un documento
técnico utilizado para soporte de software.

La imagen pertenece a la página
{numero_pagina} del documento.

El objetivo es generar conocimiento que pueda
ser utilizado posteriormente por un agente de
soporte técnico Nivel 1.

Analizá únicamente información que pueda
observarse realmente en la imagen.

Prestá especial atención a:

- pantallas del sistema
- nombres de botones
- menús
- campos
- mensajes de error
- códigos de error
- configuraciones
- rutas
- valores visibles
- procedimientos
- pasos
- advertencias
- títulos
- opciones seleccionadas
- relaciones entre elementos

Si es una captura de pantalla:

1. Identificá qué aplicación o pantalla aparece,
   si puede determinarse visualmente.

2. Describí los elementos relevantes.

3. Identificá botones, campos y opciones visibles.

4. Indicá cualquier mensaje de error.

5. Describí cualquier procedimiento que pueda
   inferirse directamente de los elementos visibles.

Si contiene texto:

Transcribí los fragmentos técnicos relevantes.

Si contiene un diagrama:

Explicá las relaciones visibles entre los elementos.

IMPORTANTE:

No inventes información.

No supongas acciones que no sean visibles.

No completes información faltante.

La descripción debe ser técnica, clara y útil
para un agente de soporte.

Respondé en español.
"""

        response = client.responses.create(

            model="gpt-4.1-mini",

            input=[

                {
                    "role": "user",

                    "content": [

                        {
                            "type": "input_text",

                            "text": prompt
                        },

                        {
                            "type": "input_image",

                            "image_url":
                                f"data:{mime_type};base64,{imagen_base64}"
                        }

                    ]
                }

            ]
        )

        resultado = response.output_text

        if resultado:

            return resultado.strip()

        return (
            "La imagen fue procesada pero "
            "no se obtuvo una descripción."
        )

    except Exception as e:

        print(
            f"Error analizando imagen: {e}"
        )

        return (
            f"No se pudo analizar la imagen: {str(e)}"
        )


# ============================================================
# EXTRAER IMÁGENES DEL PDF
# ============================================================

def extraer_imagenes_pdf(
    ruta_pdf,
    nombre_archivo
):

    resultados = []

    nombre_base = os.path.splitext(
        nombre_archivo
    )[0]

    nombre_base = secure_filename(
        nombre_base
    )

    carpeta_imagenes = os.path.join(
        IMAGES_DIR,
        nombre_base
    )

    os.makedirs(
        carpeta_imagenes,
        exist_ok=True
    )

    try:

        documento = fitz.open(
            ruta_pdf
        )

        contador = 0

        imagenes_procesadas = set()

        for numero_pagina, pagina in enumerate(
            documento,
            start=1
        ):

            imagenes = pagina.get_images(
                full=True
            )

            numero_imagen_pagina = 0

            for imagen in imagenes:

                xref = imagen[0]

                clave = (
                    xref,
                    numero_pagina
                )

                if clave in imagenes_procesadas:

                    continue

                imagenes_procesadas.add(
                    clave
                )

                try:

                    datos = documento.extract_image(
                        xref
                    )

                    extension = datos.get(
                        "ext",
                        "png"
                    )

                    numero_imagen_pagina += 1

                    contador += 1

                    nombre_imagen = (
                        f"pagina_"
                        f"{numero_pagina:03d}"
                        f"_imagen_"
                        f"{numero_imagen_pagina:03d}"
                        f".{extension}"
                    )

                    ruta_imagen = os.path.join(
                        carpeta_imagenes,
                        nombre_imagen
                    )

                    with open(
                        ruta_imagen,
                        "wb"
                    ) as archivo:

                        archivo.write(
                            datos["image"]
                        )

                    print(
                        f"Imagen extraída: "
                        f"{nombre_imagen}"
                    )

                    descripcion = (
                        analizar_imagen_con_ia(
                            ruta_imagen,
                            numero_pagina
                        )
                    )

                    resultados.append({

                        "pagina":
                            numero_pagina,

                        "archivo":
                            nombre_imagen,

                        "ruta":
                            ruta_imagen.replace(
                                "\\",
                                "/"
                            ),

                        "descripcion":
                            descripcion

                    })

                except Exception as e:

                    print(
                        f"Error procesando imagen "
                        f"de página "
                        f"{numero_pagina}: {e}"
                    )

                    resultados.append({

                        "pagina":
                            numero_pagina,

                        "archivo":
                            "",

                        "ruta":
                            "",

                        "descripcion":
                            (
                                "Error procesando "
                                f"imagen: {str(e)}"
                            )

                    )

        documento.close()

        print(
            f"Total de imágenes procesadas: "
            f"{contador}"
        )

        return resultados

    except Exception as e:

        print(
            f"Error extrayendo imágenes "
            f"del PDF: {e}"
        )

        return []


# ============================================================
# INICIO
# ============================================================

@app.route("/")
def home():

    documentos = cargar_documentos()

    return render_template(
        "index.html",
        section=None,
        documentos=documentos
    )


# ============================================================
# AGENTES
# ============================================================

@app.route("/agentes")
def agentes():

    documentos = cargar_documentos()

    return render_template(
        "index.html",
        section="agentes",
        documentos=documentos
    )


# ============================================================
# CONFIGURACIÓN DEL AGENTE
# ============================================================

@app.route("/agentes/configurar")
def agentes_configurar():

    documentos = cargar_documentos()

    return render_template(
        "index.html",
        section="agente_config",
        documentos=documentos
    )


# ============================================================
# KNOWLEDGE BASE
# ============================================================

@app.route("/knowledge")
def knowledge():

    documentos = cargar_documentos()

    return render_template(
        "index.html",
        section="knowledge",
        documentos=documentos
    )


# ============================================================
# SUBIR DOCUMENTO
# ============================================================

@app.route(
    "/knowledge/upload",
    methods=["POST"]
)
def knowledge_upload():

    archivo = request.files.get(
        "archivo"
    )

    if not archivo:

        flash(
            "No se seleccionó ningún archivo."
        )

        return redirect(
            url_for("knowledge")
        )

    if not archivo.filename:

        flash(
            "El archivo no tiene nombre."
        )

        return redirect(
            url_for("knowledge")
        )

    nombre_archivo = secure_filename(
        archivo.filename
    )

    extension = os.path.splitext(
        nombre_archivo
    )[1].lower()

    if extension != ".pdf":

        flash(
            "Solo se permiten archivos PDF."
        )

        return redirect(
            url_for("knowledge")
        )

    # --------------------------------------------------------
    # GUARDAR PDF
    # --------------------------------------------------------

    ruta_pdf = os.path.join(
        DOCUMENTS_DIR,
        nombre_archivo
    )

    archivo.save(
        ruta_pdf
    )

    print(
        f"PDF guardado: {ruta_pdf}"
    )

    # --------------------------------------------------------
    # EXTRAER TEXTO
    # --------------------------------------------------------

    try:

        texto_extraido = (
            extraer_texto_pdf(
                ruta_pdf
            )
        )

    except Exception as e:

        print(
            f"Error extrayendo texto: {e}"
        )

        texto_extraido = ""

        flash(
            "El PDF se cargó, pero "
            "no se pudo extraer el texto."
        )

    # --------------------------------------------------------
    # EXTRAER Y ANALIZAR IMÁGENES
    # --------------------------------------------------------

    print(
        "Comenzando procesamiento "
        "de imágenes..."
    )

    imagenes_extraidas = (
        extraer_imagenes_pdf(
            ruta_pdf,
            nombre_archivo
        )
    )

    # --------------------------------------------------------
    # DATOS DEL DOCUMENTO
    # --------------------------------------------------------

    documento = {

        "archivo":
            nombre_archivo,

        "nombre":
            request.form.get(
                "nombre_documento",
                ""
            ).strip(),

        "producto":
            request.form.get(
                "producto",
                ""
            ).strip(),

        "categoria":
            request.form.get(
                "categoria",
                ""
            ).strip(),

        "subcategoria":
            request.form.get(
                "subcategoria",
                ""
            ).strip(),

        "nivel":
            request.form.get(
                "nivel",
                ""
            ).strip(),

        "estado":
            request.form.get(
                "estado",
                ""
            ).strip(),

        "fuente":
            request.form.get(
                "fuente",
                ""
            ).strip(),

        "descripcion":
            request.form.get(
                "descripcion",
                ""
            ).strip(),

        "texto_extraido":
            texto_extraido,

        "imagenes":
            imagenes_extraidas,

        "cantidad_imagenes":
            len(imagenes_extraidas)

    }

    # --------------------------------------------------------
    # GUARDAR METADATA
    # --------------------------------------------------------

    documentos = cargar_documentos()

    documentos.append(
        documento
    )

    guardar_documentos(
        documentos
    )

    print(
        "Documento agregado a la KB:"
    )

    print(
        documento
    )

    flash(
        "Documento incorporado "
        "correctamente a la Knowledge Base."
    )

    return redirect(
        url_for("knowledge")
    )


# ============================================================
# VER CONTENIDO DEL DOCUMENTO
# ============================================================

@app.route(
    "/knowledge/documento/<int:indice>"
)
def ver_documento(indice):

    documentos = cargar_documentos()

    if indice < 0 or indice >= len(
        documentos
    ):

        flash(
            "Documento no encontrado."
        )

        return redirect(
            url_for("knowledge")
        )

    documento = documentos[
        indice
    ]

    return render_template(
        "index.html",
        section="documento",
        documento=documento,
        documentos=documentos
    )


# ============================================================
# CONEXIONES
# ============================================================

@app.route("/conexiones")
def conexiones():

    documentos = cargar_documentos()

    return render_template(
        "index.html",
        section="conexiones",
        documentos=documentos
    )


# ============================================================
# MÉTRICAS
# ============================================================

@app.route("/metricas")
def metricas():

    documentos = cargar_documentos()

    return render_template(
        "index.html",
        section="metricas",
        documentos=documentos
    )


# ============================================================
# PLAYGROUND
# ============================================================

@app.route("/playground")
def playground():

    documentos = cargar_documentos()

    return render_template(
        "index.html",
        section="playground",
        documentos=documentos
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "service": "Zoo Logic AI Agents"
    }


# ============================================================
# EJECUCIÓN LOCAL
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
