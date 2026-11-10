"""
rapport_s8.py
Section 8 : Les limites de l'étude (Version 2.0 actualisée)
"""
from rapport_outils import titre, paragraphe, puces


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
