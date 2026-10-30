from collections import defaultdict
from regles import REGLES_STANDARD
from joueurs import JoueurRegles
from partie import jouer_donne


def diagnostic(classe, nb_donnes, regles):
    joueurs = [classe() for _ in range(4)]
    stats = defaultdict(lambda: [0, 0, 0, 0])  # nb, réussis, points faits, coinchés
    passes = 0

    for i in range(nb_donnes):
        res = jouer_donne(i % 4, joueurs, regles)
        if res is None:
            passes += 1
            continue
        c = res["contrat"]
        s = stats[c["valeur"]]
        s[0] += 1
        s[1] += res["reussi"]
        s[2] += res["points"][c["joueur"] % 2]
        s[3] += c["coinche"] > 0

    print(f"Donnes où tout le monde passe : {100 * passes / nb_donnes:.1f} %\n")
    print("Contrat | Annoncé | Réussite | Points faits (moy.) | Coinchés")
    for valeur in sorted(stats):
        nb, ok, pts, co = stats[valeur]
        nom = "CAPOT" if valeur == regles["valeur_capot"] else valeur
        print(f"{nom:>7} | {nb:7} | {100 * ok / nb:6.1f} % | {pts / nb:19.1f} | {co:8}")


if __name__ == "__main__":
    diagnostic(JoueurRegles, 20000, REGLES_STANDARD)
