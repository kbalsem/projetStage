# generation/mkdocs_generator.py
import os
import yaml
import logging

from generation.ecrivain import chemin_doc_fichier

logger = logging.getLogger(__name__)


def construire_arbre_nav(docs_fichiers: dict) -> dict:
    arbre = {}
    for chemin_source in docs_fichiers.keys():
        chemin_doc = chemin_doc_fichier(chemin_source)
        segments = os.path.normpath(chemin_doc).split(os.sep)

        # Supprimer le préfixe "fichiers/" inutile dans la nav
        if segments[0] == "fichiers":
            segments = segments[1:]

        noeud = arbre
        for segment in segments[:-1]:
            noeud = noeud.setdefault(segment, {})

        nom_fichier = segments[-1]
        noeud[nom_fichier] = chemin_doc

    return arbre


def arbre_vers_nav_yaml(arbre: dict) -> list:
    items = []
    dossiers = sorted(k for k, v in arbre.items() if isinstance(v, dict) and v)
    fichiers = sorted(k for k, v in arbre.items() if isinstance(v, str))

    for nom_dossier in dossiers:
        sous_items = arbre_vers_nav_yaml(arbre[nom_dossier])
        items.append({nom_dossier: sous_items})

    for nom_fichier in fichiers:
        nom_affiche = os.path.splitext(nom_fichier)[0]
        items.append({nom_affiche: arbre[nom_fichier]})

    return items


def generer_mkdocs_yml(
    nom_propre: str,
    docs_fichiers: dict,
    dossier_sortie: str,
    theme: str = "material",
    nav_extra: list = None
) -> str:
    arbre = construire_arbre_nav(docs_fichiers)
    nav_fichiers = arbre_vers_nav_yaml(arbre)

    nav = [
        {"Accueil": "index.md"},
        {"Vue d'ensemble": "global.md"},
        {"Architecture": "architecture.md"},
    ]

    # Ajouter les fichiers directement (pas de double encapsulation)
    if nav_fichiers:
        nav.append({"Fichiers": nav_fichiers})

    if nav_extra:
        nav.extend(nav_extra)

    config = {
        "site_name": nom_propre,
        "use_directory_urls": False,  # ← AJOUTER CECI
        "nav": nav,
        "theme": {"name": theme if theme == "material" else "readthedocs"},
    }

    racine_doc = os.path.join(dossier_sortie, nom_propre)
    chemin_mkdocs = os.path.join(racine_doc, "mkdocs.yml")
    os.makedirs(racine_doc, exist_ok=True)

    with open(chemin_mkdocs, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    logger.info(f"mkdocs.yml généré : {chemin_mkdocs}")
    return chemin_mkdocs