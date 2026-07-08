# tests/tests/test_appctx.py

## 📋 Résumé
Contient 1 classe(s) : CustomRequestGlobals. Expose 34 fonction(s). Utilise 3 import(s)

**Langage** : python
**Chemin dans l'architecture cible** : `tests/tests/test_appctx.py`

## 🏗️ Classes (1)
- **CustomRequestGlobals** (ligne 163)
  - `__init__(self)`
## ⚡ Fonctions (34)
- **test_basic_url_generation(app)** (ligne 10)
- **index()** (ligne 15)
- **test_url_generation_requires_server_name(app)** (ligne 23)
- **test_url_generation_without_context_fails()** (ligne 29)
- **test_request_context_means_app_context(app)** (ligne 34)
## 📦 Imports
- `from flask.globals import app_ctx`
- `import sys`
- `from flask.testing import FlaskClient`
