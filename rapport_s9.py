from rapport_outils import titre, paragraphe, puces, tableau, encadre


def section_bareme(doc):
    titre(doc, "9. L'influence du barème : la chute à 160 points")
    paragraphe(doc, "Toutes les conclusions précédentes ont été établies avec le barème standard "
               "« on marque ou on chute la valeur du contrat ». Mais à la coinche, les variantes sont "
               "fréquentes. Une règle très répandue consiste à fixer la pénalité de chute à "
               "**160 points fixes pour la défense** (320 coinché), quel que soit le niveau du contrat.")
    paragraphe(doc, "Grâce à notre IA, nous avons rejoué des dizaines de milliers de donnes sous ce "
               "nouveau barème pour mesurer comment la stratégie optimale doit s'adapter.")

    titre(doc, "1. La marge dans les enchères disputées : plus de prudence", 2)
    paragraphe(doc, "Sous le barème standard, chuter un contrat de 80 ne donnait que 80 points aux "
               "adversaires : on pouvait se permettre de pousser les enchères avec une marge de 30 points. "
               "Avec la chute à 160, **chuter un contrat de 80 coûte deux fois plus cher**.")
    tableau(doc, ["Marge testée", "Écart barème standard", "Écart barème « Chute 160 »", "Verdict"], [
        ["Marge 0 (aucune)", "−20,0", "−15,8 ± 1,1", "Ne pas se battre reste très mauvais"],
        ["Marge 10", "−7,9", "−4,3 ± 1,1", "Trop timide"],
        ["Marge 20", "−2,0", "+1,2 ± 0,8", "Devient la marge optimale (prouvé)"],
        ["Marge 30", "référence (optimale)", "référence", "Dépassée par la marge 20"],
        ["Marge 40", "−7,6", "−14,1 ± 1,1", "Pénalité doublée : bluff trop punitif"],
    ], largeurs=[3.5, 4.5, 4.5, 4.5])
    puces(doc, [
        "**L'agressivité optimale baisse d'un cran** : la marge idéale passe de 30 à **20 points**.",
        "**Pousser au-delà (marge 40) devient désastreux (−14,1)** : une chute évitable donne "
        "immédiatement 160 points à la défense.",
    ])

    titre(doc, "2. La coinche : une prime à l'agressivité", 2)
    paragraphe(doc, "À l'inverse, pour la défense, coincher un contrat de 80 qui chute rapporte désormais "
               "**320 points au lieu de 160** :")
    tableau(doc, ["Seuil de coinche", "Écart barème standard", "Écart barème « Chute 160 »"], [
        ["Seuil 2 (très agressif)", "inapplicable", "−19,2 ± 1,7"],
        ["Seuil 3 (agressif)", "−8,7 ± 1,2", "−0,7 ± 1,4 (fait jeu égal avec le seuil 4)"],
        ["Seuil 4 (référence)", "référence (optimale)", "référence (optimale)"],
        ["Seuil 5 (prudent)", "−4,5 ± 0,8", "−7,3 ± 1,0 (très pénalisant)"],
    ], largeurs=[5.5, 5.5, 6])
    puces(doc, [
        "**Le seuil 3 devient tout à fait viable** : alors qu'il était nettement perdant sous le barème "
        "standard (−8,7), il fait désormais quasiment jeu égal avec le seuil 4 (−0,7).",
        "**La passivité est plus lourdement punie** : ne pas coincher (seuil 5) coûte deux fois plus "
        "cher (−7,3 contre −4,5), car on laisse passer une prime de 320 points.",
    ])

    encadre(doc, "**À retenir pour la table** : si votre table joue la chute à 160 points fixes, "
            "**réduisez votre marge d'enchères à 20 points** (ne sur-enchérissez pas trop léger sur "
            "les petits contrats) et **coinchez un cran plus tôt** (la récompense de 320 points justifie "
            "une prise de risque accrue).")
