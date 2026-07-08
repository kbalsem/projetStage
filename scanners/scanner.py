# scanners/scanner.py
"""
Scanner de dépôt Git - clone et analyse la structure d'un repository.
"""

import git
import os
import stat
import gc
import logging
from shutil import rmtree
from typing import Dict, List

from constants import (
    FICHIERS_STRATEGIQUES, EXTENSIONS_AST,
    MAX_FICHIERS_AST, MAX_TAILLE_FICHIER, MAX_FICHIERS_TOTAL, TRONCATURE_STRATEGIQUE
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DEPUIS .ENV (override des constantes si présentes)
# ═══════════════════════════════════════════════════════════════════════════════

DOSSIER_TEMP_DEFAUT = os.getenv("SCANNER_DOSSIER_TEMP", "./temp_repo")
PROFONDEUR_CLONE = int(os.getenv("SCANNER_PROFONDEUR_CLONE", "1"))
MAX_COMMITS = int(os.getenv("SCANNER_MAX_COMMITS", "100"))
DEBUG_SCANNER = os.getenv("DEBUG_SCANNER", "false").lower() == "true"


def extraire_extensions(fichiers: List[str]) -> List[str]:
    """
    Extrait les technologies détectées à partir des extensions de fichiers.
    
    Args:
        fichiers: Liste des chemins de fichiers
        
    Returns:
        Liste triée des technologies détectées
    """
    mapping = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".java": "Java", ".cpp": "C++", ".c": "C", ".cs": "C#",
        ".go": "Go", ".rs": "Rust", ".php": "PHP", ".rb": "Ruby",
        ".swift": "Swift", ".kt": "Kotlin",
        ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
        ".vue": "Vue.js", ".jsx": "React", ".tsx": "React/TypeScript",
        ".sql": "SQL", ".sh": "Shell",
        ".yml": "YAML/CI-CD", ".yaml": "YAML/CI-CD",
        ".json": "JSON", ".md": "Markdown", ".dockerfile": "Docker",
    }

    technologies = set()
    for fichier in fichiers:
        # Détection spéciale Dockerfile
        if "dockerfile" in fichier.lower():
            technologies.add("Docker")
            continue
        
        ext = "." + fichier.split(".")[-1].lower() if "." in fichier else ""
        if ext in mapping:
            technologies.add(mapping[ext])

    return sorted(list(technologies))


def _forcer_suppression(dossier: str) -> None:
    """
    Force la suppression d'un dossier même en lecture seule.
    
    Args:
        dossier: Chemin du dossier à supprimer
    """
    if not os.path.exists(dossier):
        return
    
    def gerer_erreur(func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass
    
    gc.collect()
    try:
        rmtree(dossier, onerror=gerer_erreur)
        if DEBUG_SCANNER:
            logger.debug(f"Dossier supprimé : {dossier}")
    except Exception as e:
        logger.error(f"Erreur suppression {dossier}: {e}")


def cloner_depot(url: str, dossier_temp: str = None) -> str:
    """
    Clone un dépôt Git localement.
    
    Args:
        url: URL du dépôt Git
        dossier_temp: Dossier temporaire pour le clone
        
    Returns:
        Chemin du dossier cloné
    """
    if dossier_temp is None:
        dossier_temp = DOSSIER_TEMP_DEFAUT
    
    _forcer_suppression(dossier_temp)
    logger.info(f"Clonage de {url}...")
    
    repo = git.Repo.clone_from(url, dossier_temp, depth=PROFONDEUR_CLONE)
    repo.close()
    logger.info(f"Dépôt cloné dans {dossier_temp}")
    return dossier_temp


def analyser_repo(url: str, dossier_temp: str = None) -> Dict:
    """
    Analyse un dépôt Git et extrait toutes les informations pertinentes.
    
    Args:
        url: URL du dépôt Git
        dossier_temp: Dossier temporaire pour le clone
        
    Returns:
        Dictionnaire contenant les informations du dépôt
    """
    if dossier_temp is None:
        dossier_temp = DOSSIER_TEMP_DEFAUT
    
    chemin_clone = cloner_depot(url, dossier_temp)
    repo = git.Repo(chemin_clone)

    # ═══════════ MÉTADONNÉES DU DÉPÔT ═══════════
    repo_name = url.rstrip("/").split("/")[-1].replace(".git", "") if url else "Inconnu"

    try:
        author = repo.head.commit.author.name
    except Exception:
        author = "Inconnu"

    try:
        branch = repo.active_branch.name
    except Exception:
        branch = "main"

    try:
        commits = len(list(repo.iter_commits(max_count=MAX_COMMITS)))
    except Exception:
        commits = 0

    # ═══════════ LISTE DES FICHIERS ═══════════
    fichiers = []
    try:
        for item in repo.tree().traverse():
            if item.type == "blob":
                fichiers.append(item.path)
                if len(fichiers) >= MAX_FICHIERS_TOTAL:
                    logger.warning(f"Limite de {MAX_FICHIERS_TOTAL} fichiers atteinte")
                    break
    except Exception as e:
        logger.warning(f"Erreur lecture fichiers: {e}")

    # ═══════════ CONTENU DES FICHIERS ═══════════
    contenu_strategique = {}
    sources_ast = {}
    compteur_ast = 0
    fichiers_strategiques_lower = [f.lower() for f in FICHIERS_STRATEGIQUES]

    for chemin in fichiers:
        nom_fichier = chemin.split("/")[-1].lower()
        ext = os.path.splitext(chemin)[1].lower()

        try:
            blob = repo.tree() / chemin
            taille = blob.size

            # Fichiers stratégiques
            if nom_fichier in fichiers_strategiques_lower:
                texte = blob.data_stream.read().decode("utf-8", errors="ignore")
                contenu_strategique[chemin] = texte[:TRONCATURE_STRATEGIQUE]
                if DEBUG_SCANNER:
                    logger.debug(f"Fichier stratégique : {chemin}")

            # Fichiers pour AST
            if compteur_ast < MAX_FICHIERS_AST and ext in EXTENSIONS_AST and taille <= MAX_TAILLE_FICHIER:
                texte = blob.data_stream.read().decode("utf-8", errors="ignore")
                sources_ast[chemin] = texte
                compteur_ast += 1

        except Exception as e:
            if DEBUG_SCANNER:
                logger.debug(f"Erreur lecture {chemin}: {e}")

    # ═══════════ TECHNOLOGIES ═══════════
    langages = extraire_extensions(fichiers)
    
    repo.close()
    
    logger.info(
        f"Scan terminé : {len(fichiers)} fichiers, "
        f"{commits} commits, {len(langages)} langages, "
        f"{compteur_ast} fichiers AST"
    )

    return {
        "repo_name": repo_name,
        "author": author,
        "branch": branch,
        "commits": commits,
        "fichiers": fichiers,
        "contenu_strategique": contenu_strategique,
        "sources_ast": sources_ast,
        "langages": langages,
        "stars": 0,  # Peut être enrichi via API GitHub
        "licence": "Non spécifiée",  # Peut être enrichi
        "description": "",  # Peut être enrichi
    }