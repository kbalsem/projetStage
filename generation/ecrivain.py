import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def nettoyer_nom_repo(repo_name: str) -> str:
    """
    Nettoie le nom du repo pour en faire un nom de dossier valide.
    """
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in repo_name)


def chemin_doc_fichier(chemin_source: str) -> str:
    """
    Convertit un chemin de fichier source en chemin de fichier doc.
    "controllers/user.py" → "fichiers/controllers/user.md"
    """
    chemin_sans_ext = os.path.splitext(chemin_source)[0]
    return f"fichiers/{chemin_sans_ext}.md"


def ecrire_fichier(chemin_complet: str, contenu: str):
    """
    Écrit un fichier sur disque, en créant les dossiers parents si besoin.
    """
    try:
        Path(chemin_complet).parent.mkdir(parents=True, exist_ok=True)
        with open(chemin_complet, "w", encoding="utf-8") as f:
            f.write(contenu)
        logger.info(f"Fichier écrit : {chemin_complet}")
    except Exception as e:
        logger.error(f"Erreur écriture {chemin_complet} : {e}")
        raise


def ecrire_documentation_complete(
    repo_name        : str,
    dossier_sortie   : str,
    readme           : str,
    doc_globale      : str,
    doc_architecture : str,
    docs_fichiers    : dict
) -> str:
    nom_propre = nettoyer_nom_repo(repo_name)
    racine     = os.path.join(dossier_sortie, nom_propre)
    docs_dir   = os.path.join(racine, "docs")          # ← nouveau sous-dossier

    logger.info(f"Écriture de la documentation dans : {docs_dir}")

    # ── Fichiers racine ─────────────────────────────────────────
    ecrire_fichier(os.path.join(docs_dir, "index.md"), readme)
    ecrire_fichier(os.path.join(docs_dir, "global.md"), doc_globale)
    ecrire_fichier(os.path.join(docs_dir, "architecture.md"), doc_architecture)

    # ── Fichiers par module ─────────────────────────────────────
    compteur = 0
    for chemin_source, contenu in docs_fichiers.items():
        chemin_relatif = chemin_doc_fichier(chemin_source)
        chemin_complet = os.path.join(docs_dir, chemin_relatif)   # ← docs_dir, pas racine
        ecrire_fichier(chemin_complet, contenu)
        compteur += 1

    logger.info(f"Documentation complète écrite : {compteur} fichiers de module + 3 fichiers principaux")

    return racine   # ← on retourne toujours la racine du projet, pas docs_dir