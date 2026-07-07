# utils/tree_utils.py
"""
Utilitaires de manipulation d'arborescence JSON.
"""


def aplatir_arbre(arbre: dict, inclure_racine: bool = False) -> list:
    """
    Aplatie un arbre JSON en liste de chemins de fichiers relatifs.
    
    Args:
        arbre: dict avec "name", "type", "children"
        inclaire_racine: si True, inclut le nom du dossier racine dans les chemins
    
    Returns:
        Liste de chemins comme ["src/main.py", "tests/test_main.py"]
    """
    fichiers = []

    def parcourir(noeud, prefixe):
        if noeud.get("type") == "file":
            fichiers.append(prefixe + noeud["name"])
        else:
            for enfant in noeud.get("children", []):
                parcourir(enfant, prefixe + noeud["name"] + "/")

    if inclure_racine:
        parcourir(arbre, "")
    else:
        for enfant in arbre.get("children", []):
            parcourir(enfant, "")

    return fichiers


def trier_arbre(noeud: dict):
    """Trie récursivement un arbre : dossiers avant fichiers, ordre alpha."""
    if "children" in noeud:
        noeud["children"].sort(
            key=lambda x: (0 if x["type"] == "directory" else 1, x["name"].lower())
        )
        for enfant in noeud["children"]:
            trier_arbre(enfant)