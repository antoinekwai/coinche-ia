from rapport_outils import titre, paragraphe, puces, tableau, encadre


def section_methode(doc):
    titre(doc, "2. Comment on a procédé")

    titre(doc, "Un simulateur de coinche", 2)
    paragraphe(doc, "Nous avons programmé un simulateur qui respecte les règles habituelles : "
               "32 cartes, obligation de fournir, de couper et de monter à l'atout, belote, "
               "dix de der, annonces de 80 à 160 par paliers de 10, capot à 250, coinche (×2) "
               "et surcoinche (×3). Le barème étudié est le suivant :")
    puces(doc, [
        "**Contrat réussi** : l'équipe qui a pris marque la valeur du contrat.",
        "**Contrat chuté** : la défense marque la valeur du contrat.",
        "**Belote** : elle aide à atteindre le contrat, mais ne s'ajoute pas au score.",
    ])
    paragraphe(doc, "Toutes ces règles sont réglables. D'autres barèmes pourront être étudiés "
               "plus tard, et les conclusions pourraient alors changer.")

    titre(doc, "Des joueurs virtuels de différents niveaux", 2)
    tableau(doc, ["Joueur", "Comment il joue"], [
        ["Aléatoire", "Joue au hasard parmi les cartes autorisées (sert uniquement de repère)"],
        ["À règles", "Applique des principes simples : faire tomber les atouts, encaisser ses as, "
                     "prendre le pli au plus juste, charger quand le partenaire est maître"],
        ["Simulation (Monte Carlo)", "Avant chaque carte, imagine une vingtaine de répartitions "
                     "possibles des cartes cachées, joue la suite dans sa tête, et choisit la carte "
                     "qui réussit le mieux en moyenne"],
        ["Simulation qui lit les enchères", "Même principe, mais n'imagine que des répartitions "
                     "compatibles avec les annonces de chacun, passes comprises. "
                     "C'est notre meilleur joueur"],
        ["IA de jeu de la carte", "A appris à jouer en imitant les joueurs par simulation sur des "
                     "millions de décisions. Joue à leur niveau, environ 25 fois plus vite"],
    ], largeurs=[4, 12.5])
    paragraphe(doc, "Une autre IA, entraînée à **estimer les chances de réussir chaque contrat** "
               "avec une main donnée, a servi à repérer des améliorations du système d'annonces.")

    titre(doc, "Éliminer la chance : le « duplicate »", 2)
    paragraphe(doc, "À la coinche, le hasard de la donne pèse énormément : une équipe peut gagner "
               "une partie simplement parce qu'elle a reçu les beaux jeux. Pour comparer deux façons "
               "de jouer, nous utilisons donc la méthode des tournois de bridge : **chaque donne est "
               "jouée deux fois avec les mêmes cartes, en inversant les équipes**. Si l'équipe A "
               "reçoit un jeu en or à la première table, l'équipe B le reçoit à la seconde. "
               "La chance s'annule, il ne reste que la différence de niveau.")
    paragraphe(doc, "Chaque comparaison porte sur **plusieurs milliers de donnes**, et jusqu'à "
               "500 000 pour les études de situations de jeu.")

    titre(doc, "Deux autres méthodes", 2)
    puces(doc, [
        "**Les tableaux de mains** : pour une main type du preneur, des milliers de donnes sont "
        "jouées avec des mains aléatoires pour les trois autres joueurs. On mesure la probabilité "
        "d'atteindre chaque palier (section 3).",
        "**Les études de situations** : quand une situation se présente (par exemple « mon "
        "partenaire est maître, j'ai un 10 »), la donne est jouée deux fois avec les mêmes cartes, "
        "en imposant une décision puis l'autre. Le reste de la donne est joué à l'identique.",
    ])
    paragraphe(doc, "**Le choix du juge.** Chaque conclusion a été vérifiée par au moins deux joueurs "
               "virtuels différents. Pour comparer des systèmes d'annonces, le juge final est le "
               "joueur par simulation classique : il ne lit pas les enchères, et ne favorise donc "
               "aucun système.")

    titre(doc, "Comment lire un résultat", 2)
    paragraphe(doc, "Les résultats sont donnés en **points gagnés par donne**, avec une marge d'erreur. "
               "Par exemple : **+7 ± 3**.")
    puces(doc, [
        "**+7** : la méthode A rapporte en moyenne 7 points de plus par donne que la méthode B.",
        "**± 3** : le vrai écart se situe, de façon quasi certaine (95 %), entre +4 et +10.",
        "Si la marge **inclut 0** (par exemple +1 ± 2), on ne peut **pas** conclure qu'il existe "
        "une différence.",
    ])
    paragraphe(doc, "Pour parler concrètement : une partie en 1000 points dure environ **11 donnes**. "
               "Un gain de +7 par donne représente donc **environ 80 points par partie**. "
               "C'est un ordre de grandeur, pas un chiffre exact.")

    encadre(doc, "**Les contrôles** : avant de faire confiance à la méthode, nous avons opposé un "
            "joueur à lui-même. Le résultat devait être zéro, et il l'a été à chaque fois. "
            "Chaque résultat surprenant a aussi été **revérifié avec davantage de donnes** "
            "avant d'être retenu.")

