import logging
from .signaux import SIGNAUX_DOSSIERS, SIGNAUX_FRAMEWORKS, POIDS, SEUILS_TAILLE, FACTEUR_ZONE_GRISE
logger = logging.getLogger(__name__)


def extraire_dossiers(fichiers: list) -> dict:
    """
    Extrait tous les noms de dossiers uniques depuis la liste des fichiers,
    avec leur profondeur minimale (niveau le plus proche de la racine).
    ["controllers/user.py", "a/b/controllers/x.py"] → {"controllers": 1}
    """
    dossiers_profondeur = {}
    for chemin in fichiers:
        parties = chemin.replace("\\", "/").split("/")
        for niveau, partie in enumerate(parties[:-1], start=1):  # Exclure le nom du fichier
            nom = partie.lower().strip()
            if nom not in dossiers_profondeur or niveau < dossiers_profondeur[nom]:
                dossiers_profondeur[nom] = niveau
    return dossiers_profondeur


def poids_profondeur(profondeur: int) -> float:
    """
    Calcule le facteur de poids selon la profondeur du dossier.
    Profondeur 1 (racine) = 1.0, profondeur 2 = 0.5, profondeur 3 = 0.33, etc.
    """
    return 1.0 / max(profondeur, 1)

def extraire_frameworks(contenu_strategique: dict) -> list:
    """
    Extrait les noms de frameworks depuis le contenu des fichiers stratégiques.
    Cherche dans requirements.txt, package.json, pom.xml, etc.
    """
    frameworks_trouves = []
    
    for chemin, contenu in contenu_strategique.items():
        contenu_lower = contenu.lower()
        nom_fichier   = chemin.split("/")[-1].lower()
        
        # Tous les frameworks connus à chercher
        tous_frameworks = set()
        for liste in SIGNAUX_FRAMEWORKS.values():
            tous_frameworks.update(liste)
        
        for framework in tous_frameworks:
            if framework in contenu_lower:
                frameworks_trouves.append(framework)
                logger.info(f"Framework détecté : {framework} dans {nom_fichier}")
    
    # Cas spécial : docker-compose présent = signal microservices fort
    for chemin in contenu_strategique:
        if "docker-compose" in chemin.lower():
            frameworks_trouves.append("docker-compose")
    
    return list(set(frameworks_trouves))

def calculer_scores(dossiers: dict, frameworks: list) -> dict:
    """
    Calcule le score de chaque architecture candidate,
    pondéré par la profondeur des dossiers détectés.
    """
    scores = {
        "MVC"          : 0,
        "MVP"          : 0,
        "MVVM"         : 0,
        "COUCHES"      : 0,
        "CLEAN"        : 0,
        "MICROSERVICES": 0,
        "MONOLITHIQUE" : 0
    }

    # ── Scoring par dossiers (pondéré par profondeur) ─────────────
    for architecture, signaux in SIGNAUX_DOSSIERS.items():
        for signal in signaux:
            signal_lower = signal.lower()
            if signal_lower in dossiers:
                profondeur = dossiers[signal_lower]
                facteur    = poids_profondeur(profondeur)
                points     = POIDS["dossier"] * facteur
                scores[architecture] += points
                logger.info(
                    f"Signal dossier '{signal}' (profondeur {profondeur}) "
                    f"→ +{points:.2f} pour {architecture}"
                )

    # ── Scoring par frameworks (inchangé) ──────────────────────────
    for architecture, signaux in SIGNAUX_FRAMEWORKS.items():
        for signal in signaux:
            if signal.lower() in frameworks:
                scores[architecture] += POIDS["framework"]
                logger.info(
                    f"Signal framework '{signal}' → +{POIDS['framework']} pour {architecture}"
                )

    # ── Bonus microservices si docker-compose présent ─────────────
    if "docker-compose" in frameworks:
        scores["MICROSERVICES"] += POIDS["dockerfile"]
        logger.info(f"Bonus docker-compose → +{POIDS['dockerfile']} pour MICROSERVICES")

    # ── Si aucun signal → Monolithique par défaut ─────────────────
    total = sum(scores.values())
    if total == 0:
        scores["MONOLITHIQUE"] = 1

    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))

