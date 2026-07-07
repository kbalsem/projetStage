# architecture/signaux.py
"""
Base de connaissances unifiée pour la détection d'architecture.

Ce module contient TOUTE la connaissance métier sur les patterns
architecturaux. Ces données NE SONT PAS configurables via .env
car elles représentent la logique experte du système.

Pour modifier les seuils et paramètres ajustables, voir le fichier .env
et les modules detecteur.py et ollama_detecteur.py.
"""

import os

# ═══════════════════════════════════════════════════════════════════════════════
# CONNAISSANCE MÉTIER (non configurable)
# ═══════════════════════════════════════════════════════════════════════════════

SIGNAUX = {
    "MVC": {
        "dossiers": [
            {"nom": "controllers", "fiabilite": "forte"},
            {"nom": "controller", "fiabilite": "forte"},
            {"nom": "views", "fiabilite": "forte"},
            {"nom": "view", "fiabilite": "moyenne"},
            {"nom": "models", "fiabilite": "moyenne"},
            {"nom": "model", "fiabilite": "moyenne"},
            {"nom": "templates", "fiabilite": "moyenne"},
            {"nom": "template", "fiabilite": "faible"},
            {"nom": "static", "fiabilite": "faible"},
            {"nom": "flask", "fiabilite": "moyenne"},
        ],
        "frameworks": [
            {"nom": "django", "fiabilite": "forte"},
            {"nom": "rails", "fiabilite": "forte"},
            {"nom": "laravel", "fiabilite": "forte"},
            {"nom": "spring-mvc", "fiabilite": "forte"},
            {"nom": "asp.net core mvc", "fiabilite": "forte"},
            {"nom": "symfony", "fiabilite": "forte"},
            {"nom": "flask", "fiabilite": "moyenne"},
            {"nom": "express", "fiabilite": "moyenne"},
        ],
        "fichiers": [
            {"nom": "urls.py", "fiabilite": "forte"},
            {"nom": "views.py", "fiabilite": "forte"},
            {"nom": "models.py", "fiabilite": "forte"},
            {"nom": "admin.py", "fiabilite": "forte"},
            {"nom": "forms.py", "fiabilite": "forte"},
            {"nom": "wsgi.py", "fiabilite": "forte"},
            {"nom": "asgi.py", "fiabilite": "forte"},
            {"nom": "manage.py", "fiabilite": "forte"},
            {"nom": "app.py", "fiabilite": "moyenne"},
            {"nom": "routes.py", "fiabilite": "moyenne"},
        ],
        "imports": [
            {"nom": "django", "fiabilite": "forte"},
            {"nom": "flask", "fiabilite": "forte"},
            {"nom": "django.db.models", "fiabilite": "forte"},
            {"nom": "django.urls", "fiabilite": "forte"},
            {"nom": "django.views", "fiabilite": "forte"},
            {"nom": "django.contrib", "fiabilite": "forte"},
            {"nom": "flask.views", "fiabilite": "forte"},
            {"nom": "flask.blueprints", "fiabilite": "forte"},
            {"nom": "werkzeug", "fiabilite": "moyenne"},
            {"nom": "jinja2", "fiabilite": "faible"},
        ],
        "decorateurs": [
            {"nom": "@app.route", "fiabilite": "forte"},
            {"nom": "@bp.route", "fiabilite": "forte"},
            {"nom": "@blueprint.route", "fiabilite": "forte"},
            {"nom": "@router.route", "fiabilite": "moyenne"},
            {"nom": "@action", "fiabilite": "forte"},
            {"nom": "@view", "fiabilite": "moyenne"},
            {"nom": "@get", "fiabilite": "faible"},
            {"nom": "@post", "fiabilite": "faible"},
        ],
        "dependances": [
            {"nom": "django", "fiabilite": "forte"},
            {"nom": "flask", "fiabilite": "forte"},
            {"nom": "rails", "fiabilite": "forte"},
            {"nom": "spring-boot-starter-web", "fiabilite": "forte"},
            {"nom": "jinja2", "fiabilite": "moyenne"},
            {"nom": "werkzeug", "fiabilite": "moyenne"},
        ],
        "classes": [
            {"nom": "ModelForm", "fiabilite": "forte"},
            {"nom": "TemplateView", "fiabilite": "forte"},
            {"nom": "ListView", "fiabilite": "forte"},
            {"nom": "DetailView", "fiabilite": "forte"},
            {"nom": "CreateView", "fiabilite": "forte"},
            {"nom": "UpdateView", "fiabilite": "forte"},
            {"nom": "DeleteView", "fiabilite": "forte"},
            {"nom": "View", "fiabilite": "moyenne"},
            {"nom": "Controller", "fiabilite": "forte"},
            {"nom": "Flask", "fiabilite": "moyenne"},
            {"nom": "Blueprint", "fiabilite": "moyenne"},
        ],
    },
    "MVP": {
        "dossiers": [
            {"nom": "presenter", "fiabilite": "forte"},
            {"nom": "presenters", "fiabilite": "forte"},
            {"nom": "interactor", "fiabilite": "forte"},
            {"nom": "interactors", "fiabilite": "forte"},
        ],
        "frameworks": [
            {"nom": "android", "fiabilite": "forte"},
            {"nom": "gwt", "fiabilite": "forte"},
            {"nom": "winforms", "fiabilite": "forte"},
        ],
        "fichiers": [
            {"nom": "presenter.py", "fiabilite": "forte"},
            {"nom": "interactor.py", "fiabilite": "forte"},
            {"nom": "presenter.java", "fiabilite": "forte"},
        ],
        "imports": [
            {"nom": "presenter", "fiabilite": "forte"},
            {"nom": "interactor", "fiabilite": "forte"},
        ],
        "decorateurs": [
            {"nom": "@presenter", "fiabilite": "forte"},
            {"nom": "@inject", "fiabilite": "faible"},
        ],
        "dependances": [],
        "classes": [
            {"nom": "Presenter", "fiabilite": "forte"},
            {"nom": "Interactor", "fiabilite": "forte"},
            {"nom": "BasePresenter", "fiabilite": "forte"},
        ],
    },
    "MVVM": {
        "dossiers": [
            {"nom": "viewmodel", "fiabilite": "forte"},
            {"nom": "viewmodels", "fiabilite": "forte"},
            {"nom": "binding", "fiabilite": "moyenne"},
            {"nom": "bindings", "fiabilite": "moyenne"},
            {"nom": "components", "fiabilite": "faible"},
        ],
        "frameworks": [
            {"nom": "angular", "fiabilite": "forte"},
            {"nom": "knockout", "fiabilite": "forte"},
            {"nom": "wpf", "fiabilite": "forte"},
            {"nom": "swiftui", "fiabilite": "forte"},
            {"nom": "jetpack", "fiabilite": "forte"},
            {"nom": "vue", "fiabilite": "moyenne"},
            {"nom": "react", "fiabilite": "faible"},
        ],
        "fichiers": [
            {"nom": "viewmodel.dart", "fiabilite": "forte"},
            {"nom": "binding.dart", "fiabilite": "forte"},
            {"nom": "viewmodel.ts", "fiabilite": "forte"},
            {"nom": "viewmodel.js", "fiabilite": "moyenne"},
        ],
        "imports": [
            {"nom": "databinding", "fiabilite": "forte"},
            {"nom": "live_data", "fiabilite": "forte"},
            {"nom": "viewmodel", "fiabilite": "forte"},
            {"nom": "observable", "fiabilite": "moyenne"},
            {"nom": "@angular/core", "fiabilite": "forte"},
            {"nom": "vue", "fiabilite": "moyenne"},
        ],
        "decorateurs": [
            {"nom": "@bindable", "fiabilite": "forte"},
            {"nom": "@observable", "fiabilite": "forte"},
            {"nom": "@input", "fiabilite": "moyenne"},
            {"nom": "@output", "fiabilite": "moyenne"},
            {"nom": "@component", "fiabilite": "faible"},
        ],
        "dependances": [
            {"nom": "vuex", "fiabilite": "forte"},
            {"nom": "pinia", "fiabilite": "forte"},
            {"nom": "@angular/core", "fiabilite": "forte"},
            {"nom": "@angular/common", "fiabilite": "forte"},
            {"nom": "vue", "fiabilite": "moyenne"},
            {"nom": "react", "fiabilite": "faible"},
            {"nom": "react-dom", "fiabilite": "faible"},
        ],
        "classes": [
            {"nom": "ViewModel", "fiabilite": "forte"},
            {"nom": "LiveData", "fiabilite": "forte"},
            {"nom": "ObservableObject", "fiabilite": "forte"},
            {"nom": "Component", "fiabilite": "faible"},
        ],
    },
    "COUCHES": {
        "dossiers": [
            {"nom": "presentation", "fiabilite": "forte"},
            {"nom": "infrastructure", "fiabilite": "moyenne"},
            {"nom": "domain", "fiabilite": "moyenne"},
            {"nom": "application", "fiabilite": "moyenne"},
            {"nom": "service", "fiabilite": "moyenne"},
            {"nom": "services", "fiabilite": "moyenne"},
            {"nom": "repository", "fiabilite": "moyenne"},
            {"nom": "repositories", "fiabilite": "moyenne"},
            {"nom": "persistence", "fiabilite": "moyenne"},
            {"nom": "modules", "fiabilite": "moyenne"},
            {"nom": "common", "fiabilite": "faible"},
            {"nom": "config", "fiabilite": "faible"},
            {"nom": "configuration", "fiabilite": "faible"},
        ],
        "frameworks": [
            {"nom": "spring-boot", "fiabilite": "forte"},
            {"nom": "spring", "fiabilite": "forte"},
            {"nom": "nestjs", "fiabilite": "forte"},
            {"nom": "quarkus", "fiabilite": "forte"},
            {"nom": "micronaut", "fiabilite": "forte"},
            {"nom": "express", "fiabilite": "moyenne"},
            {"nom": "flask", "fiabilite": "faible"},
        ],
        "fichiers": [
            {"nom": "database.py", "fiabilite": "faible"},
            {"nom": "session.py", "fiabilite": "faible"},
            {"nom": "application.properties", "fiabilite": "forte"},
            {"nom": "application.yml", "fiabilite": "forte"},
            {"nom": "application.yaml", "fiabilite": "forte"},
            {"nom": "pom.xml", "fiabilite": "forte"},
            {"nom": "build.gradle", "fiabilite": "forte"},
        ],
        "imports": [
            {"nom": "springframework", "fiabilite": "forte"},
            {"nom": "spring", "fiabilite": "forte"},
            {"nom": "sqlalchemy", "fiabilite": "forte"},
            {"nom": "hibernate", "fiabilite": "forte"},
            {"nom": "typeorm", "fiabilite": "forte"},
            {"nom": "jakarta.persistence", "fiabilite": "forte"},
            {"nom": "jpa", "fiabilite": "forte"},
            {"nom": "entitymanager", "fiabilite": "forte"},
            {"nom": "repository", "fiabilite": "moyenne"},
            {"nom": "service", "fiabilite": "moyenne"},
            {"nom": "@autowired", "fiabilite": "forte"},
            {"nom": "@inject", "fiabilite": "moyenne"},
        ],
        "decorateurs": [
            {"nom": "@service", "fiabilite": "forte"},
            {"nom": "@repository", "fiabilite": "forte"},
            {"nom": "@autowired", "fiabilite": "forte"},
            {"nom": "@component", "fiabilite": "moyenne"},
            {"nom": "@inject", "fiabilite": "moyenne"},
            {"nom": "@Controller", "fiabilite": "moyenne"},
            {"nom": "@Injectable", "fiabilite": "forte"},
            {"nom": "@Module", "fiabilite": "forte"},
            {"nom": "@controller", "fiabilite": "moyenne"},
            {"nom": "@restcontroller", "fiabilite": "moyenne"},
        ],
        "dependances": [
            {"nom": "spring-boot-starter-data-jpa", "fiabilite": "forte"},
            {"nom": "spring-boot", "fiabilite": "forte"},
            {"nom": "spring", "fiabilite": "forte"},
            {"nom": "hibernate-core", "fiabilite": "forte"},
            {"nom": "typeorm", "fiabilite": "forte"},
            {"nom": "sequelize", "fiabilite": "forte"},
            {"nom": "sqlalchemy", "fiabilite": "forte"},
            {"nom": "@nestjs/core", "fiabilite": "forte"},
            {"nom": "@nestjs/common", "fiabilite": "forte"},
            {"nom": "express", "fiabilite": "moyenne"},
        ],
        "classes": [
            {"nom": "ServiceImpl", "fiabilite": "forte"},
            {"nom": "RepositoryImpl", "fiabilite": "forte"},
            {"nom": "DaoImpl", "fiabilite": "forte"},
            {"nom": "JpaRepository", "fiabilite": "forte"},
            {"nom": "CrudRepository", "fiabilite": "forte"},
            {"nom": "Service", "fiabilite": "moyenne"},
            {"nom": "Repository", "fiabilite": "moyenne"},
        ],
    },
    "CLEAN": {
        "dossiers": [
            {"nom": "use_cases", "fiabilite": "forte"},
            {"nom": "usecases", "fiabilite": "forte"},
            {"nom": "entities", "fiabilite": "forte"},
            {"nom": "entity", "fiabilite": "forte"},
            {"nom": "adapters", "fiabilite": "forte"},
            {"nom": "adapter", "fiabilite": "moyenne"},
            {"nom": "interfaces", "fiabilite": "moyenne"},
            {"nom": "ports", "fiabilite": "moyenne"},
        ],
        "frameworks": [
            {"nom": "fastapi", "fiabilite": "forte"},
            {"nom": "hexagonal", "fiabilite": "forte"},
        ],
        "fichiers": [
            {"nom": "usecase.py", "fiabilite": "forte"},
            {"nom": "entity.py", "fiabilite": "forte"},
            {"nom": "adapter.py", "fiabilite": "forte"},
            {"nom": "gateway.py", "fiabilite": "moyenne"},
            {"nom": "interface.py", "fiabilite": "moyenne"},
            {"nom": "port.py", "fiabilite": "moyenne"},
        ],
        "imports": [
            {"nom": "fastapi", "fiabilite": "forte"},
            {"nom": "dependency-injector", "fiabilite": "forte"},
            {"nom": "pydantic", "fiabilite": "moyenne"},
            {"nom": "starlette", "fiabilite": "moyenne"},
            {"nom": "usecase", "fiabilite": "forte"},
            {"nom": "entity", "fiabilite": "moyenne"},
            {"nom": "adapter", "fiabilite": "moyenne"},
            {"nom": "port", "fiabilite": "moyenne"},
        ],
        "decorateurs": [
            {"nom": "@usecase", "fiabilite": "forte"},
            {"nom": "@adapter", "fiabilite": "forte"},
            {"nom": "@inject", "fiabilite": "moyenne"},
        ],
        "dependances": [
            {"nom": "fastapi", "fiabilite": "forte"},
            {"nom": "dependency-injector", "fiabilite": "forte"},
            {"nom": "pydantic", "fiabilite": "forte"},
            {"nom": "starlette", "fiabilite": "moyenne"},
            {"nom": "uvicorn", "fiabilite": "forte"},
        ],
        "classes": [
            {"nom": "UseCase", "fiabilite": "forte"},
            {"nom": "Interactor", "fiabilite": "forte"},
            {"nom": "Adapter", "fiabilite": "moyenne"},
            {"nom": "Gateway", "fiabilite": "moyenne"},
            {"nom": "Port", "fiabilite": "moyenne"},
            {"nom": "Entity", "fiabilite": "moyenne"},
        ],
    },
    "MICROSERVICES": {
        "dossiers": [
            {"nom": "api-gateway", "fiabilite": "forte"},
            {"nom": "api_gateway", "fiabilite": "forte"},
            {"nom": "gateway", "fiabilite": "moyenne"},
            {"nom": "docker", "fiabilite": "faible"},
            {"nom": "k8s", "fiabilite": "forte"},
        ],
        "frameworks": [
            {"nom": "kubernetes", "fiabilite": "forte"},
            {"nom": "kafka", "fiabilite": "forte"},
            {"nom": "rabbitmq", "fiabilite": "forte"},
            {"nom": "consul", "fiabilite": "forte"},
            {"nom": "docker", "fiabilite": "faible"},
            {"nom": "nginx", "fiabilite": "faible"},
        ],
        "fichiers": [
            {"nom": "deployment.yaml", "fiabilite": "forte"},
            {"nom": "service.yaml", "fiabilite": "forte"},
            {"nom": "ingress.yaml", "fiabilite": "forte"},
            {"nom": "docker-compose.yml", "fiabilite": "faible"},
            {"nom": "docker-compose.yaml", "fiabilite": "faible"},
            {"nom": "Dockerfile", "fiabilite": "faible"},
            {"nom": "helmfile.yaml", "fiabilite": "forte"},
        ],
        "imports": [
            {"nom": "grpc", "fiabilite": "forte"},
            {"nom": "feign", "fiabilite": "forte"},
            {"nom": "kafka", "fiabilite": "forte"},
            {"nom": "rabbitmq", "fiabilite": "forte"},
            {"nom": "resttemplate", "fiabilite": "moyenne"},
        ],
        "decorateurs": [
            {"nom": "@feign", "fiabilite": "forte"},
            {"nom": "@restcontroller", "fiabilite": "moyenne"},
            {"nom": "@requestmapping", "fiabilite": "moyenne"},
        ],
        "dependances": [
            {"nom": "spring-cloud-starter", "fiabilite": "forte"},
            {"nom": "eureka-client", "fiabilite": "forte"},
            {"nom": "rabbitmq", "fiabilite": "forte"},
            {"nom": "kafka-client", "fiabilite": "forte"},
            {"nom": "grpc", "fiabilite": "forte"},
        ],
        "classes": [
            {"nom": "Proxy", "fiabilite": "moyenne"},
            {"nom": "MessageBroker", "fiabilite": "forte"},
            {"nom": "Feign", "fiabilite": "forte"},
        ],
    },
    "MONOLITHIQUE": {
        "dossiers": [
            {"nom": "src", "fiabilite": "faible"},
            {"nom": "lib", "fiabilite": "faible"},
            {"nom": "utils", "fiabilite": "faible"},
            {"nom": "app", "fiabilite": "faible"},
        ],
        "frameworks": [],
        "fichiers": [
            {"nom": "main.py", "fiabilite": "faible"},
            {"nom": "app.py", "fiabilite": "faible"},
            {"nom": "index.js", "fiabilite": "faible"},
            {"nom": "server.js", "fiabilite": "faible"},
        ],
        "imports": [],
        "decorateurs": [],
        "dependances": [],
        "classes": [],
    },
}

