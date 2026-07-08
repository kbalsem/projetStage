# src/flask/globals.py

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