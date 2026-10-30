import random
from collections import Counter
from moteur import distribuer, COULEURS, texte_main

from systeme_corrige import niveau_corrige as niveau_ouverture

from joueur_reseau import probabilites
from entrainer import PALIERS

SEUIL = 0.8
NIVEAUX = [0] + PALIERS + [250]


def niveau_systeme(main):
    c = max(COULEURS, key=lambda c: niveau_ouverture(main, c))
    return niveau_ouverture(main, c), c


def niveau_reseau(probas):
    meilleur, couleur = 0, None
    for c in COULEURS:
        niv = 0
        for palier, p in zip(PALIERS, probas[c]):
            if p >= SEUIL:
                niv = palier
        if niv > meilleur:
            meilleur, couleur = niv, c
    return meilleur, couleur


if __name__ == "__main__":
    random.seed(1)
    tableau = Counter()
    sous_estimees, surestimees = [], []

    for _ in range(10000):
        main = distribuer()[0]
        s, cs = niveau_systeme(main)
        probas = probabilites(main, 1.0)
        r, cr = niveau_reseau(probas)
        tableau[(s, r)] += 1
        if s == 0 and r >= 90 and len(sous_estimees) < 5:
            sous_estimees.append((main, r, cr, probas[cr]))
        if s >= 90 and r <= s - 20 and s != 250 and len(surestimees) < 5:
            c = cs
            surestimees.append((main, s, c, probas[c]))

    print("Lignes = votre système, colonnes = réseau (seuil 80 %)\n")
    print("Système | " + " ".join(f"{('pas' if n == 0 else n):>5}" for n in NIVEAUX))
    for s in NIVEAUX:
        if sum(tableau[(s, r)] for r in NIVEAUX) == 0:
            continue
        print(f"{('passe' if s == 0 else s):>7} | " + " ".join(f"{tableau[(s, r)]:5}" for r in NIVEAUX))

    print("\n=== Mains où votre système passe, mais le réseau ouvre ===")
    for main, niv, c, p in sous_estimees:
        print(f"  {texte_main(main):32} -> réseau : {niv} {c}  (80: {100*p[0]:.0f} %, 100: {100*p[2]:.0f} %)")

    print("\n=== Mains où votre système annonce plus haut que le réseau ===")
    for main, niv, c, p in surestimees:
        print(f"  {texte_main(main):32} -> système : {niv} {c}  (80: {100*p[0]:.0f} %, 100: {100*p[2]:.0f} %)")
