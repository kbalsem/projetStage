from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Utilisateurs(db.Model):
    __tablename__ = 'utilisateurs'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    theme_preference = db.Column(db.String(20), default='dark')
    date_inscription = db.Column(db.DateTime, default=datetime.utcnow)
    
    historiques = db.relationship('Historique', backref='utilisateur', lazy=True)
    
    def __repr__(self):
        return f'<Utilisateurs {self.nom}>'

class Historique(db.Model):
    __tablename__ = 'historique'

    id  = db.Column(db.Integer, primary_key=True)
    utilisateurs_id  = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    url  = db.Column(db.String(500), nullable=False)
    repo_name  = db.Column(db.String(200))
    author = db.Column(db.String(200))
    branch  = db.Column(db.String(100))
    commits  = db.Column(db.Integer, default=0)
    stars  = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    licence  = db.Column(db.String(100))
    consulte  = db.Column(db.Boolean, default=False)
    date_analyse  = db.Column(db.DateTime, default=datetime.utcnow)
    resume_ia  = db.Column(db.Text)
    langages  = db.Column(db.Text)
    fichiers_count  = db.Column(db.Integer, default=0)
    architecture = db.Column(db.Text)
    documentation_preview  = db.Column(db.Text)

    # ── Nouveaux champs pour l'orchestration en arrière-plan ──
    statut                  = db.Column(db.String(20), default='en_cours')   # en_cours | termine | erreur
    chemin_doc               = db.Column(db.String(500))                     # ex: output/flask-sqlalchemy
    confiance_architecture   = db.Column(db.String(20))                      # élevée | moyenne | faible
    message_erreur           = db.Column(db.Text)

    def __repr__(self):
        return f'<Historique {self.repo_name} - {self.date_analyse}>'