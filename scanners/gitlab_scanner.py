import requests
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "")

EXTENSIONS_AST = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".php", ".rb", ".c", ".cpp"}
MAX_FICHIERS_AST = 50
MAX_TAILLE_FICHIER = 100_000  # 100 Ko

def extraire_owner_repo(url: str):
    url = url.rstrip("/").replace(".git", "")
    parties = url.split("gitlab.com/")
    if len(parties) < 2:
        raise ValueError(f"URL GitLab invalide : {url}")
    segments = parties[1].split("/")
    if len(segments) < 2:
        raise ValueError(f"URL GitLab incomplète : {url}")
    return segments[0], segments[1]


def construire_headers():
    headers = {"Content-Type": "application/json"}
    if GITLAB_TOKEN:
        headers["PRIVATE-TOKEN"] = GITLAB_TOKEN
    return headers


FICHIERS_STRATEGIQUES = [
    "requirements.txt", "Pipfile", "setup.py", "pyproject.toml",
    "package.json", "pom.xml", "build.gradle",
    "composer.json", "docker-compose.yml",
    "docker-compose.yaml", "Dockerfile",
    "angular.json", "Gemfile", "go.mod"
]


def lire_fichiers_strategiques(owner, repo, fichiers, headers):
    contenu = {}
    project_path = f"{owner}/{repo}".replace("/", "%2F")
    for chemin in fichiers:
        nom_fichier = chemin.split("/")[-1].lower()
        if nom_fichier in [f.lower() for f in FICHIERS_STRATEGIQUES]:
            try:
                chemin_encode = chemin.replace("/", "%2F")
                url = (
                    f"https://gitlab.com/api/v4/projects/{project_path}"
                    f"/repository/files/{chemin_encode}/raw"
                )
                r = requests.get(url, headers=headers)
                if r.status_code == 200:
                    contenu[chemin] = r.text[:3000]
                    logger.info(f"Fichier stratégique lu : {chemin}")
            except Exception as e:
                logger.warning(f"Impossible de lire {chemin} : {e}")
    return contenu


def telecharger_fichiers_sources(owner: str, repo: str,
                                  fichiers: list, headers: dict,
                                  branch: str = "main") -> dict:
    """
    Télécharge le contenu des fichiers sources pour l'analyse AST.
    Retourne un dict { chemin: contenu_texte }
    """
    sources = {}
    compteur = 0
    project_path = f"{owner}/{repo}".replace("/", "%2F")

    for chemin in fichiers:
        if compteur >= MAX_FICHIERS_AST:
            logger.warning(f"Limite de {MAX_FICHIERS_AST} fichiers AST atteinte")
            break

        ext = Path(chemin).suffix.lower()
        if ext not in EXTENSIONS_AST:
            continue

        try:
            chemin_encode = chemin.replace("/", "%2F")
            url = (
                f"https://gitlab.com/api/v4/projects/{project_path}"
                f"/repository/files/{chemin_encode}/raw?ref={branch}"
            )
            r = requests.get(url, headers=headers)

            if r.status_code != 200:
                continue

            # Ignorer les fichiers trop grands
            if len(r.content) > MAX_TAILLE_FICHIER:
                logger.info(f"Fichier ignoré (trop grand) : {chemin}")
                continue

            sources[chemin] = r.text
            compteur += 1
            logger.info(f"Source téléchargée : {chemin}")

        except Exception as e:
            logger.warning(f"Impossible de télécharger {chemin} : {e}")

    logger.info(f"{len(sources)} fichiers sources téléchargés pour l'AST")
    return sources


def scanner_gitlab(url: str) -> dict:
    owner, repo = extraire_owner_repo(url)
    headers = construire_headers()
    project_path = f"{owner}/{repo}".replace("/", "%2F")
    base_url = f"https://gitlab.com/api/v4/projects/{project_path}"

    logger.info(f"Analyse GitLab : {owner}/{repo}")

    # ─── Étape 1 : Infos principales ───────────────────────────────
    reponse = requests.get(base_url, headers=headers)
    if reponse.status_code == 404:
        raise Exception(f"Dépôt introuvable : {owner}/{repo}")
    elif reponse.status_code == 401:
        raise Exception("Token GitLab invalide ou manquant")
    elif reponse.status_code != 200:
        raise Exception(f"Erreur API GitLab : {reponse.status_code}")

    info = reponse.json()
    repo_name   = info.get("name", "Inconnu")
    description = info.get("description", "") or ""
    stars       = info.get("star_count", 0)
    branch      = info.get("default_branch", "main")
    author      = info.get("namespace", {}).get("name", "Inconnu")
    licence     = "Non spécifiée"

    # ─── Étape 2 : Commits ─────────────────────────────────────────
    commits = 0
    try:
        r_commits = requests.get(f"{base_url}/repository/commits?per_page=1&page=1", headers=headers)
        if r_commits.status_code == 200:
            commits = int(r_commits.headers.get("X-Total", 0))
    except Exception as e:
        logger.warning(f"Impossible de récupérer les commits : {e}")

    # ─── Étape 3 : Liste des fichiers ──────────────────────────────
    fichiers = []
    try:
        tree_url = f"{base_url}/repository/tree?recursive=true&per_page=100"
        page = 1
        while len(fichiers) < 1000:
            r_tree = requests.get(f"{tree_url}&page={page}", headers=headers)
            if r_tree.status_code != 200:
                break
            items = r_tree.json()
            if not items:
                break
            for item in items:
                if item.get("type") == "blob":
                    fichiers.append(item["path"])
                    if len(fichiers) >= 1000:
                        break
            page += 1
    except Exception as e:
        logger.warning(f"Erreur lors de la récupération des fichiers : {e}")
        fichiers = ["Erreur de lecture des fichiers"]

    logger.info(f"Scan terminé : {len(fichiers)} fichiers trouvés, {commits} commits, {stars} stars")

    # ─── Étape 4 : Fichiers stratégiques ───────────────────────────
    contenu_strategique = lire_fichiers_strategiques(owner, repo, fichiers, headers)

    # ─── Étape 5 : Sources pour l'AST ──────────────────────────────
    sources_ast = telecharger_fichiers_sources(owner, repo, fichiers, headers, branch)

    return {
        "repo_name"           : repo_name,
        "author"              : author,
        "branch"              : branch,
        "commits"             : commits,
        "fichiers"            : fichiers,
        "stars"               : stars,
        "licence"             : licence,
        "description"         : description,
        "contenu_strategique" : contenu_strategique,
        "sources_ast"         : sources_ast,       # ← nouveau
    }