# tests/tests/test_basic.py

## 📋 Résumé
Contient 7 classe(s) : PrefixPathMiddleware, MyException, ForbiddenSubclass. Expose 245 fonction(s). Utilise 3 import(s)

**Langage** : python
**Chemin dans l'architecture cible** : `tests/tests/test_basic.py`

## 🏗️ Classes (7)
- **PrefixPathMiddleware** (ligne 289)
  - `__init__(self, app, prefix)`
  - `__call__(self, environ, start_response)`
- **MyException** (ligne 971)
- **ForbiddenSubclass** (ligne 987)
- **E1** (ligne 1019)
- **E2** (ligne 1022)
## ⚡ Fonctions (245)
- **test_options_work(app, client)** (ligne 32)
- **index()** (ligne 34)
- **test_options_on_multiple_rules(app, client)** (ligne 42)
- **index()** (ligne 44)
- **index_put()** (ligne 48)
## 📦 Imports
- `import importlib.metadata`
- `from werkzeug.routing import BuildError`
- `from flask.debughelpers import DebugFilesKeyError`
