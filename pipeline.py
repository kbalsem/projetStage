# pipeline.py
"""
Pipeline principal d'analyse et de génération de documentation.

Fichier UNIQUE qui gère absolument tout ce qui concerne l'analyse d'un
dépôt : orchestration du pipeline (scan -> détection -> AST -> doc ->
mkdocs -> publication) ET l'exécution en arrière-plan qui met à jour la
base de données (fusion de l'ancien pipeline.py + taches.py).

Ce fichier n'importe jamais app.py. C'est app.py qui l'importe. Le sens
de dépendance est donc à sens unique : app.py -> pipeline.py.
"""

import logging
import subprocess
import os
import shutil
import json
from typing import Dict, List, Tuple, Optional

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

from architecture.classifieur_fichiers import deviner_role
from utils.tree_utils import aplatir_arbre, trier_arbre
from architecture.signaux import SIGNAUX
from models import db, Historique

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

SCORE_MAX = int(os.getenv("SCORE_MAX", "210"))
SCORE_MULTIPLICATEUR_CONFIANCE = int(os.getenv("SCORE_MULTIPLICATEUR_CONFIANCE", "2"))
SEUIL_CONFLIT_CONFIANCE = int(os.getenv("SEUIL_CONFLIT_CONFIANCE", "80"))
PENALITE_CONFLIT_POINTS = int(os.getenv("PENALITE_CONFLIT_POINTS", "10"))

ARCHITECTURES_DESCRIPTIONS = {
    "MVC": "Le pattern Model-View-Controller sépare l'application en trois composants : le Modèle (données), la Vue (interface) et le Contrôleur (logique).",
    "MVVM": "Model-View-ViewModel facilite la liaison de données entre la vue et le modèle via un ViewModel.",
    "Clean Architecture": "Architecture en couches concentriques avec dépendances vers l'intérieur.",
    "Hexagonale": "Architecture Ports & Adapters qui isole le cœur applicatif derrière des interfaces.",
    "Microservices": "Architecture distribuée où chaque service est indépendant et communique via API.",
    "Layered": "Architecture en couches classique (présentation, business, données).",
    "MVP": "Model-View-Presenter — le Presenter gère toute la logique de l'interface utilisateur.",
    "COUCHES": "Architecture en couches — Présentation / Métier / Données.",
    "CLEAN": "Clean Architecture — Use Cases / Entities / Repositories.",
    "MONOLITHIQUE": "Application monolithique — structure simple sans séparation claire en modules distincts.",
}


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES — CONSTRUCTION D'ARBRES
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
    """Construit un arbre simple à partir d'une liste de chemins de fichiers."""
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
    """Ré-indexe les infos AST selon les chemins de l'architecture cible."""
    from architecture.restructeur import _collecter_fichiers

    fichiers_cibles = _collecter_fichiers(arbre_cible)

    index_par_nom = {}
    for chemin_original, infos in infos_ast.items():
        nom_fichier = chemin_original.split("/")[-1]
        if nom_fichier not in index_par_nom:
            index_par_nom[nom_fichier] = []
        index_par_nom[nom_fichier].append((chemin_original, infos))

    infos_cibles = {}
    for fichier_cible in fichiers_cibles:
        nom = fichier_cible["nom"]
        chemin_cible = "/".join(fichier_cible["dossier_parts"] + [nom])

        if nom in index_par_nom:
            _, infos = index_par_nom[nom][0]
            infos_cibles[chemin_cible] = infos

    logger.info(f"Infos AST ré-indexées : {len(infos_cibles)} fichiers cibles")
    return infos_cibles


def lister_fichiers_depuis_arbre(arbre: dict) -> list:
    """Aplatie un tree_json en liste de chemins (rétrocompatibilité)."""
    return aplatir_arbre(arbre, inclure_racine=False)


def extraire_resume(readme: str, longueur_max: int = 500) -> str:
    """Extrait un résumé court du README généré."""
    if not readme:
        return ""

    lignes = [l.strip() for l in readme.splitlines()]
    paragraphes = []
    for ligne in lignes:
        if ligne.startswith("#"):
            continue
        if ligne:
            paragraphes.append(ligne)
        if sum(len(p) for p in paragraphes) >= longueur_max:
            break

    resume = " ".join(paragraphes)
    return resume[:longueur_max].rstrip() + ("…" if len(resume) > longueur_max else "")


