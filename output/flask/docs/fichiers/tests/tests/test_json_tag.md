# tests/tests/test_json_tag.py

## 📋 Résumé
Contient 5 classe(s) : TagDict, Foo, TagFoo. Expose 5 fonction(s). Utilise 3 import(s)

**Langage** : python
**Chemin dans l'architecture cible** : `tests/tests/test_json_tag.py`

## 🏗️ Classes (5)
- **TagDict** (ligne 33)
- **Foo** (ligne 44)
  - `__init__(self, data)`
- **TagFoo** (ligne 48)
  - `check(self, value)`
  - `to_json(self, value)`
  - `to_python(self, value)`
- **Tag1** (ligne 74)
- **Tag2** (ligne 77)
## ⚡ Fonctions (5)
- **test_dump_load_unchanged(data)** (ligne 27)
- **test_duplicate_tag()** (ligne 32)
- **test_custom_tag()** (ligne 43)
- **test_tag_interface()** (ligne 66)
- **test_tag_order()** (ligne 73)
## 📦 Imports
- `from flask.json.tag import JSONTag`
- `from markupsafe import Markup`
- `from uuid import uuid4`
