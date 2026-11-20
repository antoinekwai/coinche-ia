"""
rapport_s10_match_play.py
Section 10 : La Stratégie de Match Play — Comment le score transforme les décisions de fin de match
"""
from rapport_outils import titre, paragraphe, puces, tableau, encadre


def section_match_play(doc):
    titre(doc, "10. La Stratégie de Match Play : L'Équation de Bellman")
    paragraphe(doc, "Jusqu'ici, les décisions étaient analysées à l'échelle d'une donne isolée, comme si chaque mène "
               "démarrait à 0-0. Or, dans une vraie partie en 1 000 points (ou 1 500 en FFB), **le score global du match "
               "bouleverse la valeur relative des risques** à l'approche de la ligne d'arrivée.")

    paragraphe(doc, "En appliquant la méthode de programmation dynamique des super-ordinateurs de Backgammon et de Bridge "
               "(Résolution rétrograde de l'Équation de Bellman), notre modèle a calculé la matrice complète d'équité de match "
               "qui donne la **probabilité réelle de victoire finale P(Win) pour chaque score possible**.")

    titre(doc, "1. La Carte Thermique de la Victoire", 2)
    tableau(doc, ["Score (NOUS — EUX)", "P(Victoire) Barème Sec (1000)", "P(Victoire) Barème FFB (1500)", "Enseignement clé"], [
        ["500 — 500", "50,0 %", "50,0 %", "Parité parfaite"],
        ["600 — 400 (ou 900-600)", "70,2 %", "64,5 %", "Avance plus fragile en FFB"],
        ["800 — 500 (ou 1200-750)", "84,1 %", "74,8 %", "Deux donnes suffisent à combler l'écart en FFB"],
        ["900 — 700 (ou 1350-1050)", "83,5 %", "67,5 %", "Vigilance défensive requise en FFB"],
        ["940 — 900 (ou 1440-1400)", "51,1 %", "54,2 %", "Fin de match au coude-à-coude"],
        ["300 — 800 (ou 450-1200)", "7,2 %", "15,4 %", "Le FFB offre 2 fois plus d'espoir en retard"],
        ["200 — 920 (ou 300-1420)", "1,3 % (condamné)", "9,4 % (remontada vivante)", "La prime de coinche FFB relance le match"],
        ["960 — 400 (ou 1460-600)", "96,9 %", "92,7 %", "Victoire quasi-assurée"],
    ], largeurs=[4.5, 4.5, 4.5, 4.5])

    titre(doc, "2. Le Théorème de Normalité : 90 % du match se joue normalement", 2)
    paragraphe(doc, "L'enseignement majeur de la programmation dynamique est le **Théorème de Normalité** : tant que le match "
               "n'est pas entré dans ses deux dernières donnes décisives, **toute déviation par rapport au bon jeu classique est néfaste**. "
               "On conserve son niveau d'enchères habituel, sa marge normale et son seuil de coinche 4 strict. "
               "Le jeu ne bascule que dans deux situations limites très précises :")

    puces(doc, [
        "**La Règle du « Passager Clandestin » (En tête à la fin)** : en barème officiel FFB (1 500 pts), si votre équipe est à **60 points ou moins du but (score >= 1440)** avec une avance d'au moins **130 points** (ex: 1440 vs 1310) : **PASSEZ D'ENTRÉE SYSTÉMATIQUEMENT** ! Les ~60 points garantis par la défense suffisent pour franchir 1500 sans risquer la moindre chute à -240. Prendre un contrat est la seule façon de perdre un match gagné.",
        "**Le Plafond de Victoire (Match serré à la fin)** : si vous êtes à moins de 80 points du but sans matelas suffisant pour passer (ex: 1440 vs 1400), **plafonnez votre ouverture au palier minimum qui gagne (80)**. Même avec un jeu de 110, monter n'apporte rien et réintroduit un risque de chute inutile.",
        "**Le All-In du Désespoir (En grand retard)** : si l'adversaire approche du but (>= 1420 en FFB ou >= 920 en Sec) avec plus de 400 points d'avance sur vous, passer garantit la défaite (P_win < 3 %). **La coinche kamikaze devient obligatoire dès le seuil 2-2,5**. La prime de 500 points en FFB est votre unique chance de survie (l'espérance de victoire passe de 3 % à 18 %).",
    ])

    encadre(doc, "**À retenir pour le Match Play** : jouez votre jeu d'école le plus propre pendant 90 % de la partie. "
            "Ne changez de braquet que dans les deux dernières donnes : **le Passager Clandestin pour verrouiller la gagne, "
            "le All-In pour braquer le destin.**")
