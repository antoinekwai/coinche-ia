import random
from collections import Counter, defaultdict
from moteur import distribuer, COULEURS
from joueur_reseau import probabilites
from mains_types import MAINS_TYPES

SEUIL = 0.8
NB = 50000


def profil_main(main, a):
    atouts = [r for r, c in main if c == a]
    nas = sum(1 for r, c in main if r == "A" and c != a)
    return ("V" in atouts, "9" in atouts, len(atouts), min(nas, 3))


def profil_type(spec):
    at = spec.get("atouts", [])
    n = len(at) + spec.get("petits", 0)
    nas = spec.get("as", 0) + (1 if spec.get("as10") or spec.get("as10x") else 0)
    return ("V" in at, "9" in at, n, min(nas, 3))


def texte(p):
    v, neuf, n, nas = p
    tete = " ".join(x for x, ok in (("V", v), ("9", neuf)) if ok) or "sans V ni 9"
    return f"{tete}, {n} atouts, {nas}{'+' if nas == 3 else ''} as à côté"


if __name__ == "__main__":
    random.seed(1)
    couverts = {profil_type(spec) for _, spec in MAINS_TYPES}
    compte, p80 = Counter(), defaultdict(list)
    ouvrables = 0

    for _ in range(NB):
        main = distribuer()[0]
        probas = probabilites(main, 1.0)
        a = max(COULEURS, key=lambda c: probas[c][0])
        if probas[a][0] >= SEUIL:
            ouvrables += 1
            p = profil_main(main, a)
            compte[p] += 1
            p80[p].append(probas[a][0])

    nb_couv = sum(n for p, n in compte.items() if p in couverts)
    print(f"{100 * ouvrables / NB:.1f} % des mains justifient d'ouvrir (80 réussi au moins 4 fois sur 5)")
    print(f"{100 * nb_couv / ouvrables:.1f} % de ces mains ont un profil couvert par nos mains types\n")

    print("Profils fréquents NON couverts            | Part des ouvertures | P(80) moyenne")
    manquants = [(n, p) for p, n in compte.items() if p not in couverts]
    for n, p in sorted(manquants, reverse=True)[:15]:
        moy = sum(p80[p]) / len(p80[p])
        print(f"  {texte(p):40} | {100 * n / ouvrables:6.1f} %            | {100 * moy:4.0f} %")

    print("\nCombien de profils faut-il pour couvrir les ouvertures ?")
    cumul = 0
    for k, (p, n) in enumerate(compte.most_common(), 1):
        cumul += n
        if k in (5, 10, 20, 30, 40):
            print(f"  {k:2} profils les plus fréquents : {100 * cumul / ouvrables:5.1f} % des ouvertures")
    print("\nLes 30 profils les plus fréquents :")
    for k, (p, n) in enumerate(compte.most_common(30), 1):
        moy = sum(p80[p]) / len(p80[p])
        marque = "couvert" if p in couverts else "MANQUANT"
        print(f"  {k:2}. {texte(p):40} | {100 * n / ouvrables:5.1f} % | P(80) {100 * moy:3.0f} % | {marque}")
