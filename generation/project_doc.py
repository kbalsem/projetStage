import logging
from .prompts          import PROMPT_GLOBAL
from .ollama_generator import generer

logger = logging.getLogger(__name__)

def generer_doc_globale(data_scanner, resultat_archi, infos_ast) -> str:

    fichiers_tries = sorted(
        infos_ast.items(),
        key=lambda x: len(x[1].get("classes", [])),
        reverse=True
    )
    fichiers_principaux = [f[0] for f in fichiers_tries[:5]]  # ← 5 au lieu de 10

    prompt = PROMPT_GLOBAL.format(
        repo_name           = data_scanner.get("repo_name", "Inconnu"),
        architecture        = resultat_archi.get("architecture", "Inconnue"),
        frameworks          = ", ".join(resultat_archi.get("frameworks", [])[:5]),
        nb_fichiers         = len(data_scanner.get("fichiers", [])),
        fichiers_principaux = "\n".join(f"- {f}" for f in fichiers_principaux)
    )

    logger.info("Génération documentation globale...")
    return generer(prompt, max_tokens=800)  # ← 800 au lieu de 1000

def generer_doc_architecture(resultat_archi: dict) -> str:
    """
    Génère une page dédiée à l'architecture détectée.
    """
    architecture  = resultat_archi.get("architecture", "Inconnue")
    confiance     = resultat_archi.get("confiance", "inconnue")
    justification = resultat_archi.get("justification") or "Détection automatique par scoring, sans confirmation IA disponible."
    elements      = resultat_archi.get("elements_cles", [])
    scores        = resultat_archi.get("scores", {})

    avertissement = ""
    if confiance == "faible":
        avertissement = "\n> ⚠️ Confiance faible — une vérification manuelle de l'architecture est recommandée.\n"

    contenu = f"""# Architecture du projet

## Type détecté : {architecture}

**Niveau de confiance : {confiance}**
{avertissement}
{justification}

## Éléments clés identifiés
{chr(10).join(f'- {el}' for el in elements) if elements else '- Détection automatique par scoring'}

## Scores de détection
"""
    for arch, score in scores.items():
        score_arrondi = max(0, min(10, round(score)))
        barre         = "█" * score_arrondi + "░" * (10 - score_arrondi)
        contenu      += f"- {arch:<15} {barre} ({score:.2f} pts)\n"

    return contenu