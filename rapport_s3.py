from rapport_outils import titre, paragraphe, puces, tableau, encadre
from donnees_mains import V9, VALET, NEUF, SANS_V9, V9_FORTES

LARGEURS = [6.2, 1.5, 1.5, 1.4, 1.4, 1.4, 1.4, 1.8]


def lignes(donnees):
    return [[m, str(n), str(pts)] + [f"{p} %" for p in probas] + [palier]
            for (m, n, pts, *probas, palier) in donnees]


def famille(doc, nom, donnees):
    titre(doc, nom, 2)
    tableau(doc, ["Main du preneur", "Atouts", "Pts", "80", "100", "120", "140", "Palier 4/5"],
            lignes(donnees), largeurs=LARGEURS, taille=9)


def section_mains(doc):
    titre(doc, "3. Ce que vaut une main")
    paragraphe(doc, "Pour 48 mains « types » du preneur, nous avons joué des milliers de donnes avec "
               "des joueurs par simulation aux quatre places. Les cartes clés sont fixées, le reste "
               "est complété au hasard par des cartes sans valeur particulière (pas d'as, de 10 ni "
               "de belote, sauf mention contraire). Les mains du partenaire et des adversaires sont "
               "quelconques : c'est la valeur d'une main **avant toute enchère**.")
    paragraphe(doc, "**Ces mains types couvrent environ 98 % des mains qui justifient d'ouvrir.** "
               "Les colonnes 80 à 140 donnent la probabilité que l'équipe du preneur atteigne le "
               "palier (belote comprise). « Pts » est le nombre moyen de points réalisés. "
               "« Palier 4/5 » est le palier le plus haut atteint au moins 4 fois sur 5. "
               "Dans chaque famille, les mains sont classées de la plus faible à la plus forte.")

    famille(doc, "Valet et 9 d'atout (2 à 4 atouts)", V9)
    titre(doc, "Valet et 9 d'atout (5 atouts et plus)", 2)
    tableau(doc, ["Main du preneur", "Atouts", "Pts", "120", "140", "160", "Capot", "Palier 4/5"],
            lignes(V9_FORTES), largeurs=LARGEURS, taille=9)
    paragraphe(doc, "La colonne « Capot » est mesurée quand l'équipe **vise** le capot et que la "
                    "défense cherche à l'empêcher.")
    famille(doc, "Valet sans le 9", VALET)
    famille(doc, "9 sans le valet", NEUF)
    famille(doc, "Ni valet ni 9", SANS_V9)

    titre(doc, "Ce que vaut chaque carte", 2)
    tableau(doc, ["Élément ajouté", "Gain moyen"], [
        ["Le valet au lieu du 9", "+13 points"],
        ["Un atout supplémentaire", "+10 à +13 points"],
        ["Le 9 à côté du valet", "+12 points"],
        ["Un as à côté", "+11 à +12 points"],
        ["Un 2e ou un 3e as", "+10 points"],
        ["Le 10 qui accompagne un as", "+6 à +10 points"],
        ["L'as d'atout au lieu d'un petit atout (avec V 9)", "+4 points"],
        ["Un 10 sec au lieu d'une petite carte", "−2 à −4 points"],
    ], largeurs=[10, 4])

    titre(doc, "Les enseignements", 2)
    puces(doc, [
        "**Chaque bonne carte vaut 10 à 12 points** : un as, un atout de plus, le 9 avec le "
        "valet. Un 4e atout vaut un as.",
        "**Le valet long est une vraie force** : valet quatrième avec un as vaut autant que "
        "V 9 troisièmes avec un as.",
        "**V 9 secs se jouent dès qu'on a des as** : avec 1, 2 ou 3 as, on atteint 80, 90 ou 100 "
        "environ 4 fois sur 5.",
        "**Le 9 sans le valet est faible** : il faut 4 atouts, ou 3 atouts et 2 as, pour ouvrir.",
        "**Sans valet ni 9, on passe**, sauf avec A R D et la belote.",
        "**Pour les mains fortes, la forme compte plus que les as** : As-10 troisième avec deux "
        "couleurs absentes donne 67 % de capots, contre 39 % avec deux as secs.",
        "**Le 10 sec est un léger handicap** : sur une main à la limite, il fait descendre d'un cran.",
        "**La position compte très peu** : entamer ou non ne change les probabilités que de 1 à 3 %.",
    ])
    encadre(doc, "**Attention au double comptage** : ces chiffres incluent l'aide **moyenne** d'un "
            "partenaire quelconque. Ce ne sont donc **pas** des niveaux d'ouverture dans un système "
            "où le partenaire remonte avec ses as : l'ouvreur annonce sa propre main, le partenaire "
            "complète. En pratique, aligner directement les ouvertures sur ce tableau n'a rapporté "
            "qu'environ 1,5 point par donne, car les deux approches aboutissent souvent au même "
            "contrat final.")

