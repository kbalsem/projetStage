import requests
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL      = "llama3"


# Ordre de priorité des fichiers stratégiques à privilégier pour le prompt
FICHIERS_PRIORITAIRES = [
    "requirements.txt", "package.json", "pom.xml",
    "build.gradle", "composer.json", "cargo.toml",
    "docker-compose.yml", "docker-compose.yaml",
    "main.py", "app.py", "index.js", "server.js"
]

def choisir_fichier_strategique(contenu: dict) -> tuple:
    if not contenu:
        return None, None

    for nom_prioritaire in FICHIERS_PRIORITAIRES:
        for chemin, texte in contenu.items():
            if chemin.lower().endswith(nom_prioritaire):
                return chemin, texte

    chemin, texte = list(contenu.items())[0]
    return chemin, texte

def construire_prompt(data: dict, candidat: str, scores: dict, conflit: dict = None) -> str:
    dossiers   = data.get("dossiers", [])[:20]
    frameworks = data.get("frameworks", [])
    contenu    = data.get("contenu_strategique", {})

    chemin, texte = choisir_fichier_strategique(contenu)
    contenu_formate = f"{chemin}:\n{texte[:300]}" if chemin else "aucun"

    dossiers_str   = ', '.join(dossiers)
    frameworks_str = ', '.join(frameworks) if frameworks else 'aucun'

    if conflit and conflit.get("conflit"):
        candidat_1 = conflit["candidat_1"]
        candidat_2 = conflit["candidat_2"]

        prompt = f"""Tu es un expert en architecture logicielle. Analyse ce projet Git.

Dossiers : {dossiers_str}
Frameworks : {frameworks_str}
Fichier clé : {contenu_formate}

Le système de scoring hésite entre deux architectures à égalité :
- {candidat_1}
- {candidat_2}

Analyse les indices ci-dessus et choisis celle qui correspond le mieux.

RÈGLE STRICTE : tu dois OBLIGATOIREMENT répondre avec "{candidat_1}" ou "{candidat_2}".
Aucune autre architecture n'est acceptée, même si elle te semble plus appropriée.

Réponds UNIQUEMENT avec ce JSON, rien d'autre :
{{"architecture": "{candidat_1}_ou_{candidat_2}", "justification": "raison courte", "confiance": "élevée/moyenne/faible", "elements_cles": ["el1", "el2"]}}"""

        return prompt.strip()

    top_scores = list(scores.items())[:3]
    scores_formate = " | ".join(f"{a}:{s}pts" for a, s in top_scores)

    prompt = f"""Tu es un expert en architecture logicielle. Analyse ce projet Git.

Dossiers : {dossiers_str}
Frameworks : {frameworks_str}
Fichier clé : {contenu_formate}
Scoring propose : {candidat} ({scores_formate})

Réponds UNIQUEMENT avec ce JSON, rien d'autre :
{{"architecture": "<UNE_DES_OPTIONS>", "justification": "raison courte", "confiance": "élevée/moyenne/faible", "elements_cles": ["el1", "el2"]}}

Choisis parmi : MVC, MVP, MVVM, COUCHES, CLEAN, MICROSERVICES, MONOLITHIQUE"""

    return prompt.strip()

