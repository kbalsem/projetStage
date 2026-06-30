import os
import yaml
import logging

from generation.ecrivain import chemin_doc_fichier

logger = logging.getLogger(__name__)


def construire_arbre_nav(docs_fichiers: dict) -> dict:
    """
    Construit un arbre imbriqué reflétant l'arborescence réelle des fichiers,
    à partir des chemins sources de docs_fichiers.

    Exemple :
    { "src/flask_sqlalchemy/model.py": "...", "tests/test_model.py": "..." }
    →
    {
        "src": { "flask_sqlalchemy": { "model.md": "fichiers/src/flask_sqlalchemy/model.md" } },
        "tests": { "test_model.md": "fichiers/tests/test_model.md" }
    }
    """
    arbre = {}

    for chemin_source in docs_fichiers.keys():
        chemin_doc = chemin_doc_fichier(chemin_source)          # "fichiers/src/flask_sqlalchemy/model.md"
        segments   = chemin_doc.split("/")                       # ["fichiers", "src", "flask_sqlalchemy", "model.md"]

        noeud = arbre
        for segment in segments[:-1]:
            noeud = noeud.setdefault(segment, {})

        nom_fichier = segments[-1]
        noeud[nom_fichier] = chemin_doc

    return arbre


def arbre_vers_nav_yaml(arbre: dict) -> list:
    """
    Convertit récursivement un arbre en structure de nav mkdocs.
    Une feuille (str) devient {nom_affiche: chemin}.
    Un sous-dossier (dict) devient {nom_dossier: [sous-items...]}.
    Le tri est alphabétique, dossiers avant fichiers, pour une nav stable et lisible.
    """
    items = []

    dossiers = sorted(k for k, v in arbre.items() if isinstance(v, dict))
    fichiers = sorted(k for k, v in arbre.items() if isinstance(v, str))

    for nom_dossier in dossiers:
        sous_items = arbre_vers_nav_yaml(arbre[nom_dossier])
        items.append({nom_dossier: sous_items})

    for nom_fichier in fichiers:
        nom_affiche = os.path.splitext(nom_fichier)[0]
        chemin      = arbre[nom_fichier]
        items.append({nom_affiche: chemin})

    return items


def generer_mkdocs_yml(
    nom_propre     : str,
    docs_fichiers  : dict,
    dossier_sortie : str,
    theme          : str = "material"
) -> str:
    arbre = construire_arbre_nav(docs_fichiers)
    nav_fichiers = arbre_vers_nav_yaml(arbre)
    nav_fichiers_sans_prefixe = nav_fichiers[0]["fichiers"] if nav_fichiers else []

    nav = [
        {"Accueil": "index.md"},
        {"Vue d'ensemble": "global.md"},
        {"Architecture": "architecture.md"},
        {"Fichiers": nav_fichiers_sans_prefixe},
    ]

    config = {
        "site_name": nom_propre,
        "nav": nav,
        "theme": {"name": theme if theme == "material" else "readthedocs"},
    }

    racine_doc    = os.path.join(dossier_sortie, nom_propre)   # même racine que ecrire_documentation_complete
    chemin_mkdocs = os.path.join(racine_doc, "mkdocs.yml")

    os.makedirs(racine_doc, exist_ok=True)

    with open(chemin_mkdocs, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    logger.info(f"mkdocs.yml généré : {chemin_mkdocs}")
    return chemin_mkdocs