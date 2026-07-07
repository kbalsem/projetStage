# architecture/detecteur.py
import logging
import os

from .signaux import (
    SIGNAUX, REGLES, ANTI_SIGNAUX,
    POIDS, FIABILITE_POIDS, BONUS_PAR_CONDITION, PENALITE_ANTI_SIGNAL
    # ❌ Ne plus importer SEUIL_CONFLIT, SEUILS_TAILLE, FACTEUR_ZONE_GRISE
)

logger = logging.getLogger(__name__)

# ═══════════ CHARGEMENT DEPUIS .ENV ═══════════
SEUIL_CONFLIT = float(os.getenv("SEUIL_CONFLIT_ARCHITECTURE", "0.2"))
SEUILS_TAILLE = {
    "minimal": int(os.getenv("SEUIL_TAILLE_MINIMAL", "10")),
    "moyen": int(os.getenv("SEUIL_TAILLE_MOYEN", "25"))
}
FACTEUR_ZONE_GRISE = float(os.getenv("FACTEUR_ZONE_GRISE", "0.5"))

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def _normaliser(texte: str) -> str:
    return texte.lower().strip()


def _poids_profondeur(profondeur: int) -> float:
    return 1.0 / max(profondeur, 1)


def _collecter_tous_signaux_par_categorie(categorie: str) -> set:
    tous = set()
    for archi in SIGNAUX.values():
        for signal in archi.get(categorie, []):
            tous.add(signal["nom"])
    return tous


# ═══════════════════════════════════════════════════════════════════════════════
# EXTRACTION DES SIGNAUX
# ═══════════════════════════════════════════════════════════════════════════════

def extraire_dossiers(fichiers: list) -> dict:
    dossiers = {}
    for chemin in fichiers:
        parties = chemin.replace("\\", "/").split("/")
        for niveau, partie in enumerate(parties[:-1], start=1):
            nom = _normaliser(partie)
            if nom not in dossiers or niveau < dossiers[nom]:
                dossiers[nom] = niveau
    return dossiers


def extraire_fichiers_caracteristiques(fichiers: list) -> set:
    return {_normaliser(f.split("/")[-1]) for f in fichiers}


def extraire_frameworks(contenu_strategique: dict) -> set:
    frameworks_connus = _collecter_tous_signaux_par_categorie("frameworks")
    frameworks_trouves = set()
    for chemin, contenu in contenu_strategique.items():
        contenu_lower = contenu.lower()
        for fw in frameworks_connus:
            if fw in contenu_lower:
                frameworks_trouves.add(fw)
    return frameworks_trouves


def extraire_imports_depuis_ast(infos_ast: dict) -> set:
    imports = set()
    for chemin, infos in infos_ast.items():
        for imp in infos.get("imports", []):
            imp = imp.strip()
            if imp.startswith("from "):
                module = imp[5:].split(" import ")[0].strip()
                imports.add(_normaliser(module.split(".")[0]))
            elif imp.startswith("import "):
                module = imp[7:].split(" as ")[0].strip()
                imports.add(_normaliser(module.split(".")[0]))
    return imports


def extraire_decorateurs(sources_ast: dict) -> set:
    decorateurs = set()
    for chemin, code in sources_ast.items():
        for ligne in code.split("\n"):
            ligne = ligne.strip()
            if ligne.startswith("@"):
                decorateurs.add(ligne.split("(")[0].strip())
    return decorateurs


def extraire_classes_depuis_ast(infos_ast: dict) -> set:
    classes = set()
    for chemin, infos in infos_ast.items():
        for classe in infos.get("classes", []):
            nom = classe.get("nom", "")
            if nom:
                classes.add(nom)
    return classes