def interroger_ollama(prompt: str, max_retries: int = 2) -> dict:
    """
    Envoie le prompt à Ollama et retourne la réponse parsée.
    Réessaie automatiquement en cas d'erreur HTTP ou de timeout
    (utile notamment au premier appel, le temps qu'Ollama charge le modèle en mémoire).
    """
    payload = {
        "model"  : MODEL,
        "prompt" : prompt,
        "stream" : False,
        "options": {
            "temperature": 0.1,
            "num_predict": 200    # Réduit — on veut juste un JSON court
        }
    }

    reponse = None
    texte = None

    for tentative in range(max_retries + 1):
        try:
            reponse = requests.post(OLLAMA_URL, json=payload, timeout=120)
            reponse.raise_for_status()
            break  # succès → on sort de la boucle de retry

        except requests.exceptions.HTTPError as e:
            # On capture le corps de la réponse AVANT de perdre l'info — c'est ça
            # qui donne la vraie cause du 500 (mémoire, modèle, payload, etc.)
            corps_erreur = reponse.text if reponse is not None else "(pas de corps de réponse)"
            logger.error(
                f"Erreur HTTP Ollama (tentative {tentative + 1}/{max_retries + 1}) : {e}"
            )
            logger.error(f"Corps de la réponse Ollama : {corps_erreur}")
            print(f"  [DEBUG] Erreur Ollama détaillée : {corps_erreur}")
            if tentative == max_retries:
                return None
            continue

        except requests.exceptions.ConnectionError:
            logger.error("Ollama non disponible (connexion refusée)")
            return None

        except requests.exceptions.Timeout:
            logger.error(
                f"Timeout Ollama après 120s (tentative {tentative + 1}/{max_retries + 1})"
            )
            if tentative == max_retries:
                return None
            continue

    try:
        texte = reponse.json().get("response", "").strip()

        # Afficher la réponse brute pour debug
        logger.info(f"Réponse brute Ollama : '{texte}'")
        print(f"  [DEBUG] Réponse Ollama brute : {texte[:200]}")

        if not texte:
            logger.error("Ollama a retourné une réponse vide")
            return None

        # Nettoyer — extraire le JSON
        if "```json" in texte:
            texte = texte.split("```json")[1].split("```")[0].strip()
        elif "```" in texte:
            texte = texte.split("```")[1].split("```")[0].strip()

        # Chercher le JSON dans la réponse si entouré de texte
        if "{" in texte and "}" in texte:
            debut = texte.index("{")
            fin   = texte.rindex("}") + 1
            texte = texte[debut:fin]

        # Parser le JSON
        resultat = json.loads(texte)

        # Valider les champs
        architectures_valides = [
            "MVC", "MVP", "MVVM", "COUCHES",
            "CLEAN", "MICROSERVICES", "MONOLITHIQUE"
        ]
        if resultat.get("architecture") not in architectures_valides:
            logger.warning(f"Architecture invalide : {resultat.get('architecture')}")
            return None

        return resultat

    except json.JSONDecodeError as e:
        logger.error(f"Réponse Ollama non parseable : {e}")
        print(f"  [DEBUG] Texte reçu : '{texte}'")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors du traitement de la réponse Ollama : {e}")
        return None

