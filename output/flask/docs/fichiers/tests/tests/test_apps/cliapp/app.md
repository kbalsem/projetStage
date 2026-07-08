# tests/tests/test_apps/cliapp/app.py

## 📋 Résumé
Contient 1 classe(s) : Flask. Expose 5 fonction(s). Utilise 3 import(s)

**Langage** : python
**Chemin dans l'architecture cible** : `tests/tests/test_apps/cliapp/app.py`

## 🏗️ Classes (1)
- **Flask** (ligne 109)
  - `__init_subclass__(cls, **kwargs: t.Any)`
  - `__init__(self, import_name: str, static_url_path: str | None = None, static_folder: str | os.PathLike[str] | None = "static", static_host: str | None = None, host_matching: bool = False, subdomain_matching: bool = False, template_folder: str | os.PathLike[str] | None = "templates", instance_path: str | None = None, instance_relative_config: bool = False, root_path: str | None = None)`
  - `get_send_file_max_age(self, filename: str | None)`
  - `send_static_file(self, filename: str)`
  - `open_resource(self, resource: str, mode: str = "rb", encoding: str | None = None)`
## ⚡ Fonctions (5)
- **_make_timedelta(value: timedelta | int | None)** (ligne 73)
- **remove_ctx(f: F)** (ligne 85)
- **wrapper(self: Flask, *args: t.Any, **kwargs: t.Any)** (ligne 86)
- **add_ctx(f: F)** (ligne 97)
- **wrapper(self: Flask, *args: t.Any, **kwargs: t.Any)** (ligne 98)
## 📦 Imports
- `from datetime import timedelta`
- `from .testing import FlaskClient`
- `from werkzeug.routing import RoutingException`
