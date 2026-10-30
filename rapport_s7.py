from rapport_outils import titre, paragraphe, puces, tableau, encadre


def section_carte(doc):
    titre(doc, "7. Le jeu de la carte et les signaux")
    paragraphe(doc, "Avec ce barème, bien jouer la carte ne rapporte que lorsque cela **change l'issue "
               "du contrat** : faire 112 au lieu de 95 sur un contrat à 80 ne rapporte rien. "
               "Son poids dépend donc fortement de la façon dont on annonce.")

    titre(doc, "Ce que rapporte un meilleur jeu", 2)
    tableau(doc, ["Contexte (joueur par simulation contre joueur à règles)", "Écart par donne"], [
        ["Annonces prudentes (9 contrats sur 10 réussis), pas de coinche", "+4,4 ± 0,7"],
        ["Annonces ajustées au plus juste, pas de coinche", "+18,2 ± 1,6"],
        ["Annonces ajustées au plus juste, coinche active", "+23,8 ± 1,8"],
    ], largeurs=[11, 5.5])
    puces(doc, [
        "**Mieux on annonce, plus le jeu de la carte compte.** Avec des annonces au plus juste, "
        "beaucoup de contrats se jouent à quelques points, et chaque carte peut renverser l'issue.",
        "**La coinche renforce l'effet** : une erreur sur un contrat coinché coûte double.",
        "**Viser le contrat plutôt que les points** change peu en moyenne (0 à +2 points), mais "
        "aide pour le capot : sur les mêmes donnes, le taux de capots réussis passe de 34 % à 46 %.",
        "**20 répartitions imaginées suffisent** : avec 10, le joueur par simulation perd environ "
        "4 points par donne ; avec 50 ou 100, il n'en gagne aucun.",
    ])

    titre(doc, "Écouter les enchères aide aussi à jouer la carte", 2)
    paragraphe(doc, "Notre joueur par simulation imaginait d'abord les cartes cachées au hasard, en "
               "tenant compte uniquement des cartes jouées. Nous lui avons appris à n'imaginer que "
               "des mains **compatibles avec les enchères** : celui qui a ouvert avait une main "
               "d'ouverture, celui qui a passé d'entrée n'en avait pas.")
    tableau(doc, ["Situation", "Gain par donne"], [
        ["Il connaît le système d'annonces des adversaires", "+6,0 ± 2,5"],
        ["Il l'interprète avec de mauvaises conventions", "+2,0 ± 2,2 (aucune perte)"],
    ], largeurs=[11, 5.5])
    paragraphe(doc, "Les annonces, **y compris les passes**, renseignent sur le placement des cartes. "
               "Le bénéfice est réel quand on connaît la façon d'annoncer de ses adversaires, et "
               "lire les enchères avec de mauvaises conventions ne coûte rien.")

    titre(doc, "Une IA qui a appris à jouer", 2)
    paragraphe(doc, "Nous avons entraîné une IA à jouer la carte, d'abord seule contre elle-même, puis en "
               "imitant le joueur par simulation. Voici ses progrès, mesurés contre le joueur à règles :")
    tableau(doc, ["Étape", "Gain par donne"], [
        ["Apprentissage seule, en jouant contre elle-même (une nuit)", "+7"],
        ["Imitation du joueur par simulation", "+15"],
        ["Imitation, en apprenant à comparer les cartes entre elles", "+20"],
        ["Imitation du joueur qui lit les enchères (plus de données)", "+25"],
    ], largeurs=[11, 5.5])
    paragraphe(doc, "Elle joue désormais **au niveau du joueur par simulation**, à 2,5 points de sa "
               "version qui lit les enchères, environ **25 fois plus vite**, ce qui a permis les "
               "études détaillées ci-dessous. Le progrès le plus important n'est pas venu de données "
               "supplémentaires, mais d'une **meilleure façon de poser la question** : au lieu de "
               "prédire si le contrat allait passer, l'IA a appris à estimer de combien une carte "
               "est meilleure qu'une autre.")

    titre(doc, "Deux situations de table étudiées en détail", 2)
    paragraphe(doc, "Chaque donne a été jouée deux fois avec les mêmes cartes, en imposant une "
               "décision puis l'autre, le reste étant joué à l'identique. Chaque conclusion a été "
               "vérifiée par **trois joueurs virtuels** : l'IA par apprentissage, le joueur par "
               "simulation, et une version de ce dernier qui tient compte des enchères. Seules "
               "les conclusions partagées sont retenues.")
    paragraphe(doc, "**Mon partenaire a pris, j'ai la main, je ne sais pas où est le valet : "
               "faut-il rejouer atout ?**")
    tableau(doc, ["Mes atouts", "Atout plutôt qu'autre chose (IA / simul. / simul. + enchères)",
                  "Conclusion"], [
        ["3 ou plus", "+6,0 / +9,1 / +6,9", "Rejouer atout"],
        ["2", "+4,2 / 0,0 / +2,5", "Indifférent"],
        ["1 seul", "−1,8 / −0,5 / −1,5", "Indifférent ; plutôt garder un 9 ou un As"],
    ], largeurs=[2.8, 8.2, 5.5])
    paragraphe(doc, "**Mon partenaire est maître du pli : faut-il charger mon 10 ?**")
    tableau(doc, ["Situation", "Charger plutôt que garder (IA / simul. / simul. + enchères)",
                  "Conclusion"], [
        ["Défense, je joue en dernier", "+13,5 / +11,9 / +12,2", "Charger"],
        ["Défense, autres cas", "+9,8 / +4,7 / +4,6 (en moyenne)", "Plutôt charger"],
        ["Attaque, un adversaire joue après moi", "−4,2 / −4,5 / −9,0", "Garder"],
        ["Attaque, mon 10 est maître", "−2,8 / −0,7 / −9,8", "Plutôt garder"],
        ["Attaque, je joue en dernier", "+1,6 / +4,3 / −3,0", "Indifférent"],
    ], largeurs=[5, 7, 4.5])
    paragraphe(doc, "**Faut-il laisser passer son As pour capturer le 10 plus tard (impasse) ?**")
    tableau(doc, ["Situation (l'As gagnerait le pli)", "Mettre l'As plutôt que passer (IA / simul. + enchères)",
                  "Conclusion"], [
        ["Adversaire maître, je joue 2e", "+7,8 / +11,1", "Mettre l'As"],
        ["Adversaire maître, je joue en dernier", "−6,9 / +6,8", "Mettre l'As (non confirmé pour l'impasse)"],
    ], largeurs=[5, 6.5, 5])
    paragraphe(doc, "L'impasse ne réussit que si le 10 est placé derrière soi. Elle n'est pas "
               "rentable en moyenne, même lorsqu'elle est imprévisible.")
    encadre(doc, "**À retenir** : avec 3 atouts, on rejoue atout pour le preneur. Sur le pli du "
            "partenaire, on charge son 10 en défense, on le garde en attaque. Quand l'As gagne "
            "le pli, on le met.")
    paragraphe(doc, "**En défense, faut-il entamer sa singlette et rejouer celle du partenaire ?**")
    tableau(doc, ["Situation", "Gain du retour dans la couleur (IA / simul. + enchères)", "Conclusion"], [
        ["Toutes situations", "+2,6 / +4,6", "Le partenaire doit rejouer la couleur"],
        ["Si le défenseur a 1 seul atout", "+5,2 / +9,2", "Retour prioritaire (coupe assurée)"],
        ["Si le défenseur a 2 atouts ou plus", "+0,3 / +1,0", "Indifférent"],
    ], largeurs=[5.5, 6.5, 4.5])
    paragraphe(doc, "Entamer sa singlette n'est pas obligatoire en soi (−0,6 point en moyenne), mais "
               "**le retour du partenaire quand il prend la main est très rentable**, car il valorise "
               "l'atout unique du défenseur avant que l'attaque ne le fasse tomber.")

    titre(doc, "Les signaux de défausse", 2)
    paragraphe(doc, "Nous avons testé une convention courante : défausser **l'as** signifie « je suis "
               "maître derrière (j'ai le 10) », défausser **le 10** signifie « je n'ai pas l'as », "
               "défausser **une autre carte** signifie « j'ai peut-être l'as de cette couleur ».")
    tableau(doc, ["Test", "Écart par donne"], [
        ["Lire les signaux du partenaire", "+0,5 ± 1,7"],
        ["Bilan : émettre et lire, contre ne pas signaler", "−1,5 ± 1,6"],
    ], largeurs=[11, 5.5])
    paragraphe(doc, "**Aucun gain mesurable.** Émettre un signal oblige parfois à défausser une carte "
               "moins utile, et une défausse ordinaire est lue à tort comme un signal. Ce résultat "
               "vaut pour nos joueurs virtuels : des partenaires humains habitués l'un à l'autre en "
               "tirent peut-être davantage.")


