from flask import Flask, render_template

app = Flask(__name__)


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
    return render_template("index.html", section="knowledge")


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
