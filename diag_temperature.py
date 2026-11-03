"""Distribution des écarts de note du réseau (carte jouée - carte préférée),
pour régler la température du détective v4. Tourne dans un seul processus."""
import numpy as np
import test_detective2 as t
import detective_v4

NB = 50
faites, graine = 0, t.PREMIERE_GRAINE
while faites < NB:
    r = t.tester_une_donne(graine)
    graine += 1
    if r is None:
        continue
    if "erreur" in r:
        print("Erreur :", r["erreur"])
        break
    faites += 1

e = np.array(detective_v4.ECARTS)
print(f"\n{len(e)} lectures sur {faites} donnes")
if len(e):
    print("Percentiles 10/25/50/75/90 :", np.round(np.percentile(e, [10, 25, 50, 75, 90]), 3))
    print(f"Carte jouée = carte préférée du réseau : {100 * np.mean(e >= -1e-9):.0f} %")
    for T in [0.1, 0.3, 1.0, 3.0]:
        au_plancher = np.mean(np.exp(e / T) < detective_v4.PLANCHER)
        print(f"  T = {T:<4} : {100 * au_plancher:3.0f} % des lectures tombent au plancher de 5 %")
