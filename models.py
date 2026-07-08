# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from utils.tree_utils import aplatir_arbre

db = SQLAlchemy()


class Utilisateurs(db.Model):
    __tablename__ = 'utilisateurs'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    theme_preference = db.Column(db.String(20), default='dark')
    date_inscription = db.Column(db.DateTime, default=datetime.utcnow)

    historiques = db.relationship('Historique', backref='utilisateur', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Utilisateurs {self.nom}>'


class Historique(db.Model):
    __tablename__ = 'historique'
    __table_args__ = (
        db.Index('idx_historique_utilisateur', 'utilisateurs_id'),
        db.Index('idx_historique_statut', 'statut'),
    )

    id = db.Column(db.Integer, primary_key=True)
    utilisateurs_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    repo_name = db.Column(db.String(200))
    author = db.Column(db.String(200))
    branch = db.Column(db.String(100))
    commits = db.Column(db.Integer, default=0)
    stars = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    licence = db.Column(db.String(100))
    consulte = db.Column(db.Boolean, default=False)
    date_analyse = db.Column(db.DateTime, default=datetime.utcnow)
    resume_ia = db.Column(db.Text)
    langages = db.Column(db.Text)
    fichiers_count = db.Column(db.Integer, default=0)
    architecture = db.Column(db.String(100))
    confiance_architecture = db.Column(db.String(20))
    documentation_preview = db.Column(db.Text)
    chemin_doc = db.Column(db.String(500))
    tree_json = db.Column(db.Text, nullable=True)
    statut = db.Column(db.String(20), default='en_cours')
    message_erreur = db.Column(db.Text)
    chemin_site_html = db.Column(db.String(500))

    def get_langages(self):
        try:
            return json.loads(self.langages or '[]')
        except (json.JSONDecodeError, TypeError):
            return []


    def get_tree(self):
        try:
            return json.loads(self.tree_json or '{}')
        except (json.JSONDecodeError, TypeError):
            return {}


    def get_fichiers_liste(self):
        return aplatir_arbre(self.get_tree(), inclure_racine=False)

    def to_dict(self):
        return {
            'id': self.id,
            'repo_name': self.repo_name,
            'url': self.url,
            'architecture': self.architecture,
            'statut': self.statut,
            'date_analyse': self.date_analyse.isoformat() if self.date_analyse else None,
            'commits': self.commits,
            'stars': self.stars,
            'fichiers_count': self.fichiers_count,
            'langages': self.get_langages(),
        }

    def __repr__(self):
        return f'<Historique {self.repo_name} - {self.date_analyse}>'