# architecture/classifieur_fichiers.py
"""
Classifieur de fichiers par analyse du nom et du contenu.

Détermine le rôle architectural d'un fichier (controller, model, etc.)
en se basant sur son nom et son contenu AST.
"""

import logging
import os
import re
from typing import List, Optional

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DEPUIS .ENV
# ═══════════════════════════════════════════════════════════════════════════════

# Patterns de classification par nom de fichier
# Format: "mots_cles1,mots_cles2|role1,role2"
MOTS_CLES_NOM_STR = os.getenv(
    "CLASSIFIEUR_MOTS_CLES_NOM",
    "controller,controllers,handler,handlers,route,routes|controller,route,handlers;"
    "service,services|service,business,metier;"
    "repository,repositories,repo,dao|repository,data,donnees;"
    "gateway,gateways,proxy|gateway,proxy;"
    "usecase,usecases,interactor,interactors|usecase,application,interactors;"
    "viewmodel,viewmodels|viewmodel,state,store;"
    "presenter,presenters|presenter,logic,business;"
    "view,views,template,templates,component,components|view,ui,components;"
    "model,models,entity,entities,schema,schemas|model,entities,domain;"
    "error,errors,exception,exceptions|errors,exceptions;"
    "logging,logger,log|infrastructure,infra,utils;"
    "middleware,config,util,utils|infrastructure,infra,utils"
)

# Patterns d'imports pour la classification par contenu
IMPORTS_CONTROLLER_STR = os.getenv(
    "CLASSIFIEUR_IMPORTS_CONTROLLER",
    "apirouter,blueprint,django.urls,flask.blueprint,"
    "rest_framework.views,@router.,app.include_router"
)

IMPORTS_REPOSITORY_STR = os.getenv(
    "CLASSIFIEUR_IMPORTS_REPOSITORY",
    "sqlalchemy,psycopg2,sqlite3,pymongo,mongoose,"
    "cursor,django.db,asyncpg,session.query,"
    "repositories.base,repository.base,.repositories,.repository"
)

IMPORTS_MODEL_STR = os.getenv(
    "CLASSIFIEUR_IMPORTS_MODEL",
    "declarative_base,db.model,models.model,pydantic,"
    "@entity,dataclass,django.db.models"
)

DOSSIERS_INFRASTRUCTURE_STR = os.getenv(
    "CLASSIFIEUR_DOSSIERS_INFRA",
    "settings,config,configuration,migrations,env,environments"
)

# Flag debug
DEBUG_CLASSIFIEUR = os.getenv("DEBUG_CLASSIFIEUR", "false").lower() == "true"

# ═══════════════════════════════════════════════════════════════════════════════
# INITIALISATION DES STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

def _parser_mots_cles(chaines: str) -> List[tuple]:
    """
    Parse la configuration des mots-clés depuis .env.
    
    Format: "mot1,mot2|role1,role2;mot3,mot4|role3,role4"
    
    Args:
        chaines: Chaîne de configuration
        
    Returns:
        Liste de tuples (set_mots_cles, liste_roles)
    """
    resultats = []
    
    for groupe in chaines.split(";"):
        if "|" not in groupe:
            continue
        
        mots_str, roles_str = groupe.split("|", 1)
        mots_cles = set(m.strip().lower() for m in mots_str.split(",") if m.strip())
        roles = [r.strip().lower() for r in roles_str.split(",") if r.strip()]
        
        if mots_cles and roles:
            resultats.append((mots_cles, roles))
    
    return resultats


def _parser_imports(chaines: str) -> tuple:
    """Parse la configuration des imports."""
    return tuple(i.strip().lower() for i in chaines.split(",") if i.strip())


# Initialisation des structures depuis .env
MOTS_CLES_NOM = _parser_mots_cles(MOTS_CLES_NOM_STR)
IMPORTS_CONTROLLER = _parser_imports(IMPORTS_CONTROLLER_STR)
IMPORTS_REPOSITORY = _parser_imports(IMPORTS_REPOSITORY_STR)
IMPORTS_MODEL = _parser_imports(IMPORTS_MODEL_STR)
DOSSIERS_INFRASTRUCTURE = set(
    d.strip().lower() for d in DOSSIERS_INFRASTRUCTURE_STR.split(",") if d.strip()
)

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE TOKENISATION
# ═══════════════════════════════════════════════════════════════════════════════

def _tokeniser_nom(nom_fichier: str) -> List[str]:
    """
    Tokenise un nom de fichier en mots-clés.
    
    Exemples:
        user_controller.py → ["user", "controller"]
        UserController.java → ["user", "controller"]
        api-routes.ts → ["api", "routes"]
    
    Args:
        nom_fichier: Nom du fichier
        
    Returns:
        Liste de tokens normalisés
    """
    # Enlever l'extension
    nom = nom_fichier.rsplit(".", 1)[0]
    
    # Convertir CamelCase en snake_case
    nom = re.sub(r"(?<!^)(?=[A-Z])", "_", nom)
    
    # Remplacer les tirets par des underscores
    nom = nom.replace("-", "_")
    
    # Splitter et filtrer
    return [t.lower() for t in nom.split("_") if t]


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFICATION PAR NOM
# ═══════════════════════════════════════════════════════════════════════════════

