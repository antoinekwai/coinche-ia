"""
rapport_s7.py
Section 7 : Le jeu de la carte & Section 8 : Les limites de l'étude (Version 2.0 actualisée)
"""
from rapport_outils import titre, paragraphe, puces, tableau, encadre


def section_carte(doc):
    titre(doc, "7. Le jeu de la carte et les conventions")
    paragraphe(doc, "Avec le barème officiel où l'on marque ou chute la valeur du contrat, bien jouer la carte "
               "ne sert qu'à une chose : **faire basculer l'issue du contrat**. Faire 115 points au lieu de 90 sur un contrat à 80 "
               "ne rapporte rien de plus ; en revanche, faire 81 points au lieu de 80 transforme une défaite à -160 en une victoire à +160. "
               "Chaque carte décisive peut créer un saut de plus de 300 points de marque d'un coup.")

    titre(doc, "La découverte de l'architecture hybride (Plis 1-3 IA, Plis 4-8 MC)", 2)
    paragraphe(doc, "Pendant longtemps, la théorie informatique supposait que plus un joueur simulait de donnes dès le Pli 1, "
               "meilleur il était. Nos benchmarks appariés sur plus de 15 000 donnes ont prouvé l'exact inverse :")
    puces(doc, [
        "**Au Pli 1**, aucune carte n'est encore tombée. L'espace combinatoire est infini (32 cartes inconnues). "
        "Lancer 20 ou 40 simulations Monte-Carlo dans un brouillard total engendre une variance d'échantillonnage destructrice : "
        "le bot sur-réfléchit, s'invente des fantômes et commet des entames aberrantes (jouer petit sous un honneur, délaisser l'atout).",
        "**Le réseau de neurones**, entraîné sur des millions de situations, possède un instinct d'entame bien plus sûr et direct "
        "(purger les atouts au preneur, attaquer ses As maîtres francs).",
        "**La bascule optimale au Pli 4** : en confiant les Plis 1, 2 et 3 à l'IA pure, puis en passant le relais au Monte-Carlo à 40 simulations "
        "dès le Pli 4 (quand 12 cartes sont visibles et les coupes révélées), le bot réalise un bond de **+26,4 points de marque** "
        "tout en divisant son temps de calcul par deux (1,3 s/partie) !"
    ])

    titre(doc, "Autopsie face au jeu parfait : où se perdent les contrats ?", 2)
    paragraphe(doc, "En comparant nos meilleurs moteurs face au solveur exact minimax cartes ouvertes (l'Oracle), "
               "nous avons mesuré à quel pli précis se produisait la première divergence fatale où le contrat devenait définitivement infaisable :")
    tableau(doc,
        ["Moment du premier décrochage fatal", "Part des donnes perdues", "Coût moyen de l'erreur"],
        [
            ["Pli 1 (Entame de la donne)", "41,7 % des donnes", "-14,1 points"],
            ["Pli 2 (Premier retour / Deuxième pli)", "20,0 % des donnes", "-18,2 points (l'erreur la plus coûteuse !)"],
            ["Pli 3", "13,3 % des donnes", "-11,8 points"],
            ["Pli 4", "8,3 % des donnes", "-11,0 points"],
            ["Plis 5 à 7", "1,7 % des donnes", "quasiment zéro divergence"],
            ["Pli 8 (Départage final du dix de der)", "15,0 % des donnes", "0 point (jeu équivalent)"]
        ]
    )
    doc.add_page_break()
    encadre(doc, "**ENSEIGNEMENT CAPITAL POUR LA TABLE** : 62 % du sort d'une donne pour la table** : **62 % du sort d'une donne de coinche se joue aux Plis 1 et 2 !** "
            "Contrairement à une idée reçue, les fautes décisives ne se produisent pas en fin de manche (où tout le monde sait compter les atouts), "
            "mais dès l'entame et le premier retour de main. Une mauvaise entame ou un partenaire passif au départ ne se rattrapent jamais.")

    titre(doc, "La Décomposition du Regret : Cartes cachées vs Faute de jeu", 2)
    paragraphe(doc, "Sur les donnes où l'Oracle bat notre meilleur bot, nous avons mesuré ce que faisait le bot si on lui révélait "
               "la vraie distribution des 4 mains dans sa tête (expérience du *Détective Omniscient*) :")
    puces(doc, [
        "**26 % de Regret Informationnel** : le bot gagne dès qu'il connaît les cartes. La défaite initiale venait uniquement du brouillard de guerre "
        "(les cartes cachées qu'aucun humain n'aurait pu deviner sans voir à travers les cartons).",
        "**74 % de Regret Tactique** : même en voyant les 4 mains ouvertes, le bot chute encore ! Cela prouve que le défi principal n'est pas "
        "de deviner les cartes adverses, mais d'exécuter le bon plan de jeu (gestion des communications, timing des coupes et conservation des As maîtres)."
    ])

    titre(doc, "La convention indispensable : le départage As-10", 2)
    paragraphe(doc, "Sans règle explicite, un moteur Monte-Carlo ou un joueur hésitant tire à pile ou face (50/50) entre défausser l'As ou le 10 "
               "sur une tenue As-10, car l'écart direct n'est que de 1 point. Pour le partenaire, cette hésitation est désastreuse.")
    encadre(doc, "**RÈGLE OFFICIELLE : Départage de la séquence maîtresse** : En attaque de la séquence maîtresse** : En attaque, sur une défausse où le pli est garanti à notre camp "
            "(en 4e position ou sur maître incontesté du preneur en 3e position), si le joueur défausse dans une couleur où il détient une séquence maîtresse "
            "(As-10, As-10-Roi, ou 10-Roi si l'As est tombé), il fournit impérativement **la carte la plus haute**. "
            "À l'inverse, en défense sur pli perdu, il jette **la plus basse** pour sauver 1 point.")
    paragraphe(doc, "Sens tactique : jeter l'As garantit au preneur que le 10 est affranchi derrière pour une reprise certaine, à coût mathématique nul.")

    titre(doc, "Le mythe de la purge aveugle au Pli 2", 2)
    paragraphe(doc, "Nous avons testé une règle rigide forçant le camp d'attaque à rejouer systématiquement atout au Pli 2 si la défense n'est pas purgée. "
               "Le résultat expérimental a été sans appel : **la marque s'effondre de -53,7 points par donne et le taux de succès est divisé par deux (26 % vs 46 %)** !")
    puces(doc, [
        "Rejouer atout à l'aveugle dénude prématurément le preneur de ses protections et l'empêche de couper les longues adverses en fin de coup.",
        "Le jeu d'élite ne purge au Pli 2 que dans environ **59 % des cas**. Dans les 41 % restants, préserver ses atouts et affranchir ses couleurs extérieures est supérieur."
    ])