def normaliser_scores_par_taille(scores: dict, nombre_fichiers: int, nombre_dossiers: int) -> dict:
    """
    Normalise les scores en fonction de la taille du projet.
    Approche B : score relatif à la densité de dossiers pertinents.
    """
    if nombre_dossiers == 0:
        return scores

    # Facteur de base : densité = signaux / dossiers totaux
    facteur_densite = 1.0 / max(nombre_dossiers, 1)

    # Zone grise : projet petit-moyen → réduction supplémentaire
    facteur_zone_grise = 1.0
    if SEUILS_TAILLE["minimal"] <= nombre_fichiers < SEUILS_TAILLE["moyen"]:
        facteur_zone_grise = FACTEUR_ZONE_GRISE

    facteur_final = facteur_densite * facteur_zone_grise

    scores_normalises = {
        architecture: round(score * facteur_final, 4)
        for architecture, score in scores.items()
    }

    logger.info(
        f"Normalisation appliquée : densité={facteur_densite:.3f}, "
        f"zone_grise={facteur_zone_grise}, facteur_final={facteur_final:.4f}"
    )

    return scores_normalises

def decider_architecture(scores: dict) -> tuple:
    """
    Décide l'architecture finale et calcule le niveau de confiance.
    Retourne (architecture_choisie, niveau_confiance)
    """
    scores_positifs = {k: v for k, v in scores.items() if v > 0}
    
    if not scores_positifs:
        return "MONOLITHIQUE", "faible"
    
    meilleur      = list(scores.items())[0]
    architecture  = meilleur[0]
    score_max     = meilleur[1]
    score_total   = sum(scores.values())
    
    # Niveau de confiance basé sur le pourcentage du score dominant
    if score_total == 0:
        confiance = "faible"
    else:
        ratio = score_max / score_total
        if ratio >= 0.6:
            confiance = "élevée"
        elif ratio >= 0.4:
            confiance = "moyenne"
        else:
            confiance = "faible"
    
    return architecture, confiance

SEUIL_CONFLIT = 0.2  # Écart relatif en dessous duquel on considère qu'il y a conflit

def detecter_conflit(scores: dict) -> dict:
    """
    Détecte si les deux meilleurs scores sont trop proches pour trancher
    de façon fiable. Retourne les infos de conflit si applicable.
    """
    scores_tries = list(scores.items())

    if len(scores_tries) < 2:
        return {"conflit": False}

    candidat_1, score_1 = scores_tries[0]
    candidat_2, score_2 = scores_tries[1]

    # Pas de conflit si le meilleur score est nul ou si le 2e est à 0
    if score_1 == 0 or score_2 == 0:
        return {"conflit": False}

    ecart_relatif = (score_1 - score_2) / score_1

    if ecart_relatif < SEUIL_CONFLIT:
        logger.info(
            f"Conflit détecté entre {candidat_1} ({score_1:.2f}) et "
            f"{candidat_2} ({score_2:.2f}) — écart relatif : {ecart_relatif:.2%}"
        )
        return {
            "conflit"    : True,
            "candidat_1" : candidat_1,
            "score_1"    : score_1,
            "candidat_2" : candidat_2,
            "score_2"    : score_2,
            "ecart"      : ecart_relatif
        }

    return {"conflit": False}

