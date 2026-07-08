# tests/tests/type_check/typing_route.py

## 📋 Résumé
Contient 2 classe(s) : StatusJSON, RenderTemplateView. Expose 16 fonction(s). Utilise 3 import(s)

**Langage** : python
**Chemin dans l'architecture cible** : `tests/tests/type_check/typing_route.py`

## 🏗️ Classes (2)
- **StatusJSON** (ligne 41)
- **RenderTemplateView** (ligne 101)
  - `__init__(self: RenderTemplateView, template_name: str)`
  - `dispatch_request(self: RenderTemplateView)`
## ⚡ Fonctions (16)
- **hello_str()** (ligne 17)
- **hello_bytes()** (ligne 22)
- **hello_json()** (ligne 27)
- **hello_json_dict()** (ligne 32)
- **hello_json_list()** (ligne 37)
## 📦 Imports
- `from flask.templating import render_template`
- `from http import HTTPStatus`
- `import typing as t`