def extraire_dependances(contenu_strategique: dict) -> set:
    dependances_connues = _collecter_tous_signaux_par_categorie("dependances")
    dependances_trouves = set()
    fichiers_deps = {
        "requirements.txt", "pipfile", "setup.py", "pyproject.toml",
        "package.json", "pom.xml", "build.gradle", "composer.json",
        "gemfile", "go.mod", "cargo.toml"
    }
    for chemin, contenu in contenu_strategique.items():
        if chemin.split("/")[-1].lower() in fichiers_deps:
            contenu_lower = contenu.lower()
            for dep in dependances_connues:
                if dep in contenu_lower:
                    dependances_trouves.add(dep)
    return dependances_trouves


# ═══════════════════════════════════════════════════════════════════════════════
# CALCUL DES SCORES
# ═══════════════════════════════════════════════════════════════════════════════

def _calculer_score_signaux(signaux_detectes: set, signaux_attendus: list,
                            categorie: str, dossiers_profondeur: dict = None) -> tuple:
    score = 0
    trouves = []
    for signal in signaux_attendus:
        nom = _normaliser(signal["nom"])
        fiabilite = signal.get("fiabilite", "moyenne")
        multiplicateur = FIABILITE_POIDS.get(fiabilite, 0.6)
        if nom in signaux_detectes:
            points = POIDS.get(categorie, 2) * multiplicateur
            if categorie == "dossiers" and dossiers_profondeur:
                points *= _poids_profondeur(dossiers_profondeur.get(nom, 1))
            score += points
            trouves.append(f"{categorie}:{nom}")
    return score, trouves


def calculer_scores(data: dict) -> tuple:
    fichiers = data.get("fichiers", [])
    contenu_strategique = data.get("contenu_strategique", {})
    sources_ast = data.get("sources_ast", {})
    infos_ast = data.get("infos_ast", {})

    dossiers_detectes = extraire_dossiers(fichiers)
    fichiers_detectes = extraire_fichiers_caracteristiques(fichiers)
    frameworks_detectes = extraire_frameworks(contenu_strategique)
    imports_detectes = extraire_imports_depuis_ast(infos_ast)
    decorateurs_detectes = extraire_decorateurs(sources_ast)
    classes_detectes = extraire_classes_depuis_ast(infos_ast)
    dependances_detectes = extraire_dependances(contenu_strategique)

    signaux_par_categorie = {
        "dossiers": dossiers_detectes,
        "fichiers": fichiers_detectes,
        "frameworks": frameworks_detectes,
        "imports": imports_detectes,
        "decorateurs": decorateurs_detectes,
        "classes": classes_detectes,
        "dependances": dependances_detectes,
    }

    architectures = list(SIGNAUX.keys())
    scores = {archi: 0 for archi in architectures}
    details = {archi: {"signaux": [], "regles": [], "anti_signaux": []} for archi in architectures}
    total_signaux = {archi: 0 for archi in architectures}
    signaux_attendus_count = {archi: 0 for archi in architectures}

    for archi in architectures:
        for categorie, signaux_attendus in SIGNAUX[archi].items():
            detectes = signaux_par_categorie.get(categorie, set())
            score, trouves = _calculer_score_signaux(detectes, signaux_attendus, categorie, dossiers_detectes)
            scores[archi] += score
            details[archi]["signaux"].extend(trouves)
            total_signaux[archi] += len(trouves)
            signaux_attendus_count[archi] += len(signaux_attendus)

    for regle in REGLES:
        archi = regle["architecture"]
        conditions_remplies = sum(
            1 for cat, nom in regle["conditions"]
            if _normaliser(nom) in signaux_par_categorie.get(cat, set())
        )
        if conditions_remplies == len(regle["conditions"]):
            bonus = conditions_remplies * BONUS_PAR_CONDITION
            scores[archi] += bonus
            details[archi]["regles"].append(f"{regle['nom']} (+{bonus})")

    for archi, anti_signaux in ANTI_SIGNAUX.items():
        for cat, nom in anti_signaux:
            if _normaliser(nom) in signaux_par_categorie.get(cat, set()):
                scores[archi] = max(0, scores[archi] - PENALITE_ANTI_SIGNAL)
                details[archi]["anti_signaux"].append(f"{cat}:{nom} (-{PENALITE_ANTI_SIGNAL})")

    total = sum(scores.values())
    if total == 0:
        scores["MONOLITHIQUE"] = 1

    return (
        dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)),
        details,
        total_signaux,
        signaux_attendus_count,
        signaux_par_categorie,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# DÉCISION
