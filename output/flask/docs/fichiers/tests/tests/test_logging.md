# tests/tests/test_logging.py

## 📋 Résumé
Expose 9 fonction(s). Utilise 3 import(s)

**Langage** : python
**Chemin dans l'architecture cible** : `tests/tests/test_logging.py`

## ⚡ Fonctions (9)
- **reset_logging(pytestconfig)** (ligne 13)
- **test_logger(app)** (ligne 36)
- **test_logger_debug(app)** (ligne 42)
- **test_existing_handler(app)** (ligne 48)
- **test_wsgi_errors_stream(app, client)** (ligne 54)
## 📦 Imports
- `from flask.logging import wsgi_errors_stream`
- `from io import StringIO`
- `import sys`
