#readme_generator.py
import logging
from .prompts          import PROMPT_README
from utils.ollama_client import generer

logger = logging.getLogger(__name__)


def construire_structure_fichiers(fichiers: list, max_fichiers: int = 40) -> str:
    """
    Construit une représentation texte de l'arborescence réelle du projet,
    pour éviter qu'Ollama n'invente une structure fictive.
    """
    fichiers_tries = sorted(fichiers)[:max_fichiers]
    lignes = [f"- {f}" for f in fichiers_tries]
    if len(fichiers) > max_fichiers:
        lignes.append(f"- ... et {len(fichiers) - max_fichiers} autres fichiers")
    return "\n".join(lignes)


def generer_readme(
    data_scanner  : dict,
    resultat_archi: dict
) -> str:
    """
    Génère un README complet et amélioré.
    """
    structure = construire_structure_fichiers(data_scanner.get("fichiers", []))

    prompt = PROMPT_README.format(
        repo_name           = data_scanner.get("repo_name", "Inconnu"),
        author              = data_scanner.get("author", "Inconnu"),
        architecture        = resultat_archi.get("architecture", "Inconnue"),
        frameworks          = ", ".join(resultat_archi.get("frameworks", [])),
        description         = data_scanner.get("description", "Aucune description"),
        structure_fichiers  = structure
    )

    logger.info("Génération README...")
    return generer(prompt, max_tokens=1200)