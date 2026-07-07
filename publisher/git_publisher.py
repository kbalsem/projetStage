# publisher/git_publisher.py
"""
Gère le clonage local, le dépôt des fichiers générés, le commit et le push.

Ce module orchestre la publication de la documentation sur Git.
"""

import os
import shutil
import logging
from urllib.parse import urlparse, urlunparse
from git import Repo, GitCommandError

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DEPUIS .ENV
# ═══════════════════════════════════════════════════════════════════════════════

# Dossier temporaire pour les clones
DOSSIER_TEMP = os.getenv("PUBLISHER_DOSSIER_TEMP", "/tmp")

# Préfixe pour les dossiers de publication
PREFIXE_DOSSIER_PUBLISH = os.getenv("PUBLISHER_PREFIXE_DOSSIER", "publish_")

# Dossier de documentation dans le repo
DOSSIER_DOCS_REPO = os.getenv("PUBLISHER_DOSSIER_DOCS", "docs")

# Fichiers à copier
FICHIER_MKDOCS = os.getenv("PUBLISHER_FICHIER_MKDOCS", "mkdocs.yml")
FICHIER_README = os.getenv("PUBLISHER_FICHIER_README", "README.md")

# Message de commit par défaut
MESSAGE_COMMIT_DEFAUT = os.getenv(
    "PUBLISHER_MESSAGE_COMMIT",
    "docs: génération automatique de documentation (architecture + AST + IA)"
)

# Branche par défaut
BRANCHE_DEFAUT = os.getenv("PUBLISHER_BRANCHE_DEFAUT", "docs/auto-generated")

# Flag pour le nettoyage automatique
NETTOYER_AUTO = os.getenv("PUBLISHER_NETTOYER_AUTO", "true").lower() == "true"

# Flag debug
DEBUG_PUBLISHER = os.getenv("DEBUG_PUBLISHER", "false").lower() == "true"

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS D'AUTHENTIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def inserer_token_dans_url(url_repo: str, token: str, plateforme: str = "github") -> str:
    """
    Insère le token d'authentification dans l'URL pour permettre le push.
    
    Args:
        url_repo: URL du dépôt
        token: Token d'authentification
        plateforme: "github" ou "gitlab"
        
    Returns:
        URL avec token intégré
        
    Exemples:
        GitHub: https://TOKEN@github.com/user/projet.git
        GitLab: https://oauth2:TOKEN@gitlab.com/user/projet.git
    """
    parsed = urlparse(url_repo)

    formats_token = {
        "github": f"{token}@{parsed.netloc}",
        "gitlab": f"oauth2:{token}@{parsed.netloc}",
    }
    
    netloc = formats_token.get(plateforme, f"{token}@{parsed.netloc}")

    url_avec_token = urlunparse((
        parsed.scheme,
        netloc,
        parsed.path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))
    
    if DEBUG_PUBLISHER:
        # Masquer le token dans les logs
        url_masquee = url_avec_token.replace(token, "***TOKEN***")
        logger.debug(f"URL avec token : {url_masquee}")
    
    return url_avec_token


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE CLONAGE
# ═══════════════════════════════════════════════════════════════════════════════

def cloner_pour_publication(url_repo: str, token: str, 
                            plateforme: str = "github", 
                            dossier_base: str = None) -> tuple:
    """
    Clone le dépôt original localement pour y écrire la documentation.
    
    Args:
        url_repo: URL du dépôt à cloner
        token: Token d'authentification
        plateforme: "github" ou "gitlab"
        dossier_base: Dossier de base pour le clone (défaut: /tmp)
        
    Returns:
        Tuple (repo, chemin_local)
    """
    if dossier_base is None:
        dossier_base = DOSSIER_TEMP
    
    nom_projet = url_repo.rstrip("/").split("/")[-1].replace(".git", "")
    chemin = os.path.join(dossier_base, f"{PREFIXE_DOSSIER_PUBLISH}{nom_projet}")

    # Nettoyer si le dossier existe déjà
    if os.path.exists(chemin):
        shutil.rmtree(chemin)
        if DEBUG_PUBLISHER:
            logger.debug(f"Dossier existant supprimé : {chemin}")

    url_auth = inserer_token_dans_url(url_repo, token, plateforme)

    try:
        repo = Repo.clone_from(url_auth, chemin)
        logger.info(f"Dépôt cloné avec succès dans {chemin}")
        return repo, chemin
    except GitCommandError as e:
        logger.error(f"Erreur lors du clonage : {e}")
        raise


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE DÉPÔT
# ═══════════════════════════════════════════════════════════════════════════════

def deposer_doc(chemin_repo: str, dossier_docs_generes: str, 
                mkdocs_yml_path: str = None, 
                readme_genere_path: str = None) -> None:
    """
    Copie les fichiers de documentation générés dans le dépôt cloné.
    
    Args:
        chemin_repo: Chemin du dépôt cloné
        dossier_docs_generes: Dossier contenant la documentation générée
        mkdocs_yml_path: Chemin du fichier mkdocs.yml (optionnel)
        readme_genere_path: Chemin du README généré (optionnel)
    """
    destination_docs = os.path.join(chemin_repo, DOSSIER_DOCS_REPO)

    # Copier la documentation
    if os.path.exists(dossier_docs_generes):
        shutil.copytree(dossier_docs_generes, destination_docs, dirs_exist_ok=True)
        logger.info(f"Documentation copiée vers {destination_docs}")
    else:
        raise FileNotFoundError(f"Dossier de documentation introuvable : {dossier_docs_generes}")

    # Copier mkdocs.yml
    if mkdocs_yml_path and os.path.exists(mkdocs_yml_path):
        shutil.copy(mkdocs_yml_path, os.path.join(chemin_repo, FICHIER_MKDOCS))
        logger.info(f"{FICHIER_MKDOCS} copié")

    # Copier README
    if readme_genere_path and os.path.exists(readme_genere_path):
        shutil.copy(readme_genere_path, os.path.join(chemin_repo, FICHIER_README))
        logger.info(f"{FICHIER_README} mis à jour")


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE BRANCHE
# ═══════════════════════════════════════════════════════════════════════════════

