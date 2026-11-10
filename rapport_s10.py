"""
rapport_s10.py
Section 10 : Le simulateur en ligne & Mode d'entraînement (Version 2.0 actualisée)
"""
from rapport_outils import titre, paragraphe, puces, encadre


def section_simulateur(doc):
    titre(doc, "10. Le simulateur en ligne & Mode d'entraînement")
    paragraphe(doc, "Pour permettre à chacun de s'entraîner, de vérifier ces principes et de mesurer son niveau face à l'IA, "
               "l'ensemble de ces travaux de recherche a été intégré dans une application web interactive complète, "
               "accessible gratuitement sur tout navigateur (ordinateur, tablette, smartphone) :")

    encadre(doc, "🌐 **Accès direct au jeu en ligne** : **https://coinche-ia.onrender.com**\n\n"
            "*(Hébergé en accès libre. Lors de la première visite, le serveur peut mettre une trentaine de secondes à se réveiller).*")

    titre(doc, "Fonctionnalités de l'outil d'entraînement", 2)
    puces(doc, [
        "**Deux niveaux de jeu nets** : affrontez soit l'**IA Rapide** (réseau de neurones pur V2, jeu instantané en 11 ms), soit le **Grand Maître** propulsé par notre champion officiel **Bot-MC-IA v6** (Plis 1-3 en réseau V2, Plis 4-8 en Monte-Carlo 40 simulations avec Détective v3, calculé en 1,5 s par partie).",
        "**Multi-joueurs étanche** : chaque joueur dispose de sa propre table de jeu isolée par session UUID : zéro interférence entre joueurs.",
        "**Vraie ergonomie de table** :",
        "  • *Éventail de grandes cartes chevauchées* : les cartes se déploient en éventail avec index toujours visible et se soulèvent de manière feutrée au survol.",
        "  • *Distribution authentique 3-2-3* : tour de table horaire à partir de la gauche du donneur, avec découverte brute des cartes avant rassemblement par couleur.",
        "  • *Widget permanent « Dernier Pli »* : disposé en croix aux 4 points cardinaux dans le coin supérieur gauche du tapis avec carte gagnante cerclée d'or, et zoom grand format plein écran au clic.",
        "  • *Prise en charge de la Surcoinche (x3)* lorsque l'adversaire ose contrer votre contrat.",
        "  • *Contrôles clavier intégraux* : touche `Entrée` pour enchaîner les donnes, valider les choix et fermer les zooms ; touche `Espace` pour passer aux annonces.",
        "**Mode Professeur & Bilan pédagogique** :",
        "  • *Aux enchères* : analyse tour par tour avec tableau comparatif des espérances en points de marque des 3 meilleures options et confrontation à la grille officielle du Système v2.",
        "  • *Au jeu de la carte* : évaluation de chacun de vos 8 plis par le moteur champion v6, avec détection des erreurs tactiques, des manquements aux conventions maîtresses (As-10) et des dons de points.",
        "  • *Revue interactive du replay* : possibilité de revoir n'importe quel pli au centre du tapis vert avec les 4 mains reconstituées en temps réel.",
        "**Baromètre de chance scientifique en fin de match** :",
        "  • *Potentiel de Maître (0 à 67 pts)* : mesure objective de la part de distribution reçue par votre équipe (indépendamment de l'atout choisi), basée sur les couleurs 5es V-9 et les As.",
        "  • *Vrais Bad Beats (Poisse certifiée)* : décompte des contrats raisonnables chutés alors que vous avez joué sans commettre la moindre faute tactique.",
        "  • *Braquages réussis (Coups de chance)* : décompte des contrats tendus réussis ou des chutes adverses provoquées malgré un jeu inférieur.",
        "**Bouton d'exportation en 1 clic (📋)** : copie instantanément le rapport complet de la donne (mains de départ, enchères, film des plis, décompte) pour analyse ultérieure."
    ])

    paragraphe(doc, "Cet outil a été conçu pour faire le pont entre la théorie statistique du laboratoire et la pratique réelle de la table : "
               "il permet d'acquérir les bons automatismes d'annonces, de coinche et d'entames en toute bienveillance.")
