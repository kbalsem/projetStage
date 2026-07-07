# utils/db_helpers.py — Version finale

from flask import session, flash, redirect, url_for, jsonify
from models import db, Historique


def get_historique_or_403(historique_id):
    """Pour les routes WEB : retourne (historique, None) ou (None, redirect)."""
    historique = db.session.get(Historique, historique_id)
    if not historique or historique.utilisateurs_id != session['user_id']:
        flash("Accès non autorisé", "danger")
        return None, redirect(url_for('dashboard'))
    return historique, None


def get_historique_or_403_api(historique_id):
    """Pour les routes API : retourne (historique, None) ou (None, jsonify 403)."""
    historique = db.session.get(Historique, historique_id)
    if not historique or historique.utilisateurs_id != session['user_id']:
        return None, jsonify({"error": "Accès non autorisé"}), 403
    return historique, None