def construire_tree_json(data_scanner: dict, infos_ast: dict = None) -> dict:
    """Construit l'arborescence JSON complète avec rôles des fichiers."""
    fichiers = data_scanner.get("fichiers", [])
    repo_name = data_scanner.get("repo_name", "projet")
    infos_ast = infos_ast or {}

    def ajouter_chemin(arbre, chemin_parts, chemin_complet):
        if not chemin_parts:
            return
        nom = chemin_parts[0]
        reste = chemin_parts[1:]

        enfant = next((e for e in arbre.get("children", []) if e["name"] == nom), None)

        if enfant is None:
            if len(reste) == 0:
                role = deviner_role(chemin_complet, infos_ast.get(chemin_complet))
                enfant = {"name": nom, "type": "file", "role": role, "children": []}
            else:
                enfant = {"name": nom, "type": "directory", "children": []}
            arbre.setdefault("children", []).append(enfant)

        if reste:
            ajouter_chemin(enfant, reste, chemin_complet)

    arbre = {"name": repo_name, "type": "directory", "children": []}

    for fichier in fichiers:
        chemin = fichier.replace("\\", "/")
        ajouter_chemin(arbre, chemin.split("/"), chemin)

    trier_arbre(arbre)
    logger.info(f"Tree JSON construit : {len(fichiers)} fichiers")
    return arbre


# ═══════════════════════════════════════════════════════════════════════════════
# INTERPRÉTATION DES RÉSULTATS (score, radar, conflits) — anciennement dans app.py
# ═══════════════════════════════════════════════════════════════════════════════

def extraire_pourcentage_confiance(confiance_str: Optional[str]) -> int:
    if not confiance_str: return 0
    try:
        if '%' in confiance_str: return int(confiance_str.split('%')[0].split()[-1])
        else: return int(confiance_str.split()[-1])
    except (ValueError, IndexError): return 0

def calculer_radar_data(architecture_detectee: str, confiance_pct: int) -> Dict[str, int]:
    radar_data = {}
    for archi_key in SIGNAUX.keys():
        radar_data[archi_key] = confiance_pct if archi_key == architecture_detectee else 0
    return radar_data

def calculer_score_global(confiance_pct: int, nb_signaux: int, nb_conflits: int) -> int:
    score = confiance_pct * SCORE_MULTIPLICATEUR_CONFIANCE - nb_conflits * PENALITE_CONFLIT_POINTS
    return min(SCORE_MAX, max(0, score))

def get_description_architecture(architecture: Optional[str]) -> str:
    if not architecture: return "Architecture non détectée."
    for archi_key, desc in ARCHITECTURES_DESCRIPTIONS.items():
        if archi_key.lower() in architecture.lower(): return desc
    return f"Architecture '{architecture}' détectée."

def calculer_stats_transformation(mappings: List[dict]) -> Dict[str, int]:
    stats = {"nouveaux_dossiers": 0, "fichiers_deplaces": 0, "fichiers_inchanges": 0, "fichiers_supprimes": 0}
    for m in mappings:
        if m.get("type") == "directory" and m["status"] == "new": stats["nouveaux_dossiers"] += 1
        elif m["status"] == "moved": stats["fichiers_deplaces"] += 1
        elif m["status"] == "unchanged": stats["fichiers_inchanges"] += 1
        elif m["status"] == "deleted": stats["fichiers_supprimes"] += 1
    return stats

def detecter_conflits(radar_data: Dict[str, int], confiance_pct: int) -> Tuple[int, str]:
    conflits, message = 0, ""
    if confiance_pct < SEUIL_CONFLIT_CONFIANCE:
        conflits += 1; message = f"Confiance faible ({confiance_pct}%)"
    scores_eleves = [s for s in radar_data.values() if s > 60]
    if len(scores_eleves) > 1:
        conflits += 1; message = (message + " | " if message else "") + "Plusieurs architectures possibles"
    if conflits > 0: message = "⚠️ " + message
    return conflits, message

def get_architecture_fallback() -> str:
    architectures = list(SIGNAUX.keys())
    return architectures[0] if architectures else "MVC"


# ═══════════════════════════════════════════════════════════════════════════════
# NAVIGATION DE LA DOC GÉNÉRÉE (mkdocs) — anciennement dans app.py
# ═══════════════════════════════════════════════════════════════════════════════

