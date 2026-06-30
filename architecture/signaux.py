# ─── Signaux basés sur les dossiers ───────────────────────────────────────────
SIGNAUX_DOSSIERS = {
    "MVC": [
        "controllers", "controller",
        "views", "view",
        "models", "model",
        "templates"
    ],
    "MVP": [
        "presenter", "presenters",
        "interactor"
        # "view" et "model" retirés — trop génériques
    ],
    "MVVM": [
        "viewmodel", "viewmodels",
        "binding", "bindings"
        # "view" et "model" retirés — trop génériques
    ],
    "COUCHES": [
        "presentation",
        "business",
        "service", "services",
        "repository", "repositories",
        "domain", "core",
        "infrastructure"
        # "data", "ui" retirés — trop génériques
    ],
    "CLEAN": [
        "use_cases", "usecases",
        "entities", "entity",
        "repositories",
        "domain",
        "infrastructure",
        "adapters"
    ],
    "MICROSERVICES": [
        "gateway", "api-gateway",
        "api_gateway"
        # "services", "frontend", "backend", "auth" retirés — trop génériques
    ],
    "MONOLITHIQUE": []
}

# ─── Signaux basés sur les frameworks ────────────────────────────────────────
SIGNAUX_FRAMEWORKS = {
    "MVC": [
        "django", "rails", "laravel",
        "spring-mvc", "codeigniter"
        # "flask" et "express" retirés — frameworks légers, pas forcément MVC
    ],
    "MVP": [
        "android", "gwt",
        "winforms"
    ],
    "MVVM": [
        "angular", "vue", "vuex",
        "knockout", "wpf",
        "swiftui", "jetpack"
        # "react" retiré — peut être n'importe quelle architecture
    ],
    "COUCHES": [
        "spring-boot", "nestjs",
        "hibernate", "sqlalchemy",
        "typeorm", "sequelize",
        "flask",        # Flask → architecture en couches par défaut
        "express"       # Express → idem
    ],
    "CLEAN": [
        "fastapi", "hexagonal",
        "onion"
    ],
    "MICROSERVICES": [
        "kubernetes", "kafka",
        "rabbitmq", "consul", "nginx"
        # "docker-compose" retiré — géré séparément avec moins de poids
    ],
    "MONOLITHIQUE": []
}

# ─── Poids des signaux ────────────────────────────────────────────────────────
POIDS = {
    "dossier"    : 2,
    "framework"  : 3,
    "dockerfile" : 2    # Réduit de 4 à 2 — docker-compose seul ne suffit pas
}
# ─── Seuils de taille de projet (Étape 1 - normalisation par taille) ─────────
SEUILS_TAILLE = {
    "minimal": 15,   # En dessous → MONOLITHIQUE direct, sans scoring
    "moyen"  : 30     # Entre minimal et moyen → zone grise, scoring + forte réduction
}

# Facteur de réduction appliqué dans la zone grise (entre minimal et moyen)
FACTEUR_ZONE_GRISE = 0.5