def detecter_avec_ollama(data_scanner: dict, resultat_scoring: dict) -> dict:
    """
    Fonction principale — combine scoring + Ollama.
    """
    candidat   = resultat_scoring["architecture"]
    scores     = resultat_scoring["scores"]
    confiance  = resultat_scoring["confiance"]
    conflit    = resultat_scoring.get("conflit", {"conflit": False})

    logger.info(f"Scoring propose : {candidat} (confiance : {confiance})")
    if conflit.get("conflit"):
        logger.info(
            f"Conflit en attente d'arbitrage Ollama entre "
            f"{conflit['candidat_1']} et {conflit['candidat_2']}"
        )
    logger.info("Interrogation d'Ollama pour confirmation...")

    contexte = {
        "repo_name"           : data_scanner.get("repo_name", ""),
        "dossiers"            : resultat_scoring.get("dossiers", []),
        "frameworks"          : resultat_scoring.get("frameworks", []),
        "fichiers_originaux"  : data_scanner.get("fichiers", []),
        "contenu_strategique" : data_scanner.get("contenu_strategique", {})
    }

    prompt = construire_prompt(contexte, candidat, scores, conflit)
    reponse_ollama = interroger_ollama(prompt)

    if reponse_ollama:
        architecture_ollama = reponse_ollama["architecture"]
        confiance_ollama     = reponse_ollama["confiance"]
        justification        = reponse_ollama["justification"]
        elements_cles        = reponse_ollama.get("elements_cles", [])

        # ── Cas conflit résolu par Ollama ──────────────────────────
        if conflit.get("conflit"):
            candidat_1 = conflit["candidat_1"]
            candidat_2 = conflit["candidat_2"]

            if architecture_ollama in (candidat_1, candidat_2):
                # Ollama a respecté les deux options proposées
                decision_finale  = architecture_ollama
                confiance_finale = confiance_ollama
                source           = "ollama (arbitrage de conflit)"
                logger.info(f"Ollama tranche le conflit en faveur de : {architecture_ollama}")
            else:
                # Ollama a halluciné une 3e architecture hors des deux proposées
                # → on rejette sa réponse et on retombe sur le meilleur score brut
                logger.warning(
                    f"Ollama a proposé '{architecture_ollama}' hors du conflit "
                    f"({candidat_1} vs {candidat_2}) — réponse rejetée, "
                    f"retour au candidat du scoring : {candidat}"
                )
                decision_finale  = candidat
                confiance_finale = "faible"  # On garde une confiance faible car le conflit n'est pas vraiment résolu
                source           = "scoring (rejet de la réponse Ollama hors-périmètre)"

        # ── Cas normal : confirmation ou correction ────────────────
        elif architecture_ollama == candidat:
            decision_finale = architecture_ollama

            # Étape 5 : n'upgrader que si Ollama est lui-même confiant
            if confiance_ollama in ("moyenne", "élevée"):
                if confiance == "faible":
                    confiance_finale = "moyenne"
                elif confiance == "moyenne":
                    confiance_finale = "élevée"
                else:
                    confiance_finale = "élevée"
                source = "scoring + ollama (accord, confiance renforcée)"
            else:
                # Ollama d'accord mais peu sûr de lui → pas d'upgrade
                confiance_finale = confiance
                source = "scoring + ollama (accord, mais Ollama peu confiant)"

            logger.info(
                f"Accord scoring/Ollama sur {architecture_ollama} — "
                f"confiance scoring={confiance}, confiance Ollama={confiance_ollama} "
                f"→ confiance finale={confiance_finale}"
            )

        else:
            score_architecture_ollama = scores.get(architecture_ollama, 0)

            if score_architecture_ollama == 0:
                decision_finale  = candidat
                confiance_finale = "faible"
                source           = "scoring (correction Ollama rejetée, aucun signal structurel)"
                justification    = (
                    f"Détection par scoring (candidat : {candidat}). "
                    f"Ollama avait suggéré '{architecture_ollama}' mais cette proposition "
                    f"a été rejetée car aucun signal structurel ne la soutient."
                )
                logger.warning(
                    f"Ollama propose {architecture_ollama} mais son score de scoring "
                    f"est de 0 (aucun signal détecté) — correction rejetée, "
                    f"on garde le scoring : {candidat}"
                )

            elif confiance_ollama == "élevée":
                decision_finale  = architecture_ollama
                confiance_finale = confiance_ollama
                source           = "ollama (correction du scoring, confiance élevée)"
                logger.info(
                    f"Ollama corrige avec confiance élevée : "
                    f"{candidat} → {architecture_ollama}"
                )

            else:
                decision_finale  = candidat
                confiance_finale = "faible"
                source           = "scoring (correction Ollama rejetée, confiance insuffisante)"
                justification    = (
                    f"Détection par scoring (candidat : {candidat}). "
                    f"Ollama avait suggéré '{architecture_ollama}' avec une confiance "
                    f"insuffisante ({confiance_ollama}) — proposition rejetée."
                )
                logger.warning(
                    f"Ollama propose {architecture_ollama} (confiance={confiance_ollama}) "
                    f"mais pas assez confiant pour écraser le scoring ({candidat}) "
                    f"→ on garde le scoring avec confiance faible"
                )

        return {
            "architecture"       : decision_finale,
            "confiance"          : confiance_finale,
            "scores"             : scores,
            "dossiers"           : resultat_scoring.get("dossiers", []),
            "frameworks"         : resultat_scoring.get("frameworks", []),
            "justification"      : justification,
            "elements_cles"      : elements_cles,
            "source"             : source,
            "candidat_scoring"   : candidat,
            "reponse_ollama"     : architecture_ollama,
            "etait_en_conflit"   : conflit.get("conflit", False)
        }

    else:
        logger.warning("Ollama indisponible — résultat basé sur le scoring uniquement")
        # Si on était en conflit et qu'Ollama ne répond pas, on garde confiance faible
        confiance_fallback = "faible" if conflit.get("conflit") else confiance
        return {
            "architecture"     : candidat,
            "confiance"        : confiance_fallback,
            "scores"           : scores,
            "dossiers"         : resultat_scoring.get("dossiers", []),
            "frameworks"       : resultat_scoring.get("frameworks", []),
            "justification"    : "Détection par scoring uniquement (Ollama indisponible)",
            "elements_cles"    : [],
            "source"           : "scoring uniquement",
            "candidat_scoring" : candidat,
            "reponse_ollama"   : None,
            "etait_en_conflit" : conflit.get("conflit", False)
        }