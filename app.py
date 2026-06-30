from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import db, Utilisateurs, Historique
from scanners.scanner_router import analyser_repo
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime
import logging
import json
from summarize_repo import resumer_repo, extraire_extensions
from dotenv import load_dotenv
import threading
from taches import executer_analyse
from comparateur_architecture import construire_comparaison

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/gitdoc'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    if not Utilisateurs.query.filter_by(email='admin@example.com').first():
        admin = Utilisateurs(
            nom='Administrateur',
            email='admin@example.com',
            mot_de_passe=generate_password_hash('admin123')
        )
        db.session.add(admin)
        db.session.commit()
        logger.info("Admin créé: admin@example.com / admin123")

# ════════════════════════════════════════════════
#   CONTEXT PROCESSOR
# ════════════════════════════════════════════════

@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = db.session.get(Utilisateurs, session['user_id'])
    return dict(current_user=user)

# ════════════════════════════════════════════════
#   ROUTES
# ════════════════════════════════════════════════

@app.route("/")
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Veuillez remplir tous les champs", "danger")
            return render_template("login.html")

        utilisateur = Utilisateurs.query.filter_by(email=email).first()

        if utilisateur and check_password_hash(utilisateur.mot_de_passe, password):
            session['user_id'] = utilisateur.id
            session['user_nom'] = utilisateur.nom
            session['user_email'] = utilisateur.email
            flash(f"Bienvenue {utilisateur.nom} !", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Email ou mot de passe incorrect", "danger")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not nom or not email or not password:
            flash("Tous les champs sont obligatoires", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Les mots de passe ne correspondent pas", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Le mot de passe doit contenir au moins 6 caractères", "danger")
            return render_template("register.html")

        if Utilisateurs.query.filter_by(email=email).first():
            flash("Cet email est déjà utilisé", "danger")
            return render_template("register.html")

        utilisateur = Utilisateurs(
            nom=nom,
            email=email,
            mot_de_passe=generate_password_hash(password)
        )
        db.session.add(utilisateur)
        db.session.commit()

        flash("Inscription réussie ! Connectez-vous", "success")
        return redirect(url_for('login'))

    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        flash("Veuillez vous connecter", "warning")
        return redirect(url_for('login'))

    utilisateurs = db.session.get(Utilisateurs, session['user_id'])
    historiques = Historique.query.filter_by(
        utilisateurs_id=utilisateurs.id
    ).order_by(Historique.date_analyse.desc()).all()

    non_consultees = sum(1 for h in historiques if not h.consulte)

    return render_template("dashboard.html",
        utilisateurs=utilisateurs,
        historiques=historiques,
        non_consultees=non_consultees
    )

@app.route("/analyser", methods=["POST"])
def analyser():
    if 'user_id' not in session:
        flash("Veuillez vous connecter", "warning")
        return redirect(url_for('login'))

    url = request.form.get("url", "").strip()
    if not url:
        flash("Veuillez fournir une URL valide", "danger")
        return redirect(url_for('dashboard'))

    # Insert minimal immédiat — le reste sera rempli par le thread à la fin
    historique = Historique(
        utilisateurs_id = session['user_id'],
        url             = url,
        statut          = "en_cours",
    )
    db.session.add(historique)
    db.session.commit()

    # Lancement du pipeline en arrière-plan
    thread = threading.Thread(
        target=executer_analyse,
        args=(app, historique.id, url),
        daemon=True
    )
    thread.start()

    return redirect(url_for('voir_historique', id=historique.id))

@app.route("/historique/<int:id>")
def voir_historique(id):
    if 'user_id' not in session:
        flash("Veuillez vous connecter", "warning")
        return redirect(url_for('login'))

    historique = db.session.get(Historique, id)
    if not historique or historique.utilisateurs_id != session['user_id']:
        flash("Accès non autorisé", "danger")
        return redirect(url_for('dashboard'))

    if historique.statut == "en_cours":
        return render_template("en_cours.html", historique=historique)

    if historique.statut == "erreur":
        return render_template("erreur.html", error=historique.message_erreur)

    # statut == "termine"
    if not historique.consulte:
        historique.consulte = True
        db.session.commit()

    analyse = {
        "id":                     historique.id,
        "repo_name":              historique.repo_name,
        "date_analyse":           historique.date_analyse,
        "resume_ia":              historique.resume_ia,
        "commits":                historique.commits,
        "stars":                  historique.stars,
        "langages":               json.loads(historique.langages or "[]"),
        "fichiers":               historique.fichiers_count,
        "architecture":           historique.architecture,
        "confiance_architecture": historique.confiance_architecture,
        "documentation_preview":  historique.documentation_preview,
    }

    return render_template("resultat.html", analyse=analyse)

@app.route("/historique/<int:id>/statut")
def statut_historique(id):
    if 'user_id' not in session:
        return jsonify({"error": "Non authentifié"}), 401

    historique = db.session.get(Historique, id)
    if not historique or historique.utilisateurs_id != session['user_id']:
        return jsonify({"error": "Accès non autorisé"}), 403

    return jsonify({
        "statut": historique.statut,
        "repo_name": historique.repo_name,
    })

@app.route("/historique/supprimer/<int:id>", methods=["POST"])
def supprimer_historique(id):
    if 'user_id' not in session:
        return jsonify({"error": "Non authentifié"}), 401

    historique = db.session.get(Historique, id)
    if not historique:
        return jsonify({"error": "Historique introuvable"}), 404
    if historique.utilisateurs_id != session['user_id']:
        return jsonify({"error": "Accès non autorisé"}), 403

    try:
        db.session.delete(historique)
        db.session.commit()
        flash("Analyse supprimée avec succès", "success")
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/historique/supprimer-tout", methods=["POST"])
def supprimer_tout_historique():
    if 'user_id' not in session:
        return jsonify({"error": "Non authentifié"}), 401

    try:
        Historique.query.filter_by(utilisateurs_id=session['user_id']).delete()
        db.session.commit()
        flash("Toutes les analyses ont été supprimées", "success")
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/logout")
def logout():
    session.clear()
    flash("Déconnexion réussie", "info")
    return redirect(url_for('home'))

@app.route("/api/theme", methods=["POST"])
def set_theme():
    if 'user_id' not in session:
        return jsonify({"error": "Non authentifié"}), 401

    data = request.get_json()
    theme = data.get('theme', 'dark')

    if theme not in ['light', 'dark']:
        return jsonify({"error": "Thème invalide"}), 400

    utilisateur = db.session.get(Utilisateurs, session['user_id'])
    if utilisateur:
        try:
            utilisateur.theme_preference = theme
            db.session.commit()
        except:
            pass

    return jsonify({"success": True, "theme": theme})

@app.route("/historique/<int:id>/comparaison-architecture")
def comparaison_architecture(id):
    historique = Historique.query.get_or_404(id)
    
    # Adapte selon où tu stockes la liste des dossiers détectés
    # (probablement dans un champ JSON ou dans resultat_scoring sauvegardé)
    dossiers_reels = json.loads(historique.dossiers_detectes or "[]")  
    architecture   = historique.architecture

    comparaison = construire_comparaison(dossiers_reels, architecture)
    return jsonify(comparaison)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)