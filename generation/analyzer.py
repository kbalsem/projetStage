# generation/analyzer.py
"""
Analyseur de code source par AST (Abstract Syntax Tree).

Utilise tree-sitter pour parser le code et extraire classes, fonctions, imports.
"""

import os
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DEPUIS .ENV
# ═══════════════════════════════════════════════════════════════════════════════

# Extensions supportées
EXTENSIONS_SUPPORTEES_STR = os.getenv(
    "ANALYZER_EXTENSIONS",
    ".py:python,.js:javascript,.ts:typescript,.jsx:javascript,.tsx:typescript,"
    ".java:java,.go:go,.rs:rust,.php:php,.rb:ruby,.cs:c_sharp,.cpp:cpp,.c:c"
)

# Taille maximale du code brut à conserver
MAX_CODE_BRUT = int(os.getenv("ANALYZER_MAX_CODE_BRUT", "2000"))

# Taille maximale des imports à conserver
MAX_IMPORT_TEXTE = int(os.getenv("ANALYZER_MAX_IMPORT_TEXTE", "120"))

# Flag debug
DEBUG_ANALYZER = os.getenv("DEBUG_ANALYZER", "false").lower() == "true"

# ═══════════════════════════════════════════════════════════════════════════════
# INITIALISATION
# ═══════════════════════════════════════════════════════════════════════════════

def _parser_extensions() -> Dict[str, str]:
    """Parse la configuration des extensions depuis .env."""
    extensions = {}
    for item in EXTENSIONS_SUPPORTEES_STR.split(","):
        if ":" in item:
            ext, lang = item.split(":", 1)
            extensions[ext.strip()] = lang.strip()
    return extensions

EXTENSIONS_SUPPORTEES = _parser_extensions()

# Mapping tree-sitter
TREE_SITTER_MODULES = {
    "python": "tree_sitter_python",
    "javascript": "tree_sitter_javascript",
    "typescript": "tree_sitter_typescript",
    "java": "tree_sitter_java",
    "go": "tree_sitter_go",
    "rust": "tree_sitter_rust",
    "php": "tree_sitter_php",
    "ruby": "tree_sitter_ruby",
    "c": "tree_sitter_c",
    "cpp": "tree_sitter_cpp",
    "c_sharp": "tree_sitter_c_sharp",
}

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE PARSING
# ═══════════════════════════════════════════════════════════════════════════════

def _get_parser(langage: str):
    """
    Obtient un parser tree-sitter pour un langage donné.
    
    Args:
        langage: Nom du langage
        
    Returns:
        Parser tree-sitter ou None
    """
    try:
        import tree_sitter
        from importlib import import_module

        nom_module = TREE_SITTER_MODULES.get(langage)
        if nom_module is None:
            if DEBUG_ANALYZER:
                logger.debug(f"Langage non supporté : {langage}")
            return None

        module = import_module(nom_module)

        # Gestion des cas spéciaux
        if langage == "typescript":
            lang = tree_sitter.Language(module.language_typescript())
        elif langage == "php":
            lang = tree_sitter.Language(module.language_php())
        elif langage == "c_sharp":
            lang = tree_sitter.Language(module.language())
        else:
            lang = tree_sitter.Language(module.language())

        return tree_sitter.Parser(lang)

    except ImportError as e:
        logger.warning(f"Module tree-sitter manquant pour {langage} : {e}")
        return None
    except Exception as e:
        logger.warning(f"Parser non disponible pour {langage} : {e}")
        return None


