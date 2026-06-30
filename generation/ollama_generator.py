import requests
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL      = "llama3"


def generer(prompt: str, max_tokens: int = 800) -> str:
    """
    Envoie un prompt à Ollama et retourne le texte généré, nettoyé.
    """
    payload = {
        "model"  : MODEL,
        "prompt" : prompt[:3000],
        "stream" : False,
        "options": {
            "temperature": 0.2,
            "num_predict": max_tokens
        }
    }

    try:
        reponse = requests.post(OLLAMA_URL, json=payload, timeout=180)
        reponse.raise_for_status()
        texte_brut = reponse.json().get("response", "").strip()
        return nettoyer_reponse_markdown(texte_brut)

    except requests.exceptions.ConnectionError:
        logger.error("Ollama non disponible")
        return "[Erreur : Ollama non disponible]"
    except Exception as e:
        logger.error(f"Erreur Ollama : {e}")
        return f"[Erreur : {e}]"



def nettoyer_reponse_markdown(texte: str) -> str:
    """
    Retire les phrases parasites qu'Ollama ajoute parfois avant/après
    le Markdown demandé, malgré l'instruction de ne générer que ça.
    """
    lignes = texte.strip().split("\n")

    # Phrases d'intro typiques à retirer en début de réponse
    phrases_intro = [
        "here is", "voici", "i hope", "j'espère",
        "this meets", "cela répond", "```markdown", "```"
    ]

    # Retirer les lignes d'intro/outro en début et fin
    while lignes and any(p in lignes[0].lower() for p in phrases_intro):
        lignes.pop(0)
    while lignes and any(p in lignes[-1].lower() for p in phrases_intro):
        lignes.pop()

    # Retirer les balises de bloc de code Markdown si tout le texte en est entouré
    resultat = "\n".join(lignes).strip()
    if resultat.startswith("```"):
        resultat = resultat.split("\n", 1)[-1]
    if resultat.endswith("```"):
        resultat = resultat.rsplit("```", 1)[0]

    return resultat.strip()