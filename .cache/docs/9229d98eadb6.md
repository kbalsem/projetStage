# src/flask/helpers.py

## 📋 Résumé
Helper functions for Flask applications.

## 🎯 Rôle du fichier
This file provides various helper functions to simplify the development of Flask applications. These functions can be used to streamline tasks such as error handling, environment loading, and context management.

## 🏗️ Classes et méthodes

* _CollectErrors: a class for collecting errors in a Flask application.
* get_debug_flag(): returns the debug flag for the current request.
* get_load_dotenv(default: bool = True): loads the .env file if it exists or returns None otherwise.
* stream_with_context(generator_or_function: t.Iterator[t.AnyStr]): streams a generator or function with context.
* stream_with_context(generator_or_function: t.Callable[..., t.Iterator[t.AnyStr]]): streams a callable that returns an iterator of strings.
* stream_with_context(generator_or_function: t.Iterator[t.AnyStr] | t.Callable[..., t.Iterator[t.AnyStr]]): streams a generator or function with context.

## ⚡ Fonctions principales

* get_debug_flag()
* get_load_dotenv()
* stream_with_context()

## 📦 Dépendances et imports

* from .wrappers import Response
* from werkzeug.wrappers import Response as BaseResponse
* from werkzeug.exceptions import abort as _wz_abort
* from __future__ import annotations
* importlib.util
* os
* sys
* typing as t
* datetime
* functools
* types

### FILE: src/flask/globals.py
## 📋 Résumé
Global variables and context management for Flask applications.

## 🎯 Rôle du fichier
This file provides global variables and context management functionality for Flask applications. It allows developers to access and manipulate application-wide settings and contexts.

## 🏗️ Classes et méthodes

* ProxyMixin: a mixin class for creating proxy objects.
* FlaskProxy: a proxy object for the current Flask application.
* AppContextProxy: a proxy object for the current application context.
* _AppCtxGlobalsProxy: a proxy object for the current application context variables.
* RequestProxy: a proxy object for the current request.

## ⚡ Fonctions principales

* __getattr__(name: str): gets an attribute from the current application context or raises an AttributeError if it does not exist.

## 📦 Dépendances et imports

* from .app import Flask
* from werkzeug.local import LocalProxy
* import typing as t
* contextvars
* functools

### RÈGLES STRICTES - Format EXACT pour chaque fichier: