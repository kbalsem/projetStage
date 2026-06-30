"""
comparateur_architecture.py

Construit deux arborescences comparables :
  - "ancienne"  : la structure réelle des dossiers détectée par le scanner
  - "proposee"  : la structure de référence attendue pour l'architecture
                  détectée par GitDoc (ex: MVC, MVP, CLEAN...)

Le résultat est renvoyé sous un format exploitable directement par D3.js
(liste de nœuds avec un statut : "ok", "manquant", "extra").
"""

# Templates de référence par architecture — à enrichir selon tes besoins réels
TEMPLATES_ARCHITECTURE = {
    "MVC": ["models", "views", "controllers", "routes", "config"],
    "MVP": ["model", "view", "presenter", "app", "res"],
    "MVVM": ["model", "view", "viewmodel", "binding"],
    "COUCHES": ["presentation", "metier", "donnees", "domain", "infrastructure"],
    "CLEAN": ["entities", "usecases", "interfaces", "infrastructure", "presentation"],
    "MICROSERVICES": ["services", "gateway", "shared", "docker"],
    "MONOLITHIQUE": ["src", "lib", "core"]
}


def normaliser(nom_dossier: str) -> str:
    """Normalise un nom de dossier pour comparaison insensible à la casse / accents simples."""
    return nom_dossier.strip().lower()


def construire_comparaison(dossiers_reels: list, architecture_detectee: str) -> dict:
    """
    dossiers_reels : liste des noms de dossiers détectés par le scanner
                      (ex: resultat_scoring["dossiers"])
    architecture_detectee : ex. "MVC", "MVP", etc.

    Retourne :
    {
        "ancienne": [ {"nom": ..., "statut": "ok"|"extra"}, ... ],
        "proposee": [ {"nom": ..., "statut": "ok"|"manquant"}, ... ],
        "architecture": "MVC"
    }
    """
    dossiers_attendus = TEMPLATES_ARCHITECTURE.get(architecture_detectee, [])

    set_reels    = {normaliser(d) for d in dossiers_reels}
    set_attendus = {normaliser(d) for d in dossiers_attendus}

    # Arborescence "ancienne" (réelle) — on marque ce qui ne fait PAS partie
    # du schéma attendu comme "extra" (hors convention)
    ancienne = []
    for dossier in dossiers_reels:
        statut = "ok" if normaliser(dossier) in set_attendus else "extra"
        ancienne.append({"nom": dossier, "statut": statut})

    # Arborescence "proposée" (référence) — on marque ce qui manque
    # dans le projet réel comme "manquant"
    proposee = []
    for dossier in dossiers_attendus:
        statut = "ok" if normaliser(dossier) in set_reels else "manquant"
        proposee.append({"nom": dossier, "statut": statut})

    return {
        "ancienne": ancienne,
        "proposee": proposee,
        "architecture": architecture_detectee
    }