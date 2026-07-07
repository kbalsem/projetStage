## 📋 Résumé du projet
Le projet Calculatrice-en-java est une application qui permet de réaliser des opérations mathématiques simples.

## 🏛️ Architecture générale
L'architecture de ce projet est MONOLITHIQUE, ce qui signifie que tous les composants sont regroupés dans un seul fichier ou package. Dans ce cas, le projet est divisé en plusieurs fichiers Java qui interagissent entre eux pour fournir la fonctionnalité souhaitée.

## 📁 Modules principaux
### src/Affichage.java
Rôle : Afficher les résultats des opérations mathématiques.
Contenu : Code pour afficher les résultats sur l'écran.
Responsabilités : Gérer l'affichage des résultats, interagir avec les autres modules.

### src/CalcEventAbout.java
Rôle : Gérer les événements liés à la page d'aide.
Contenu : Code pour gérer les événements de la page d'aide.
Responsabilités : Interagir avec les autres modules pour fournir des informations sur l'utilisation de l'application.

### src/CalcEventButton.java
Rôle : Gérer les événements liés aux boutons de l'interface utilisateur.
Contenu : Code pour gérer les événements des boutons.
Responsabilités : Interagir avec les autres modules pour fournir la fonctionnalité souhaitée.

### src/CalcEventClear.java
Rôle : Gérer les événements liés à la suppression de l'historique d'opérations.
Contenu : Code pour gérer les événements de suppression.
Responsabilités : Interagir avec les autres modules pour fournir la fonctionnalité souhaitée.

### src/CalcEventImport.java
Rôle : Gérer les événements liés à l'importation de données.
Contenu : Code pour gérer les événements d'importation.
Responsabilités : Interagir avec les autres modules pour fournir la fonctionnalité souhaitée.

## 🔄 Flux du programme
Les fichiers Java interagissent entre eux via des imports. Les fichiers principaux (Affichage, CalcEventAbout, CalcEventButton, CalcEventClear, CalcEventImport) importent les classes et méthodes nécessaires pour fournir la fonctionnalité souhaitée.

## 🛠️ Technologies utilisées
* Java

## 📊 Statistiques
- Nombre total de fichiers : 17
- Architecture : MONOLITHIQUE
- Frameworks : Aucun framework détecté

## 🗂️ Organisation du code
Le projet est organisé dans un seul dossier (src) qui contient les fichiers Java principaux. Les fichiers sont nommés de manière descriptive pour faciliter la compréhension et la maintenance du code.