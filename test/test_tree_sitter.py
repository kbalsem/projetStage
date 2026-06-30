# tests/test_tree_sitter.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from generation.analyzer import extraire_infos_depuis_code  # ajuste le nom du module


def test_extraction_python():
    print("\n=== TEST : Extraction tree-sitter sur du code Python ===")
    code = '''
import os
from app.models import User

class UserController:
    def get_user(self, user_id):
        return User.find(user_id)

    def create_user(self, name, email):
        return User.create(name, email)


def helper_function(x, y):
    return x + y
'''
    resultat = extraire_infos_depuis_code(code, "controllers/user.py", "python")
    print("Classes :", resultat["classes"])
    print("Fonctions :", resultat["fonctions"])
    print("Imports :", resultat["imports"])

    assert len(resultat["classes"]) == 1
    assert resultat["classes"][0]["nom"] == "UserController"
    assert len(resultat["classes"][0]["methodes"]) == 2
    assert len(resultat["fonctions"]) == 1
    print("✓ OK")


if __name__ == "__main__":
    test_extraction_python()