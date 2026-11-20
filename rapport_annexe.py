"""
rapport_annexe.py
Annexe : Fiche mémo pour la table (Version 2.1 actualisée)
"""
from rapport_outils import titre, paragraphe, tableau, encadre


def annexe_fiche(doc):
    titre(doc, "Annexe : fiche mémo pour la table")
    paragraphe(doc, "Barème : on marque ou on chute la valeur du contrat (Standard en 1 000 pts) ou points faits + contrat (FFB en 1 500 pts). "
               "Principe : **ouvrir au palier que l'on réussit environ 4 fois sur 5 (80 %)**.")

    titre(doc, "Les ouvertures (la grille universelle v2)", 2)
    tableau(doc, ["Ouverture", "Main de l'ouvreur (atout)"], [
        ["Capot", "Toutes les cartes maîtresses"],
        ["140", "V 9 cinquièmes + 2 as ; V 9 sixièmes + 1 as ; V 9 cinquièmes + A 10 x"],
        ["130", "Une main qui assure 130 seule (le partenaire passe)"],
        ["120", "V 9 cinquièmes + 1 as ; V 9 quatrièmes + 2 as ; V 9 sixièmes"],
        ["110", "V 9 quatrièmes + 1 as ; V 9 cinquièmes ; V 9 troisièmes + 2 as ; V quatrième + 2 as ; V cinquième + 1 as"],
        ["100", "V A R D ; V 9 quatrièmes (90 avec un 10 sec) ; V 9 secs + 3 as ; V quatrième + 1 as ; V cinquième ; V troisième + 3 as"],
        ["90", "A R D + 2 petits ; V 9 troisièmes + 1 as ; V troisième + 2 as ; V 9 secs + 2 as ; 9 quatrième + 2 as ; 9 cinquième + 1 as"],
        ["80", "V 9 troisièmes ; V 9 secs + 1 as ; V troisième + 1 as (ou as d'atout, ou belote) ; V quatrième ; 9 quatrième ; 9 troisième + 2 as"],
        ["Passe", "9 troisième avec un seul as, 4 petits sans V ni 9, et le reste"],
    ], largeurs=[3.0, 15.0])

    titre(doc, "Les réponses du partenaire", 2)
    tableau(doc, ["Ouverture du partenaire", "Je remonte de…"], [
        ["80", "+10 pour le V, +10 pour le 9 ; +10 par As si j'ai 2 atouts ou plus, +10 pour 2 As si j'en ai 1. En FFB : Passe strict si 0 atout !"],
        ["90", "2 atouts ou plus : +10 par As ; 1 atout : +10 pour 2 As. 0 atout : Passe."],
        ["100, 110, 120", "+10 par As extérieur"],
        ["130 et plus", "Je passe systématiquement"],
    ], largeurs=[5.5, 12.5])

    # SAUT DE PAGE PROPRE POUR AVOIR LE TABLEAU TACTIQUE COMPLET SUR LA PAGE SUIVANTE
    doc.add_page_break()

    titre(doc, "Règles tactiques de table et Match Play", 2)
    tableau(doc, ["Situation", "Règle tactique certifiée"], [
        ["Couleur adverse aux enchères", "BANNIE : interdiction absolue de prendre ou surenchérir dans la couleur de l'ennemi !"],
        ["Les adversaires parlent (Combat)", "Surenchérir à 110+ exige : >= 5 atouts, OU 4 atouts + chicane, OU Belote en main (+20), OU soutien du partenaire. Marge de 20 en FFB (prouvé sur 3 000 donnes), 30 en Sec."],
        ["Coincher (90 % du match)", "On ne coinche que ce que l'on bat soi-même ! Seuil 4 contre 80, 3 contre 100, 2 contre 120. Formule : V=2, 9 (avec 3 atouts)=1, longueur au-delà du 2e=1, R ou D=1."],
        ["All-In (Fin de match en retard)", "Adversaire >= 1420 FFB (ou >= 920 Sec) avec retard >= 400 pts : seuil de coinche abaissé à 2-2.5 (seule chance de survie)."],
        ["Ligne d'arrivée (Fin de match serrée)", "À moins de 80 pts du but : plafonner à 80 même avec jeu de 100 pour supprimer tout risque de chute."],
        ["Passager Clandestin (Fin de match FFB)", "Il manque <= 60 pts ET avance >= 130 pts : PASSEZ systématiquement, les points de défense suffisent pour clore le match !"],
        ["Belote annoncée au jeu", "Dès que le partenaire pose R ou D d'atout avec Belote, son deuxième atout lui est garanti. S'il reste 1 atout dehors, la défense adverse est purgée : déroulez vos As !"],
        ["Partenaire preneur, j'ai la main", "Atout au preneur dès que possible pour purger et lui donner la main. Encaisser un As extérieur d'abord si communication nécessaire."],
        ["Convention As-10", "En attaque sur pli garanti : défausser impérativement l'As depuis As-10. En défense sur pli perdu : jeter le 10 (sauver 1 pt)."],
        ["Partenaire maître, j'ai un 10", "Défense : je charge, surtout en 4e position. Attaque sur pli contesté : je garde, surtout si un adversaire joue après moi."],
    ], largeurs=[6.0, 12.0])

    encadre(doc, "**PIÈGES CLASSIQUES** : le 9 sans le Valet est très faible ; un 10 sec vaut moins qu'une petite carte ; "
            "purger aveuglément au Pli 2 détruit le score (-53 pts) ; le sacrifice est suicidaire en FFB ; "
            "un capot ne s'annonce jamais sur un compte de plis théorique.")
