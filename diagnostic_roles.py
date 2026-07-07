# diagnostic_roles.py
import json
from app import app
from models import db, Historique

with app.app_context():
    h = db.session.get(Historique, 22)
    arbre = json.loads(h.tree_json)

    def lister(noeud, chemin_parent=""):
        nom = noeud.get("name", "")
        chemin = f"{chemin_parent}/{nom}" if chemin_parent else nom

        if noeud.get("type") == "file":
            print(f"{chemin}  ->  role={noeud.get('role')}")
        else:
            for enfant in noeud.get("children", []):
                lister(enfant, chemin)

    lister(arbre)