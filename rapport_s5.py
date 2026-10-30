from rapport_outils import titre, paragraphe, puces, tableau, encadre


def section_coinche(doc):
    titre(doc, "5. La coinche")
    paragraphe(doc, "Nous avons traduit en règle une façon de coincher fondée sur les atouts. "
               "On mesure la **force défensive** de sa main dans l'atout adverse :")
    tableau(doc, ["Élément", "Force"], [
        ["Valet d'atout", "+2"],
        ["9 d'atout, avec au moins 3 atouts", "+1"],
        ["Chaque atout au-delà du 2e", "+1"],
        ["Roi ou Dame d'atout (l'adversaire n'a pas la belote)", "+1"],
    ], largeurs=[11, 3])
    paragraphe(doc, "**On coinche si la force atteint 4 contre un contrat à 80**, avec 1 de moins "
               "tous les 20 points : 3 contre un 100, 2 contre un 120, etc. Plus l'adversaire "
               "annonce haut, moins il faut de cartes pour le faire chuter. "
               "**On ne surcoinche jamais.**")
    paragraphe(doc, "Exemples contre un 80 : V + 9 + un petit atout (2 + 1 + 1 = 4), ou "
               "V + R + deux petits atouts (2 + 1 + 1 = 4).")

    titre(doc, "Les résultats", 2)
    tableau(doc, ["Seuil de force (contre un 80)", "Écart contre le seuil 4"], [
        ["3 (plus agressif)", "−4,7 ± 1,7"],
        ["4", "référence"],
        ["5 (plus prudent)", "−5,9 ± 1,2"],
        ["6", "−9,2 ± 1,3"],
    ], largeurs=[8, 6])
    puces(doc, [
        "**Cette coinche rapporte +8,7 ± 1,2 points par donne** par rapport à une coinche très rare.",
        "**Le seuil 4 est le meilleur** : coincher plus souvent, ou moins souvent, fait perdre des points.",
        "**3 contrats coinchés sur 4 chutent** (77 %). Une coinche est rentable dès que plus de la "
        "moitié des contrats coinchés chutent.",
        "Face à un coincheur efficace, la meilleure marge dans les enchères disputées reste "
        "20 à 30 points ; au-delà (40), on est nettement puni.",
    ])
    titre(doc, "Une règle revérifiée", 2)
    paragraphe(doc, "Avec un meilleur jeu de la carte, le seuil 4 reste le meilleur (seuil 3 : −8,7 ; "
               "seuil 5 : −3,9 par donne). Nous avons aussi observé que les contrats disputés chutent "
               "plus souvent, et que les défenseurs qui ont des as les font plus souvent chuter. "
               "Nous avons donc testé des variantes qui en tiennent compte :")
    tableau(doc, ["Variante (contre la règle actuelle)", "Écart par donne"], [
        ["Jamais de coinche sous une force de 2", "+0,8 ± 1,5 (pas de différence)"],
        ["Seuil −1 contre un contrat disputé, +1 sinon", "−2,5 ± 1,6"],
        ["Les as à côté comptent dans la force", "0,0 ± 1,6"],
        ["Les deux combinés", "−5,1 ± 1,9"],
    ], largeurs=[10, 6.5])
    paragraphe(doc, "**Aucune ne fait mieux.** Coincher arrête les enchères : face à un contrat "
               "disputé, on se prive souvent de prendre soi-même un contrat plus rentable. "
               "La règle simple, fondée sur les atouts, reste la meilleure.")

    encadre(doc, "**À retenir** : on coinche sur les atouts, pas sur les as. Le valet, la longueur "
            "et le roi ou la dame (qui prive l'adversaire de la belote) font chuter les contrats.")
    paragraphe(doc, "Dans nos simulations, où les quatre joueurs annoncent de façon assez audacieuse, "
               "environ **un contrat sur quatre** est coinché. À une table plus prudente, ce "
               "chiffre serait plus faible.")
    doc.add_page_break()


def section_capot(doc):
    titre(doc, "6. Le capot")
    paragraphe(doc, "Le capot rapporte 250 points, mais une chute en donne autant aux adversaires. "
               "Il n'est rentable que s'il réussit **au moins 3 fois sur 4** environ ; en dessous, "
               "jouer 140 ou 160 rapporte davantage en moyenne.")

    titre(doc, "Compter ses plis ne suffit pas", 2)
    paragraphe(doc, "Notre premier système annonçait capot en additionnant les cartes maîtresses de "
               "l'ouvreur et celles annoncées par le partenaire. Résultat : **à peine 1 capot sur 5 "
               "réussissait**. Les causes :")
    puces(doc, [
        "**Les coupes adverses** : As-10-Roi d'une couleur ne font pas 3 plis si un adversaire "
        "coupe au 2e tour.",
        "**La communication** : les cartes maîtresses du partenaire ne servent que si l'on peut "
        "lui donner la main dans cette couleur.",
        "**Le double emploi** : les atouts maîtres du partenaire font souvent doublon avec ceux "
        "de l'ouvreur.",
    ])
    paragraphe(doc, "En revanche, le capot annoncé d'entrée avec **toutes les cartes maîtresses** "
               "a réussi à chaque fois (13 sur 13).")

    titre(doc, "Simuler plutôt que compter", 2)
    paragraphe(doc, "Nous avons ensuite décidé le capot par simulation : dès que l'ouvreur compte "
               "7 plis théoriques, l'ordinateur imagine des donnes compatibles avec les enchères "
               "(réponses du partenaire, passes des adversaires), les joue, et choisit l'annonce "
               "la plus rentable.")
    tableau(doc, ["Méthode (150 situations de capot possible)", "Capots annoncés", "Réussis",
                  "Gain par situation"], [
        ["Comptage des plis (avec 1 pli de marge)", "11", "8", "référence"],
        ["Simulation, annonce la plus rentable", "36", "32", "+57 ± 37"],
        ["Simulation, au moins 90 % de réussite", "15", "13", "+37 ± 35"],
    ], largeurs=[7, 3, 2.5, 4])
    paragraphe(doc, "La simulation annonce **trois fois plus de capots et en réussit davantage** "
               "(89 % contre 73 %). Mais la situation est rare (environ une donne sur 670) : "
               "l'effet sur l'ensemble d'une partie reste faible.")

    titre(doc, "Les conseils pour la table", 2)
    puces(doc, [
        "**Compter ses perdantes**, et vérifier que chacune est couverte par une carte maîtresse "
        "du partenaire dans une couleur où l'on peut lui donner la main.",
        "**Garder un pli de marge**, surtout quand l'adversaire entame.",
        "**La forme de la main compte plus que les as** : avec 5 atouts V 9 et As-10 troisième "
        "(deux couleurs absentes), on réussit 2 capots sur 3, contre 2 sur 5 avec deux as secs.",
    ])
    encadre(doc, "**À retenir** : on n'annonce pas un capot sur un compte de plis théorique. "
            "On se demande plutôt : « chacune de mes cartes perdantes est-elle vraiment couverte ? »")