REGLES = [
    {"nom": "Django MVC", "architecture": "MVC", "conditions": [
        ("framework", "django"), ("fichier", "urls.py"), ("fichier", "views.py"), ("fichier", "models.py")
    ]},
    {"nom": "Flask MVC/Route", "architecture": "MVC", "conditions": [
        ("import", "flask"), ("decorateur", "@app.route"), ("fichier", "app.py")
    ]},
    {"nom": "Flask Blueprint", "architecture": "MVC", "conditions": [
        ("import", "flask"), ("decorateur", "@bp.route")
    ]},
    {"nom": "Express MVC", "architecture": "MVC", "conditions": [
        ("dependance", "express"), ("framework", "express"), ("fichier", "app.js")
    ]},
    {"nom": "Rails MVC", "architecture": "MVC", "conditions": [
        ("framework", "rails"), ("dossier", "controllers"), ("dossier", "views"), ("dossier", "models")
    ]},
    {"nom": "Spring MVC", "architecture": "MVC", "conditions": [
        ("framework", "spring-mvc"), ("dossier", "controllers"), ("dossier", "views")
    ]},
    {"nom": "Laravel MVC", "architecture": "MVC", "conditions": [
        ("framework", "laravel"), ("dossier", "controllers"), ("dossier", "views")
    ]},
    {"nom": "Clean FastAPI", "architecture": "CLEAN", "conditions": [
        ("framework", "fastapi"), ("dossier", "usecases"), ("dossier", "entities")
    ]},
    {"nom": "Clean typique", "architecture": "CLEAN", "conditions": [
        ("dossier", "usecases"), ("dossier", "entities"), ("dossier", "adapters")
    ]},
    {"nom": "FastAPI CLEAN", "architecture": "CLEAN", "conditions": [
        ("dependance", "fastapi"), ("import", "fastapi")
    ]},
    {"nom": "FastAPI pydantic", "architecture": "CLEAN", "conditions": [
        ("import", "fastapi"), ("dependance", "pydantic")
    ]},
    {"nom": "Couches Spring", "architecture": "COUCHES", "conditions": [
        ("framework", "spring-boot"), ("decorateur", "@service"), ("decorateur", "@repository")
    ]},
    {"nom": "Spring Boot COUCHES", "architecture": "COUCHES", "conditions": [
        ("framework", "spring-boot"), ("dependance", "spring-boot-starter-data-jpa")
    ]},
    {"nom": "Spring COUCHES", "architecture": "COUCHES", "conditions": [
        ("import", "springframework"), ("import", "jpa")
    ]},
    {"nom": "Spring annotations", "architecture": "COUCHES", "conditions": [
        ("decorateur", "@service"), ("decorateur", "@autowired")
    ]},
    {"nom": "NestJS COUCHES", "architecture": "COUCHES", "conditions": [
        ("dependance", "@nestjs/core"), ("decorateur", "@Injectable"),
        ("decorateur", "@Controller"), ("decorateur", "@Module")
    ]},
    {"nom": "NestJS modules", "architecture": "COUCHES", "conditions": [
        ("framework", "nestjs"), ("dossier", "modules"), ("decorateur", "@Module")
    ]},
    {"nom": "Couches Repository", "architecture": "COUCHES", "conditions": [
        ("dossier", "service"), ("dossier", "repository"), ("import", "jpa")
    ]},
    {"nom": "Microservices K8s", "architecture": "MICROSERVICES", "conditions": [
        ("framework", "kubernetes"), ("fichier", "deployment.yaml"), ("fichier", "service.yaml")
    ]},
    {"nom": "Microservices Spring Cloud", "architecture": "MICROSERVICES", "conditions": [
        ("dependance", "spring-cloud-starter"), ("dependance", "eureka-client")
    ]},
    {"nom": "Microservices Docker", "architecture": "MICROSERVICES", "conditions": [
        ("fichier", "Dockerfile"), ("fichier", "docker-compose.yml"), ("fichier", "deployment.yaml")
    ]},
    {"nom": "Angular MVVM v2", "architecture": "MVVM", "conditions": [
        ("dependance", "@angular/core"), ("dependance", "@angular/common")
    ]},
    {"nom": "Angular MVVM", "architecture": "MVVM", "conditions": [
        ("dependance", "@angular/core"), ("framework", "angular")
    ]},
    {"nom": "MVVM Angular", "architecture": "MVVM", "conditions": [
        ("framework", "angular"), ("dossier", "viewmodel")
    ]},
    {"nom": "MVVM Vue", "architecture": "MVVM", "conditions": [
        ("dependance", "vue"), ("dependance", "vuex")
    ]},
    {"nom": "MVVM Components", "architecture": "MVVM", "conditions": [
        ("dossier", "viewmodel"), ("dossier", "components"), ("import", "observable")
    ]},
    {"nom": "MVP Android", "architecture": "MVP", "conditions": [
        ("framework", "android"), ("dossier", "presenter")
    ]},
    {"nom": "MVP Presenter", "architecture": "MVP", "conditions": [
        ("dossier", "presenter"), ("import", "presenter"), ("classe", "Presenter")
    ]},
]

