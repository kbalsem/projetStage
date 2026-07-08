# tests/tests/test_user_error_handler.py

## 📋 Résumé
Contient 8 classe(s) : CustomException, ParentException, ChildExceptionUnregistered. Expose 32 fonction(s). Utilise 3 import(s)

**Langage** : python
**Chemin dans l'architecture cible** : `tests/tests/test_user_error_handler.py`

## 🏗️ Classes (8)
- **CustomException** (ligne 11)
- **ParentException** (ligne 62)
- **ChildExceptionUnregistered** (ligne 65)
- **ChildExceptionRegistered** (ligne 68)
- **ForbiddenSubclassRegistered** (ligne 101)
## ⚡ Fonctions (32)
- **test_error_handler_no_match(app, client)** (ligne 10)
- **custom_exception_handler(e)** (ligne 15)
- **handle_500(e)** (ligne 30)
- **custom_test()** (ligne 44)
- **key_error()** (ligne 48)
## 📦 Imports
- `from werkzeug.exceptions import NotFound`
- `from werkzeug.exceptions import InternalServerError`
- `from werkzeug.exceptions import Forbidden`
