# tests/tests/test_helpers.py

## 📋 Résumé
Contient 13 classe(s) : FakePath, PyBytesIO, TestSendfile. Expose 9 fonction(s). Utilise 3 import(s)

**Langage** : python
**Chemin dans l'architecture cible** : `tests/tests/test_helpers.py`

## 🏗️ Classes (13)
- **FakePath** (ligne 11)
  - `__init__(self, path)`
  - `__fspath__(self)`
- **PyBytesIO** (ligne 25)
  - `__init__(self)`
  - `__getattr__(self, name)`
- **TestSendfile** (ligne 33)
  - `test_send_file(self, app, req_ctx)`
  - `test_static_file(self, app, req_ctx)`
  - `test_send_from_directory(self, app, req_ctx)`
- **StaticFileApp** (ligne 69)
  - `get_send_file_max_age(self, filename)`
- **TestUrlFor** (ligne 94)
  - `test_url_for_with_anchor(self, app, req_ctx)`
  - `index()`
  - `test_url_for_with_scheme(self, app, req_ctx)`
  - `index()`
  - `test_url_for_with_scheme_not_external(self, app, req_ctx)`
## ⚡ Fonctions (9)
- **test_redirect_no_app()** (ligne 164)
- **test_redirect_with_app(app)** (ligne 170)
- **redirect(location)** (ligne 171)
- **test_abort_no_app()** (ligne 180)
- **test_app_aborter_class()** (ligne 188)
## 📦 Imports
- `import io`
- `from flask.views import MethodView`
- `import os`
