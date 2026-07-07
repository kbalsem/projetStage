# generation/ecrivain.py
"""
Module d'écriture de la documentation sur disque.

Gère la création de l'arborescence des fichiers Markdown
selon l'architecture cible détectée.
"""

import os
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DEPUIS .ENV
# ═══════════════════════════════════════════════════════════════════════════════

# Dossier contenant les fichiers documentés
DOSSIER_FICHIERS_DOC = os.getenv("ECRIVAIN_DOSSIER_FICHIERS", "fichiers")

# Fichiers principaux générés
FICHIER_INDEX = os.getenv("ECRIVAIN_FICHIER_INDEX", "index.md")
FICHIER_GLOBAL = os.getenv("ECRIVAIN_FICHIER_GLOBAL", "global.md")
FICHIER_ARCHITECTURE = os.getenv("ECRIVAIN_FICHIER_ARCHITECTURE", "architecture.md")

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def nettoyer_nom_repo(repo_name: str) -> str:
    """
    Nettoie le nom du dépôt pour créer un nom de dossier valide.
    
    Args:
        repo_name: Nom brut du dépôt
        
    Returns:
        Nom nettoyé (lettres, chiffres, - et _ uniquement)
    """
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in repo_name)


def chemin_doc_fichier(chemin_source: str) -> str:
    """
    Convertit un chemin source en chemin relatif pour la documentation.
    
    Exemples:
        controllers/UserController.py → fichiers/controllers/UserController.md
        models/User.py               → fichiers/models/User.md
        services/AuthService.py      → fichiers/services/AuthService.md
        app.py                       → fichiers/app.md
    
    Args:
        chemin_source: Chemin du fichier source dans l'architecture cible
        
    Returns:
        Chemin relatif du fichier .md dans le dossier docs/
    """
    # Enlever l'extension
    chemin_sans_ext = os.path.splitext(chemin_source)[0]
    
    # Normaliser les séparateurs
    chemin_sans_ext = chemin_sans_ext.replace("\\", "/")
    
    # Si le chemin contient déjà "fichiers/", ne pas le doubler
    if chemin_sans_ext.startswith(f"{DOSSIER_FICHIERS_DOC}/"):
        return f"{chemin_sans_ext}.md"
    
    # Ajouter le préfixe fichiers/
    return f"{DOSSIER_FICHIERS_DOC}/{chemin_sans_ext}.md"


def ecrire_fichier(chemin_complet: str, contenu: str) -> None:
    """
    Écrit un fichier sur disque en créant les dossiers parents si nécessaire.
    
    Args:
        chemin_complet: Chemin absolu du fichier à écrire
        contenu: Contenu texte à écrire
    """
    try:
        Path(chemin_complet).parent.mkdir(parents=True, exist_ok=True)
        with open(chemin_complet, "w", encoding="utf-8") as f:
            f.write(contenu)
        logger.debug(f"Fichier écrit : {chemin_complet}")
    except Exception as e:
        logger.error(f"Erreur écriture {chemin_complet} : {e}")
        raise


def ecrire_documentation_complete(
    repo_name: str,
    dossier_sortie: str,
    readme: str,
    doc_globale: str,
    doc_architecture: str,
    docs_fichiers: Dict[str, str]
) -> str:
    """
    Écrit toute la documentation sur disque.
    
    Structure créée :
        output/
        └── nom_projet/
            ├── mkdocs.yml (généré par mkdocs_generator.py)
            └── docs/
                ├── index.md           (README)
                ├── global.md          (Documentation globale)
                ├── architecture.md    (Documentation d'architecture)
                └── fichiers/
                    ├── controllers/
                    │   ├── UserController.md
                    │   └── HomeController.md
                    ├── models/
                    │   └── User.md
                    └── services/
                        └── AuthService.md
    
    Args:
        repo_name: Nom du dépôt
        dossier_sortie: Dossier racine de sortie
        readme: Contenu du README
        doc_globale: Documentation globale du projet
        doc_architecture: Documentation de l'architecture
        docs_fichiers: Dictionnaire {chemin_source: contenu_markdown}
        
    Returns:
        Chemin racine de la documentation générée
    """
    nom_propre = nettoyer_nom_repo(repo_name)
    racine = os.path.join(dossier_sortie, nom_propre)
    docs_dir = os.path.join(racine, "docs")

    logger.info(f"Écriture documentation dans : {docs_dir}")
    logger.info(f"  - Fichiers à documenter : {len(docs_fichiers)}")

    # Écrire les fichiers principaux
    ecrire_fichier(os.path.join(docs_dir, FICHIER_INDEX), readme)
    logger.info(f"  ✓ {FICHIER_INDEX}")
    
    ecrire_fichier(os.path.join(docs_dir, FICHIER_GLOBAL), doc_globale)
    logger.info(f"  ✓ {FICHIER_GLOBAL}")
    
    ecrire_fichier(os.path.join(docs_dir, FICHIER_ARCHITECTURE), doc_architecture)
    logger.info(f"  ✓ {FICHIER_ARCHITECTURE}")

    # Écrire les fichiers documentés (organisés par architecture cible)
    fichiers_ecrits = 0
    dossiers_crees = set()
    
    for chemin_source, contenu in docs_fichiers.items():
        chemin_relatif = chemin_doc_fichier(chemin_source)
        chemin_complet = os.path.join(docs_dir, chemin_relatif)
        
        # Suivre les dossiers créés pour les logs
        dossier_parent = os.path.dirname(chemin_relatif)
        dossiers_crees.add(dossier_parent)
        
        ecrire_fichier(chemin_complet, contenu)
        fichiers_ecrits += 1

    logger.info(f"  ✓ {fichiers_ecrits} fichiers dans {len(dossiers_crees)} dossiers")
    logger.info(f"Documentation complète dans : {racine}")
    
    return racine


def lister_fichiers_generes(racine: str) -> list:
    """
    Liste tous les fichiers Markdown générés dans la documentation.
    Utile pour le débogage.
    
    Args:
        racine: Chemin racine de la documentation
        
    Returns:
        Liste des chemins relatifs des fichiers .md
    """
    fichiers = []
    docs_dir = os.path.join(racine, "docs")
    
    if not os.path.exists(docs_dir):
        return fichiers
    
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md'):
                chemin_complet = os.path.join(root, file)
                chemin_relatif = os.path.relpath(chemin_complet, docs_dir)
                fichiers.append(chemin_relatif)
    
    return sorted(fichiers)