# tests/tests/type_check/typing_error_handler.py

## 📋 Résumé
Expose 4 fonction(s). Utilise 3 import(s)

**Langage** : python
**Chemin dans l'architecture cible** : `tests/tests/type_check/typing_error_handler.py`

## ⚡ Fonctions (4)
- **handle_400(e: BadRequest)** (ligne 16)
- **handle_custom(e: ValueError)** (ligne 21)
- **handle_accept_base(e: Exception)** (ligne 26)
- **handle_multiple(e: BadRequest | NotFound)** (ligne 32)
## 📦 Imports
- `from flask import Flask`
- `from werkzeug.exceptions import NotFound`
- `from http import HTTPStatus`
