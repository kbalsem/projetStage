# architecture/api_route_detector.py
"""
Détecteur de routes API par analyse statique du code Python.

Supporte Flask, FastAPI et autres frameworks Python avec décorateurs de route.
"""

import ast
import os
from typing import Dict, List, Optional, Set

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DEPUIS .ENV
# ═══════════════════════════════════════════════════════════════════════════════

# Méthodes HTTP valides
METHODES_HTTP_VALIDES: Set[str] = set(
    m.strip().lower() for m in os.getenv(
        "API_METHODES_HTTP",
        "get,post,put,delete,patch,options,head"
    ).split(",")
)

# Noms d'objets routeur courants
NOMS_OBJETS_ROUTEUR: Set[str] = set(
    n.strip().lower() for n in os.getenv(
        "API_NOMS_ROUTEUR",
        "app,blueprint,bp,router,api,application,web"
    ).split(",")
)

# Extensions de fichiers à analyser
EXTENSIONS_ANALYSEES: Set[str] = set(
    ext.strip() for ext in os.getenv(
        "API_EXTENSIONS_FICHIERS",
        ".py"
    ).split(",")
)

# Méthode par défaut si non spécifiée
METHODE_DEFAUT = os.getenv("API_METHODE_DEFAUT", "GET").upper()

# Flag debug
DEBUG_API = os.getenv("DEBUG_API_DETECTOR", "false").lower() == "true"

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS PRINCIPALES
# ═══════════════════════════════════════════════════════════════════════════════

def detecter_routes(fichiers: Dict[str, str]) -> List[dict]:
    """
    Détecte toutes les routes API dans un ensemble de fichiers Python.
    
    Args:
        fichiers: Dictionnaire {chemin: contenu} des fichiers
        
    Returns:
        Liste des routes détectées avec leur méthode, chemin, etc.
    """
    toutes_les_routes: List[dict] = []

    for chemin_fichier, contenu in fichiers.items():
        # Vérifier l'extension du fichier
        if not any(chemin_fichier.endswith(ext) for ext in EXTENSIONS_ANALYSEES):
            continue

        try:
            arbre = ast.parse(contenu, filename=chemin_fichier)
        except (SyntaxError, ValueError) as e:
            if DEBUG_API:
                import logging
                logging.getLogger(__name__).debug(
                    f"Erreur parsing {chemin_fichier}: {e}"
                )
            continue

        routes_du_fichier = _extraire_routes_du_fichier(arbre, chemin_fichier)
        toutes_les_routes.extend(routes_du_fichier)
        
        if DEBUG_API and routes_du_fichier:
            import logging
            logging.getLogger(__name__).debug(
                f"{len(routes_du_fichier)} route(s) dans {chemin_fichier}"
            )

    return toutes_les_routes


def _extraire_routes_du_fichier(arbre: ast.AST, chemin_fichier: str) -> List[dict]:
    """
    Extrait les routes d'un fichier Python parsé.
    
    Args:
        arbre: AST du fichier
        chemin_fichier: Chemin du fichier source
        
    Returns:
        Liste des routes trouvées
    """
    routes = []
    
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for decorateur in noeud.decorator_list:
            info_route = _analyser_decorateur(decorateur)
            if info_route is None:
                continue

            methodes, chemin_route, framework = info_route
            
            for methode in methodes:
                routes.append({
                    "methode": methode,
                    "chemin": chemin_route,
                    "fonction": noeud.name,
                    "fichier": chemin_fichier,
                    "framework": framework,
                    "ligne": decorateur.lineno,
                })

    return routes


def _analyser_decorateur(decorateur: ast.expr) -> Optional[tuple]:
    """
    Analyse un décorateur pour extraire les informations de route.
    
    Args:
        decorateur: Noeud AST du décorateur
        
    Returns:
        Tuple (methodes, chemin, framework) ou None
    """
    if not isinstance(decorateur, ast.Call):
        return None

    fonction_appelee = decorateur.func
    if not isinstance(fonction_appelee, ast.Attribute):
        return None

    nom_attribut = fonction_appelee.attr
    objet_racine = _nom_objet_racine(fonction_appelee.value)

    # Vérifier que l'objet racine est un routeur connu
    if objet_racine is None or objet_racine.lower() not in NOMS_OBJETS_ROUTEUR:
        return None

    # Extraire le chemin de la route
    chemin_route = _extraire_chemin(decorateur)
    if chemin_route is None:
        return None

    # Cas Flask: @app.route("/path", methods=["GET", "POST"])
    if nom_attribut == "route":
        methodes = _extraire_methodes_flask(decorateur)
        return methodes, chemin_route, "flask"

    # Cas FastAPI/Flask: @app.get("/path"), @router.post("/path")
    if nom_attribut in METHODES_HTTP_VALIDES:
        return [nom_attribut.upper()], chemin_route, "fastapi_ou_flask"

    return None


def _nom_objet_racine(noeud: ast.expr) -> Optional[str]:
    """
    Extrait le nom de l'objet racine d'un appel de méthode.
    
    Exemples:
        app.route → "app"
        bp.get → "bp"
        router.post → "router"
    
    Args:
        noeud: Noeud AST représentant l'objet
        
    Returns:
        Nom de l'objet ou None
    """
    if isinstance(noeud, ast.Name):
        return noeud.id
    
    # Support des appels chaînés simples: flask_app.route
    if isinstance(noeud, ast.Attribute):
        return noeud.attr
    
    return None


def _extraire_chemin(appel: ast.Call) -> Optional[str]:
    """
    Extrait le chemin d'une route depuis un appel de décorateur.
    
    Args:
        appel: Noeud AST de l'appel
        
    Returns:
        Chemin de la route ou None
    """
    if not appel.args:
        return None

    premier_argument = appel.args[0]
    
    # Python 3.8+ : ast.Constant
    if isinstance(premier_argument, ast.Constant) and isinstance(premier_argument.value, str):
        return premier_argument.value
    
    # Python 3.7- : ast.Str (déprécié mais encore utilisé)
    if hasattr(ast, 'Str') and isinstance(premier_argument, ast.Str):
        return premier_argument.s

    return None


def _extraire_methodes_flask(appel: ast.Call) -> List[str]:
    """
    Extrait les méthodes HTTP d'un décorateur Flask @app.route().
    
    Args:
        appel: Noeud AST de l'appel @app.route()
        
    Returns:
        Liste des méthodes HTTP
    """
    for mot_cle in appel.keywords:
        if mot_cle.arg == "methods" and isinstance(mot_cle.value, (ast.List, ast.Tuple)):
            methodes_trouvees = []
            
            for elt in mot_cle.value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    methodes_trouvees.append(elt.value.upper())
                elif hasattr(ast, 'Str') and isinstance(elt, ast.Str):
                    methodes_trouvees.append(elt.s.upper())
            
            if methodes_trouvees:
                return methodes_trouvees

    # Par défaut, une route sans methods=... accepte GET
    return [METHODE_DEFAUT]