# tests/tests/test_reqctx.py

## 📋 Résumé
Contient 5 classe(s) : SessionError, FailingSessionInterface, CustomFlask. Expose 25 fonction(s). Utilise 3 import(s)

**Langage** : python
**Chemin dans l'architecture cible** : `tests/tests/test_reqctx.py`

## 🏗️ Classes (5)
- **SessionError** (ligne 178)
- **FailingSessionInterface** (ligne 181)
  - `open_session(self, app, request)`
- **CustomFlask** (ligne 185)
- **PathAwareSessionInterface** (ligne 204)
  - `get_cookie_name(self, app)`
- **CustomFlask** (ligne 211)
## ⚡ Fonctions (25)
- **test_teardown_on_pop(app)** (ligne 15)
- **end_of_request(exception)** (ligne 19)
- **test_teardown_with_previous_exception(app)** (ligne 29)
- **end_of_request(exception)** (ligne 33)
- **test_teardown_with_handled_exception(app)** (ligne 46)
## 📦 Imports
- `import collections.abc as cabc`
- `from flask.sessions import SecureCookieSessionInterface`
- `import warnings`
