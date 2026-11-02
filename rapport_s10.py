from rapport_outils import titre, paragraphe, puces, encadre

def section_simulateur(doc):
    titre(doc, "10. Le simulateur en ligne & Mode Professeur")
    paragraphe(doc, "Pour permettre à chacun de s'entraîner, de tester ces principes et de se mesurer "
               "à l'IA, l'ensemble de ces travaux a été intégré dans une application web interactive, "
               "accessible gratuitement sur tout navigateur (ordinateur, tablette, smartphone) :")

    encadre(doc, "🌐 **Accès direct au jeu en ligne :**\n"
            "👉 **https://coinche-ia.onrender.com**\n\n"
            "*(Hébergé en accès libre. Lors de la première connexion, le serveur peut mettre "
            "une trentaine de secondes à démarrer son moteur d'IA).*")

    titre(doc, "Fonctionnalités de l'outil d'entraînement", 2)
    puces(doc, [
        "**Jouer contre 3 IA de haut niveau** : Votre partenaire (Nord) et vos adversaires (Est et Ouest) "
        "jouent avec le réseau de neurones calibré et appliquent le Système Recommandé aux enchères.",
        "**Le Mode Professeur (Analyse post-donne)** : À la fin de chaque donne, le moteur Monte Carlo "
        "décortique l'ensemble de vos décisions :",
        "  • *Aux enchères* : Analyse tour par tour avec calcul d'espérance mathématique réelle "
        "(gains comparés entre Passer, Surenchérir ou Coincher d'après vos 8 cartes exactes).",
        "  • *Au jeu de la carte* : Évaluation de chacun de vos 8 plis avec détection des erreurs, "
        "imprécisions, ou coups d'excellence, et explication tactique détaillée.",
        "**Revue interactive pli par pli** : Possibilité de revoir n'importe quel pli au centre du tapis vert "
        "avec les 4 mains reconstituées en temps réel telles qu'elles étaient à cet instant.",
        "**Jeton de donneur & Ordre de jeu** : Affichage visuel du donneur (🟡 D) et pastilles numérotées "
        "(①, ②, ③, ④) sur les cartes du pli pour suivre la chronologie exacte des levées.",
        "**Bouton d'exportation de donne (📋)** : Copie en 1 clic le rapport complet d'une donne "
        "(mains de départ, enchères, film des plis, décompte) pour analyse ultérieure.",
    ])

    paragraphe(doc, "Cet outil a été conçu pour faire le pont entre la théorie statistique et la pratique "
               "de la table : il permet d'acquérir les bons automatismes d'annonces et d'entames "
               "en toute bienveillance.")
