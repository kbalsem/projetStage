# summarize_repo.py
import logging
from utils.ollama_client import generer
from scanners.scanner import extraire_extensions

logger = logging.getLogger(__name__)


def resumer_repo(data: dict) -> str:
    """
    Prend les données du scanner et génère un résumé IA via Ollama.
    Retourne un texte de résumé en français (3 phrases max).
    """
    repo_name = data.get("repo_name", "Inconnu")
    author = data.get("author", "Inconnu")
    branch = data.get("branch", "main")
    commits = data.get("commits", 0)
    stars = data.get("stars", 0)
    licence = data.get("licence", "Non spécifiée")
    description = data.get("description", "")
    fichiers = data.get("fichiers", [])

    extensions = extraire_extensions(fichiers)

    prompt = f"""Tu es un assistant technique. Analyse ce dépôt Git et génère un résumé TRÈS COURT en français.

Informations du dépôt :
- Nom : {repo_name}
- Auteur : {author}
- Branche principale : {branch}
- Nombre de commits : {commits}
- Stars : {stars}
- Licence : {licence}
- Description : {description if description else "Non fournie"}
- Nombre de fichiers : {len(fichiers)}
- Technologies détectées : {", ".join(extensions) if extensions else "Non détectées"}
- Exemples de fichiers : {", ".join(fichiers[:10])}

Génère un résumé en EXACTEMENT 3 phrases maximum, en français :
1ère phrase : ce qu'est le projet.
2ème phrase : les technologies utilisées.
3ème phrase : un point notable sur la structure ou l'état du projet.

IMPORTANT : pas de liste à puces, pas de titres, pas de retour à la ligne. Juste un seul paragraphe de 3 phrases maximum, direct et concis."""

    logger.info(f"Envoi du prompt à Ollama pour : {repo_name}")

    resume = generer(
        prompt=prompt,
        max_tokens=200,
        temperature=0.3,
        timeout=120,
        max_retries=1,
        nettoyer=True
    )

    if resume.startswith("[Erreur"):
        raise Exception(resume)

    logger.info(f"Résumé généré avec succès pour : {repo_name}")
    return resume