# tests/tests/test_blueprints.py

## 📋 Résumé
Contient 3 classe(s) : MyDecoratorException, MyFunctionException, MyBlueprint. Expose 164 fonction(s). Utilise 3 import(s)

**Langage** : python
**Chemin dans l'architecture cible** : `tests/tests/test_blueprints.py`

## 🏗️ Classes (3)
- **MyDecoratorException** (ligne 47)
- **MyFunctionException** (ligne 50)
- **MyBlueprint** (ligne 224)
  - `get_send_file_max_age(self, filename)`
## ⚡ Fonctions (164)
- **test_blueprint_specific_error_handling(app, client)** (ligne 8)
- **frontend_forbidden(e)** (ligne 14)
- **frontend_no()** (ligne 18)
- **backend_forbidden(e)** (ligne 22)
- **backend_no()** (ligne 26)
## 📦 Imports
- `from blueprintapp import app`
- `from werkzeug.http import parse_cache_control_header`
- `from jinja2 import TemplateNotFound`
