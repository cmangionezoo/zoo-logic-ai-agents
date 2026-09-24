from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/agentes")
def agentes():
    return render_template("index.html", section="agentes")


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
    app.run(debug=True)