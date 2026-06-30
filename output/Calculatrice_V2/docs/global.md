# Calculatrice_V2 - Architecture Logicielle

## Architecture générale
Le projet Calculatrice_V2 applique l'architecture MVP (Model-View-Presenter) pour séparer les couches de logique métier, d'affichage et de gestion des interactions utilisateur. Cette architecture permet une meilleure organisation du code et une plus grande facilité à maintenir et à élargir le projet.

## Modules principaux
Voici les modules principaux du projet Calculatrice_V2 :

* **Model** : gère les données de l'application, notamment les opérations mathématiques et les résultats.
* **View** : définit la structure de l'écran d'affichage et gère les interactions utilisateur (touches, clics, etc.).
* **Presenter** : coordonne les actions entre le Model et la View, en prenant en charge les traitements de données et les mises à jour de l'interface.

## Flux du programme
Voici comment les composants interagissent :

1. L'utilisateur effectue une action (par exemple, appuie sur un bouton).
2. La View notifie le Presenter de l'action.
3. Le Presenter récupère les données nécessaires du Model.
4. Le Model calcule le résultat de l'opération mathématique demandée.
5. Le Presenter met à jour la View avec le résultat.
6. La View affiche le résultat à l'utilisateur.

## Technologies utilisées
Voici les technologies détectées dans le projet Calculatrice_V2 :

* Android (framework)
* Java (langage de programmation)

Note : ce document décrit l'architecture logicielle du projet Calculatrice_V2, mais ne contient pas de détails sur la mise en œuvre technique.