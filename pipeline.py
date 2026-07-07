# pipeline.py
"""
Pipeline principal d'analyse et de génération de documentation.

Orchestre l'ensemble du processus : scan → détection → analyse → documentation → publication.
"""

import logging
import subprocess
import os
import shutil
from typing import Dict, Optional

from generation.ecrivain import ecrire_documentation_complete, nettoyer_nom_repo
from generation.mkdocs_generator import generer_mkdocs_yml
from scanners.scanner import analyser_repo
from architecture.detecteur import detecter_architecture
from architecture.ollama_detecteur import detecter_avec_ollama
from generation.analyzer import analyser_projet_memoire
from generation.doc_generator import generer_doc_tous_fichiers
from generation.project_doc import generer_doc_globale, generer_doc_architecture
from generation.readme_generator import generer_readme
from publisher.strategie import publier_avec_strategie

from architecture.api_route_detector import detecter_routes
from architecture.openapi_generator import generer_spec_openapi
from generation.swagger_page_generator import generer_page_swagger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DEPUIS .ENV
# ═══════════════════════════════════════════════════════════════════════════════

DOSSIER_SORTIE_DEFAUT = os.getenv("PIPELINE_DOSSIER_SORTIE", "output")
PLATEFORME_DEFAUT = os.getenv("PIPELINE_PLATEFORME_DEFAUT", "github")
STRATEGIE_DEFAUT = os.getenv("PIPELINE_STRATEGIE_DEFAUT", "branche")
BRANCHE_DEFAUT = os.getenv("PIPELINE_BRANCHE_DEFAUT", "docs/auto-generated")
MKDOCS_BUILD_TIMEOUT = int(os.getenv("PIPELINE_MKDOCS_BUILD_TIMEOUT", "120"))
DEBUG_PIPELINE = os.getenv("DEBUG_PIPELINE", "false").lower() == "true"


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def _adapter_fichiers_pour_detection(sources_ast) -> Dict:
    """Adapte le format des sources AST pour la détection de routes API."""
    if isinstance(sources_ast, dict):
        return sources_ast
    
    if isinstance(sources_ast, list):
        return {
            item["path"]: item["content"]
            for item in sources_ast
            if isinstance(item, dict) and "path" in item and "content" in item
        }
    
    logger.warning("Format de sources_ast non reconnu pour la détection API.")
    return {}


def _build_tree_from_files(fichiers: list) -> dict:
    """
    Construit un arbre simple à partir d'une liste de chemins de fichiers.
    
    Args:
        fichiers: Liste de chemins comme ["app.py", "models/user.py", ...]
        
    Returns:
        Arbre au format {name, type, children}
    """
    arbre = {
        "name": "Projet",
        "type": "directory",
        "children": []
    }
    
    for chemin in fichiers:
        parties = chemin.replace("\\", "/").split("/")
        _inserer_dans_arbre(arbre, parties)
    
    return arbre


def _inserer_dans_arbre(noeud: dict, parties: list) -> None:
    """Insère un chemin dans l'arbre (récursif)."""
    if not parties:
        return
    
    nom = parties[0]
    reste = parties[1:]
    
    # Chercher si le noeud existe déjà
    enfant = next((e for e in noeud.get("children", []) if e["name"] == nom), None)
    
    if enfant is None:
        enfant = {
            "name": nom,
            "type": "file" if not reste else "directory",
            "children": [] if reste else None
        }
        noeud.setdefault("children", []).append(enfant)
    
    if reste:
        _inserer_dans_arbre(enfant, reste)


