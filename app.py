# app.py
import os
import json
import logging
import threading
from typing import Dict, List, Tuple, Optional
import shutil
import tempfile
import yaml
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from models import db, Utilisateurs, Historique
from taches import executer_analyse, lister_fichiers_depuis_arbre
from summarize_repo import resumer_repo
from utils.auth import login_required
from utils.db_helpers import get_historique_or_403
from architecture.restructeur import construire_arbre_avec_mappings
from architecture.signaux import SIGNAUX

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

SCORE_MAX = int(os.getenv("SCORE_MAX", "210"))
SCORE_MULTIPLICATEUR_CONFIANCE = int(os.getenv("SCORE_MULTIPLICATEUR_CONFIANCE", "2"))
SEUIL_CONFLIT_CONFIANCE = int(os.getenv("SEUIL_CONFLIT_CONFIANCE", "80"))
PENALITE_CONFLIT_POINTS = int(os.getenv("PENALITE_CONFLIT_POINTS", "10"))

ARCHITECTURES_DESCRIPTIONS = {
    "MVC": "Le pattern Model-View-Controller sépare l'application en trois composants : le Modèle (données), la Vue (interface) et le Contrôleur (logique).",
    "MVVM": "Model-View-ViewModel facilite la liaison de données entre la vue et le modèle via un ViewModel.",
    "Clean Architecture": "Architecture en couches concentriques avec dépendances vers l'intérieur.",
    "Hexagonale": "Architecture Ports & Adapters qui isole le cœur applicatif derrière des interfaces.",
    "Microservices": "Architecture distribuée où chaque service est indépendant et communique via API.",
    "Layered": "Architecture en couches classique (présentation, business, données).",
    "MVP": "Model-View-Presenter — le Presenter gère toute la logique de l'interface utilisateur.",
    "COUCHES": "Architecture en couches — Présentation / Métier / Données.",
    "CLEAN": "Clean Architecture — Use Cases / Entities / Repositories.",
    "MONOLITHIQUE": "Application monolithique — structure simple sans séparation claire en modules distincts.",
}

def extraire_pourcentage_confiance(confiance_str: Optional[str]) -> int:
    if not confiance_str: return 0
    try:
        if '%' in confiance_str: return int(confiance_str.split('%')[0].split()[-1])
        else: return int(confiance_str.split()[-1])
    except (ValueError, IndexError): return 0

def calculer_radar_data(architecture_detectee: str, confiance_pct: int) -> Dict[str, int]:
    radar_data = {}
    for archi_key in SIGNAUX.keys():
        radar_data[archi_key] = confiance_pct if archi_key == architecture_detectee else 0
    return radar_data

def calculer_score_global(confiance_pct: int, nb_signaux: int, nb_conflits: int) -> int:
    score = confiance_pct * SCORE_MULTIPLICATEUR_CONFIANCE - nb_conflits * PENALITE_CONFLIT_POINTS
    return min(SCORE_MAX, max(0, score))

def get_description_architecture(architecture: Optional[str]) -> str:
    if not architecture: return "Architecture non détectée."
    for archi_key, desc in ARCHITECTURES_DESCRIPTIONS.items():
        if archi_key.lower() in architecture.lower(): return desc
    return f"Architecture '{architecture}' détectée."

def calculer_stats_transformation(mappings: List[dict]) -> Dict[str, int]:
    stats = {"nouveaux_dossiers": 0, "fichiers_deplaces": 0, "fichiers_inchanges": 0, "fichiers_supprimes": 0}
    for m in mappings:
        if m.get("type") == "directory" and m["status"] == "new": stats["nouveaux_dossiers"] += 1
        elif m["status"] == "moved": stats["fichiers_deplaces"] += 1
        elif m["status"] == "unchanged": stats["fichiers_inchanges"] += 1
        elif m["status"] == "deleted": stats["fichiers_supprimes"] += 1
    return stats

def detecter_conflits(radar_data: Dict[str, int], confiance_pct: int) -> Tuple[int, str]:
    conflits, message = 0, ""
    if confiance_pct < SEUIL_CONFLIT_CONFIANCE:
        conflits += 1; message = f"Confiance faible ({confiance_pct}%)"
    scores_eleves = [s for s in radar_data.values() if s > 60]
    if len(scores_eleves) > 1:
        conflits += 1; message = (message + " | " if message else "") + "Plusieurs architectures possibles"
    if conflits > 0: message = "⚠️ " + message
    return conflits, message

def get_architecture_fallback() -> str:
    architectures = list(SIGNAUX.keys())
    return architectures[0] if architectures else "MVC"

@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session: user = db.session.get(Utilisateurs, session['user_id'])
    return dict(current_user=user)

