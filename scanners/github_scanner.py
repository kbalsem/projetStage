import requests
import logging
import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from summarize_repo import extraire_extensions    # ← nouveau

load_dotenv()
logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

EXTENSIONS_AST = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".php", ".rb", ".c", ".cpp"}
MAX_FICHIERS_AST = 50
MAX_TAILLE_FICHIER = 100_000  # 100 Ko

def extraire_owner_repo(url: str):
    url = url.rstrip("/").replace(".git", "")
    parties = url.split("github.com/")
    if len(parties) < 2:
        raise ValueError(f"URL GitHub invalide : {url}")
    segments = parties[1].split("/")
    if len(segments) < 2:
        raise ValueError(f"URL GitHub incomplète : {url}")
    return segments[0], segments[1]


def construire_headers():
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
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
    for chemin in fichiers:
        nom_fichier = chemin.split("/")[-1].lower()
        if nom_fichier in [f.lower() for f in FICHIERS_STRATEGIQUES]:
            try:
                url = f"https://api.github.com/repos/{owner}/{repo}/contents/{chemin}"
                r = requests.get(url, headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    texte = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
                    contenu[chemin] = texte[:3000]
                    logger.info(f"Fichier stratégique lu : {chemin}")
            except Exception as e:
                logger.warning(f"Impossible de lire {chemin} : {e}")
    return contenu


def telecharger_fichiers_sources(owner: str, repo: str,
                                  fichiers: list, headers: dict) -> dict:
    """
    Télécharge le contenu des fichiers sources pour l'analyse AST.
    Retourne un dict { chemin: contenu_texte }
    """
    sources = {}
    compteur = 0

    for chemin in fichiers:
        if compteur >= MAX_FICHIERS_AST:
            logger.warning(f"Limite de {MAX_FICHIERS_AST} fichiers AST atteinte")
            break

        ext = Path(chemin).suffix.lower()
        if ext not in EXTENSIONS_AST:
            continue

        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{chemin}"
            r = requests.get(url, headers=headers)

            if r.status_code != 200:
                continue

            data = r.json()

            # Ignorer les fichiers trop grands
            if data.get("size", 0) > MAX_TAILLE_FICHIER:
                logger.info(f"Fichier ignoré (trop grand) : {chemin}")
                continue

            texte = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            sources[chemin] = texte
            compteur += 1
            logger.info(f"Source téléchargée : {chemin}")

        except Exception as e:
            logger.warning(f"Impossible de télécharger {chemin} : {e}")

    logger.info(f"{len(sources)} fichiers sources téléchargés pour l'AST")
    return sources


def scanner_github(url: str) -> dict:
    owner, repo = extraire_owner_repo(url)
    headers = construire_headers()
    base_url = f"https://api.github.com/repos/{owner}/{repo}"

    logger.info(f"Analyse GitHub : {owner}/{repo}")

    # ─── Étape 1 : Infos principales ───────────────────────────────
    reponse = requests.get(base_url, headers=headers)
    if reponse.status_code == 404:
        raise Exception(f"Dépôt introuvable : {owner}/{repo}")
    elif reponse.status_code == 403:
        raise Exception("Limite API GitHub atteinte. Ajoutez un GITHUB_TOKEN dans votre .env")
    elif reponse.status_code != 200:
        raise Exception(f"Erreur API GitHub : {reponse.status_code}")

    info = reponse.json()
    repo_name   = info.get("name", "Inconnu")
    description = info.get("description", "") or ""
    stars       = info.get("stargazers_count", 0)
    branch      = info.get("default_branch", "main")
    author      = info.get("owner", {}).get("login", "Inconnu")
    licence_data = info.get("license")
    licence = licence_data.get("name", "Non spécifiée") if licence_data else "Non spécifiée"

    # ─── Étape 2 : Commits ─────────────────────────────────────────
    commits = 0
    try:
        r_commits = requests.get(f"{base_url}/commits?per_page=1", headers=headers)
        if r_commits.status_code == 200:
            link_header = r_commits.headers.get("Link", "")
            if 'rel="last"' in link_header:
                for part in link_header.split(","):
                    if 'rel="last"' in part:
                        commits = int(part.split("page=")[-1].split(">")[0])
                        break
            else:
                commits = len(r_commits.json())
    except Exception as e:
        logger.warning(f"Impossible de récupérer les commits : {e}")

    # ─── Étape 3 : Liste des fichiers ──────────────────────────────
    fichiers = []
    try:
        r_tree = requests.get(f"{base_url}/git/trees/{branch}?recursive=1", headers=headers)
        if r_tree.status_code == 200:
            tree_data = r_tree.json()
            if tree_data.get("truncated"):
                logger.warning("Arbre tronqué par GitHub (repo trop grand)")
            for item in tree_data.get("tree", []):
                if item.get("type") == "blob":
                    fichiers.append(item["path"])
                    if len(fichiers) >= 1000:
                        break
    except Exception as e:
        logger.warning(f"Erreur lors de la récupération des fichiers : {e}")
        fichiers = ["Erreur de lecture des fichiers"]

    logger.info(f"Scan terminé : {len(fichiers)} fichiers trouvés, {commits} commits, {stars} stars")

    # ─── Étape 4 : Fichiers stratégiques ───────────────────────────
    contenu_strategique = lire_fichiers_strategiques(owner, repo, fichiers, headers)

    # ─── Étape 5 : Sources pour l'AST ──────────────────────────────
    sources_ast = telecharger_fichiers_sources(owner, repo, fichiers, headers)

    # ─── Étape 6 : Langages détectés ────────────────────────────────
    langages = extraire_extensions(fichiers)
    logger.info(f"Langages détectés : {langages}")
    
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