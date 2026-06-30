import logging
from .prompts          import PROMPT_FICHIER
from .ollama_generator import generer

logger = logging.getLogger(__name__)


def formater_classes(classes: list) -> str:
    if not classes:
        return "Aucune"
    result = []
    for c in classes:
        methodes = ", ".join(m["nom"] for m in c["methodes"])
        result.append(f"{c['nom']} (méthodes: {methodes})")
    return " | ".join(result)


def formater_fonctions(fonctions: list) -> str:
    if not fonctions:
        return "Aucune"
    return " | ".join(
        f"{f['nom']}({', '.join(f['args'])})"
        for f in fonctions[:10]   # Limite à 10
    )


def generer_doc_fichier(
    chemin     : str,
    infos_ast  : dict,
    architecture: str
) -> str:
    """
    Génère la documentation d'un seul fichier via Ollama.
    """
    logger.info(f"Génération doc : {chemin}")

    prompt = PROMPT_FICHIER.format(
        filename     = chemin,
        architecture = architecture,
        classes      = formater_classes(infos_ast.get("classes", [])),
        fonctions    = formater_fonctions(infos_ast.get("fonctions", [])),
        imports      = ", ".join(infos_ast.get("imports", [])[:10]),
        code         = infos_ast.get("code_brut", "")[:1500]
    )

    doc = generer(prompt)

    # Ajouter l'en-tête avec le nom du fichier
    entete = f"# {chemin}\n\n"
    return entete + doc


def generer_doc_tous_fichiers(
    infos_ast   : dict,
    architecture: str
) -> dict:
    """
    Génère la documentation pour tous les fichiers analysés.
    Retourne un dict { chemin: contenu_markdown }
    """
    docs = {}
    total = len(infos_ast)

    for i, (chemin, infos) in enumerate(infos_ast.items(), 1):
        print(f"  [{i}/{total}] Documentation : {chemin}")
        docs[chemin] = generer_doc_fichier(chemin, infos, architecture)

    return docs