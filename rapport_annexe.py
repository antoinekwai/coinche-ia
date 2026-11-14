"""
rapport_annexe.py
Annexe : Fiche mémo pour la table (Version 2.0 actualisée)
"""
from rapport_outils import titre, paragraphe, tableau, encadre
from fiche_ouvertures import OUVERTURES

T = 7.5   # taille du texte des tableaux de la fiche


def annexe_fiche(doc):
    titre(doc, "Annexe : fiche mémo pour la table")
    paragraphe(doc, "Barème : on marque ou on chute la valeur du contrat. "
               "Principe : **ouvrir au palier que l'on réussit environ 4 fois sur 5 (80 %)**.")

    tableau(doc, ["Ouverture", "Main de l'ouvreur (atout)"], OUVERTURES,
            largeurs=[2.2, 14.3], taille=T)

    tableau(doc, ["Ouverture du partenaire", "Je remonte de…"], [
        ["80", "+10 pour le V, +10 pour le 9 ; +10 par As si j'ai 2 atouts ou plus, "
               "+10 pour 2 As si j'en ai 0 ou 1. Si aucun incrément : **Passe obligatoire** sur intervention adverse."],
        ["90", "2 atouts ou plus : +10 par As ; 1 atout : +10 pour 2 As. 0 atout : Passe."],
        ["100, 110, 120", "+10 par As extérieur"],
        ["130 et plus", "Je passe systématiquement"],
    ], largeurs=[4.5, 12], taille=T)

    tableau(doc, ["Situation", "Règle tactique"], [
        ["Les adversaires parlent", "Surenchérir à 110+ exige : **>= 5 atouts**, OU **4 atouts + chicane**, OU **Belote en main (+20)**, OU **soutien du partenaire**. Sinon Passe."],
        ["Coincher", "On ne coinche que ce que l'on bat soi-même ! Force dans l'atout adverse : "
                     "**V = 2**, 9 (avec 3 atouts) = 1, chaque atout au-delà du 2e = 1, R ou D = 1. "
                     "Coincher à **4 contre 80**, 3 contre 100, 2 contre 120. Jamais de coinche spéculative."],
        ["Capot", "Chaque perdante doit être couverte, avec **un pli de marge** "
                  "(davantage si l'adversaire entame)."],
        ["Partenaire preneur, j'ai la main", "**Atout au preneur dès que possible** pour purger et lui donner la main. "
                                             "Encaisser un As extérieur d'abord si communication nécessaire."],
        ["Convention As-10 (Séquence maîtresse)", "**En attaque sur pli garanti** : défausser impérativement la plus HAUTE "
                                                  "(l'As depuis As-10) pour signaler au preneur que le 10 est affranchi. "
                                                  "**En défense sur pli perdu** : défausser la plus BASSE (sauver 1 pt)."],
        ["Partenaire maître du pli, j'ai un 10", "**Défense : je charge**, surtout en 4e position. "
                                                 "**Attaque sur pli contesté : je garde**, surtout si un adversaire joue après moi."],
        ["Jeu de la carte & Détective", "Écouter les enchères, **y compris les passes**, pour placer "
                                        "les cartes cachées dès le Pli 4."],
        ["Défense : singlette du partenaire", "Si mon partenaire a entamé une couleur et que je prends la main, "
                                              "**je rejoue sa couleur** pour lui donner la coupe."],
    ], largeurs=[4.5, 12], taille=T)

    encadre(doc, "**PIÈGES CLASSIQUES** : le 9 sans le Valet est très faible ; un 10 sec vaut moins qu'une petite carte ; "
            "purger systématiquement au Pli 2 est une erreur (-53 pts) ; un capot ne s'annonce jamais sur un compte de plis théorique.")
