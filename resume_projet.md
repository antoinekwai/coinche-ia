# CONTEXTE COINCHE IA (mise à jour)

## Utilisateur
Débutant en code, projet écrit par Claude. Mac M1 Pro, commande python3.
Attendu : explications pédagogiques, fichiers complets ou modifications ciblées,
avis professionnel et critique (dire clairement quand une idée n'est pas idéale).

## Méthode de mesure
- benchmark_nuit_v2/v3/v4/confirmation.py : résultats écrits donne par donne (.jsonl),
  reprise automatique, hasard fixé par donne, comparaisons appariées, marge à 95 %.
- Oracle exact dès le pli 2 (pli 1 joué par le réseau, pour la vitesse).
- Adversaire commun : MC-Enchères. Camp testé : équipe 0. Enchères transmises aux bots (v3+).
- test_detective2.py : qualité des donnes imaginées par critères (écarts atouts, longueurs,
  As, proba vraie sur V/9/As d'atout, Brier). Quelques secondes.

## Résultats clés
- Tous les bots annoncent via systeme.py + niveau_v2 (Système v2). Enchères déterministes (50/50).
- Sans enchères transmises, l'IA pure était handicapée (+2,3 pts quand on les lui donne).
- Ancien détective (generateur_contraintes.py) : ~20 % de donnes impossibles après 4 plis,
  fourchettes d'atouts fausses, répartitions biaisées.
- detective_v3.py : tirage au hasard + filtre des règles du jeu + rejeu des enchères
  (tolérance 0,1 par différence, 300 essais). Après 4 plis : proba vraie 72 % (vs 60 %), Brier 0,086.
- bot_mc_ia_v3.py (BotMCIAv3) = Bot-MC-IA + détective v3. NOUVEAU CHAMPION.
- Confirmation 5000 donnes neuves (graine 5 000 000) :
  Oracle 94,6 | v3 84,8 | Bot-MC-IA 82,1 | IA pure 82,1 pts/donne.
  v3 - IA pure : global +2,7 ± 0,5 ; attaque +4,5 ± 0,7 ; défense +0,9 ± 0,7.
  v3 : 3,1 s par partie (vs 0,4 s IA pure).
  Limite : mesuré quand tous les joueurs annoncent en Système v2.
- Bot-Coop : signaux inefficaces car émetteur et lecteur ne suivent pas la même règle,
  « rejet » traité comme un appel, partenaire simulé arbitraire (retour[0]), singlette supposée partout.
- test_as_10.py : avec As+10 en défausse, IA pure jette l'As 17 fois, le 10 jamais
  (règle en dur dans ia_joueur.py) ; v3 : 5 As / 5 dix (illisible pour le partenaire).

## Conventions décidées
- Attaque, première défausse seulement. As défaussé = j'ai la carte maître suivante.
  10 non maître défaussé = je n'ai pas l'As. Petite carte (7 à R) = appel.
- Politiques à comparer : témoin, appel direct, appel croisé (rouge/noir ; couleur orpheline
  de la paire d'atout = appel direct), rejet.
- Signal par départage : seulement parmi les cartes que le Monte-Carlo juge équivalentes.
  Couleur appelée libre (préférence : la plus courte, sauf si annoncée par l'adversaire).
- Défense : pas d'appel ; singlette au jugement de l'IA, lue par la lecture naturelle.
- Lecture : par tous les joueurs (adversaires compris), avec tolérance aux violations.
- Détective v4 prévu : v3 + pondération des mains imaginées par le réseau
  (« un bon joueur aurait-il joué cette carte ? ») sur l'entame et la première défausse.
- Règle As-10 : une seule règle partagée (celle de ia_joueur.py), à appliquer au v3,
  aux joueurs simulés et au détective. signaux2.py (compter_violations) garde le rôle de lecture.

## Fichiers créés récemment
benchmark_nuit_v2/v3/v4.py, benchmark_confirmation.py, comparer_fichiers.py, comparer_v3_ia.py,
test_detective.py, test_detective2.py, detective_v2.py, detective_v3.py, bot_mc_ia_v3.py,
signaux2.py (l'ancien signaux.py est conservé), test_as_10.py, qui_annonce.py.

## Tâches en attente
1. Commit Git (avec .gitignore : ~$*, *.jsonl, __pycache__/, .DS_Store). Pas de push.
2. Vérifier dans Render : branche surveillée et Auto-Deploy.
3. Règle As-10 unifiée : envoyer cartes_sont_equivalentes_rapide (grep -n "equivalentes" ia_joueur.py).
   Décider si elle s'applique partout (défense, quand on fournit).
4. Test 40 simulations (BotMCIAv3x40, 2000 donnes, graine 6 000 000).
5. Test de robustesse : adversaires annonçant autrement que le Système v2.
6. Détective v4, puis comparaison des politiques de signaux.
7. Interface : wc -l app.py templates/index.html ; ce qui gêne, qui l'utilise, envies.
8. Ménage des fichiers expérimentaux.
