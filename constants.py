# constants.py
"""
Constantes partagées par tous les modules du projet.

Ces constantes peuvent être surchargées via le fichier .env.
Les valeurs ici servent de fallback si la variable d'environnement n'existe pas.
"""

import os

# ═══════════════════════════════════════════════════════════════════════════════
# FICHIERS STRATÉGIQUES
# ═══════════════════════════════════════════════════════════════════════════════

FICHIERS_STRATEGIQUES_DEFAUT = [
    "requirements.txt", "Pipfile", "setup.py", "pyproject.toml",
    "package.json", "package-lock.json",
    "pom.xml", "build.gradle",
    "composer.json",
    "docker-compose.yml", "docker-compose.yaml", "Dockerfile",
    "angular.json", ".angular-cli.json",
    "Gemfile", "go.mod", "cargo.toml"
]

FICHIERS_STRATEGIQUES = [
    f.strip() for f in os.getenv(
        "CONSTANTS_FICHIERS_STRATEGIQUES",
        ",".join(FICHIERS_STRATEGIQUES_DEFAUT)
    ).split(",") if f.strip()
]

# ═══════════════════════════════════════════════════════════════════════════════
# EXTENSIONS SUPPORTÉES POUR L'ANALYSE AST
# ═══════════════════════════════════════════════════════════════════════════════

EXTENSIONS_AST_DEFAUT = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".go", ".rs", ".php", ".rb",
    ".c", ".cpp"
}

EXTENSIONS_AST = set(
    ext.strip() for ext in os.getenv(
        "CONSTANTS_EXTENSIONS_AST",
        ",".join(EXTENSIONS_AST_DEFAUT)
    ).split(",") if ext.strip()
)

# ═══════════════════════════════════════════════════════════════════════════════
# LIMITES DE TRAITEMENT
# ═══════════════════════════════════════════════════════════════════════════════

MAX_FICHIERS_AST = int(os.getenv(
    "CONSTANTS_MAX_FICHIERS_AST", "100"
))  # Nombre max de fichiers sources pour AST

MAX_TAILLE_FICHIER = int(os.getenv(
    "CONSTANTS_MAX_TAILLE_FICHIER", "100000"
))  # Taille max d'un fichier (100 Ko)

MAX_FICHIERS_TOTAL = int(os.getenv(
    "CONSTANTS_MAX_FICHIERS_TOTAL", "1000"
))  # Nombre max de fichiers listés

TRONCATURE_STRATEGIQUE = int(os.getenv(
    "CONSTANTS_TRONCATURE_STRATEGIQUE", "3000"
))  # Troncature du contenu des fichiers stratégiques

# ═══════════════════════════════════════════════════════════════════════════════
# TIMEOUTS
# ═══════════════════════════════════════════════════════════════════════════════

TIMEOUT_CLONE = int(os.getenv("CONSTANTS_TIMEOUT_CLONE", "300"))  # secondes
TIMEOUT_MKDOCS_BUILD = int(os.getenv("CONSTANTS_TIMEOUT_MKDOCS", "120"))  # secondes