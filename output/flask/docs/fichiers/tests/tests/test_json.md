# tests/tests/test_json.py

## 📋 Résumé
Contient 4 classe(s) : FixedOffset, X, CustomProvider. Expose 30 fonction(s). Utilise 3 import(s)

**Langage** : python
**Chemin dans l'architecture cible** : `tests/tests/test_json.py`

## 🏗️ Classes (4)
- **FixedOffset** (ligne 145)
  - `__init__(self, hours, name)`
  - `utcoffset(self, dt)`
  - `tzname(self, dt)`
  - `dst(self, dt)`
- **X** (ligne 224)
  - `__init__(self, val)`
- **CustomProvider** (ligne 234)
  - `object_hook(self, obj)`
  - `loads(self, s)`
- **ObjectWithHTML** (ligne 341)
  - `__html__(self)`
## ⚡ Fonctions (30)
- **test_bad_request_debug_message(app, client, debug)** (ligne 15)
- **post_json()** (ligne 20)
- **test_json_bad_requests(app, client)** (ligne 30)
- **return_json()** (ligne 32)
- **test_json_custom_mimetypes(app, client)** (ligne 39)
## 📦 Imports
- `import io`
- `from flask.json.provider import DefaultJSONProvider`
- `import uuid`
