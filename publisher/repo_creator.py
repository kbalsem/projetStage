# publisher/repo_creator.py
"""
Création d'un nouveau dépôt distant (GitHub ou GitLab) pour la documentation.
"""

import os
import logging
import requests
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DEPUIS .ENV
# ═══════════════════════════════════════════════════════════════════════════════

# URLs des API
GITHUB_API_URL = os.getenv("PUBLISHER_GITHUB_API", "https://api.github.com")
GITLAB_API_URL = os.getenv("PUBLISHER_GITLAB_API", "https://gitlab.com/api/v4")

# Suffixe pour le nom du dépôt de documentation
SUFFIXE_NOM_REPO_DOC = os.getenv("PUBLISHER_SUFFIXE_REPO_DOC", "-docs")

# Description par défaut
DESCRIPTION_DEFAUT = os.getenv(
    "PUBLISHER_DESCRIPTION_DEFAUT",
    "Documentation générée automatiquement par GitDoc AI"
)

# Flag debug
DEBUG_REPO_CREATOR = os.getenv("DEBUG_REPO_CREATOR", "false").lower() == "true"

# ═══════════════════════════════════════════════════════════════════════════════
# EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class RepoCreationError(Exception):
    """Erreur lors de la création d'un dépôt distant."""
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# CRÉATION GITHUB
# ═══════════════════════════════════════════════════════════════════════════════

def creer_repo_github(token: str, nom: str, 
                      description: str = "", 
                      prive: bool = False, 
                      organisation: Optional[str] = None) -> Dict:
    """
    Crée un nouveau dépôt GitHub.
    
    Args:
        token: Token GitHub
        nom: Nom du dépôt
        description: Description du dépôt
        prive: True pour un dépôt privé
        organisation: Organisation GitHub (optionnel)
        
    Returns:
        Dictionnaire avec clone_url, html_url, full_name
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "name": nom,
        "description": description or DESCRIPTION_DEFAUT,
        "private": prive,
        "auto_init": True
    }

    if organisation:
        url = f"{GITHUB_API_URL}/orgs/{organisation}/repos"
    else:
        url = f"{GITHUB_API_URL}/user/repos"

    if DEBUG_REPO_CREATOR:
        logger.debug(f"Création repo GitHub: {url} - {nom}")

    r = requests.post(url, headers=headers, json=payload)

    if r.status_code not in (200, 201):
        logger.error(f"Erreur création repo GitHub : {r.status_code} - {r.text}")
        raise RepoCreationError(f"Impossible de créer le dépôt GitHub : {r.text}")

    data = r.json()
    logger.info(f"Dépôt GitHub créé : {data['full_name']}")

    return {
        "clone_url": data["clone_url"],
        "html_url": data["html_url"],
        "full_name": data["full_name"]
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CRÉATION GITLAB
# ═══════════════════════════════════════════════════════════════════════════════

def creer_repo_gitlab(token: str, nom: str, 
                      description: str = "", 
                      prive: bool = False, 
                      namespace_id: Optional[int] = None) -> Dict:
    """
    Crée un nouveau dépôt GitLab.
    
    Args:
        token: Token GitLab
        nom: Nom du dépôt
        description: Description du dépôt
        prive: True pour un dépôt privé
        namespace_id: ID du namespace GitLab (optionnel)
        
    Returns:
        Dictionnaire avec clone_url, html_url, full_name
    """
    headers = {"PRIVATE-TOKEN": token}
    payload = {
        "name": nom,
        "description": description or DESCRIPTION_DEFAUT,
        "visibility": "private" if prive else "public",
        "initialize_with_readme": True
    }

    if namespace_id:
        payload["namespace_id"] = namespace_id

    url = f"{GITLAB_API_URL}/projects"
    
    if DEBUG_REPO_CREATOR:
        logger.debug(f"Création repo GitLab: {url} - {nom}")

    r = requests.post(url, headers=headers, json=payload)

    if r.status_code not in (200, 201):
        logger.error(f"Erreur création repo GitLab : {r.status_code} - {r.text}")
        raise RepoCreationError(f"Impossible de créer le dépôt GitLab : {r.text}")

    data = r.json()
    logger.info(f"Dépôt GitLab créé : {data['path_with_namespace']}")

    return {
        "clone_url": data["http_url_to_repo"],
        "html_url": data["web_url"],
        "full_name": data["path_with_namespace"]
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

def creer_repo_documentation(token: str, plateforme: str, 
                              nom_projet_original: str, 
                              description: str = None,
                              prive: bool = False, 
                              organisation: str = None, 
                              namespace_id: int = None) -> Dict:
    """
    Point d'entrée unique : crée un dépôt pour la documentation.
    
    Args:
        token: Token d'authentification
        plateforme: "github" ou "gitlab"
        nom_projet_original: Nom du projet source
        description: Description du dépôt
        prive: True pour un dépôt privé
        organisation: Organisation (GitHub)
        namespace_id: Namespace ID (GitLab)
        
    Returns:
        Dictionnaire avec les informations du dépôt créé
    """
    nom_repo = f"{nom_projet_original}{SUFFIXE_NOM_REPO_DOC}"

    if description is None:
        description = f"Documentation générée automatiquement pour le projet {nom_projet_original}"

    createurs = {
        "github": lambda: creer_repo_github(token, nom_repo, description, prive, organisation),
        "gitlab": lambda: creer_repo_gitlab(token, nom_repo, description, prive, namespace_id),
    }

    createur = createurs.get(plateforme)
    if createur is None:
        raise ValueError(f"Plateforme non supportée : {plateforme}")

    return createur()