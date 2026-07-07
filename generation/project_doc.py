# generation/project_doc.py
import logging
from .prompts import PROMPT_GLOBAL
from utils.ollama_client import generer

logger = logging.getLogger(__name__)


def generer_doc_globale(data_scanner, resultat_archi, infos_ast) -> str:
    fichiers_tries = sorted(
        infos_ast.items(),
        key=lambda x: len(x[1].get("classes", [])),
        reverse=True
    )
    fichiers_principaux = [f[0] for f in fichiers_tries[:5]]

    signaux = resultat_archi.get("signaux_detectes", {})
    couverture = resultat_archi.get("couverture", {})

    prompt = PROMPT_GLOBAL.format(
        repo_name=data_scanner.get("repo_name", "Inconnu"),
        architecture=resultat_archi.get("architecture", "Inconnue"),
        frameworks=", ".join(resultat_archi.get("frameworks", [])[:5]),
        nb_fichiers=len(data_scanner.get("fichiers", [])),
        fichiers_principaux="\n".join(f"- {f}" for f in fichiers_principaux)
    )

    logger.info("Génération documentation globale...")
    return generer(prompt, max_tokens=1000)


def generer_doc_architecture(resultat_archi: dict) -> str:
    architecture = resultat_archi.get("architecture", "Inconnue")
    confiance = resultat_archi.get("confiance", "inconnue")
    justification = resultat_archi.get("justification") or "Détection automatique par scoring."
    elements = resultat_archi.get("elements_cles", [])
    scores = resultat_archi.get("scores", {})
    details = resultat_archi.get("details", {})
    couverture = resultat_archi.get("couverture", {})
    signaux_detectes = resultat_archi.get("signaux_detectes", {})

    avertissement = ""
    if confiance in ("faible", "suggérée"):
        avertissement = "\n> ⚠️ Confiance faible — vérification manuelle recommandée.\n"

    contenu = f"""# Architecture du projet

## Type détecté : {architecture}

**Niveau de confiance : {confiance}**
{avertissement}
{justification}

## Éléments clés identifiés
{chr(10).join(f'- {el}' for el in elements) if elements else '- Détection automatique par scoring'}

## Signaux détectés
"""

    for cat, sigs in signaux_detectes.items():
        if sigs:
            contenu += f"- **{cat}** : {len(sigs)} signal(aux)\n"

    if details.get("regles"):
        contenu += "\n## Règles activées\n"
        for r in details["regles"]:
            contenu += f"- {r}\n"

    if details.get("anti_signaux"):
        contenu += "\n## Anti-signaux détectés\n"
        for a in details["anti_signaux"]:
            contenu += f"- {a}\n"

    contenu += "\n## Scores de détection\n"
    for arch, score in scores.items():
        barre = "█" * min(int(score), 15) + "░" * max(0, 15 - min(int(score), 15))
        couv = couverture.get(arch, 0)
        contenu += f"- {arch:<15} {barre} {score:.1f} pts (couverture: {couv}%)\n"

    return contenu