def section_limites(doc):
    titre(doc, "8. Les limites de l'étude")
    paragraphe(doc, "Ces résultats sont solides dans le cadre de la simulation. Avant de les appliquer "
               "à la table, il faut garder en tête :")
    puces(doc, [
        "**Des adversaires prévisibles** : dans la plupart des tests, les adversaires annoncent avec "
        "le même système. Face à d'autres joueurs, les réglages optimaux peuvent varier. Un test face "
        "à un autre système a toutefois donné des résultats très proches, et la marge et la coinche "
        "ont été revérifiées avec un bien meilleur jeu de la carte.",
        "**Un jeu de la carte imparfait** : nos meilleurs joueurs virtuels jouent bien, mais pas "
        "parfaitement. Ils ne bluffent pas et ne cherchent pas à cacher leur jeu. Lire les enchères "
        "ne leur profite pleinement que s'ils connaissent les conventions adverses.",
        "**Le piège du « joueur faible »** : un outil entraîné face à des joueurs faibles apprend "
        "à exploiter leurs défauts. Nous l'avons constaté deux fois (IA d'évaluation, enchères "
        "simulées). C'est pourquoi les conclusions retenues ont été revérifiées avec le meilleur "
        "jeu de la carte disponible.",
        "**Les règles trop fines** : un joueur virtuel trouve parfois des nuances qui ne valent "
        "que pour sa propre façon de jouer. Seuls les résultats retrouvés par plusieurs joueurs "
        "différents figurent dans ce document. Plusieurs nuances proposées par l'IA ont ainsi "
        "été écartées, dont l'impasse à l'As.",
        "**Un barème particulier** : on marque ou on chute la valeur du contrat. Avec un autre barème "
        "(points faits comptés, chute fixe à 160…), les conclusions peuvent changer.",
        "**Des mains « types » complétées au hasard** : une main réelle peut s'écarter de la moyenne.",
        "**Pas de psychologie** : les habitudes des adversaires, la fatigue ou le score de la partie "
        "ne sont pas pris en compte.",
        "**Les observations trompeuses** : en défense, les contrats disputés chutent beaucoup plus "
        "souvent, et les défenseurs qui ont des as les font plus souvent chuter. Pourtant, adapter "
        "la coinche à ces observations a fait perdre des points (−2,5 et −5,1 par donne). "
        "Coincher arrête les enchères, et les facteurs observés se mélangent. Seule la mesure "
        "directe d'une décision permet de conclure.",
        "**Le choix du juge** : l'IA et le joueur qui lit les enchères ont appris les conventions "
        "de notre système. Pour comparer des systèmes d'annonces, nous avons donc utilisé comme "
        "juge final le joueur par simulation classique, qui ne lit pas les enchères et ne favorise "
        "aucun système.",
    ])
    encadre(doc, "Les chiffres de ce document sont des **repères**, pas des lois. Ils indiquent dans "
            "quelle direction corriger son jeu, et dans quelles proportions.")