# ═══════════ ROUTES PUBLIQUES ═══════════
@app.route("/")
def home():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        if not email or not password: flash("Veuillez remplir tous les champs", "danger"); return render_template("login.html")
        utilisateur = Utilisateurs.query.filter_by(email=email).first()
        if utilisateur and check_password_hash(utilisateur.mot_de_passe, password):
            session['user_id'] = utilisateur.id; session['user_nom'] = utilisateur.nom; session['user_email'] = utilisateur.email
            flash(f"Bienvenue {utilisateur.nom} !", "success"); return redirect(url_for('dashboard'))
        else: flash("Email ou mot de passe incorrect", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    if request.method == "POST":
        nom = request.form.get("nom", "").strip(); email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip(); confirm_password = request.form.get("confirm_password", "").strip()
        if not nom or not email or not password: flash("Tous les champs sont obligatoires", "danger"); return render_template("register.html")
        if password != confirm_password: flash("Les mots de passe ne correspondent pas", "danger"); return render_template("register.html")
        if len(password) < 6: flash("Le mot de passe doit contenir au moins 6 caractères", "danger"); return render_template("register.html")
        if Utilisateurs.query.filter_by(email=email).first(): flash("Cet email est déjà utilisé", "danger"); return render_template("register.html")
        utilisateur = Utilisateurs(nom=nom, email=email, mot_de_passe=generate_password_hash(password))
        db.session.add(utilisateur); db.session.commit()
        flash("Inscription réussie !", "success"); return redirect(url_for('login'))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear(); flash("Déconnexion réussie", "info"); return redirect(url_for('home'))

# ═══════════ ROUTES PROTÉGÉES ═══════════
@app.route("/dashboard")
@login_required
def dashboard():
    utilisateur = db.session.get(Utilisateurs, session['user_id'])
    historiques = Historique.query.filter_by(utilisateurs_id=utilisateur.id).order_by(Historique.date_analyse.desc()).all()
    non_consultees = sum(1 for h in historiques if not h.consulte)
    return render_template("dashboard.html", utilisateurs=utilisateur, historiques=historiques, non_consultees=non_consultees)

@app.route("/analyser", methods=["POST"])
@login_required
def analyser():
    url = request.form.get("url", "").strip()
    if not url: flash("Veuillez fournir une URL valide", "danger"); return redirect(url_for('dashboard'))
    historique = Historique(utilisateurs_id=session['user_id'], url=url, statut="en_cours")
    db.session.add(historique); db.session.commit()
    thread = threading.Thread(target=executer_analyse, args=(app, historique.id, url), daemon=True)
    thread.start()
    return redirect(url_for('voir_historique', id=historique.id))

@app.route("/historique/<int:id>")
@login_required
def voir_historique(id):
    historique, erreur = get_historique_or_403(id)
    if erreur: return erreur
    if historique.statut == "en_cours": return render_template("en_cours.html", historique=historique)
    if historique.statut == "erreur": return render_template("erreur.html", error=historique.message_erreur)
    if not historique.consulte: historique.consulte = True; db.session.commit()

    arbre_original = None; arbre_nouveau = None; mappings = []
    stats_transfo = {"nouveaux_dossiers": 0, "fichiers_deplaces": 0, "fichiers_inchanges": 0, "fichiers_supprimes": 0}
    radar_data = {}; confiance_pct = 0

    if historique.tree_json:
        try:
            arbre_original = json.loads(historique.tree_json)
            architecture = historique.architecture or get_architecture_fallback()
            arbre_nouveau, mappings = construire_arbre_avec_mappings(arbre_original, architecture)
            stats_transfo = calculer_stats_transformation(mappings)
        except Exception as e: logger.error(f"Erreur construction arbre cible: {e}")

    confiance_pct = extraire_pourcentage_confiance(historique.confiance_architecture)
    architecture = historique.architecture
    if confiance_pct > 0 and architecture: radar_data = calculer_radar_data(architecture, confiance_pct)
    signaux_detectes = len([s for s in radar_data.values() if s > 0])
    conflits_detectes, message_conflit = detecter_conflits(radar_data, confiance_pct)
    score_total = calculer_score_global(confiance_pct, signaux_detectes, conflits_detectes)

    analyse = {
        "id": historique.id, "repo_name": historique.repo_name, "date_analyse": historique.date_analyse,
        "resume_ia": historique.resume_ia, "commits": historique.commits, "stars": historique.stars,
        "langages": json.loads(historique.langages or "[]"), "fichiers": historique.fichiers_count,
        "architecture": architecture or "Non détectée", "confiance_architecture": historique.confiance_architecture or "0%",
        "confiance_pourcentage": confiance_pct, "description_architecture": get_description_architecture(architecture),
        "documentation_preview": historique.documentation_preview,
        "documentation_disponible": bool(historique.chemin_site_html and os.path.isdir(historique.chemin_site_html)),
        "arbre_original": arbre_original, "arbre_nouveau": arbre_nouveau, "mappings": mappings,
        "stats_transfo": stats_transfo, "radar_data": radar_data, "score_total": score_total,
        "score_max": SCORE_MAX, "signaux_detectes": signaux_detectes, "conflits_detectes": conflits_detectes,
        "message_conflit": message_conflit
    }
    return render_template("resultat.html", analyse=analyse)

@app.route("/historique/<int:id>/statut")
@login_required
def statut_historique(id):
    historique = db.session.get(Historique, id)
    if not historique or historique.utilisateurs_id != session['user_id']: return jsonify({"error": "Accès non autorisé"}), 403
    return jsonify({"statut": historique.statut, "repo_name": historique.repo_name})

@app.route("/historique/supprimer/<int:id>", methods=["POST"])
@login_required
def supprimer_historique(id):
    historique = db.session.get(Historique, id)
    if not historique: return jsonify({"error": "Historique introuvable"}), 404
    if historique.utilisateurs_id != session['user_id']: return jsonify({"error": "Accès non autorisé"}), 403
    try: db.session.delete(historique); db.session.commit(); flash("Analyse supprimée", "success"); return jsonify({"success": True})
    except Exception as e: db.session.rollback(); return jsonify({"error": str(e)}), 500

@app.route("/historique/supprimer-tout", methods=["POST"])
@login_required
def supprimer_tout_historique():
    try: Historique.query.filter_by(utilisateurs_id=session['user_id']).delete(); db.session.commit(); flash("Tout supprimé", "success"); return jsonify({"success": True})
    except Exception as e: db.session.rollback(); return jsonify({"error": str(e)}), 500

@app.route("/api/theme", methods=["POST"])
@login_required
def set_theme():
    data = request.get_json(); theme = data.get('theme', 'dark')
    if theme not in ['light', 'dark']: return jsonify({"error": "Thème invalide"}), 400
    utilisateur = db.session.get(Utilisateurs, session['user_id'])
    if utilisateur:
        try: utilisateur.theme_preference = theme; db.session.commit()
        except Exception: pass
    return jsonify({"success": True, "theme": theme})

@app.route("/historique/<int:historique_id>/arborescence")
@login_required
def arborescence(historique_id):
    historique, erreur = get_historique_or_403(historique_id)
    if erreur: return jsonify({"error": "Accès non autorisé"}), 403
    if not historique.tree_json: return jsonify({"name": historique.repo_name or "Projet", "type": "directory", "children": []})
    try: return jsonify(json.loads(historique.tree_json))
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/historique/<int:id>/generer-resume-ia", methods=["POST"])
@login_required
def generer_resume_ia(id):
    historique, erreur = get_historique_or_403(id)
    if erreur: return jsonify({"succes": False, "erreur": "Accès non autorisé"}), 403
    data = {"repo_name": historique.repo_name, "author": historique.author, "branch": historique.branch,
            "commits": historique.commits, "stars": historique.stars, "licence": historique.licence,
            "description": historique.description, "fichiers": lister_fichiers_depuis_arbre(historique.get_tree())}
    try:
        resume = resumer_repo(data); historique.resume_ia = resume; db.session.commit()
        return jsonify({"succes": True, "resume": resume})
    except Exception as e: return jsonify({"succes": False, "erreur": str(e)}), 502

@app.route("/historique/<int:historique_id>/arborescence-cible")
@login_required
def arborescence_cible(historique_id):
    historique, erreur = get_historique_or_403(historique_id)
    if erreur: return jsonify({"error": "Accès non autorisé"}), 403
    if not historique.tree_json: return jsonify({"name": "Structure cible", "type": "directory", "children": []})
    try:
        arbre_original = json.loads(historique.tree_json)
        architecture = historique.architecture or get_architecture_fallback()
        arbre_cible, _, _ = construire_arbre_avec_mappings(arbre_original, architecture)
        return jsonify(arbre_cible)
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/historique/<int:id>/telecharger")
@login_required
def telecharger_depot(id):
    historique, erreur = get_historique_or_403(id)
    if erreur: return erreur
    if not historique.chemin_doc or not os.path.isdir(historique.chemin_doc): flash("Non disponible", "warning"); return redirect(url_for('voir_historique', id=id))
    chemin_zip = os.path.join(tempfile.gettempdir(), f"{historique.repo_name}_documente")
    shutil.make_archive(chemin_zip, 'zip', historique.chemin_doc); chemin_zip += '.zip'
    return send_from_directory(os.path.dirname(chemin_zip), os.path.basename(chemin_zip), as_attachment=True, download_name=f"{historique.repo_name}_documente.zip")

# ═══════════ ROUTES DOCUMENTATION ═══════════
@app.route("/historique/<int:id>/documentation/")
@app.route("/historique/<int:id>/documentation/<path:filename>")
@login_required
def voir_documentation(id, filename="index.html"):
    historique, erreur = get_historique_or_403(id)
    if erreur: return erreur
    if not historique.chemin_site_html or not os.path.isdir(historique.chemin_site_html): flash("Non disponible", "warning"); return redirect(url_for('voir_historique', id=id))
    racine = historique.chemin_site_html; chemin_absolu = os.path.join(racine, filename)
    if os.path.isdir(chemin_absolu):
        index_path = os.path.join(chemin_absolu, "index.html")
        if os.path.isfile(index_path): return send_from_directory(chemin_absolu, "index.html")
        return "Page introuvable", 404
    if not os.path.isfile(chemin_absolu) and not filename.endswith('.html'):
        if os.path.isfile(chemin_absolu + '.html'): return send_from_directory(racine, filename + '.html')
    return send_from_directory(racine, filename)

@app.route('/historique/<int:id>/documentation/page/<path:sous_chemin>')
@login_required
def voir_page_documentation(id, sous_chemin):
    historique, erreur = get_historique_or_403(id)
    if erreur: return erreur
    if not historique.chemin_site_html or not os.path.isdir(historique.chemin_site_html): flash("Non disponible", "warning"); return redirect(url_for('voir_historique', id=id))
    return send_from_directory(historique.chemin_site_html, sous_chemin)

@app.route('/historique/<int:id>/documentation/assets/<path:filename>')
@login_required
def voir_assets_documentation(id, filename):
    historique, erreur = get_historique_or_403(id)
    if erreur: return erreur
    if not historique.chemin_site_html: return "Non disponible", 404
    for dossier in ['', 'assets', 'stylesheets', 'javascripts', 'fonts', 'images', 'search']:
        chemin = os.path.join(historique.chemin_site_html, dossier)
        if os.path.isfile(os.path.join(chemin, filename)): return send_from_directory(chemin, filename)
    for root, dirs, files in os.walk(historique.chemin_site_html):
        if filename in files: return send_from_directory(root, filename)
    return "Fichier non trouvé", 404

@app.route('/historique/<int:id>/documentation/structure')
@login_required
def structure_documentation(id):
    historique, erreur = get_historique_or_403(id)
    if erreur: return jsonify({"error": "Accès non autorisé"}), 403
    if not historique.chemin_site_html or not os.path.isdir(historique.chemin_site_html): return jsonify([])
    racine_doc = os.path.dirname(historique.chemin_site_html)
    chemin_mkdocs_yml = os.path.join(racine_doc, 'mkdocs.yml')
    if os.path.exists(chemin_mkdocs_yml):
        try:
            with open(chemin_mkdocs_yml, 'r', encoding='utf-8') as f: config = yaml.safe_load(f)
            arbre = _convertir_nav_mkdocs(config.get('nav', []))
            if arbre: return jsonify(arbre)
        except Exception as e: logger.warning(f"Erreur mkdocs.yml: {e}")
    return jsonify(_scanner_dossier_site_complet(historique.chemin_site_html))

def _convertir_nav_mkdocs(nav, base=''):
    resultat = []
    for item in nav:
        if isinstance(item, dict):
            for label, valeur in item.items():
                if isinstance(valeur, str): resultat.append({"label": label, "url": valeur.replace('.md', '.html'), "enfants": []})
                elif isinstance(valeur, list): resultat.append({"label": label, "url": None, "enfants": _convertir_nav_mkdocs(valeur)})
        elif isinstance(item, str): resultat.append({"label": item, "url": item, "enfants": []})
    return resultat

def _scanner_dossier_site_complet(chemin_site):
    arbre = []
    try:
        for entree in sorted(os.listdir(chemin_site)):
            chemin_complet = os.path.join(chemin_site, entree)
            if entree.startswith('.') or entree in ('assets', 'search', 'stylesheets', 'javascripts', 'fonts', 'img'): continue
            if os.path.isdir(chemin_complet):
                enfants = _scanner_dossier_site_complet(chemin_complet)
                if enfants: arbre.append({"label": entree.replace('_', ' ').title(), "url": None, "enfants": enfants})
            elif entree.endswith('.html'):
                label = entree.replace('.html', '').replace('_', ' ').title()
                if entree == 'index.html': label = 'Accueil'
                chemin_relatif = os.path.relpath(chemin_complet, chemin_site).replace('\\', '/')
                arbre.append({"label": label, "url": chemin_relatif, "enfants": []})
    except Exception as e: logger.error(f"Erreur scan: {e}")
    return arbre

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)