def trouver_signaux_differenciants(dossiers: dict, frameworks: list, candidat_1: str, candidat_2: str) -> str:
    """
    Cherche un signal qui n'appartient qu'à candidat_1 OU candidat_2,
    mais pas aux deux. Retourne le candidat favorisé, ou None si aucun trouvé.
    """
    signaux_c1 = set(s.lower() for s in SIGNAUX_DOSSIERS.get(candidat_1, []))
    signaux_c1.update(s.lower() for s in SIGNAUX_FRAMEWORKS.get(candidat_1, []))

    signaux_c2 = set(s.lower() for s in SIGNAUX_DOSSIERS.get(candidat_2, []))
    signaux_c2.update(s.lower() for s in SIGNAUX_FRAMEWORKS.get(candidat_2, []))

    # Signaux exclusifs à chaque candidat (présents chez l'un, absents chez l'autre)
    exclusifs_c1 = signaux_c1 - signaux_c2
    exclusifs_c2 = signaux_c2 - signaux_c1

    signaux_presents = set(dossiers.keys()) | set(frameworks)

    trouve_c1 = signaux_presents & exclusifs_c1
    trouve_c2 = signaux_presents & exclusifs_c2

    if trouve_c1 and not trouve_c2:
        logger.info(f"Signal différenciant trouvé pour {candidat_1} : {trouve_c1}")
        return candidat_1
    elif trouve_c2 and not trouve_c1:
        logger.info(f"Signal différenciant trouvé pour {candidat_2} : {trouve_c2}")
        return candidat_2

    return None

def detecter_architecture(data: dict) -> dict:
    """
    Fonction principale — reçoit le dictionnaire du scanner
    et retourne le résultat de détection complet.
    """
    fichiers             = data.get("fichiers", [])
    contenu_strategique  = data.get("contenu_strategique", {})
    nombre_fichiers      = len(fichiers)

    logger.info("Début de la détection d'architecture...")
    logger.info(f"Nombre de fichiers détectés : {nombre_fichiers}")

    # ── Étape 1.2 : court-circuit pour les petits projets ─────────
    if nombre_fichiers < SEUILS_TAILLE["minimal"]:
        logger.info(
            f"Projet trop petit ({nombre_fichiers} fichiers < "
            f"{SEUILS_TAILLE['minimal']}) → MONOLITHIQUE par défaut"
        )
        return {
            "architecture"  : "MONOLITHIQUE",
            "confiance"     : "élevée",
            "scores"        : {"MONOLITHIQUE": 1},
            "dossiers"      : [],
            "frameworks"    : [],
            "raison_court_circuit": f"Projet trop petit ({nombre_fichiers} fichiers)"
        }

    # ── Extraction des signaux ────────────────────────────────────
    dossiers   = extraire_dossiers(fichiers)
    frameworks = extraire_frameworks(contenu_strategique)

    logger.info(f"Dossiers détectés  : {dossiers}")
    logger.info(f"Frameworks détectés : {frameworks}")

    # ── Calcul des scores ─────────────────────────────────────────
    scores = calculer_scores(dossiers, frameworks)

    # ── Étape 1.3 : normalisation par taille ──────────────────────
    scores = normaliser_scores_par_taille(scores, nombre_fichiers, len(dossiers))
    scores = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))

    # ── Décision finale ───────────────────────────────────────────
    architecture, confiance = decider_architecture(scores)

    # ── Étape 3 : détection et résolution de conflit ──────────────
    info_conflit = detecter_conflit(scores)

    if info_conflit["conflit"]:
        gagnant = trouver_signaux_differenciants(
            dossiers, frameworks,
            info_conflit["candidat_1"], info_conflit["candidat_2"]
        )
        if gagnant:
            architecture = gagnant
            confiance    = "moyenne"  # Tranché par signal différenciant, pas totalement certain
        else:
            confiance = "faible"  # Reste ambigu, Ollama devra trancher (étape 4)

    logger.info(f"Architecture choisie : {architecture} (confiance : {confiance})")

    return {
        "architecture"  : architecture,
        "confiance"     : confiance,
        "scores"        : scores,
        "dossiers"      : list(dossiers),
        "frameworks"    : frameworks,
        "conflit"       : info_conflit
    }

