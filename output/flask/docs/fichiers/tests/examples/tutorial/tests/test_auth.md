# tests/examples/tutorial/tests/test_auth.py

## 📋 Résumé
Expose 5 fonction(s). Utilise 3 import(s)

**Langage** : python
**Chemin dans l'architecture cible** : `tests/examples/tutorial/tests/test_auth.py`

## ⚡ Fonctions (5)
- **test_register(client, app)** (ligne 8)
- **test_register_validate_input(client, username, password, message)** (ligne 32)
- **test_login(client, auth)** (ligne 39)
- **test_login_validate_input(auth, username, password, message)** (ligne 59)
- **test_logout(client, auth)** (ligne 64)
## 📦 Imports
- `import pytest`
- `from flask import session`
- `from flaskr.db import get_db`
