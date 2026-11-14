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
    tableau(doc, ["Comparaison (jeu de la carte impartial par simulation)", "Écart par donne"], [
        ["BILAN GLOBAL : Système Recommandé complet vs Système d'origine", "+13,2 ± 1,6 (prouvé)"],
        ["Système corrigé initial contre système d'origine", "+7,4 ± 2,8"],
        ["Ouvertures calibrées sur les mains types (v2) contre système corrigé", "+1,5 ± 1,1"],
        ["Réponse prudente sur 80 (0 ou 1 atout) contre réponse habituelle", "+2,1 ± 1,6"],
        ["IA par apprentissage contre système recommandé", "+0,8 ± 2,9 (égalité parfaite)"],
    ], largeurs=[11.5, 5.0])


    paragraphe(doc, "Les règles corrigées, applicables à la table, **font jeu égal avec l'IA**. "
               "Les principales corrections : ne plus ouvrir au 9 sans le valet avec un seul as, "
               "accepter la longueur d'atout ou la belote à la place de l'as à côté, et annoncer "
               "plus haut avec les belles mains.")
    encadre(doc, "**Des réglages robustes** : l'audace d'ouverture, la marge, le plafond à 130 et la "
            "coinche ont été revérifiés avec notre meilleur joueur virtuel au jeu de la carte. "
            "Toutes les conclusions sont restées identiques.")

    titre(doc, "Les enchères disputées et la Loi des Levées Totales", 2)
    paragraphe(doc, "Quand les adversaires interviennent dans une couleur concurrente, la donne bascule dans un duel bicolore. "
               "Pour comprendre la physique réelle de ces affrontements sans aucun biais de détective ou de simulation imaginaire, "
               "nous avons fait jouer **2 500 donnes réelles disputées dans les deux sens** (chaque camp jouant successivement dans son atout sur les mêmes cartes). "
               "Les résultats révèlent les lois mécaniques de l'affrontement :")

    puces(doc, [
        "**La Loi des Levées Totales à la coinche** : en moyenne, le Camp 0 fait 113,2 points dans son atout et le Camp 1 fait 115,2 points dans le sien. "
        "La somme des deux camps atteint **228,4 points (soit un surplus offensif massif de +66,4 points au-delà de 162)** ! "
        "L'équipe qui joue dans son atout convertit ses petites cartes en levées grâce aux coupes : laisser jouer l'adversaire à 80 ou 90 coûte en moyenne -67 à -77 points de marque en défense.",
        "**Le mur du palier 110 avec 3 atouts** : un preneur détenant 3 atouts dont le partenaire a passé ne réussit à 110 que dans **23,0 % des cas réels** (chute dans plus de 3 donnes sur 4 !). "
        "Surenchérir seul à 110 avec 3 atouts sans soutien est une faute mathématique lourde.",
        "**Le saut qualitatif du 5e atout** : passer de 3 à 4 atouts ne fait gagner que +3,7 points réels ; en revanche, **passer de 4 à 5 atouts fait exploser le score de +12,4 points réels** (de 113,6 à 126,0 pts) et porte le taux de réussite à 110 à **77,6 %** (le seuil de sécurité) !",
        "**La chicane franche rapporte deux fois plus qu'un As** : un As extérieur apporte +6,8 points réels, alors qu'une chicane franche apporte **+11,7 points d'un coup** grâce aux coupes franches et à l'affranchissement des couleurs.",
        "**La Belote en main (+20 points inaliénables)** : avec 3 atouts sans Belote, le taux de succès à 110 est de 23 % ; avec la Belote (R et D d'atout), **il bondit à 68,5 %** !"
    ])

    doc.add_page_break()
    encadre(doc, "**RÈGLE OFFICIELLE : Les 4 critères objectifs de surenchère à 110+ (validés sur 2 500 donnes)** :\n"
            "Pour disputer un contrat au palier 110 ou au-delà face à l'adversaire, l'équipe doit impérativement détenir au moins l'un de ces 4 atouts de sécurité :\n"
            "  1. Le preneur possède **au moins 5 atouts** dans sa couleur (77,6 % de succès réel d'office).\n"
            "  2. Le preneur possède **4 atouts ET au moins une chicane franche** (+11,7 pts réels de coupe).\n"
            "  3. Le preneur détient **la Belote en main** (R et D d'atout : +20 pts garantis, succès = 68,5 %).\n"
            "  4. Le partenaire a explicitement **soutenu la couleur** (promettant >= 2 atouts de soutien).\n"
            "Sans l'un de ces quatre critères, la surenchère est bannie : le Passe est obligatoire.")

    paragraphe(doc, "Nous avons opposé dans un **duel en duplicate de 250 donnes** des bots appliquant ces 4 règles objectives "
               "face à des bots simulant chaque décision d'enchère par Monte-Carlo dans le noir complet. "
               "**Résultat : les règles objectives battent la simulation de +5,4 ± 11,9 points de marque par donne**, "
               "tout en prenant 0,0001 seconde par décision. Dans le brouillard complet des annonces, les règles physiques déduites des grands nombres "
               "surpassent le bruit d'échantillonnage.")
