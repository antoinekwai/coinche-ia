from rapport_outils import titre, paragraphe, puces, tableau, encadre
from fiche_ouvertures import OUVERTURES



def section_annonces(doc):
    titre(doc, "4. Les annonces")
    paragraphe(doc, "Avec un barème où l'on marque, ou l'on chute, la valeur du contrat, les annonces "
               "sont le principal levier. Nous sommes partis d'un système de joueur expérimenté, "
               "puis nous l'avons corrigé à l'aide de l'IA par apprentissage et des tableaux de la "
               "section précédente.")
    paragraphe(doc, "Le résultat est le **système recommandé**, résumé dans la fiche mémo en annexe. "
               "Il a été construit par étapes : système d'origine, puis système corrigé (ouvertures "
               "issues de l'IA par apprentissage), puis ouvertures alignées sur les tableaux de mains, "
               "et enfin réponse du partenaire ajustée sur une ouverture à 80.")

    titre(doc, "Le bon niveau d'audace", 2)
    paragraphe(doc, "Nous avons fait varier l'audace d'un même joueur, c'est-à-dire le nombre de points "
               "ajoutés à son estimation avant d'annoncer. Le résultat dessine une courbe nette :")
    puces(doc, [
        "**Trop prudent**, on laisse les adversaires jouer des donnes qu'on aurait gagnées.",
        "**Trop audacieux**, les chutes et les coinches coûtent plus cher que les contrats gagnés.",
        "**L'optimum** : annoncer le palier le plus haut que l'on réussit **environ 4 fois sur 5**. "
        "À 1 chance sur 2, on perd plus de 20 points par donne ; à 9 chances sur 10, on est trop timide.",
    ])
    paragraphe(doc, "Avec ce barème, **une chute coûte plus cher qu'une occasion manquée**.")

    titre(doc, "Les ouvertures (personne n'a parlé)", 2)
    tableau(doc, ["Annonce", "Main de l'ouvreur (atout)"], OUVERTURES, largeurs=[2.2, 14.3])


    titre(doc, "Les réponses du partenaire (adversaires silencieux)", 2)
    tableau(doc, ["Ouverture", "Le partenaire remonte de…"], [
        ["80", "+10 pour le V, +10 pour le 9 ; +10 par as si j'ai 2 atouts ou plus, "
               "+10 pour 2 as si j'en ai 0 ou 1"],
        ["90", "Avec 2 atouts ou plus : +10 par as. Avec 1 atout : +10 pour 2 as"],
        ["100, 110, 120", "+10 par as"],
        ["130 et plus", "Passe"],
    ], largeurs=[3.5, 13])
    paragraphe(doc, "L'ouvreur annonce **sa propre main**, le partenaire complète. Sur une main très "
               "forte, l'ouvreur peut remonter de 10 pour **demander les cartes maîtresses** en "
               "vue du capot (voir section 6).")
    paragraphe(doc, "**Sur une ouverture à 80, un partenaire court à l'atout reste prudent** : avec 0 ou "
               "1 atout, un as seul ne justifie pas de remonter, il en faut deux. L'ouvreur, qui n'a "
               "souvent que 3 atouts, affronterait sinon trop d'atouts adverses, et ses cartes "
               "maîtresses risqueraient d'être coupées. La règle devient ainsi identique à celle "
               "de l'ouverture à 90.")

    titre(doc, "Ce que rapportent les corrections", 2)
    tableau(doc, ["Comparaison (jeu de la carte par simulation)", "Écart par donne"], [
        ["Système corrigé contre système d'origine", "+7,4 ± 2,8"],
        ["IA par apprentissage contre système d'origine", "+8,2 ± 2,9"],
        ["IA par apprentissage contre système corrigé", "+0,8 ± 2,9 (pas de différence)"],
        ["Ouvertures alignées sur les tableaux de mains (v2) contre système corrigé", "+1,5 ± 1,1"],
        ["Réponse prudente sur 80 (0 ou 1 atout) contre réponse habituelle", "+2,1 ± 1,6"],
    ], largeurs=[11, 5.5])

    paragraphe(doc, "Les règles corrigées, applicables à la table, **font jeu égal avec l'IA**. "
               "Les principales corrections : ne plus ouvrir au 9 sans le valet avec un seul as, "
               "accepter la longueur d'atout ou la belote à la place de l'as à côté, et annoncer "
               "plus haut avec les belles mains.")
    encadre(doc, "**Des réglages robustes** : l'audace d'ouverture, la marge, le plafond à 130 et la "
            "coinche ont été revérifiés avec notre meilleur joueur virtuel au jeu de la carte. "
            "Toutes les conclusions sont restées identiques.")

    titre(doc, "Les enchères disputées", 2)
    paragraphe(doc, "Quand les adversaires parlent, la règle testée est : **monter jusqu'à la valeur de "
               "sa main + une marge, sans dépasser 130**. La valeur de la main est le niveau "
               "d'ouverture, augmenté de 10 par as annoncé par le partenaire.")
    tableau(doc, ["Marge", "Écart contre la marge de 30"], [
        ["10", "−7,9 ± 1,5"],
        ["20", "−0,5 ± 1,1 (équivalent)"],
        ["30", "référence"],
        ["40", "−6,7 ± 1,4"],
    ], largeurs=[4, 8])
    puces(doc, [
        "**Une marge de 20 à 30 points est la meilleure.** Sans marge, on perd environ 20 points "
        "par donne : l'adversaire « vole » des donnes qu'on aurait gagnées.",
        "**Le plafond à 130 s'applique à la marge, pas au jeu réel** : une équipe dont le niveau "
        "dépasse 130 peut le défendre. En revanche, pousser la marge au-delà de 130 fait perdre "
        "des points (−0,8 ± 0,6).",
        "Tenir compte de la réponse du partenaire ou de sa belote pour se défendre est naturel, "
        "mais ne change rien de mesurable.",
        "Nous avons aussi essayé de remplacer cette règle par une **simulation informatique** de "
        "milliers de donnes à chaque décision. Avec un bon jeu de la carte, elle ne fait pas mieux "
        "(+0,5 ± 1,3).",
    ])
    encadre(doc, "**À retenir** : la règle « main + 20 à 30, sans dépasser 130 » est simple, "
            "s'applique sans calcul, et fait aussi bien qu'un ordinateur.")