ANTI_SIGNAUX = {
    "MVC": [
        ("dossier", "usecases"), ("dossier", "adapters"),
        ("dependance", "@nestjs/core"), ("decorateur", "@Injectable"), ("decorateur", "@Module"),
    ],
    "MVP": [("dossier", "viewmodel")],
    "MVVM": [("dossier", "presenter"), ("dossier", "controllers")],
    "COUCHES": [("dossier", "usecases"), ("dossier", "viewmodel")],
    "CLEAN": [("dossier", "controllers"), ("dossier", "templates")],
    "MICROSERVICES": [("dossier", "controllers"), ("dossier", "templates")],
    "MONOLITHIQUE": [("framework", "kubernetes"), ("framework", "kafka")],
}

# ═══════════════════════════════════════════════════════════════════════════════
# PARAMÈTRES DE SCORING (semi-configurable via .env)
# ═══════════════════════════════════════════════════════════════════════════════

POIDS = {
    "dossier": int(os.getenv("SIGNAUX_POIDS_DOSSIER", "2")),
    "framework": int(os.getenv("SIGNAUX_POIDS_FRAMEWORK", "5")),
    "fichier": int(os.getenv("SIGNAUX_POIDS_FICHIER", "2")),
    "import": int(os.getenv("SIGNAUX_POIDS_IMPORT", "4")),
    "decorateur": int(os.getenv("SIGNAUX_POIDS_DECORATEUR", "4")),
    "dependance": int(os.getenv("SIGNAUX_POIDS_DEPENDANCE", "5")),
    "classe": int(os.getenv("SIGNAUX_POIDS_CLASSE", "1")),
}

