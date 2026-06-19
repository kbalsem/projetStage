from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/result")
def result():
    return render_template(
        "result.html",
        repo_name="Mon Projet",
        author="Khaled",
        branch="main",
        commits=25,
        documentation="""
Ce projet analyse automatiquement un dépôt Git
et génère une documentation technique grâce à Ollama.
"""
    )

if __name__ == "__main__":
    app.run(debug=True)