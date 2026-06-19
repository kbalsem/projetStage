from flask import Flask, render_template, request  
import git
import os
import stat
from shutil import rmtree
import gc

app = Flask(__name__)

def forcer_suppression(dossier):
    # Convertir en chemin absolu si nécessaire
    if not os.path.exists(dossier):
        return
        
    def gerer_erreur(func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        try:
            func(path)
        except PermissionError:
            # Sur Windows, parfois besoin de réessayer
            pass
    
    # Force garbage collection pour libérer les handles
    gc.collect()
    
    try:
        rmtree(dossier, onerror=gerer_erreur)
        print(f"{dossier} supprimé avec succès")
    except Exception as e:
        print(f"Erreur lors de la suppression de {dossier}: {e}")

def scanner_repo(chemin_ou_url):
    dossier_local = "./temp_repo"
    
    forcer_suppression(dossier_local)
    
    print(f"Clonage de {chemin_ou_url}...")
    repo = git.Repo.clone_from(chemin_ou_url, dossier_local)
    
    structure = {
        "repo_name": repo.remotes.origin.url.split("/")[-1].replace(".git", "") if repo.remotes else chemin_ou_url.split("/")[-1],
        "author": repo.head.commit.author.name,
        "branch": repo.active_branch.name,
        "commits": len(list(repo.iter_commits())),
        "fichiers": [item.path for item in repo.tree().traverse() if item.type == "blob"]
    }
    
    # Important : fermer explicitement le repo pour libérer les ressources
    repo.close()
    del repo
    
    # Force garbage collection
    gc.collect()
    
    print(f"Scan terminé : {len(structure['fichiers'])} fichiers trouvés")
    return structure

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyser", methods=["POST"])
def analyser():
    url = request.form["url"]  
    try:
        data = scanner_repo(url)
        
        # Supprimer le repo temporaire
        forcer_suppression("./temp_repo")
        
        return render_template("result.html",
            repo_name=data["repo_name"],
            author=data["author"],
            branch=data["branch"],
            commits=data["commits"],
            documentation=f"Fichiers détectés : {len(data['fichiers'])}\n" + "\n".join(data["fichiers"])
        )
    
    except Exception as e:
        # Nettoyer même en cas d'erreur
        try:
            forcer_suppression("./temp_repo")
        except:
            pass
        return f"<h2>Erreur : {str(e)}</h2><a href='/'>Retour</a>"

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)