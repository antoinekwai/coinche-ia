from rapport_outils import titre, paragraphe, tableau, encadre
from fiche_ouvertures import OUVERTURES


T = 9   # taille du texte des tableaux de la fiche


def annexe_fiche(doc):
    titre(doc, "Annexe : fiche mémo pour la table")
    paragraphe(doc, "Barème : on marque ou on chute la valeur du contrat. "
               "Principe : **ouvrir au palier que l'on réussit environ 4 fois sur 5**.")

    tableau(doc, ["Ouverture", "Main de l'ouvreur (atout)"], OUVERTURES,
            largeurs=[2.2, 14.3], taille=T)


    tableau(doc, ["Ouverture du partenaire", "Je remonte de…"], [
        ["80", "+10 pour le V, +10 pour le 9 ; +10 par as si j'ai 2 atouts ou plus, "
               "+10 pour 2 as si j'en ai 0 ou 1"],
        ["90", "2 atouts ou plus : +10 par as ; 1 atout : +10 pour 2 as"],
        ["100, 110, 120", "+10 par as"],
        ["130 et plus", "Je passe"],
    ], largeurs=[4.5, 12], taille=T)

    tableau(doc, ["Situation", "Règle"], [
        ["Les adversaires parlent", "Monter jusqu'au **niveau de l'équipe + 20 à 30** "
                                    "(la belote peut s'ajouter), la marge ne faisant jamais "
                                    "dépasser **130**"],
        ["Coincher", "Force dans l'atout adverse : **V = 2**, 9 (avec 3 atouts) = 1, chaque atout "
                     "au-delà du 2e = 1, R ou D = 1. Coincher à **4 contre 80**, 1 de moins tous "
                     "les 20 points. Jamais de surcoinche"],
        ["Capot", "Chaque perdante doit être couverte, avec **un pli de marge** "
                  "(davantage si l'adversaire entame)"],
        ["Partenaire preneur, j'ai la main", "**3 atouts ou plus : je rejoue atout.** "
                                             "1 ou 2 : indifférent ; un 9 ou un As seul, "
                                             "plutôt le garder"],
        ["Partenaire maître du pli, j'ai un 10", "**Défense : je charge**, surtout en dernier. "
                                                 "**Attaque : je garde**, surtout si un "
                                                 "adversaire joue après moi"],
        ["Jeu de la carte", "Écouter les enchères, **y compris les passes**, pour placer "
                            "les cartes cachées"],
        ["Défense : singlette du partenaire", "Si mon partenaire a entamé une couleur et que je "
                                "prends la main, **je rejoue sa couleur** pour lui "
                                "donner la coupe."],

    ], largeurs=[4.5, 12], taille=T)

    encadre(doc, "**Pièges** : le 9 sans le valet est faible ; un 10 sec vaut moins qu'une petite "
            "carte ; un capot ne s'annonce pas sur un compte de plis théorique.")
