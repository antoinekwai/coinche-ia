# Cahier des charges de l'interface

## Objectifs
1. Tester les modèles : export de chaque donne (mains, enchères, plis) pour analyse.
2. Jouer à la coinche contre des IA. Choix minimal : IA réseau (rapide) et
   Grand Maître (fort, attente limitée).

## Fin de donne : « Donne suivante » ou « Analyse de la donne »
- Enchères du joueur : l'enchère était-elle bonne ? Espérance des autres enchères
  (avec marge d'incertitude).
- Jeu de la carte : comparer à la décision du Grand Maître (même information),
  et à part, au jeu parfait (cartes visibles, sans reproche).
- Module « professeur » : explications pour progresser.

## Fin de partie
- Analyse de la partie : qualité de jeu (toi vs Grand Maître avec les mêmes cartes)
  et chance (points du Grand Maître avec tes cartes vs moyenne).

## Agrément
- Vraies cartes, animations de distribution et de jeu, quelques sons, usage sur téléphone.

## Principes
- Le professeur enseigne le Système v2 : afficher une confiance, pas des verdicts.
- Le partenaire bot suppose que le joueur annonce en Système v2 : aide-mémoire du système.
- Budget de temps strict sur Render ; calculs longs en arrière-plan avec progression.
- Phases : 0 relecture, 1 enregistrement/export, 2 enchères unifiées, 3 choix IA,
  4 analyse du jeu, 5 analyse des enchères, 6 fin de partie, 7 habillage.