FIABILITE_POIDS = {
    "forte": float(os.getenv("SIGNAUX_FIABILITE_FORTE", "1.0")),
    "moyenne": float(os.getenv("SIGNAUX_FIABILITE_MOYENNE", "0.6")),
    "faible": float(os.getenv("SIGNAUX_FIABILITE_FAIBLE", "0.3")),
}

BONUS_PAR_CONDITION = int(os.getenv("SIGNAUX_BONUS_CONDITION", "5"))
PENALITE_ANTI_SIGNAL = int(os.getenv("SIGNAUX_PENALITE_ANTI", "2"))


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def get_architectures_supportees() -> list:
    """Retourne la liste des architectures supportées."""
    return list(SIGNAUX.keys())


def get_categories_architecture(architecture: str) -> list:
    """
    Retourne les catégories de dossiers pour une architecture.
    
    Args:
        architecture: Nom de l'architecture
        
    Returns:
        Liste des noms de dossiers
    """
    patterns = SIGNAUX.get(architecture, {})
    categories = []
    
    for categorie, signaux in patterns.items():
        if categorie in ("frameworks", "imports", "decorateurs", "dependances", "classes"):
            continue
        if signaux:
            categories.append(signaux[0]["nom"])
    
    return categories


def get_description_architecture(architecture: str) -> str:
    """
    Retourne une description textuelle d'une architecture.
    
    Args:
        architecture: Nom de l'architecture
        
    Returns:
        Description
    """
    descriptions = {
        "MVC": "Pattern Model-View-Controller classique",
        "MVP": "Pattern Model-View-Presenter",
        "MVVM": "Pattern Model-View-ViewModel avec data binding",
        "COUCHES": "Architecture en couches (Layered)",
        "CLEAN": "Clean Architecture avec Use Cases",
        "MICROSERVICES": "Architecture Microservices",
        "MONOLITHIQUE": "Application monolithique",
    }
    return descriptions.get(architecture, f"Architecture {architecture}")