def section_limites(doc):
    titre(doc, "8. Les limites de l'étude")
    paragraphe(doc, "Ces résultats sont solides et prouvés dans le cadre scientifique de la simulation par duplicate. "
               "Avant de les appliquer aveuglément à la table, il convient de garder à l'esprit plusieurs limites réelles :")

    puces(doc, [
        "**Un simulateur interne performant mais non parfait** : nos bots Monte-Carlo déroulent la fin de donne en faisant jouer un réseau de neurones profond (modèle V2). Même si ce réseau surclasse les versions antérieures (+2,5 pts faits), il ne calcule pas l'arbre parfait comme l'Oracle. Certaines manœuvres très fines (déblocages complexes, impasses différées) restent sous-évaluées.",
        "**L'hypothèse d'adversaires rationnels** : les déductions du détective v3 reposent sur le fait que la table annonce selon le Système v2. Face à des joueurs annonçant hors système (enchères sous-évaluées ou enchères fantaisistes), le détective peut temporairement attribuer des probabilités inexactes aux cartes cachées.",
        "**L'absence de psychologie et de gestion du score** : nos bots jouent chaque donne de manière isolée pour maximiser la marque brute. À la table, le score global du match conditionne la prise de risque : mener 950 à 300 incite à fermer le jeu et à refuser les contrats limites, alors qu'être mené 900 à 200 impose des coinches spéculatives.",
        "**Le barème particulier** : toutes les conclusions principales ont été établies sous le barème officiel « on marque ou on chute la valeur du contrat ». Sous un barème à points faits ou avec une chute forfaitaire à 160 points (étudié en section 9), les équilibres d'audace changent.",
        "**Des mains types complétées aléatoirement** : dans les tableaux d'annonces, les cartes non clés sont complétées au hasard. Une main réelle comportant des distributions très atypiques (ex : bicolore 5-5) peut s'écarter légèrement des probabilités moyennes indiquées."
    ])

    paragraphe(doc, "Les chiffres de ce document constituent des repères statistiques robustes, pas des dogmes rigides. "
               "Ils indiquent dans quelle direction orienter sa décision et avec quel niveau d'audace mathématique.")
