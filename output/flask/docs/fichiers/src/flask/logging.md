# src/flask/logging.py

## 📋 Résumé
Gestion des erreurs et création de loggers pour les applications Flask.

## 🎯 Rôle du fichier
Ce fichier fournit des fonctions pour gérer les erreurs et créer des loggers pour les applications Flask. Il s'agit d'un outil essentiel pour la mise en production et le débogage de vos applications.

## 🏗️ Classes et méthodes
Aucune classe ou méthode n'est définie dans ce fichier.

## ⚡ Fonctions principales
* `wsgi_errors_stream()`: permet de gérer les erreurs WSGI.
* `has_level_handler(logger: logging.Logger)`: vérifie si un gestionnaire d'enregistrement est défini pour un logger.
* `create_logger(app: App)`: crée un nouveau logger pour une application Flask.

## 📦 Dépendances et imports
* Importation de la bibliothèque `logging`.
* Importation du module `sys` pour utiliser les fonctions système.
* Importation de la bibliothèque `typing` pour utiliser le type checking.
* Importation du module `werkzeug.local` pour utiliser les objets `LocalProxy`.

### FICHIER: src/flask/typing.py