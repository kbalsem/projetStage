# architecture/openapi_generator.py
"""
Générateur de spécification OpenAPI à partir des routes détectées.

Produit un document OpenAPI 3.0 compatible Swagger/Redoc.
"""

import json
import os
import re
from typing import Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DEPUIS .ENV
# ═══════════════════════════════════════════════════════════════════════════════

# Version OpenAPI
OPENAPI_VERSION = os.getenv("OPENAPI_VERSION", "3.0.0")

# Titre et description par défaut
OPENAPI_TITRE_DEFAUT = os.getenv(
    "OPENAPI_TITRE_DEFAUT", 
    "API détectée automatiquement"
)
OPENAPI_DESCRIPTION_DEFAUT = os.getenv(
    "OPENAPI_DESCRIPTION_DEFAUT",
    "Documentation générée automatiquement par GitDoc AI à partir "
    "de l'analyse statique du code source."
)

# Version par défaut
OPENAPI_VERSION_API = os.getenv("OPENAPI_VERSION_API", "auto-détectée")

# Réponse par défaut
OPENAPI_REPONSE_DEFAUT = os.getenv(
    "OPENAPI_REPONSE_DEFAUT",
    "Réponse détectée par analyse statique — schéma non garanti"
)

# Regex pour les paramètres de chemin
MOTIF_PARAM_FLASK = re.compile(r"<(?:[a-zA-Z]+:)?([a-zA-Z_][a-zA-Z0-9_]*)>")
MOTIF_PARAM_OPENAPI = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS PRINCIPALES
# ═══════════════════════════════════════════════════════════════════════════════




def _grouper_routes_par_chemin(routes: List[dict]) -> Dict[str, List[dict]]:
    """
    Groupe les routes par chemin pour gérer les multiples méthodes HTTP.
    
    Args:
        routes: Liste des routes
        
    Returns:
        Dictionnaire {chemin: [routes]}
    """
    groupes: Dict[str, List[dict]] = {}
    for route in routes:
        chemin = route.get("chemin", "/")
        groupes.setdefault(chemin, []).append(route)
    return groupes


def _normaliser_chemin(chemin_flask_ou_fastapi: str) -> str:
    """
    Normalise un chemin Flask ou FastAPI au format OpenAPI.
    
    Flask: /users/<int:id> → /users/{id}
    FastAPI: /items/{item_id} → /items/{item_id} (déjà bon)
    
    Args:
        chemin_flask_ou_fastapi: Chemin original
        
    Returns:
        Chemin normalisé OpenAPI
    """
    return MOTIF_PARAM_FLASK.sub(r"{\1}", chemin_flask_ou_fastapi)


def _construire_operations(routes_du_chemin: List[dict], 
                           chemin_normalise: str) -> dict:
    """
    Construit les opérations OpenAPI pour un chemin donné.
    
    Args:
        routes_du_chemin: Routes associées à ce chemin
        chemin_normalise: Chemin normalisé OpenAPI
        
    Returns:
        Dictionnaire des opérations (get, post, etc.)
    """
    operations = {}
    noms_parametres = MOTIF_PARAM_OPENAPI.findall(chemin_normalise)

    for route in routes_du_chemin:
        methode_openapi = route["methode"].lower()

        operations[methode_openapi] = {
            "summary": f"Fonction détectée : {route['fonction']}",
            "description": (
                f"Détectée dans {route['fichier']} (ligne {route['ligne']}) "
                f"— framework : {route['framework']}"
            ),
            "tags": [_deduire_tag(route["fichier"])],
            "parameters": _construire_parametres(noms_parametres),
            "responses": {
                "200": {
                    "description": OPENAPI_REPONSE_DEFAUT,
                }
            },
        }

    return operations


def _construire_parametres(noms_parametres: List[str]) -> List[dict]:
    """
    Construit la liste des paramètres de chemin OpenAPI.
    
    Args:
        noms_parametres: Noms des paramètres extraits du chemin
        
    Returns:
        Liste des paramètres au format OpenAPI
    """
    return [
        {
            "name": nom_param,
            "in": "path",
            "required": True,
            "schema": {"type": "string"},
            "description": "Type exact non déterminé par analyse statique",
        }
        for nom_param in noms_parametres
    ]


def _deduire_tag(chemin_fichier: str) -> str:
    """
    Déduit un tag OpenAPI à partir du chemin du fichier.
    
    Exemples:
        app/routes/users.py → "routes.users"
        api/controllers/user_controller.py → "controllers.user_controller"
        main.py → "main"
    
    Args:
        chemin_fichier: Chemin du fichier source
        
    Returns:
        Tag déduit
    """
    sans_extension = chemin_fichier.rsplit(".", 1)[0]
    segments = [s for s in sans_extension.replace("\\", "/").split("/") if s]
    
    if len(segments) >= 2:
        return ".".join(segments[-2:])
    elif segments:
        return segments[-1]
    else:
        return "default"


def sauvegarder_spec(spec: dict, chemin_sortie: str) -> None:
    """
    Sauvegarde la spécification OpenAPI dans un fichier JSON.
    
    Args:
        spec: Spécification OpenAPI
        chemin_sortie: Chemin du fichier de sortie
    """
    with open(chemin_sortie, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
