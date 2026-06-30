def generer_rapport(resultat: dict, data: dict) -> str:
    """
    Génère un rapport lisible de la détection d'architecture.
    Ce rapport sera transmis à Ollama comme contexte.
    """
    architecture = resultat["architecture"]
    confiance    = resultat["confiance"]
    scores       = resultat["scores"]
    frameworks   = resultat.get("frameworks", [])
    dossiers     = resultat.get("dossiers", [])

    descriptions = {
        "MVC"          : "Modèle-Vue-Contrôleur — séparation données / affichage / logique",
        "MVP"          : "Modèle-Vue-Présentateur — Presenter gère toute la logique UI",
        "MVVM"         : "Modèle-Vue-VueModèle — data binding entre Vue et ViewModel",
        "COUCHES"      : "Architecture en couches — Présentation / Métier / Données",
        "CLEAN"        : "Clean Architecture — Use Cases / Entities / Repositories",
        "MICROSERVICES": "Microservices — services indépendants communicants",
        "MONOLITHIQUE" : "Application monolithique — structure simple sans séparation claire"
    }

    rapport = f"""
# Rapport de détection d'architecture

## Résultat
- **Architecture détectée** : {architecture}
- **Description** : {descriptions.get(architecture, "")}
- **Niveau de confiance** : {confiance}

## Signaux détectés
- **Dossiers analysés** : {", ".join(dossiers) if dossiers else "Aucun"}
- **Frameworks trouvés** : {", ".join(frameworks) if frameworks else "Aucun"}

## Scores par architecture
"""
    for arch, score in scores.items():
        barre = "█" * score + "░" * max(0, 10 - score)
        rapport += f"- {arch:<15} {barre} ({score} pts)\n"

    # ── Section Ollama (si disponible) ───────────────────────────
    if resultat.get("justification"):
        rapport += f"""
## Analyse Ollama
- **Justification** : {resultat['justification']}
- **Source**        : {resultat.get('source', 'N/A')}
"""
        if resultat.get("elements_cles"):
            rapport += "- **Éléments clés** :\n"
            for el in resultat["elements_cles"]:
                rapport += f"  - {el}\n"

        # Accord ou correction entre scoring et Ollama
        candidat = resultat.get("candidat_scoring")
        ollama   = resultat.get("reponse_ollama")
        if candidat and ollama:
            if candidat == ollama:
                rapport += f"\n✔ Ollama confirme le scoring : **{ollama}**\n"
            else:
                rapport += (
                    f"\n⚠ Ollama a corrigé le scoring : "
                    f"**{candidat}** → **{ollama}**\n"
                )

    rapport += f"""
## Projet analysé
- **Nom**      : {data.get('repo_name', 'Inconnu')}
- **Auteur**   : {data.get('author', 'Inconnu')}
- **Fichiers** : {len(data.get('fichiers', []))}
- **Commits**  : {data.get('commits', 0)}
- **Stars**    : {data.get('stars', 0)}
- **Licence**  : {data.get('licence', 'Non spécifiée')}
"""
    return rapport.strip()