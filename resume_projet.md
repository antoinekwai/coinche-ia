# CONTEXTE COINCHE IA (mise à jour)

## Utilisateur
Débutant en code, projet écrit par Claude. Mac M1 Pro, commande python3.
Attendu : explications pédagogiques, modifications ciblées ou fichiers complets
(longs fichiers : par morceaux), avis professionnel et critique.
Toujours : commit Git après chaque étape validée ; ne rien modifier pendant un benchmark.

## Méthode de mesure
- Benchmark apparié (mêmes donnes, hasard fixé par donne), résultats .jsonl donne par
  donne, reprise auto, marge à 95 %. Oracle exact dès le pli 2. Adversaire : MC-Enchères.
  Camp testé : équipe 0. Enchères transmises aux bots.
- Fichiers : benchmark_confirmation.py (référence), benchmark_simulations.py, benchmark_v4.py.
  Essai à 10 donnes avant chaque nuit. Option --analyse pour réafficher.
- INDICATEUR PRINCIPAL = POINTS DE MARQUE (comparer_marque.py [fichier]) :
  +valeur si le camp testé gagne, -valeur sinon, x2 si coinché (surcoinche non enregistrée).
  Les points faits sous-estiment les bots qui jouent le contrat.
- comparer_v3_ia.py, comparer_40.py : écarts appariés en points faits.
- test_detective2.py : qualité des mains imaginées (écarts atouts/longueurs/As,
  proba et Brier sur V/9/A d'atout ET sur As hors atout). Le contrôle « 0 pli » donne le bruit.
- diag_temperature.py : écarts de notes du réseau (un seul processus).

## Résultats clés
- detective_v3.py (tirage + filtre des règles via cartes_jouables + rejeu des enchères,
  tolérance 0,1) : bien meilleur que l'ancien generateur_contraintes.py (~20 % de donnes
  impossibles, fourchettes d'atouts fausses).
- BotMCIAv3 (bot_mc_ia_v3.py) = CHAMPION. Confirmé sur 2 x 5000 donnes neuves :
  v3 - IA pure = +2,3 à +2,7 pts faits ; en MARQUE +12,2 ± 3,9 par donne.
  Attaque forte, défense plus faible en points faits. ~3 s par partie.
  Limite : mesuré quand tous annoncent en Système v2 (test de robustesse à faire).
- 40 simulations vs 20 : points faits +0,5 ± 0,5 (non prouvé) ; MARQUE +5,6 ± 3,7
  (défense +6,7 ± 5,3). Temps x1,9. Piste : budget adaptatif (+20 sim. si décision serrée).
- Détective v4 (detective_v4.py, BotMCIAv4 et BotMCIAv4T03) : v3 + lecture par le réseau
  de l'entame et de la 1re défausse de chaque joueur (poids exp(écart/T), plancher 0,05).
  Gain modeste, seulement après 4 plis (Brier As côté 0,140 -> 0,130). Écarts de notes
  très faibles (médiane -0,007) : T=0,1 trop doux, essayer T=0,03.
  Benchmark v4 (graine 7 000 000, 5000 donnes, resultats_v4.jsonl) : lancé ou à lancer.
- Coinche (règle force d'atout, experience_coinche.py) : 24 % des contrats coinchés,
  64 % de chutes. Rentable à 110-130, équilibre à 80-90, perdante à 140 (n=30).
  Contrats normaux à 130 : ~38 % de chutes (enchères disputées à examiner).
- test_as_10.py : IA pure défausse l'As depuis As-10 (règle en dur), v3 50/50.

## Découvertes sur le code
- Tous les bots annoncent via systeme.py + niveau_v2. MAIS BotIA (jouer.py) utilise
  reponse_variante("court"), les autres la réponse standard -> à unifier (SystemeOfficiel),
  puis nouveau benchmark de référence. Le détective doit rejouer le même système.
- veut_coincher Monte-Carlo de systeme.py = code mort (masqué par SysCoinche),
  bug getattr(self,"moi",0) inactif. decision_capot et decision_disputee = crochets vides.
- nb_simulations réellement fixé par JoueurMonteCarlo.__init__ (montecarlo.py l.128,
  défaut 20), qui écrase l'attribut de classe. Correction prévue au ménage.
- App : niveaux BotCoop / BotGrandMaitre (=ancien BotMCIA) / BotIA, tous ~même force ;
  le v3 n'y est pas. L'app transmet bien enchères et historique (l.105, 185-186).
  Elle a sa propre phase d'enchères (l.105-154), distincte de partie.phase_annonces.
- Réseau ia_carte.pt (30 oct. 14:26) produit par ia_entrainer_mix3.py, qui AFFINE le
  réseau existant : non reproductible, fichier le plus précieux. FICHIER importé
  d'ia_joueur -> tout entraînement écrase ia_carte.pt (à l'avenir : ia_carte_candidat.pt).
  mix3 dépend d'ia_imitation_entrainer.py (données .npz, emplacement à vérifier).
  Encodage modifié le 30 oct. : sauvegardes .pt antérieures probablement incompatibles.
- signaux.py / experience_signaux.py : utilisés seulement par la démo de rapide.py
  (lecture à confiance fixe 0,8) = origine du chiffre « -0,9 à +1,9 pt » du rapport.
- Le lecteur v4 utilise le réseau brut (sans règle As-10) : incohérence à corriger.

## Conventions décidées (signaux)
- Attaque, 1re défausse : As défaussé = j'ai la carte maître suivante ; 10 défaussé = pas
  l'As ; petite carte (7 à R) = appel. Comparer : témoin, appel direct, appel croisé
  (rouge/noir, couleur orpheline de la paire d'atout = direct), rejet.
- Signal par départage (seulement parmi cartes équivalentes) ; couleur appelée libre.
- Défense : pas d'appel ; singlette au jugement de l'IA.
- Lecture par tous les joueurs, avec tolérance aux violations (jamais d'exclusion totale).
- Règle As-10 unique (celle d'ia_joueur.py) à appliquer au v3, aux joueurs simulés et au lecteur.

## Git et ménage
- Commits locaux : v3 confirmé, ménage 1 (22 essais -> archives/), ménage 2 (études ->
  archives/etudes/), test 40 sim. Pas de push. origin/main = « Interface épurée ».
  Avant push : vérifier dans Render la branche surveillée et Auto-Deploy ; copie de
  secours possible via git push origin main:sauvegarde ; tester l'app en local ;
  envoyer ia_carte.pt et ia_encodage.py ensemble.
- inventaire.py (points de départ : app, benchmark_confirmation, rapport, jouer,
  ia_entrainer_mix3) : 52 utilisés, 45 non utilisés.
- Ménage 3 à faire : vérifier qu'aucun fichier n'importe le groupe C, puis archiver
  ia_entrainer, ia_entrainer_mix, ia_chute160, ia_lookahead, test_lookahead, ia_evaluer2,
  mc_ia, test_mcia, test_mc_ia_vs_mc, diagnostic_ia_vs_mc, test_coinche_securisee,
  test_donnes_pures, test_donnes_pures_match, tournoi_super_joueurs, test_entame_attaque,
  test_valet, test_effet_masque. Puis examiner les cas douteux (coinche1, regle, verif,
  diagnostic, bilan_global, comparer_main, match_systeme, tournoi, verif_dispute,
  benchmark_oracle, test_mc, stats_chutes, test_mc_robustesse, ia_imitation_encheres).

## Tâches en attente (ordre proposé)
1. Résultat benchmark v4 : --analyse puis comparer_marque.py resultats_v4.jsonl.
2. Ménage 3, puis benchmark unique avec options (marque affichée), détective unique
   intégré au bot (sans remplacement temporaire), correction nb_simulations.
3. Système d'enchères officiel unique + nouveau benchmark de référence.
4. Règle As-10 unifiée ; test de robustesse (adversaires hors Système v2).
5. Budget adaptatif de simulations.
6. Enchères : benchmark en matchs de 1000 pts avec surcoinche enregistrée ; coinche
   aux extrêmes ; enchères disputées.
7. Signaux : politiques de défausse ; réentraînement du réseau sur le v3 (et sur la marque).
8. Interface : wc -l app.py templates/index.html ; v3 dans l'app après robustesse et
   mesure de vitesse sur Render.

