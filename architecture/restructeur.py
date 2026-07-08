# architecture/restructeur.py
"""
Module de restructuration de l'arborescence selon l'architecture détectée.

Ce module transforme la structure de fichiers originale en une nouvelle
structure organisée selon les patterns de l'architecture cible.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

from architecture.classifieur_fichiers import deviner_role
from architecture.signaux import SIGNAUX
from utils.tree_utils import trier_arbre

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DEPUIS .ENV
# ═══════════════════════════════════════════════════════════════════════════════

# Dossiers de documentation
DOSSIER_DOC = os.getenv("RESTRUCTEUR_DOSSIER_DOC", "documentation")
DOSSIER_DOC_ALT = os.getenv("RESTRUCTEUR_DOSSIER_DOC_ALT", "documentation_gitdoc")
FICHIERS_DOC_GENERE = os.getenv(
    "RESTRUCTEUR_FICHIERS_DOC",
    "architecture.md,changelog.md,documentation.md"
).split(",")

# Dossiers de tests
DOSSIERS_TESTS = set(
    d.strip().lower() for d in os.getenv(
        "RESTRUCTEUR_DOSSIERS_TESTS", 
        "test,tests,spec,specs,__tests__"
    ).split(",")
)

# Patterns de noms de fichiers de test
PREFIXES_TESTS = tuple(
    p.strip() for p in os.getenv(
        "RESTRUCTEUR_PREFIXES_TESTS",
        "test_,spec_"
    ).split(",")
)
SUFFIXES_TESTS = tuple(
    s.strip() for s in os.getenv(
        "RESTRUCTEUR_SUFFIXES_TESTS",
        "_test,_spec,.test,.spec"
    ).split(",")
)

# Catégories à ignorer dans l'index d'alias
CATEGORIES_IGNOREES = set(
    c.strip() for c in os.getenv(
        "RESTRUCTEUR_CATEGORIES_IGNOREES",
        "frameworks,imports,decorateurs,dependances,classes"
    ).split(",")
)

# Flag pour activer/désactiver l'ajout du nom d'architecture dans le titre
AJOUTER_ARCHITECTURE_NOM = os.getenv("RESTRUCTEUR_AJOUTER_ARCHITECTURE_NOM", "true").lower() == "true"

# Flag pour activer le mode debug (logs détaillés)
DEBUG_RESTRUCTEUR = os.getenv("DEBUG_RESTRUCTEUR", "false").lower() == "true"

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def _est_fichier_de_test(dossier_parts: List[str], nom_fichier: str) -> bool:
    """
    Détermine si un fichier est un fichier de test.
    
    Args:
        dossier_parts: Parties du chemin du dossier parent
        nom_fichier: Nom du fichier à vérifier
        
    Returns:
        True si le fichier est un fichier de test
    """
    # Vérifier si dans un dossier de test
    if any(part.lower() in DOSSIERS_TESTS for part in dossier_parts):
        return True
    
    # Vérifier les patterns de nom de fichier
    nom_sans_ext = nom_fichier.rsplit(".", 1)[0].lower()
    
    if nom_sans_ext.startswith(PREFIXES_TESTS):
        return True
    
    if nom_sans_ext.endswith(SUFFIXES_TESTS):
        return True
    
    # Vérifier les extensions de test (.test.js, .spec.ts, etc.)
    if any(nom_fichier.lower().endswith(ext) for ext in SUFFIXES_TESTS):
        return True
    
    return False


def _construire_index_alias(architecture: str) -> Tuple[Dict[str, str], List[str]]:
    """
    Construit un index qui mappe les alias de dossiers vers les noms canoniques.
    
    Args:
        architecture: Nom de l'architecture cible
        
    Returns:
        Tuple (index_alias, categories_ordonnees)
        - index_alias: dict {alias: nom_canonique}
        - categories_ordonnees: liste ordonnée des noms de dossiers canoniques
    """
    patterns_archi = SIGNAUX.get(architecture, {})
    
    if not patterns_archi:
        logger.warning(f"Architecture '{architecture}' non trouvée dans SIGNAUX")
        return {}, []
    
    index_alias = {}
    categories_ordonnees = []

    for categorie, signaux in patterns_archi.items():
        # Ignorer les catégories non structurelles
        if categorie in CATEGORIES_IGNOREES:
            continue
        
        if signaux:
            nom_dossier = signaux[0]["nom"]
            categories_ordonnees.append(nom_dossier)
            
            # Mapper tous les alias vers le nom canonique
            for signal in signaux:
                alias = signal["nom"].lower()
                if alias not in index_alias:
                    index_alias[alias] = nom_dossier
    
    if DEBUG_RESTRUCTEUR:
        logger.debug(f"Index alias pour {architecture}: {index_alias}")
        logger.debug(f"Catégories ordonnées: {categories_ordonnees}")
    
    return index_alias, categories_ordonnees


def _trouver_categorie_cible(role_tokens: Optional[List[str]], 
                              index_alias: Dict[str, str]) -> Optional[str]:
    """
    Trouve la catégorie cible correspondant aux rôles détectés.
    
    Args:
        role_tokens: Liste des rôles potentiels du fichier
        index_alias: Dictionnaire de mapping alias → catégorie
        
    Returns:
        Nom de la catégorie cible ou None
    """
    if not role_tokens:
        return None
    
    for token in role_tokens:
        categorie = index_alias.get(token.lower())
        if categorie:
            return categorie
    
    return None


def _deja_bien_range(dossier_parts: List[str], 
                      categorie: str, 
                      index_alias: Dict[str, str]) -> bool:
    """
    Vérifie si le fichier est déjà dans le bon dossier.
    
    Args:
        dossier_parts: Parties du chemin du dossier parent
        categorie: Catégorie cible attendue
        index_alias: Dictionnaire de mapping alias → catégorie
        
    Returns:
        True si le fichier est déjà bien rangé
    """
    return any(
        index_alias.get(part.lower()) == categorie
        for part in dossier_parts
    )


def _resoudre_collision(dossier_parts: List[str], 
                         nom: str, 
                         chemin_dest_dossier: str, 
                         noms_existants: Optional[Set[str]] = None) -> Tuple[str, str, bool]:
    """
    Résout les collisions de noms de fichiers.
    
    Args:
        dossier_parts: Parties du chemin d'origine
        nom: Nom du fichier
        chemin_dest_dossier: Chemin du dossier de destination
        noms_existants: Ensemble des noms déjà présents (optionnel)
        
    Returns:
        Tuple (chemin_complet, nom_final, collision_detectee)
    """
    chemin_dest = Path(chemin_dest_dossier) / nom if chemin_dest_dossier else Path(nom)

    # Vérifier si le nom existe déjà
    if noms_existants is not None:
        existe = nom in noms_existants
    else:
        existe = chemin_dest.exists() if chemin_dest_dossier else False

    if not existe:
        return str(chemin_dest), nom, False

    # Construire un nom unique
    base, ext = os.path.splitext(nom)
    origine = "_".join(p for p in dossier_parts if p) or "src"
    candidat = f"{base}__{origine}{ext}"
    chemin_dest = Path(chemin_dest_dossier) / candidat if chemin_dest_dossier else Path(candidat)

    compteur = 2
    while True:
        if noms_existants is not None:
            if candidat not in noms_existants:
                break
        else:
            if not chemin_dest.exists():
                break
        
        candidat = f"{base}__{origine}_{compteur}{ext}"
        chemin_dest = Path(chemin_dest_dossier) / candidat if chemin_dest_dossier else Path(candidat)
        compteur += 1
        
        # Protection contre les boucles infinies
        if compteur > 100:
            logger.error(f"Trop de collisions pour {nom}")
            return str(chemin_dest), candidat, True

    logger.warning(f"Collision résolue : {nom} → {candidat}")
    return str(chemin_dest), candidat, True


def _inserer_chemin(arbre: dict, 
                    chemin_parts: List[str], 
                    dossier_origine: Optional[List[str]] = None) -> None:
    """
    Insère un chemin (fichier ou dossier) dans l'arbre.
    Crée les dossiers intermédiaires si nécessaire.
    
    Args:
        arbre: Arbre cible
        chemin_parts: Parties du chemin à insérer
        dossier_origine: Dossier d'origine pour la résolution de collision
    """
    if not chemin_parts:
        return
    
    nom = chemin_parts[0]
    reste = chemin_parts[1:]

    # Résoudre les collisions pour les fichiers
    if len(reste) == 0 and dossier_origine:
        enfants = arbre.get("children", [])
        noms_existants = {e["name"] for e in enfants}
        _, nom, _ = _resoudre_collision(dossier_origine, nom, "", noms_existants)

    # Chercher si le noeud existe déjà
    enfant = next(
        (e for e in arbre.get("children", []) if e["name"] == nom), 
        None
    )
    
    if enfant is None:
        enfant = {
            "name": nom, 
            "type": "file" if not reste else "directory", 
            "children": []
        }
        arbre.setdefault("children", []).append(enfant)
    
    # Continuer récursivement pour les sous-dossiers
    if reste:
        _inserer_chemin(enfant, reste, dossier_origine)


def _collecter_fichiers(arbre: dict, 
                        dossier_parts: List[str] = None,
                        noeud_racine: dict = None) -> List[Dict]:
    """
    Collecte tous les fichiers de l'arbre avec leurs chemins et rôles.
    
    Args:
        arbre: Arbre à parcourir
        dossier_parts: Parties du chemin courant
        noeud_racine: Référence au noeud racine pour éviter de l'inclure
        
    Returns:
        Liste de dictionnaires {nom, dossier_parts, role}
    """
    if dossier_parts is None:
        dossier_parts = []
    if noeud_racine is None:
        noeud_racine = arbre
    
    fichiers = []
    
    if arbre.get("type") == "file":
        fichiers.append({
            "nom": arbre["name"],
            "dossier_parts": dossier_parts.copy(),
            "role": arbre.get("role"),
        })
    elif arbre.get("type") == "directory" and "children" in arbre:
        # Ne pas inclure le nom du noeud racine dans le chemin
        sous_dossier = dossier_parts
        if arbre is not noeud_racine:
            sous_dossier = dossier_parts + [arbre["name"]]
        
        for enfant in arbre.get("children", []):
            fichiers.extend(_collecter_fichiers(enfant, sous_dossier, noeud_racine))
    
    return fichiers


def _elaguer_dossiers_vides(noeud: dict) -> bool:
    """
    Supprime récursivement les dossiers vides de l'arbre.
    
    Args:
        noeud: Noeud à élaguer
        
    Returns:
        True si le noeud contient encore des fichiers
    """
    if noeud["type"] != "directory":
        return True
    
    enfants_valides = []
    for enfant in noeud.get("children", []):
        if enfant["type"] == "file" or _elaguer_dossiers_vides(enfant):
            enfants_valides.append(enfant)
    
    noeud["children"] = enfants_valides
    return len(enfants_valides) > 0


def _elaguer_dossiers_vides_disque(dossier_racine: str) -> None:
    """
    Supprime les dossiers vides sur le disque.
    
    Args:
        dossier_racine: Chemin racine à nettoyer
    """
    for chemin_courant, _, _ in os.walk(dossier_racine, topdown=False):
        # Ne pas supprimer .git ou la racine
        if ".git" in chemin_courant.split(os.sep) or chemin_courant == dossier_racine:
            continue
        
        try:
            if not os.listdir(chemin_courant):
                os.rmdir(chemin_courant)
                if DEBUG_RESTRUCTEUR:
                    logger.debug(f"Dossier vide supprimé: {chemin_courant}")
        except OSError as e:
            logger.debug(f"Impossible de supprimer {chemin_courant}: {e}")


def _ajouter_dossier_documentation(arbre_cible: dict) -> None:
    """
    Ajoute le dossier de documentation à l'arbre cible.
    
    Args:
        arbre_cible: Arbre de destination
    """
    # Vérifier si un dossier "documentation" existe déjà
    nom_doc = DOSSIER_DOC
    for enfant in arbre_cible.get("children", []):
        if enfant["name"] == nom_doc:
            nom_doc = DOSSIER_DOC_ALT
            break

    # Créer les fichiers de documentation
    fichiers_doc = [
        {"name": nom_fichier.strip(), "type": "file", "children": []}
        for nom_fichier in FICHIERS_DOC_GENERE
    ]

    arbre_cible["children"].append({
        "name": nom_doc,
        "type": "directory",
        "children": fichiers_doc
    })


def _nettoyer_roles(noeud: dict) -> None:
    """
    Supprime les attributs 'role' de tous les noeuds (utilisé pour l'affichage).
    
    Args:
        noeud: Noeud à nettoyer
    """
    noeud.pop("role", None)
    for enfant in noeud.get("children", []):
        _nettoyer_roles(enfant)


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS PRINCIPALES
# ═══════════════════════════════════════════════════════════════════════════════

def construire_arbre_cible(arbre_original: dict, 
                           architecture: str) -> dict:
    """
    Construit un nouvel arbre de fichiers organisé selon l'architecture cible.
    
    Args:
        arbre_original: Structure de fichiers originale
        architecture: Architecture cible (MVC, CLEAN, etc.)
        
    Returns:
        Nouvel arbre restructuré
    """
    if not arbre_original:
        logger.error("Arbre original vide")
        return {"name": "Projet", "type": "directory", "children": []}
    
    logger.info(f"Restructuration vers {architecture}...")
    
    # Construire l'index des catégories
    index_alias, categories_ordonnees = _construire_index_alias(architecture)
    
    if not index_alias:
        logger.warning(f"Aucune catégorie trouvée pour {architecture}, retour à l'original")
        return arbre_original

    # Collecter tous les fichiers
    tous_fichiers = _collecter_fichiers(arbre_original)
    logger.info(f"Fichiers à restructurer : {len(tous_fichiers)}")

    # Initialiser l'arbre cible
    nom_arbre = arbre_original.get("name", "Projet")
    if AJOUTER_ARCHITECTURE_NOM:
        nom_arbre = f"{nom_arbre} ({architecture})"
    
    arbre_cible = {
        "name": nom_arbre,
        "type": "directory",
        "children": []
    }

    # Créer les dossiers de catégories
    for nom_dossier in categories_ordonnees:
        if not any(e["name"] == nom_dossier for e in arbre_cible["children"]):
            arbre_cible["children"].append({
                "name": nom_dossier, 
                "type": "directory", 
                "children": []
            })

    # Traiter chaque fichier
    stats = {
        "deplaces": 0,
        "inchanges": 0,
        "tests": 0,
        "sans_role": 0
    }
    
    for fichier in tous_fichiers:
        # Fichiers de test → dossier tests/
        if _est_fichier_de_test(fichier["dossier_parts"], fichier["nom"]):
            chemin_parts = ["tests"] + fichier["dossier_parts"] + [fichier["nom"]]
            _inserer_chemin(arbre_cible, chemin_parts)
            stats["tests"] += 1
            continue

        role_tokens = fichier.get("role")
        
        # Fichiers sans rôle → emplacement original
        if not role_tokens:
            chemin_parts = fichier["dossier_parts"] + [fichier["nom"]]
            _inserer_chemin(arbre_cible, chemin_parts)
            stats["sans_role"] += 1
            continue

        # Trouver la catégorie cible
        categorie_cible = _trouver_categorie_cible(role_tokens, index_alias)

        # Fichier déjà bien rangé ou sans catégorie
        if not categorie_cible or _deja_bien_range(
            fichier["dossier_parts"], categorie_cible, index_alias
        ):
            chemin_parts = fichier["dossier_parts"] + [fichier["nom"]]
            _inserer_chemin(arbre_cible, chemin_parts)
            stats["inchanges"] += 1
            continue

        # Déplacer vers la catégorie cible
        _inserer_chemin(
            arbre_cible, 
            [categorie_cible, fichier["nom"]], 
            fichier["dossier_parts"]
        )
        stats["deplaces"] += 1

    # Nettoyage final
    _elaguer_dossiers_vides(arbre_cible)
    _ajouter_dossier_documentation(arbre_cible)
    _nettoyer_roles(arbre_cible)
    trier_arbre(arbre_cible)

    # Logs des statistiques
    logger.info("Restructuration terminée :")
    logger.info(f"  - {stats['deplaces']} fichier(s) déplacé(s)")
    logger.info(f"  - {stats['inchanges']} fichier(s) inchangé(s)")
    logger.info(f"  - {stats['tests']} fichier(s) de test")
    logger.info(f"  - {stats['sans_role']} fichier(s) sans rôle défini")

    return arbre_cible

def construire_arbre_avec_mappings(arbre_original: dict, 
                                    architecture: str) -> Tuple[dict, List[Dict], Dict]:
    """
    Construit l'arbre cible, les mappings de transformation ET les statistiques,
    en un seul passage garanti cohérent avec construire_arbre_cible.

    Args:
        arbre_original: Structure de fichiers originale
        architecture: Architecture cible

    Returns:
        Tuple (arbre_cible, mappings, stats)
    """
    stats_vides = {
        "nouveaux_dossiers": 0, "fichiers_deplaces": 0,
        "fichiers_inchanges": 0, "fichiers_supprimes": 0
    }

    if not arbre_original:
        logger.error("Arbre original vide")
        return {"name": "Projet", "type": "directory", "children": []}, [], stats_vides

    index_alias, categories_ordonnees = _construire_index_alias(architecture)

    if not index_alias:
        logger.warning(f"Aucune catégorie trouvée pour {architecture}, retour à l'original")
        return arbre_original, [], stats_vides

    nom_arbre = arbre_original.get("name", "Projet")
    if AJOUTER_ARCHITECTURE_NOM:
        nom_arbre = f"{nom_arbre} ({architecture})"

    arbre_cible = {"name": nom_arbre, "type": "directory", "children": []}

    # Pré-créer les dossiers de catégories (identique à construire_arbre_cible)
    for nom_dossier in categories_ordonnees:
        if not any(e["name"] == nom_dossier for e in arbre_cible["children"]):
            arbre_cible["children"].append({
                "name": nom_dossier, "type": "directory", "children": []
            })

    tous_fichiers = _collecter_fichiers(arbre_original)
    mappings = []
    dossiers_annonces = set()
    compteurs = {"deplaces": 0, "inchanges": 0, "tests": 0, "sans_role": 0}

    def _noms_existants_dans(categorie: str) -> Set[str]:
        """Renvoie les noms de fichiers déjà présents dans le dossier de catégorie cible."""
        for enfant in arbre_cible["children"]:
            if enfant["name"] == categorie:
                return {e["name"] for e in enfant.get("children", [])}
        return set()

    for fichier in tous_fichiers:
        chemin_original = "/".join(fichier["dossier_parts"] + [fichier["nom"]])
        role_tokens = fichier.get("role")

        # --- Fichier de test ---
        if _est_fichier_de_test(fichier["dossier_parts"], fichier["nom"]):
            _, nom_final, collision = _resoudre_collision(
                fichier["dossier_parts"], fichier["nom"], "",
                noms_existants=_noms_existants_dans("tests")
            )
            _inserer_chemin(arbre_cible, ["tests"] + fichier["dossier_parts"] + [nom_final])

            if "tests" not in dossiers_annonces:
                dossiers_annonces.add("tests")
                mappings.append({"from": None, "to": "tests", "status": "new", "type": "directory"})

            mappings.append({
                "from": chemin_original,
                "to": "tests/" + "/".join(fichier["dossier_parts"] + [nom_final]),
                "status": "moved", "type": "file"
            })
            compteurs["tests"] += 1
            continue

        # --- Fichier sans rôle ---
        if not role_tokens:
            _inserer_chemin(arbre_cible, fichier["dossier_parts"] + [fichier["nom"]])
            mappings.append({"from": chemin_original, "to": chemin_original,
                              "status": "unchanged", "type": "file"})
            compteurs["sans_role"] += 1
            continue

        categorie_cible = _trouver_categorie_cible(role_tokens, index_alias)

        # --- Déjà bien rangé / pas de catégorie ---
        if not categorie_cible or _deja_bien_range(fichier["dossier_parts"], categorie_cible, index_alias):
            _inserer_chemin(arbre_cible, fichier["dossier_parts"] + [fichier["nom"]])
            mappings.append({"from": chemin_original, "to": chemin_original,
                              "status": "unchanged", "type": "file"})
            compteurs["inchanges"] += 1
            continue

        # --- Déplacement avec résolution de collision cohérente avec _inserer_chemin ---
        _, nom_final, collision = _resoudre_collision(
            fichier["dossier_parts"], fichier["nom"], "",
            noms_existants=_noms_existants_dans(categorie_cible)
        )
        _inserer_chemin(arbre_cible, [categorie_cible, fichier["nom"]], fichier["dossier_parts"])

        if categorie_cible not in dossiers_annonces:
            dossiers_annonces.add(categorie_cible)
            mappings.append({"from": None, "to": categorie_cible, "status": "new", "type": "directory"})

        mappings.append({
            "from": chemin_original,
            "to": f"{categorie_cible}/{nom_final}",
            "status": "moved", "type": "file"
        })
        compteurs["deplaces"] += 1

    # Post-traitement identique à construire_arbre_cible → cohérence garantie
    _elaguer_dossiers_vides(arbre_cible)
    _ajouter_dossier_documentation(arbre_cible)
    _nettoyer_roles(arbre_cible)
    trier_arbre(arbre_cible)

    stats = {
        "nouveaux_dossiers": sum(1 for m in mappings if m["status"] == "new" and m["type"] == "directory"),
        "fichiers_deplaces": compteurs["deplaces"] + compteurs["tests"],
        "fichiers_inchanges": compteurs["inchanges"] + compteurs["sans_role"],
        "fichiers_supprimes": 0,
    }

    logger.info(
        f"Restructuration (avec mappings) terminée : "
        f"{compteurs['deplaces']} déplacé(s), {compteurs['inchanges']} inchangé(s), "
        f"{compteurs['tests']} test(s), {compteurs['sans_role']} sans rôle"
    )

    return arbre_cible, mappings, stats

def restructurer_physiquement(chemin_repo_local: str, 
                               fichiers: List[str],
                               infos_ast: Dict, 
                               architecture: str) -> Dict:
    """
    Restructure physiquement les fichiers sur le disque.
    
    Args:
        chemin_repo_local: Chemin racine du dépôt
        fichiers: Liste des chemins de fichiers
        infos_ast: Informations AST par fichier
        architecture: Architecture cible
        
    Returns:
        Dictionnaire avec les statistiques de déplacement
    """
    index_alias, _ = _construire_index_alias(architecture)
    deplaces = []

    if not index_alias:
        logger.warning("Aucun index d'alias, restructuration physique annulée")
        return {"deplaces": deplaces, "total": 0, "collisions": 0}

    for chemin_fichier in fichiers:
        chemin_relatif = chemin_fichier.replace("\\", "/")
        parties = chemin_relatif.split("/")
        nom = parties[-1]
        dossier_parts = parties[:-1]

        # Ignorer les fichiers de test
        if _est_fichier_de_test(dossier_parts, nom):
            continue

        # Deviner le rôle du fichier
        role_tokens = deviner_role(chemin_relatif, infos_ast.get(chemin_relatif))
        if not role_tokens:
            continue

        # Trouver la catégorie cible
        categorie_cible = _trouver_categorie_cible(role_tokens, index_alias)
        if not categorie_cible or _deja_bien_range(dossier_parts, categorie_cible, index_alias):
            continue

        # Vérifier que le fichier source existe
        chemin_source = Path(chemin_repo_local) / Path(*parties)
        if not chemin_source.is_file():
            logger.warning(f"Fichier source introuvable: {chemin_source}")
            continue

        # Créer le dossier de destination
        chemin_dest_dossier = Path(chemin_repo_local) / categorie_cible
        chemin_dest_dossier.mkdir(parents=True, exist_ok=True)

        # Résoudre les collisions
        chemin_dest, nom_final, collision = _resoudre_collision(
            dossier_parts, nom, str(chemin_dest_dossier)
        )

        # Déplacer le fichier
        try:
            shutil.move(str(chemin_source), chemin_dest)
            deplaces.append({
                "de": chemin_relatif,
                "vers": str(Path(categorie_cible) / nom_final),
                "collision": collision,
            })
            
            if DEBUG_RESTRUCTEUR:
                logger.debug(f"Déplacé: {chemin_relatif} → {categorie_cible}/{nom_final}")
                
        except OSError as e:
            logger.error(f"Erreur déplacement {chemin_source}: {e}")

    # Nettoyer les dossiers vides
    _elaguer_dossiers_vides_disque(chemin_repo_local)

    total_collisions = sum(1 for d in deplaces if d.get("collision"))
    
    logger.info(
        f"Restructuration physique terminée : "
        f"{len(deplaces)} déplacé(s), {total_collisions} collision(s)"
    )

    return {
        "deplaces": deplaces,
        "total": len(deplaces),
        "collisions": total_collisions,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE STATISTIQUES
# ═══════════════════════════════════════════════════════════════════════════════

def calculer_statistiques(arbre_original: dict, arbre_cible: dict) -> Dict:
    """
    Calcule les statistiques de transformation entre deux arbres.
    
    Args:
        arbre_original: Arbre source
        arbre_cible: Arbre cible
        
    Returns:
        Dictionnaire de statistiques
    """
    fichiers_originaux = set()
    fichiers_cibles = set()
    
    for f in _collecter_fichiers(arbre_original):
        fichiers_originaux.add("/".join(f["dossier_parts"] + [f["nom"]]))
    
    for f in _collecter_fichiers(arbre_cible):
        fichiers_cibles.add("/".join(f["dossier_parts"] + [f["nom"]]))
    
    return {
        "total_original": len(fichiers_originaux),
        "total_cible": len(fichiers_cibles),
        "nouveaux": len(fichiers_cibles - fichiers_originaux),
        "supprimes": len(fichiers_originaux - fichiers_cibles),
        "conserves": len(fichiers_originaux & fichiers_cibles),
    }