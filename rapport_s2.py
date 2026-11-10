"""
rapport_s2.py
Section 2 : Méthode et description des moteurs (Version 2.0 actualisée)
"""
from rapport_outils import titre, paragraphe, puces, tableau


def section_methode(doc):
    titre(doc, "2. Comment on a procédé")

    titre(doc, "Un simulateur de coinche rigoureux", 2)
    paragraphe(doc, "Nous avons programmé un simulateur complet qui respecte scrupuleusement les règles officielles "
               "de la Fédération Française de Belote : 32 cartes, obligation de fournir, de couper et de monter à l'atout, "
               "belote-rebelote, dix de der, annonces de 80 à 160 par paliers de 10, capot à 250, coinche (×2) et surcoinche (×3). "
               "Le barème étudié dans ce rapport est le barème standard :")
    puces(doc, [
        "**Contrat réussi** : l'équipe qui a pris marque la valeur de son contrat (+ belote éventuelle).",
        "**Contrat chuté** : la défense marque la valeur du contrat (+ belote éventuelle).",
        "**Belote** : elle aide à franchir le palier du contrat, et s'ajoute à la marque de l'équipe détentrice."
    ])

    titre(doc, "Des joueurs virtuels de différents niveaux", 2)
    tableau(doc,
        ["Joueur virtuel", "Comment il joue et rôle dans l'étude"],
        [
            ["Aléatoire", "Joue au hasard parmi les cartes légales autorisées. Sert de repère zéro."],
            ["À règles", "Applique des principes simples écrits à la main : faire tomber les atouts, encaisser ses As, monter au plus juste. Sert de test de robustesse."],
            ["MC-Enchères", "Adversaire étalon officiel des benchmarks. Annonce selon le Système v2 et joue en simulation Monte-Carlo classique (20 donnes imaginées dès le Pli 1)."],
            ["IA Réseau V1 / V2", "Réseau de neurones profond (324 entrées avec descripteurs experts). Évalue chaque coup en 11 millisecondes sans calcul d'arbre. Très fort à l'entame, mais limité sur les fins de manche complexes."],
            ["Bot-MC-IA v3 (Champion historique)", "Monte-Carlo combiné au Détective v3 (rejeu des enchères pour éliminer les mains impossibles). Domine l'IA pure de +12 pts de marque."],
            ["Bot-MC-IA v6 (Champion officiel)", "Architecture hybride à deux étages : Plis 1 à 3 joués par le réseau V2 d'élite (instantané, zéro bruit d'échantillonnage, respect des entames), puis Plis 4 à 8 résolus par Monte-Carlo 40 simulations avec Détective v3. Record du projet : 83,0 pts faits/donne en 1,5 seconde."],
            ["Oracle exact (Plafond absolu)", "Solveur mathématique parfait minimax rétrograde à cartes ouvertes dès le Pli 2. Calcule le plafond indépassable de chaque donne (l'équivalent de Stockfish aux échecs)."]
        ]
    )

    titre(doc, "Éliminer la chance : le « duplicate »", 2)
    paragraphe(doc, "À la coinche, le hasard de la donne pèse énormément : une équipe médiocre peut gagner une partie "
               "simplement parce qu'elle a reçu tous les Valets. Pour comparer scientifiquement deux méthodes, nous utilisons "
               "la méthode des tournois de bridge en duplicate : **chaque donne est jouée deux fois avec les mêmes cartes en inversant les camps**. "
               "Si l'équipe A reçoit une main en or à la première table, l'équipe B la reçoit à la seconde. "
               "La chance s'annule rigoureusement : seul le niveau de jeu fait la différence.")
    paragraphe(doc, "Chaque comparaison porte sur des séries de 500 à 5 000 donnes neuves, et jusqu'à 500 000 pour les études statistiques de mains.")

    titre(doc, "Comment lire un résultat", 2)
    paragraphe(doc, "Les résultats sont donnés en **points de marque gagnés par donne**, accompagnés de leur marge d'erreur à 95 %. Par exemple : **+7,0 ± 3,0**.")
    puces(doc, [
        "**+7,0** : la méthode testée rapporte en moyenne 7 points de marque de plus par donne que la référence.",
        "**± 3,0** : le vrai écart mathématique se situe, avec une certitude de 95 %, entre +4,0 et +10,0 points.",
        "**Si la marge inclut 0** (ex : +1,0 ± 2,5) : la différence n'est **pas statistiquement prouvée** (simple bruit aléatoire).",
        "Pour parler concrètement : un match en 1 000 points dure environ 10 à 11 donnes. Un gain de +15 points par donne représente un avantage massif d'environ **160 points par match**."
    ])
