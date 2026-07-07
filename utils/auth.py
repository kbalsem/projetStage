# utils/auth.py
from functools import wraps
from flask import session, flash, redirect, url_for


def login_required(f):
    """Décorateur qui vérifie que l'utilisateur est connecté."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Veuillez vous connecter", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function