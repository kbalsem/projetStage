# tests/tests/test_async.py

## 📋 Résumé
Contient 4 classe(s) : AppError, BlueprintError, AsyncView. Expose 16 fonction(s). Utilise 3 import(s)

**Langage** : python
**Chemin dans l'architecture cible** : `tests/tests/test_async.py`

## 🏗️ Classes (4)
- **AppError** (ligne 14)
- **BlueprintError** (ligne 18)
- **AsyncView** (ligne 22)
  - `dispatch_request(self)`
- **AsyncMethodView** (ligne 30)
  - `get(self)`
  - `post(self)`
## ⚡ Fonctions (16)
- **_async_app()** (ligne 41)
- **index()** (ligne 46)
- **handle(_)** (ligne 51)
- **error()** (ligne 55)
- **bp_index()** (ligne 61)
## 📦 Imports
- `from flask import Blueprint`
- `from flask.views import MethodView`
- `import asyncio`
