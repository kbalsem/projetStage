# publisher/strategie.py
"""
Stratégies de publication de la documentation.

Deux stratégies disponibles :
- "branche" : pousse sur une branche dédiée du dépôt original
- "nouveau_depot" : crée un nouveau dépôt séparé
"""

import os
import logging
from publisher.git_publisher import (
    publier_documentation, cloner_pour_publication,
    creer_branche, deposer_doc, commit_et_push, nettoyer_clone_local
)
from publisher.repo_creator import creer_repo_documentation

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DEPUIS .ENV
# ═══════════════════════════════════════════════════════════════════════════════

# Stratégies disponibles
STRATEGIE_BRANCHE = os.getenv("PUBLISHER_STRATEGIE_BRANCHE", "branche")
STRATEGIE_NOUVEAU_DEPOT = os.getenv("PUBLISHER_STRATEGIE_NOUVEAU_DEPOT", "nouveau_depot")

# Stratégie par défaut
STRATEGIE_DEFAUT = os.getenv("PUBLISHER_STRATEGIE_DEFAUT", "branche")

# Branche par défaut
BRANCHE_DOCS = os.getenv("PUBLISHER_BRANCHE_DOCS", "docs/auto-generated")

# Branche principale pour nouveau dépôt
BRANCHE_PRINCIPALE = os.getenv("PUBLISHER_BRANCHE_PRINCIPALE", "main")

# Templates d'URL pour les Pull Requests
TEMPLATE_PR_GITHUB = os.getenv(
    "PUBLISHER_TEMPLATE_PR_GITHUB",
    "{url_repo}/compare/{branche}?expand=1"
)
TEMPLATE_PR_GITLAB = os.getenv(
    "PUBLISHER_TEMPLATE_PR_GITLAB",
    "{url_repo}/-/merge_requests/new?merge_request%5Bsource_branch%5D={branche}"
)

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE STRATÉGIE
# ═══════════════════════════════════════════════════════════════════════════════

def publier_avec_strategie(strategie: str, url_repo: str, token: str, 
                            plateforme: str, dossier_docs_generes: str,
                            nom_projet: str = None, 
                            mkdocs_yml_path: str = None, 
                            readme_genere_path: str = None,
                            nom_branche: str = None, 
                            prive: bool = False,
                            organisation: str = None, 
                            namespace_id: int = None, 
                            restructuration: dict = None) -> dict:
    """
    Point d'entrée principal pour la publication.
    
    Args:
        strategie: "branche" ou "nouveau_depot"
        url_repo: URL du dépôt original
        token: Token d'authentification
        plateforme: "github" ou "gitlab"
        dossier_docs_generes: Dossier de documentation
        nom_projet: Nom du projet (pour nouveau dépôt)
        mkdocs_yml_path: Chemin mkdocs.yml
        readme_genere_path: Chemin README.md
        nom_branche: Nom de la branche cible
        prive: Dépôt privé
        organisation: Organisation GitHub
        namespace_id: Namespace GitLab
        restructuration: Options de restructuration
        
    Returns:
        Dictionnaire avec le résultat
    """
    if nom_branche is None:
        nom_branche = BRANCHE_DOCS
    
    if strategie == STRATEGIE_BRANCHE:
        return _publier_sur_branche(
            url_repo, token, plateforme, dossier_docs_generes,
            mkdocs_yml_path, readme_genere_path, nom_branche, restructuration
        )
    
    elif strategie == STRATEGIE_NOUVEAU_DEPOT:
        return _publier_nouveau_depot(
            url_repo, token, plateforme, dossier_docs_generes,
            nom_projet, mkdocs_yml_path, readme_genere_path,
            prive, organisation, namespace_id
        )
    
    else:
        raise ValueError(
            f"Stratégie inconnue : {strategie}. "
            f"Choisir '{STRATEGIE_BRANCHE}' ou '{STRATEGIE_NOUVEAU_DEPOT}'"
        )


def _publier_sur_branche(url_repo: str, token: str, plateforme: str,
                          dossier_docs_generes: str, mkdocs_yml_path: str,
                          readme_genere_path: str, nom_branche: str,
                          restructuration: dict = None) -> dict:
    """
    Stratégie 1 : Nouvelle branche sur le dépôt original.
    Non destructif, permet une Pull Request ensuite.
    """
    logger.info(f"📤 Publication sur branche '{nom_branche}'...")

    resultat = publier_documentation(
        url_repo=url_repo,
        token=token,
        dossier_docs_generes=dossier_docs_generes,
        plateforme=plateforme,
        nom_branche=nom_branche,
        mkdocs_yml_path=mkdocs_yml_path,
        readme_genere_path=readme_genere_path,
        nettoyer=True,
        restructuration=restructuration
    )

    resultat["strategie"] = STRATEGIE_BRANCHE
    resultat["url_pull_request_suggeree"] = _construire_url_pr(
        url_repo, plateforme, nom_branche
    )
    
    logger.info(f"✅ PR suggérée : {resultat['url_pull_request_suggeree']}")
    return resultat


def _publier_nouveau_depot(url_repo: str, token: str, plateforme: str,
                            dossier_docs_generes: str, nom_projet: str,
                            mkdocs_yml_path: str, readme_genere_path: str,
                            prive: bool, organisation: str, 
                            namespace_id: int) -> dict:
    """
    Stratégie 2 : Nouveau dépôt séparé pour la documentation.
    Ne touche pas au dépôt original.
    """
    logger.info("📤 Publication dans un nouveau dépôt...")

    if nom_projet is None:
        nom_projet = url_repo.rstrip("/").split("/")[-1].replace(".git", "")

    nouveau_repo = creer_repo_documentation(
        token=token,
        plateforme=plateforme,
        nom_projet_original=nom_projet,
        prive=prive,
        organisation=organisation,
        namespace_id=namespace_id
    )

    repo, chemin = cloner_pour_publication(
        nouveau_repo["clone_url"], token, plateforme
    )

    try:
        creer_branche(repo, BRANCHE_PRINCIPALE)
        deposer_doc(chemin, dossier_docs_generes, mkdocs_yml_path, readme_genere_path)
        commit_et_push(repo, BRANCHE_PRINCIPALE)

        logger.info(f"✅ Nouveau dépôt : {nouveau_repo['html_url']}")
        
        return {
            "succes": True,
            "strategie": STRATEGIE_NOUVEAU_DEPOT,
            "url_nouveau_depot": nouveau_repo["html_url"],
            "nom_complet": nouveau_repo["full_name"]
        }
    finally:
        nettoyer_clone_local(chemin)


def _construire_url_pr(url_repo: str, plateforme: str, nom_branche: str) -> str:
    """
    Construit l'URL pour ouvrir une Pull/Merge Request.
    
    Args:
        url_repo: URL du dépôt
        plateforme: "github" ou "gitlab"
        nom_branche: Nom de la branche
        
    Returns:
        URL de la PR
    """
    url_repo = url_repo.rstrip("/").replace(".git", "")

    templates = {
        "github": TEMPLATE_PR_GITHUB,
        "gitlab": TEMPLATE_PR_GITLAB,
    }

    template = templates.get(plateforme, "{url_repo}")
    return template.format(url_repo=url_repo, branche=nom_branche)