# ═══════════════════════════════════════════════════════════════════════════════

def normaliser_scores_par_taille(scores: dict, nombre_fichiers: int, nombre_dossiers: int) -> dict:
    facteur = 1.0
    if SEUILS_TAILLE["minimal"] <= nombre_fichiers < SEUILS_TAILLE["moyen"]:
        facteur = FACTEUR_ZONE_GRISE
    return {a: round(s * facteur, 2) for a, s in scores.items()}


def decider_architecture(scores: dict) -> tuple:
    items = list(scores.items())
    if not items or items[0][1] <= 0:
        return "MONOLITHIQUE", "faible"
    archi, meilleur = items[0]
    total = sum(scores.values())
    if total == 0:
        return archi, "faible"
    ratio = meilleur / total
    if ratio >= 0.6:
        return archi, "élevée"
    elif ratio >= 0.4:
        return archi, "moyenne"
    return archi, "faible"


def detecter_conflit(scores: dict) -> dict:
    items = list(scores.items())
    if len(items) < 2:
        return {"conflit": False}
    a1, s1 = items[0]
    a2, s2 = items[1]
    if s1 == 0 or s2 == 0:
        return {"conflit": False}
    ecart = (s1 - s2) / s1
    if ecart < SEUIL_CONFLIT:
        return {"conflit": True, "candidat_1": a1, "score_1": s1, "candidat_2": a2, "score_2": s2, "ecart": ecart}
    return {"conflit": False}


def detecter_architecture(data: dict) -> dict:
    fichiers = data.get("fichiers", [])
    nombre_fichiers = len(fichiers)

    if nombre_fichiers < SEUILS_TAILLE["minimal"]:
        return {
            "architecture": "MONOLITHIQUE", "confiance": "élevée",
            "scores": {"MONOLITHIQUE": 1}, "details": {},
            "signaux_detectes": {}, "couverture": {},
            "conflit": {"conflit": False}, "total_signaux": {},
            "besoin_ollama": False, "raison_ollama": "",
        }

    scores, details, total_signaux, signaux_attendus, signaux_detectes = calculer_scores(data)
    dossiers = extraire_dossiers(fichiers)
    scores = normaliser_scores_par_taille(scores, nombre_fichiers, len(dossiers))
    scores = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))

    architecture, confiance = decider_architecture(scores)
    info_conflit = detecter_conflit(scores)

    if architecture == "MONOLITHIQUE":
        for archi, score in scores.items():
            if archi != "MONOLITHIQUE" and score > 0:
                architecture = archi
                confiance = "suggérée"
                break

    couverture = {}
    for archi in total_signaux:
        attendus = signaux_attendus.get(archi, 1)
        trouves = total_signaux.get(archi, 0)
        couverture[archi] = round(trouves / max(attendus, 1) * 100, 1)

    besoin_ollama = False
    raison_ollama = ""
    if info_conflit.get("conflit"):
        besoin_ollama = True
        raison_ollama = f"Conflit entre {info_conflit['candidat_1']} et {info_conflit['candidat_2']}"
    elif confiance in ("faible", "suggérée"):
        besoin_ollama = True
        raison_ollama = f"Architecture suggérée ({architecture})" if confiance == "suggérée" else "Confiance faible"

    return {
        "architecture": architecture, "confiance": confiance,
        "scores": scores, "details": details.get(architecture, {}),
        "signaux_detectes": signaux_detectes, "couverture": couverture,
        "conflit": info_conflit, "total_signaux": total_signaux,
        "besoin_ollama": besoin_ollama, "raison_ollama": raison_ollama,
    }