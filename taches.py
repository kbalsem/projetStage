# taches.py
import logging
import json

from models import db, Historique
from pipeline import pipeline_complet
from architecture.classifieur_fichiers import deviner_role
from utils.tree_utils import aplatir_arbre, trier_arbre

logger = logging.getLogger(__name__)


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


def executer_analyse(app, historique_id: int, url: str):
    """Exécute le pipeline complet en arrière-plan et met à jour la BDD."""
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