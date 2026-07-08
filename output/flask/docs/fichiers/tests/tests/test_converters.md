# tests/tests/test_converters.py

## 📋 Résumé
Contient 2 classe(s) : ListConverter, ContextConverter. Expose 4 fonction(s). Utilise 3 import(s)

**Langage** : python
**Chemin dans l'architecture cible** : `tests/tests/test_converters.py`

## 🏗️ Classes (2)
- **ListConverter** (ligne 9)
  - `to_python(self, value)`
  - `to_url(self, value)`
- **ContextConverter** (ligne 30)
  - `to_python(self, value)`
## ⚡ Fonctions (4)
- **test_custom_converters(app, client)** (ligne 8)
- **index(args)** (ligne 20)
- **test_context_available(app, client)** (ligne 29)
- **index(name)** (ligne 39)
## 📦 Imports
- `from flask import session`
- `from werkzeug.routing import BaseConverter`
- `from flask import url_for`