def deviner_role_par_nom(nom_fichier: str) -> Optional[List[str]]:
    """
    Devine le rôle d'un fichier à partir de son nom.
    
    Args:
        nom_fichier: Nom du fichier (peut inclure le chemin)
        
    Returns:
        Liste des rôles possibles ou None
    """
    if not nom_fichier:
        return None

    # Extraire juste le nom du fichier (sans le chemin)
    nom = nom_fichier.rsplit("/", 1)[-1] if "/" in nom_fichier else nom_fichier
    tokens = set(_tokeniser_nom(nom))

    if DEBUG_CLASSIFIEUR:
        logger.debug(f"Tokens pour '{nom}': {tokens}")

    for mots_cles, roles in MOTS_CLES_NOM:
        if tokens & mots_cles:
            if DEBUG_CLASSIFIEUR:
                logger.debug(f"  → Rôle trouvé par nom: {roles[0]}")
            return roles

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFICATION PAR CONTENU
# ═══════════════════════════════════════════════════════════════════════════════

def _texte_imports(infos_ast_fichier: dict) -> str:
    """Extrait et concatène tous les imports d'un fichier."""
    return " ".join(infos_ast_fichier.get("imports", [])).lower()


def deviner_role_par_contenu(infos_ast_fichier: dict, 
                              chemin_fichier: str = "") -> Optional[List[str]]:
    """
    Devine le rôle d'un fichier à partir de son contenu AST.
    
    Args:
        infos_ast_fichier: Informations AST du fichier
        chemin_fichier: Chemin du fichier (pour le contexte)
        
    Returns:
        Liste des rôles possibles ou None
    """
    if not infos_ast_fichier:
        return None

    imports_txt = _texte_imports(infos_ast_fichier)
    classes = infos_ast_fichier.get("classes", [])
    fonctions = infos_ast_fichier.get("fonctions", [])
    
    # 1. Détecter les classes d'erreur
    if classes and any(
        c.get("nom", "").endswith(("Error", "Exception"))
        for c in classes
    ):
        if DEBUG_CLASSIFIEUR:
            logger.debug("  → Rôle trouvé par contenu: errors (classes d'erreur)")
        return ["errors", "exceptions"]
    
    # 2. Détecter les controllers par imports
    if any(mot in imports_txt for mot in IMPORTS_CONTROLLER):
        if DEBUG_CLASSIFIEUR:
            logger.debug("  → Rôle trouvé par contenu: controller (imports)")
        return ["controller", "route", "handlers"]
    
    # 3. Détecter les repositories par imports
    if any(mot in imports_txt for mot in IMPORTS_REPOSITORY):
        if DEBUG_CLASSIFIEUR:
            logger.debug("  → Rôle trouvé par contenu: repository (imports)")
        return ["repository", "data", "donnees"]
    
    # 4. Détecter l'infrastructure par dossier parent
    dossier_parent = chemin_fichier.replace("\\", "/").split("/")[-2:-1]
    dans_dossier_infra = bool(dossier_parent) and dossier_parent[0].lower() in DOSSIERS_INFRASTRUCTURE

    if dans_dossier_infra and classes:
        if DEBUG_CLASSIFIEUR:
            logger.debug("  → Rôle trouvé par contenu: infrastructure (dossier + classes)")
        return ["infrastructure", "infra", "utils"]
    
    # 5. Détecter les modèles par imports
    if any(mot in imports_txt for mot in IMPORTS_MODEL):
        if DEBUG_CLASSIFIEUR:
            logger.debug("  → Rôle trouvé par contenu: model (imports)")
        return ["model", "entities", "domain"]
    
    # 6. Si classes mais pas de pattern spécifique → probablement un modèle
    if classes:
        if DEBUG_CLASSIFIEUR:
            logger.debug("  → Rôle trouvé par contenu: model (classes génériques)")
        return ["model", "entities", "domain"]

    # 7. Si fonctions sans classes → probablement un service
    if fonctions and not classes:
        if DEBUG_CLASSIFIEUR:
            logger.debug("  → Rôle trouvé par contenu: service (fonctions sans classes)")
        return ["service", "business", "metier"]

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

def deviner_role(chemin_fichier: str, 
                 infos_ast_fichier: dict = None) -> Optional[List[str]]:
    """
    Devine le rôle architectural d'un fichier.
    
    Stratégie:
      1. D'abord via son nom (rapide, explicite)
      2. Si le nom ne donne rien, via son contenu AST
      3. Sinon None (le fichier garde son emplacement d'origine)
    
    Args:
        chemin_fichier: Chemin complet du fichier
        infos_ast_fichier: Informations AST (optionnel)
        
    Returns:
        Liste des rôles possibles ou None
    """
    nom_fichier = chemin_fichier.rsplit("/", 1)[-1]

    # 1. Classification par nom
    role = deviner_role_par_nom(nom_fichier)
    if role:
        logger.debug(f"{chemin_fichier} → rôle '{role[0]}' (nom)")
        return role

    # 2. Classification par contenu
    role = deviner_role_par_contenu(infos_ast_fichier, chemin_fichier)
    if role:
        logger.debug(f"{chemin_fichier} → rôle '{role[0]}' (contenu)")
        return role

    return None