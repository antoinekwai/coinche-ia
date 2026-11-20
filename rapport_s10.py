"""
rapport_s10.py
Section 11 : Le simulateur en ligne & Mode d'entraînement officiel
"""
from rapport_outils import titre, paragraphe, puces, encadre


def section_simulateur(doc):
    titre(doc, "11. Le simulateur en ligne & Mode d'entraînement")
    paragraphe(doc, "Pour permettre à chacun de s'entraîner, de vérifier ces principes et de mesurer son "
               "niveau face à l'IA, l'ensemble de ces travaux de recherche a été intégré dans une "
               "application web interactive complète, accessible gratuitement sur tout navigateur :")

    encadre(doc, "🌐 **Accès direct au jeu en ligne** : **https://coinche-ia.onrender.com**\n\n"
            "*(Hébergement libre : réveil en ~30s lors de la première visite).*")

    titre(doc, "Fonctionnalités de l'outil d'entraînement", 2)
    puces(doc, [
        "**Deux niveaux de jeu nets** : affrontez soit l'IA Rapide (réseau V2 pur, jeu instantané en 11 ms), soit le Grand Maître propulsé par notre champion officiel **Bot-MC-IA v6.1** (Plis 1-3 en réseau V2, Plis 4-8 en Monte-Carlo 40 simulations avec continuité de score `bilan_passe`).",
        "**Choix du Barème Officiel** : sélecteur direct au lancement entre le Barème Standard (« Contrat sec » en 1 000 pts) et le **Barème Officiel FFB** (points faits arrondis à la dizaine avec règle du Der à 5 en 1 500 pts).",
        "**Multi-joueurs étanche** : chaque joueur dispose de sa propre table de jeu isolée par session UUID : zéro interférence entre joueurs.",
        "**Ergonomie de table feutrée (960 px)** : disposition chaleureuse resserrée sur grand écran évitant tout vide, et parfaitement adaptative sur mobile et tablette.",
        "**Distribution authentique 3-2-3 & Coupe interactive** : choix de l'endroit où couper le jeu (haut, milieu, bas, aucune) avant la distribution dans le sens horaire avec paquet persistant.",
        "**Prise en charge de la Surcoinche interactive (x3)** : cycle de parole séquentiel officiel après une coinche adverse avec boutons stables fixes.",
        "**Feuille de Marque Officielle (Scoreboard)** : grand tableau carnet affiché après chaque donne avec rappel des contrats, totaux progressifs et étoile dorée **★ Capot** non annoncé.",
        "**Ambiance sonore réaliste (0 ms)** : pose feutrée sur petite carte, claquement sec d'impact sur carte maîtresse et son lourd de gong sur Coinche/Surcoinche.",
        "**Mode Professeur & Bilan pédagogique** : évaluation de chaque carte avec seuil de bienveillance à 8 %, détection des erreurs doctrinales aux enchères et calcul de la **Précision officielle des Enchères en %**.",
        "**Revue interactive du replay** : réexamen de chaque pli au centre du tapis vert avec les 4 mains reconstituées en cartes agrandies et lisibles (52x76 px).",
        "**Baromètre de chance scientifique** : calcul du Potentiel de Maître (0 à 67 pts), identification des vrais Bad Beats et des vrais Braquages réussis.",
        "**Bouton d'exportation en 1 clic (📋)** : copie instantanée du rapport complet de la donne pour analyse ou partage."
    ])

    paragraphe(doc, "Cet outil a été conçu pour faire le pont entre la théorie statistique du laboratoire et la "
               "pratique réelle de la table : il permet d'acquérir les bons automatismes d'annonces, de "
               "coinche et d'entames en toute bienveillance.")