def _adapter_infos_ast_pour_architecture_cible(infos_ast: dict, 
                                                arbre_cible: dict) -> dict:
    """
    Ré-indexe les infos AST selon les chemins de l'architecture cible.
    
    Args:
        infos_ast: Dictionnaire {chemin_original: infos}
        arbre_cible: Arbre restructuré cible
        
    Returns:
        Dictionnaire {chemin_cible: infos}
    """
    from architecture.restructeur import _collecter_fichiers
    
    # Collecter tous les fichiers de l'arbre cible
    fichiers_cibles = _collecter_fichiers(arbre_cible)
    
    # Créer un index par nom de fichier original
    index_par_nom = {}
    for chemin_original, infos in infos_ast.items():
        nom_fichier = chemin_original.split("/")[-1]
        if nom_fichier not in index_par_nom:
            index_par_nom[nom_fichier] = []
        index_par_nom[nom_fichier].append((chemin_original, infos))
    
    # Ré-indexer selon les chemins cibles
    infos_cibles = {}
    for fichier_cible in fichiers_cibles:
        nom = fichier_cible["nom"]
        chemin_cible = "/".join(fichier_cible["dossier_parts"] + [nom])
        
        if nom in index_par_nom:
            # Prendre la première correspondance
            _, infos = index_par_nom[nom][0]
            infos_cibles[chemin_cible] = infos
    
    logger.info(f"Infos AST ré-indexées : {len(infos_cibles)} fichiers cibles")
    return infos_cibles


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def pipeline_complet(
    url_repo: str,
    dossier_sortie: str = None,
    publier: bool = False,
    token: str = None,
    plateforme: str = None,
    strategie_publication: str = None,
    nom_branche: str = None,
    prive: bool = False
) -> Dict:
    """Pipeline complet d'analyse et de génération de documentation."""
    
    # Valeurs par défaut
    if dossier_sortie is None:
        dossier_sortie = DOSSIER_SORTIE_DEFAUT
    if plateforme is None:
        plateforme = PLATEFORME_DEFAUT
    if strategie_publication is None:
        strategie_publication = STRATEGIE_DEFAUT
    if nom_branche is None:
        nom_branche = BRANCHE_DEFAUT

    # ═══════════ ÉTAPE 1 : SCAN ═══════════
    print("🔍 1. Scan du repository...")
    data_scanner = analyser_repo(url_repo)
    print(f"   → {len(data_scanner['fichiers'])} fichiers trouvés")
    print(f"   → {len(data_scanner['sources_ast'])} fichiers sources téléchargés")

    # ═══════════ ÉTAPE 2 : DÉTECTION D'ARCHITECTURE ═══════════
    print("\n🏛️ 2. Détection d'architecture...")
    resultat_scoring = detecter_architecture(data_scanner)
    resultat_archi = detecter_avec_ollama(data_scanner, resultat_scoring)
    print(f"   → Architecture : {resultat_archi['architecture']} "
          f"(confiance : {resultat_archi['confiance']})")

    # ═══════════ ÉTAPE 3 : ANALYSE AST ═══════════
    print("\n🔬 3. Analyse du code (tree-sitter)...")
    infos_ast = analyser_projet_memoire(data_scanner["sources_ast"])
    print(f"   → {len(infos_ast)} fichiers analysés")

    # ═══════════ ÉTAPE 3bis : RÉ-INDEXATION POUR ARCHITECTURE CIBLE ═══════════
    print("\n🎯 3bis. Adaptation à l'architecture cible...")
    from architecture.restructeur import construire_arbre_cible
    
    # Construire l'arbre original à partir de la liste de fichiers
    arbre_original = _build_tree_from_files(data_scanner["fichiers"])
    
    # Construire l'arbre cible
    arbre_cible = construire_arbre_cible(arbre_original, resultat_archi["architecture"])
    
    # Ré-indexer les infos AST selon l'arbre cible
    infos_ast_cibles = _adapter_infos_ast_pour_architecture_cible(infos_ast, arbre_cible)
    print(f"   → {len(infos_ast_cibles)} fichiers dans l'architecture cible")

    # ═══════════ ÉTAPE 4 : GÉNÉRATION DOCUMENTATION ═══════════
    print("\n📝 4. Génération de la documentation...")
    docs_fichiers = generer_doc_tous_fichiers(infos_ast_cibles, resultat_archi["architecture"])
    doc_globale = generer_doc_globale(data_scanner, resultat_archi, infos_ast_cibles)
    doc_architecture = generer_doc_architecture(resultat_archi)
    readme = generer_readme(data_scanner, resultat_archi)
    print(f"   → {len(docs_fichiers)} fichiers documentés")

    # ═══════════ ÉTAPE 5 : ÉCRITURE DISQUE ═══════════
    print("\n💾 5. Écriture des fichiers sur disque...")
    nom_propre = nettoyer_nom_repo(data_scanner["repo_name"])
    racine_doc = ecrire_documentation_complete(
        repo_name=data_scanner["repo_name"],
        dossier_sortie=dossier_sortie,
        readme=readme,
        doc_globale=doc_globale,
        doc_architecture=doc_architecture,
        docs_fichiers=docs_fichiers
    )
    print(f"   → Racine documentation : {racine_doc}")

    # ═══════════ ÉTAPE 5bis : DÉTECTION API ═══════════
    print("\n🔌 5bis. Détection de l'API REST...")
    nav_extra = None
    fichiers_pour_detection = _adapter_fichiers_pour_detection(data_scanner["sources_ast"])
    routes_api = detecter_routes(fichiers_pour_detection)

    if routes_api:
        spec_openapi = generer_spec_openapi(routes_api, nom_projet=nom_propre)
        docs_dir = os.path.join(racine_doc, "docs")
        resultat_swagger = generer_page_swagger(
            spec_openapi, docs_dir=docs_dir, nom_projet=nom_propre
        )
        if resultat_swagger:
            nav_extra = [{"API REST": "api.md"}]
            print(f"   → {len(routes_api)} route(s) API détectée(s)")
    else:
        print("   → Aucune route API détectée")

    # ═══════════ ÉTAPE 6 : MKDOCS ═══════════
    print("\n📚 6. Génération de la configuration MkDocs...")
    chemin_mkdocs = generer_mkdocs_yml(
        nom_propre=nom_propre,
        docs_fichiers=docs_fichiers,
        dossier_sortie=dossier_sortie,
        nav_extra=nav_extra
    )
    print(f"   → mkdocs.yml généré : {chemin_mkdocs}")

    # ═══════════ ÉTAPE 6bis : BUILD HTML (AVEC NETTOYAGE) ═══════════
    print("\n🏗️ 6bis. Build du site HTML MkDocs...")
    chemin_site_html = None

    # ✅ SUPPRIMER L'ANCIEN BUILD POUR ÉVITER LE CACHE
    site_dir = os.path.join(racine_doc, "site")
    if os.path.isdir(site_dir):
        shutil.rmtree(site_dir)
        print(f"   → Ancien build supprimé : {site_dir}")

    try:
        result = subprocess.run(
            ["mkdocs", "build", "--clean"],
            cwd=racine_doc,
            check=True,
            capture_output=True,
            text=True,
            timeout=MKDOCS_BUILD_TIMEOUT
        )
        chemin_site_html = os.path.join(racine_doc, "site")
        print(f"   → Site HTML généré : {chemin_site_html}")
        
        if DEBUG_PIPELINE:
            # Vérifier qu'il n'y a pas d'index.html imbriqués (mode dossier)
            index_files = []
            for root, dirs, files in os.walk(chemin_site_html):
                if 'index.html' in files and root != chemin_site_html:
                    index_files.append(os.path.join(root, 'index.html'))
            if index_files:
                logger.warning(f"Fichiers index.html imbriqués détectés : {index_files}")
            else:
                logger.info("✅ Aucun index.html imbriqué - build propre")
                
    except FileNotFoundError:
        logger.error("MkDocs n'est pas installé. Exécutez: pip install mkdocs mkdocs-material")
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout build MkDocs (>{MKDOCS_BUILD_TIMEOUT}s)")
    except subprocess.CalledProcessError as e:
        logger.error(f"Échec build MkDocs: {e.stderr}")
        if DEBUG_PIPELINE:
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")

    print(f"\n✅ Documentation générée dans : {racine_doc}")

    # ═══════════ RÉSULTAT ═══════════
    resultat = {
        "data_scanner": data_scanner,
        "resultat_archi": resultat_archi,
        "infos_ast": infos_ast,
        "infos_ast_cibles": infos_ast_cibles,
        "arbre_cible": arbre_cible,
        "docs_fichiers": docs_fichiers,
        "doc_globale": doc_globale,
        "doc_architecture": doc_architecture,
        "readme": readme,
        "racine_doc": racine_doc,
        "chemin_doc": racine_doc,
        "chemin_mkdocs": chemin_mkdocs,
        "chemin_site_html": chemin_site_html,
        "routes_api": routes_api,
        "resultat_publication": None,
    }

    # ═══════════ ÉTAPE 7 : PUBLICATION (OPTIONNEL) ═══════════
    if publier:
        if not token:
            raise ValueError("Un token est requis pour publier la documentation.")

        print("\n🚀 7. Publication sur le dépôt Git...")
        chemin_readme = os.path.join(racine_doc, "README.md")

        resultat_publication = publier_avec_strategie(
            strategie=strategie_publication,
            url_repo=url_repo,
            token=token,
            plateforme=plateforme,
            dossier_docs_generes=os.path.join(racine_doc, "docs"),
            nom_projet=nom_propre,
            mkdocs_yml_path=chemin_mkdocs,
            readme_genere_path=chemin_readme,
            nom_branche=nom_branche,
            prive=prive,
            restructuration={
                "fichiers": data_scanner["fichiers"],
                "infos_ast": infos_ast,
                "architecture": resultat_archi["architecture"],
            },
        )

        resultat["resultat_publication"] = resultat_publication

        if resultat_publication.get("strategie") == "branche":
            print(f"   → Branche poussée : {resultat_publication['branche']}")
            print(f"   → PR suggérée : {resultat_publication['url_pull_request_suggeree']}")
        else:
            print(f"   → Nouveau dépôt créé : {resultat_publication['url_nouveau_depot']}")

    return resultat