def _parcourir(node, infos: dict, classe_courante=None):
    """
    Parcourt récursivement l'AST pour extraire les informations.
    
    Args:
        node: Noeud AST courant
        infos: Dictionnaire accumulant les résultats
        classe_courante: Classe parente si dans une classe
    """
    ttype = node.type

    # Détection de classe
    if ttype in ("class_definition", "class_declaration"):
        nom = next(
            (c.text.decode("utf-8") for c in node.children
             if c.type in ("identifier", "type_identifier")),
            "Inconnue"
        )
        classe = {"nom": nom, "ligne": node.start_point[0] + 1, "methodes": []}
        infos["classes"].append(classe)
        
        for child in node.children:
            _parcourir(child, infos, classe_courante=classe)
        return

    # Détection de fonction/méthode
    if ttype in (
        "function_definition", "function_declaration",
        "method_definition", "method_declaration",
        "arrow_function",
    ):
        nom = next(
            (c.text.decode("utf-8") for c in node.children if c.type == "identifier"),
            "<anonyme>"
        )
        params = []
        for child in node.children:
            if child.type in ("parameters", "formal_parameters"):
                params = [
                    p.text.decode("utf-8")
                    for p in child.children
                    if p.type in ("identifier", "typed_parameter", "typed_default_parameter")
                ]
        
        entree = {"nom": nom, "args": params, "ligne": node.start_point[0] + 1}
        
        if classe_courante is not None:
            classe_courante["methodes"].append(entree)
        else:
            infos["fonctions"].append(entree)

    # Détection d'import
    if ttype in ("import_statement", "import_from_statement", "import_declaration"):
        texte = node.text.decode("utf-8", errors="ignore")[:MAX_IMPORT_TEXTE]
        infos["imports"].append(texte)

    # Parcours des enfants
    for child in node.children:
        _parcourir(child, infos, classe_courante=classe_courante)


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS PRINCIPALES
# ═══════════════════════════════════════════════════════════════════════════════

def extraire_infos_depuis_code(code: str, chemin: str, langage: str) -> dict:
    """
    Extrait les informations d'un code source via AST.
    
    Args:
        code: Code source
        chemin: Chemin du fichier (pour logs)
        langage: Langage de programmation
        
    Returns:
        Dictionnaire {classes, fonctions, imports, code_brut, langage}
    """
    infos = {
        "classes": [], 
        "fonctions": [], 
        "imports": [],
        "code_brut": code[:MAX_CODE_BRUT], 
        "langage": langage
    }

    parser = _get_parser(langage)
    if parser is None:
        if DEBUG_ANALYZER:
            logger.debug(f"Pas de parser pour {langage} — code brut uniquement")
        return infos

    try:
        tree = parser.parse(bytes(code, "utf-8"))
        _parcourir(tree.root_node, infos)
        infos["imports"] = list(set(infos["imports"]))
        
        if DEBUG_ANALYZER:
            logger.debug(
                f"{chemin} → {len(infos['classes'])} classes, "
                f"{len(infos['fonctions'])} fonctions, langage : {langage}"
            )
        return infos
        
    except Exception as e:
        logger.warning(f"Erreur parsing {chemin} : {e}")
        return infos


def extraire_infos_fichier(chemin_fichier: str) -> dict:
    """
    Extrait les informations d'un fichier sur disque.
    
    Args:
        chemin_fichier: Chemin absolu du fichier
        
    Returns:
        Dictionnaire d'informations ou {} si erreur
    """
    ext = Path(chemin_fichier).suffix.lower()
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
    Analyse tous les fichiers d'un projet sur disque.
    
    Args:
        dossier_local: Chemin racine du projet
        fichiers: Liste des chemins relatifs des fichiers
        
    Returns:
        Dictionnaire {chemin: infos}
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
    
    logger.info(f"AST disque : {len(resultats)} fichiers analysés sur {len(fichiers)}")
    return resultats


def analyser_projet_memoire(sources: dict) -> dict:
    """
    Analyse des fichiers en mémoire (sans accès disque).
    
    Args:
        sources: Dictionnaire {chemin: code}
        
    Returns:
        Dictionnaire {chemin: infos}
    """
    resultats = {}
    
    for chemin, code in sources.items():
        ext = Path(chemin).suffix.lower()
        langage = EXTENSIONS_SUPPORTEES.get(ext)
        
        if langage is None:
            continue
        
        infos = extraire_infos_depuis_code(code, chemin, langage)
        if infos:
            resultats[chemin] = infos
    
    logger.info(f"AST mémoire : {len(resultats)} fichiers analysés sur {len(sources)}")
    return resultats