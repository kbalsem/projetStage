# utils/ollama_client.py
import requests
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434") + "/api/generate"
MODEL = os.getenv("MODEL", "llama3")


def generer(prompt: str, max_tokens: int = 500, temperature: float = 0.2,
            timeout: int = 120, max_retries: int = 2, nettoyer: bool = True) -> str:
    """
    Client Ollama unifié pour tous les modules du projet.
    
    Args:
        prompt: Le prompt à envoyer
        max_tokens: Nombre max de tokens en réponse
        temperature: Créativité (0.0 = déterministe, 1.0 = créatif)
        timeout: Timeout HTTP en secondes
        max_retries: Nombre de tentatives en cas d'échec
        nettoyer: Si True, nettoie les artefacts Markdown parasites
    
    Returns:
        Texte généré par Ollama, nettoyé
    """
    payload = {
        "model": MODEL,
        "prompt": prompt[:3000],
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        }
    }

    derniere_erreur = None

    for tentative in range(max_retries + 1):
        try:
            reponse = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
            reponse.raise_for_status()
            texte = reponse.json().get("response", "").strip()

            if not texte:
                logger.warning("Ollama a retourné une réponse vide")
                if tentative < max_retries:
                    continue
                return "[Erreur : Réponse vide d'Ollama]"

            if nettoyer:
                texte = _nettoyer_reponse(texte)

            return texte

        except requests.exceptions.ConnectionError:
            derniere_erreur = "Ollama non disponible (connexion refusée)"
            logger.error(derniere_erreur)

        except requests.exceptions.Timeout:
            derniere_erreur = f"Timeout Ollama après {timeout}s"
            logger.error(derniere_erreur)

        except requests.exceptions.HTTPError as e:
            derniere_erreur = f"Erreur HTTP Ollama : {e}"
            logger.error(derniere_erreur)

    return f"[Erreur : {derniere_erreur}]"


def _nettoyer_reponse(texte: str) -> str:
    """Nettoie les artefacts parasites dans la réponse d'Ollama."""
    phrases_intro = [
        "here is", "voici", "i hope", "j'espère",
        "this meets", "cela répond", "```markdown"
    ]

    lignes = texte.strip().split("\n")

    # Supprimer les lignes d'intro
    while lignes and any(p in lignes[0].lower() for p in phrases_intro):
        lignes.pop(0)

    # Supprimer les lignes d'outro
    while lignes and any(p in lignes[-1].lower() for p in phrases_intro):
        lignes.pop()

    resultat = "\n".join(lignes).strip()

    # Supprimer les blocs de code Markdown englobants
    if resultat.startswith("```"):
        resultat = resultat.split("\n", 1)[-1] if "\n" in resultat else ""
    if resultat.endswith("```"):
        resultat = resultat.rsplit("```", 1)[0]

    return resultat.strip()