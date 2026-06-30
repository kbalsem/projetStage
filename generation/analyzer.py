import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

EXTENSIONS_SUPPORTEES = {
    ".py"  : "python",
    ".js"  : "javascript",
    ".ts"  : "typescript",
    ".jsx" : "javascript",
    ".tsx" : "typescript",
    ".java": "java",
    ".go"  : "go",
    ".rs"  : "rust",
    ".php" : "php",
    ".rb"  : "ruby",
    ".cs"  : "c_sharp",
    ".cpp" : "cpp",
    ".c"   : "c",
}


def _get_parser(langage: str):
    """
    Retourne un parser tree-sitter pour le langage donné.
    """
    try:
        import tree_sitter
        from importlib import import_module

        correspondance = {
            "python"    : "tree_sitter_python",
            "javascript": "tree_sitter_javascript",
            "typescript": "tree_sitter_typescript",
            "java"      : "tree_sitter_java",
            "go"        : "tree_sitter_go",
            "rust"      : "tree_sitter_rust",
            "php"       : "tree_sitter_php",
            "ruby"      : "tree_sitter_ruby",
            "c"         : "tree_sitter_c",
            "cpp"       : "tree_sitter_cpp",
        }

        nom_module = correspondance.get(langage)
        if nom_module is None:
            logger.warning(f"Langage non supporté : {langage}")
            return None

        module = import_module(nom_module)

        if langage == "typescript":
            lang = tree_sitter.Language(module.language_typescript())
        elif langage == "php":
            lang = tree_sitter.Language(module.language_php())
        else:
            lang = tree_sitter.Language(module.language())

        return tree_sitter.Parser(lang)

    except Exception as e:
        logger.warning(f"Parser non disponible pour {langage} : {e}")
        return None


def _parcourir(node, infos: dict, classe_courante=None):
    """
    Parcourt récursivement l'arbre tree-sitter et remplit infos.
    """
    ttype = node.type

    # ── Classes ───────────────────────────────────────────────────
    if ttype in ("class_definition", "class_declaration"):
        nom = next(
            (c.text.decode("utf-8") for c in node.children
             if c.type in ("identifier", "type_identifier")),
            "Inconnue"
        )
        classe = {
            "nom"     : nom,
            "ligne"   : node.start_point[0] + 1,
            "methodes": []
        }
        infos["classes"].append(classe)
        for child in node.children:
            _parcourir(child, infos, classe_courante=classe)
        return

    # ── Fonctions / méthodes ──────────────────────────────────────
    if ttype in (
        "function_definition", "function_declaration",
        "method_definition", "method_declaration",
        "arrow_function",
    ):
        nom = next(
            (c.text.decode("utf-8") for c in node.children
             if c.type == "identifier"),
            "<anonyme>"
        )
        params = []
        for child in node.children:
            if child.type in ("parameters", "formal_parameters"):
                params = [
                    p.text.decode("utf-8")
                    for p in child.children
                    if p.type in (
                        "identifier",
                        "typed_parameter",
                        "typed_default_parameter"
                    )
                ]
        entree = {
            "nom"  : nom,
            "args" : params,
            "ligne": node.start_point[0] + 1
        }
        if classe_courante is not None:
            classe_courante["methodes"].append(entree)
        else:
            infos["fonctions"].append(entree)

    # ── Imports ───────────────────────────────────────────────────
    if ttype in (
        "import_statement",
        "import_from_statement",
        "import_declaration"
    ):
        texte = node.text.decode("utf-8", errors="ignore")[:120]
        infos["imports"].append(texte)

    # ── Récursion sur les enfants ─────────────────────────────────
    for child in node.children:
        _parcourir(child, infos, classe_courante=classe_courante)


def extraire_infos_depuis_code(code: str, chemin: str, langage: str) -> dict:
    """
    Analyse un code source (string) avec tree-sitter.
    Retourne classes, fonctions, imports, code_brut.
    """
    infos = {
        "classes"  : [],
        "fonctions": [],
        "imports"  : [],
        "code_brut": code[:2000],
        "langage"  : langage
    }

    parser = _get_parser(langage)

    # ── Fallback si parser non disponible ────────────────────────
    if parser is None:
        logger.warning(f"Pas de parser pour {langage} — code brut uniquement")
        return infos

    try:
        tree = parser.parse(bytes(code, "utf-8"))
        _parcourir(tree.root_node, infos)
        infos["imports"] = list(set(infos["imports"]))

        logger.info(
            f"{chemin} → "
            f"{len(infos['classes'])} classes, "
            f"{len(infos['fonctions'])} fonctions, "
            f"langage : {langage}"
        )
        return infos

    except Exception as e:
        logger.warning(f"Erreur parsing {chemin} : {e}")
        return infos


def extraire_infos_fichier(chemin_fichier: str) -> dict:
    """
    Lit un fichier depuis le disque et l'analyse.
    Utilisé quand temp_repo est disponible.
    """
    ext     = Path(chemin_fichier).suffix.lower()
    langage = EXTENSIONS_SUPPORTEES.get(ext)

    if langage is None:
        return {}

    try:
        with open(chemin_fichier, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
    except Exception as e:
        logger.warning(f"Impossible de lire {chemin_fichier} : {e}")
        return {}

    return extraire_infos_depuis_code(code, chemin_fichier, langage)


def analyser_projet_disque(dossier_local: str, fichiers: list) -> dict:
    """
    Analyse les fichiers depuis le disque (temp_repo).
    Utilisé après clonage GitPython.
    """
    resultats = {}

    for chemin in fichiers:
        ext = Path(chemin).suffix.lower()
        if ext not in EXTENSIONS_SUPPORTEES:
            continue

        chemin_complet = os.path.join(dossier_local, chemin)
        if not os.path.exists(chemin_complet):
            continue

        infos = extraire_infos_fichier(chemin_complet)
        if infos:
            resultats[chemin] = infos

    logger.info(f"AST disque : {len(resultats)} fichiers analysés")
    return resultats


def analyser_projet_memoire(sources: dict) -> dict:
    """
    Analyse les fichiers passés en mémoire (depuis API GitHub/GitLab).
    sources = { chemin: contenu_texte }
    Utilisé quand temp_repo n'est pas disponible.
    """
    resultats = {}

    for chemin, code in sources.items():
        ext     = Path(chemin).suffix.lower()
        langage = EXTENSIONS_SUPPORTEES.get(ext)

        if langage is None:
            continue

        infos = extraire_infos_depuis_code(code, chemin, langage)
        if infos:
            resultats[chemin] = infos

    logger.info(f"AST mémoire : {len(resultats)} fichiers analysés")
    return resultats