def convertir_nav_mkdocs(nav, base=''):
    resultat = []
    for item in nav:
        if isinstance(item, dict):
            for label, valeur in item.items():
                if isinstance(valeur, str): resultat.append({"label": label, "url": valeur.replace('.md', '.html'), "enfants": []})
                elif isinstance(valeur, list): resultat.append({"label": label, "url": None, "enfants": convertir_nav_mkdocs(valeur)})
        elif isinstance(item, str): resultat.append({"label": item, "url": item, "enfants": []})
    return resultat

def scanner_dossier_site_complet(chemin_site):
    arbre = []
    try:
        for entree in sorted(os.listdir(chemin_site)):
            chemin_complet = os.path.join(chemin_site, entree)
            if entree.startswith('.') or entree in ('assets', 'search', 'stylesheets', 'javascripts', 'fonts', 'img'): continue
            if os.path.isdir(chemin_complet):
                enfants = scanner_dossier_site_complet(chemin_complet)
                if enfants: arbre.append({"label": entree.replace('_', ' ').title(), "url": None, "enfants": enfants})
            elif entree.endswith('.html'):
                label = entree.replace('.html', '').replace('_', ' ').title()
                if entree == 'index.html': label = 'Accueil'
                chemin_relatif = os.path.relpath(chemin_complet, chemin_site).replace('\\', '/')
                arbre.append({"label": label, "url": chemin_relatif, "enfants": []})
    except Exception as e: logger.error(f"Erreur scan: {e}")
    return arbre


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL (analyse + génération de doc)
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

    arbre_original = _build_tree_from_files(data_scanner["fichiers"])
    arbre_cible = construire_arbre_cible(arbre_original, resultat_archi["architecture"])
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

    # ═══════════ ÉTAPE 6bis : BUILD HTML ═══════════
    print("\n🏗️ 6bis. Build du site HTML MkDocs...")
    chemin_site_html = None

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


# ═══════════════════════════════════════════════════════════════════════════════
# EXÉCUTION EN ARRIÈRE-PLAN (anciennement taches.py, fusionné ici)
# ═══════════════════════════════════════════════════════════════════════════════

def executer_analyse(app, historique_id: int, url: str):
    """
    Exécute le pipeline complet en arrière-plan et met à jour la BDD.

    `app` est l'objet Flask, passé par app.py au moment de lancer le
    thread (ce fichier n'importe jamais app.py).
    """
    with app.app_context():
        historique = db.session.get(Historique, historique_id)
        if not historique:
            return

        try:
            resultat = pipeline_complet(url)

            data_scanner = resultat["data_scanner"]
            resultat_archi = resultat["resultat_archi"]
            doc_globale = resultat["doc_globale"]
            readme = resultat["readme"]
            chemin_doc = resultat["chemin_doc"]
            infos_ast = resultat["infos_ast"]
            chemin_site_html = resultat.get("chemin_site_html")

            tree_json = construire_tree_json(data_scanner, infos_ast)

            historique.repo_name = data_scanner.get("repo_name", "Inconnu")
            historique.author = data_scanner.get("author", "Inconnu")
            historique.branch = data_scanner.get("branch", "Inconnue")
            historique.commits = data_scanner.get("commits", 0)
            historique.stars = data_scanner.get("stars", 0)
            historique.description = data_scanner.get("description", "")
            historique.licence = data_scanner.get("licence", "Non spécifiée")
            historique.fichiers_count = len(data_scanner.get("fichiers", []))
            historique.langages = json.dumps(data_scanner.get("langages", []))
            historique.architecture = resultat_archi.get("architecture")
            historique.confiance_architecture = resultat_archi.get("confiance")
            historique.resume_ia = extraire_resume(readme)
            historique.documentation_preview = doc_globale
            historique.chemin_doc = chemin_doc
            historique.tree_json = json.dumps(tree_json)
            historique.chemin_site_html = chemin_site_html
            historique.statut = "termine"

            db.session.commit()
            logger.info(f"Analyse terminée : {historique.repo_name}")

        except Exception as e:
            logger.exception(f"Erreur pipeline pour historique {historique_id}")
            historique.statut = "erreur"
            historique.message_erreur = str(e)
            db.session.commit()