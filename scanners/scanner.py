import git
import os
import stat
from shutil import rmtree
import gc
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def forcer_suppression(dossier):
    """
    Supprime un dossier de manière forcée en gérant les permissions
    """
    if not os.path.exists(dossier):
        return
        
    def gerer_erreur(func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except PermissionError:
            pass
        except Exception:
            pass
    
    gc.collect()
    
    try:
        rmtree(dossier, onerror=gerer_erreur)
        logger.info(f"{dossier} supprimé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de {dossier}: {e}")


FICHIERS_STRATEGIQUES = [
    "requirements.txt", "Pipfile", "setup.py", "pyproject.toml",
    "package.json", "package-lock.json",
    "pom.xml", "build.gradle",
    "composer.json",
    "docker-compose.yml", "docker-compose.yaml", "Dockerfile",
    "angular.json", ".angular-cli.json",
    "Gemfile", "go.mod", "cargo.toml"
]


def lire_fichiers_strategiques(repo, fichiers: list) -> dict:
    """
    Lit le contenu des fichiers stratégiques uniquement.
    Retourne un dict { chemin: contenu }
    """
    contenu = {}
    
    for chemin in fichiers:
        nom_fichier = chemin.split("/")[-1].lower()
        est_strategique = nom_fichier in [f.lower() for f in FICHIERS_STRATEGIQUES]
        
        if est_strategique:
            try:
                blob = repo.tree() / chemin
                texte = blob.data_stream.read().decode("utf-8", errors="ignore")
                contenu[chemin] = texte[:3000]
                logger.info(f"Fichier stratégique lu : {chemin}")
            except Exception as e:
                logger.warning(f"Impossible de lire {chemin} : {e}")
    
    return contenu


def scanner_repo(chemin_ou_url):
    """
    Scanne un dépôt Git et retourne ses informations
    """
    dossier_local = "./temp_repo"
    
    logger.info(f"Clonage de {chemin_ou_url}...")
    
    try:
        repo = git.Repo.clone_from(chemin_ou_url, dossier_local, depth=1)
        
        # ── Infos de base ─────────────────────────────────────────
        try:
            repo_name = repo.remotes.origin.url.split("/")[-1].replace(".git", "") if repo.remotes else chemin_ou_url.split("/")[-1]
        except:
            repo_name = "Inconnu"
        
        try:
            author = repo.head.commit.author.name
        except:
            author = "Inconnu"
        
        try:
            branch = repo.active_branch.name
        except:
            branch = "Inconnue"
        
        try:
            commits = len(list(repo.iter_commits(max_count=100)))
        except:
            commits = 0
        
        # ── Liste des fichiers ────────────────────────────────────
        fichiers = []
        try:
            for item in repo.tree().traverse():
                if item.type == "blob":
                    fichiers.append(item.path)
                    if len(fichiers) >= 1000:
                        logger.warning("Trop de fichiers, troncature...")
                        break
        except Exception as e:
            logger.warning(f"Erreur lors de la lecture des fichiers: {e}")
            fichiers = ["Erreur de lecture des fichiers"]
        
        # ── Fichiers stratégiques ─────────────────────────────────
        contenu_strategique = lire_fichiers_strategiques(repo, fichiers)
        
        # ── Dictionnaire final ────────────────────────────────────
        structure = {
            "repo_name"           : repo_name,
            "author"              : author,
            "branch"              : branch,
            "commits"             : commits,
            "fichiers"            : fichiers,
            "contenu_strategique" : contenu_strategique,
            "stars"               : 0,
            "licence"             : "Non spécifiée",
            "description"         : ""
        }
        
        # ── Libérer les ressources ────────────────────────────────
        repo.close()
        del repo
        gc.collect()
        
        logger.info(f"Scan terminé : {len(structure['fichiers'])} fichiers trouvés")
        return structure
        
    except git.GitCommandError as e:
        raise Exception(f"Erreur Git: {str(e)}")
    except Exception as e:
        raise Exception(f"Erreur lors du scan: {str(e)}")