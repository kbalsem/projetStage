import logging
import json

from models import db, Historique
from pipeline import pipeline_complet

logger = logging.getLogger(__name__)


def extraire_resume(readme: str, longueur_max: int = 500) -> str:
    """
    Extrait un résumé court à partir du README généré : on prend les premiers
    paragraphes non vides après le titre, tronqués à longueur_max caractères.
    """
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


def executer_analyse(app, historique_id: int, url: str):
    with app.app_context():
        historique = db.session.get(Historique, historique_id)
        if not historique:
            logger.error(f"Historique {historique_id} introuvable au lancement du thread")
            return

        try:
            resultat = pipeline_complet(url)

            data_scanner     = resultat["data_scanner"]
            resultat_archi    = resultat["resultat_archi"]
            doc_architecture  = resultat["doc_architecture"]
            doc_globale       = resultat["doc_globale"]
            readme            = resultat["readme"]
            chemin_doc        = resultat["chemin_doc"]

            historique.repo_name              = data_scanner.get("repo_name", "Inconnu")
            historique.author                 = data_scanner.get("author", "Inconnu")
            historique.branch                 = data_scanner.get("branch", "Inconnue")
            historique.commits                = data_scanner.get("commits", 0)
            historique.stars                  = data_scanner.get("stars", 0)
            historique.description            = data_scanner.get("description", "")
            historique.licence                = data_scanner.get("licence", "Non spécifiée")
            historique.fichiers_count         = len(data_scanner.get("fichiers", []))
            historique.langages               = json.dumps(data_scanner.get("langages", []))
            historique.architecture           = doc_architecture
            historique.confiance_architecture = resultat_archi.get("confiance")
            historique.resume_ia              = extraire_resume(readme)
            historique.documentation_preview  = doc_globale
            historique.chemin_doc             = chemin_doc
            historique.statut                 = "termine"

            db.session.commit()
            logger.info(f"Analyse terminée pour historique {historique_id} : {historique.repo_name}")

        except Exception as e:
            logger.exception(f"Erreur pipeline pour historique {historique_id}")
            historique.statut         = "erreur"
            historique.message_erreur = str(e)
            db.session.commit()