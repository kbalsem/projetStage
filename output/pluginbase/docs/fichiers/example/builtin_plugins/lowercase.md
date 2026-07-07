# example/builtin_plugins/lowercase.py

**Rôle**: Convert strings to lowercase
**Classes principales**: None
**Fonctions clés**: make_lowercase, setup
**Intégration**: Part of the MVC architecture, used for formatting text

```
def make_lowercase(s):
    return s.lower()


def setup(app):
    app.register_formatter('lowercase', make_lowercase)
```

### FILE: example/builtin_plugins/uppercase.py
**Rôle**: Convert strings to uppercase
**Classes principales**: None
**Fonctions clés**: make_uppercase, setup
**Intégration**: Part of the MVC architecture, used for formatting text

```
def make_uppercase(s):
    return s.upper()


def setup(app):
    app.register_formatter('uppercase', make_uppercase)