def creer_branche(repo: Repo, nom_branche: str = None) -> str:
    """
    Crée et bascule sur une nouvelle branche dédiée à la documentation.
    
    Args:
        repo: Objet Repo GitPython
        nom_branche: Nom de la branche (défaut: docs/auto-generated)
        
    Returns:
        Nom de la branche
    """
    if nom_branche is None:
        nom_branche = BRANCHE_DEFAUT
    
    branches_locales = [b.name for b in repo.branches]

    if nom_branche in branches_locales:
        repo.git.checkout(nom_branche)
        logger.info(f"Branche existante : {nom_branche}")
    else:
        repo.git.checkout("-b", nom_branche)
        logger.info(f"Nouvelle branche créée : {nom_branche}")

    return nom_branche


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE COMMIT & PUSH
# ═══════════════════════════════════════════════════════════════════════════════

def commit_et_push(repo: Repo, nom_branche: str, 
                   message_commit: str = None, 
                   force: bool = False) -> bool:
    """
    Ajoute tous les fichiers modifiés, commit, puis push vers origin.
    
    Args:
        repo: Objet Repo GitPython
        nom_branche: Branche à pousser
        message_commit: Message de commit (défaut: message automatique)
        force: Si True, force le push
        
    Returns:
        True si des changements ont été poussés
    """
    if message_commit is None:
        message_commit = MESSAGE_COMMIT_DEFAUT

    repo.git.add(A=True)

    # Vérifier s'il y a des changements
    if not repo.is_dirty(untracked_files=True) and not repo.index.diff("HEAD"):
        logger.info("Aucun changement à commit.")
        return False

    repo.index.commit(message_commit)
    logger.info(f"Commit effectué : {message_commit}")

    origin = repo.remote(name="origin")

    try:
        if force:
            origin.push(refspec=f"{nom_branche}:{nom_branche}", force=True)
            logger.info(f"Push forcé sur {nom_branche}")
        else:
            origin.push(refspec=f"{nom_branche}:{nom_branche}")
            logger.info(f"Push effectué sur {nom_branche}")
        return True
    except GitCommandError as e:
        logger.error(f"Erreur lors du push : {e}")
        raise


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE NETTOYAGE
# ═══════════════════════════════════════════════════════════════════════════════

def nettoyer_clone_local(chemin_repo: str) -> None:
    """
    Supprime le clone local temporaire après publication.
    
    Args:
        chemin_repo: Chemin du clone à supprimer
    """
    if os.path.exists(chemin_repo):
        shutil.rmtree(chemin_repo)
        logger.info(f"Clone temporaire supprimé : {chemin_repo}")


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

def publier_documentation(url_repo: str, token: str, 
                          dossier_docs_generes: str,
                          plateforme: str = "github",
                          nom_branche: str = None,
                          mkdocs_yml_path: str = None,
                          readme_genere_path: str = None,
                          nettoyer: bool = None,
                          restructuration: dict = None) -> dict:
    """
    Fonction principale : enchaîne clonage, restructuration optionnelle,
    dépôt des fichiers, commit et push.
    
    Args:
        url_repo: URL du dépôt
        token: Token d'authentification
        dossier_docs_generes: Dossier de documentation générée
        plateforme: "github" ou "gitlab"
        nom_branche: Nom de la branche cible
        mkdocs_yml_path: Chemin mkdocs.yml
        readme_genere_path: Chemin README.md
        nettoyer: Nettoyer le clone après publication
        restructuration: Options de restructuration physique
        
    Returns:
        Dictionnaire avec le résultat
    """
    if nom_branche is None:
        nom_branche = BRANCHE_DEFAUT
    if nettoyer is None:
        nettoyer = NETTOYER_AUTO
    
    repo, chemin = cloner_pour_publication(url_repo, token, plateforme)

    try:
        creer_branche(repo, nom_branche)

        # Restructuration physique optionnelle
        if restructuration:
            from architecture.restructeur import restructurer_physiquement
            resume = restructurer_physiquement(
                chemin_repo_local=chemin,
                fichiers=restructuration.get("fichiers", []),
                infos_ast=restructuration.get("infos_ast", {}),
                architecture=restructuration.get("architecture", "MVC"),
            )
            logger.info(
                f"Restructuration physique : "
                f"{resume['total']} fichier(s) déplacé(s), "
                f"{resume['collisions']} collision(s)"
            )

        deposer_doc(chemin, dossier_docs_generes, mkdocs_yml_path, readme_genere_path)
        a_pousse = commit_et_push(repo, nom_branche)

        return {
            "succes": True,
            "branche": nom_branche,
            "changements_pousses": a_pousse,
            "url_repo": url_repo
        }

    finally:
        if nettoyer:
            nettoyer_clone_local(chemin)