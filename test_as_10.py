"""
test_as_10.py
Quand un joueur a l'As ET le 10 d'une couleur et se défausse,
que choisissent l'IA pure et Bot-MC-IA v3 ?
UTILISATION : python3 test_as_10.py
"""
import random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli
from partie import phase_annonces
from ia_joueur import JoueurIA, charger, FICHIER
from ia_encodage import encoder_situation, encoder_carte
from bot_mc_ia_v3 import BotMCIAv3

NB_SITUATIONS = 60
PREMIERE_GRAINE = 3_000_000


def chercher(graine, regles):
    """Joue une donne avec l'IA jusqu'à trouver une défausse avec As + 10 jouables."""
    random.seed(graine)
    mains = distribuer()
    donneur = graine % 4
    joueurs = [JoueurIA() for _ in range(4)]
    contrat = phase_annonces(mains, donneur, joueurs, regles, afficher=False)
    if contrat is None:
        return None
    encheres = list(joueurs[(donneur + 1) % 4].encheres)
    atout = contrat["atout"]
    ia = JoueurIA()
    mains = [list(m) for m in mains]
    hist, premier = [], (donneur + 1) % 4
    for _ in range(8):
        pli = []
        for i in range(4):
            j = (premier + i) % 4
            jouables = cartes_jouables(mains[j], pli, atout, j, regles)
            if pli and not any(c[1] == pli[0][1][1] for c in mains[j]):
                for X in sorted({c[1] for c in mains[j]}):
                    if X != atout and ("A", X) in jouables and ("10", X) in jouables:
                        return dict(main=list(mains[j]), jouables=jouables, pli=list(pli),
                                    hist=list(hist), contrat=contrat, j=j, encheres=encheres, X=X)
            ia.historique, ia.encheres = list(hist), list(encheres)
            c = ia.jouer_carte(mains[j], jouables, pli, contrat, j, regles)
            mains[j].remove(c)
            pli.append((j, c))
            hist.append((j, c))
        premier = gagnant_pli(pli, atout)[0]
    return None


def note_reseau(s, carte):
    etat = encoder_situation(s["main"], s["pli"], s["hist"], s["contrat"], s["j"],
                             REGLES_STANDARD, s["encheres"])
    x = np.concatenate([etat, encoder_carte(carte, s["contrat"]["atout"])])[None, :]
    with torch.no_grad():
        return float(charger(FICHIER)(torch.from_numpy(x)).squeeze())


def choix_v3(s, graine, inverser):
    random.seed(graine); np.random.seed(graine % 2**32); torch.manual_seed(graine)
    b = BotMCIAv3()
    b.historique, b.encheres = list(s["hist"]), list(s["encheres"])
    jouables = list(reversed(s["jouables"])) if inverser else list(s["jouables"])
    return b.jouer_carte(list(s["main"]), jouables, list(s["pli"]), s["contrat"], s["j"], REGLES_STANDARD)


def classer(c, X):
    return "As" if c == ("A", X) else ("10" if c == ("10", X) else "autre")


if __name__ == "__main__":
    regles = REGLES_STANDARD
    compte = {k: {"As": 0, "10": 0, "autre": 0} for k in ["IA pure", "v3", "v3 inversé"]}
    ecarts, change, trouvees, graine = [], 0, 0, PREMIERE_GRAINE
    while trouvees < NB_SITUATIONS:
        s = chercher(graine, regles)
        graine += 1
        if s is None:
            continue
        trouvees += 1
        X = s["X"]
        ia = JoueurIA()
        ia.historique, ia.encheres = list(s["hist"]), list(s["encheres"])
        c_ia = ia.jouer_carte(list(s["main"]), list(s["jouables"]), list(s["pli"]), s["contrat"], s["j"], regles)
        c1, c2 = choix_v3(s, graine, False), choix_v3(s, graine, True)
        compte["IA pure"][classer(c_ia, X)] += 1
        compte["v3"][classer(c1, X)] += 1
        compte["v3 inversé"][classer(c2, X)] += 1
        change += (c1 != c2)
        ecarts.append(note_reseau(s, ("A", X)) - note_reseau(s, ("10", X)))
        if trouvees % 10 == 0:
            print(f"  {trouvees}/{NB_SITUATIONS} situations trouvées", flush=True)

    print("\n=== Défausse avec As + 10 de la même couleur ===")
    for k, v in compte.items():
        print(f"  {k:<11} : As {v['As']:3d}  |  10 {v['10']:3d}  |  autre carte {v['autre']:3d}")
    print(f"\n  v3 change d'avis si on inverse l'ordre des cartes : {change}/{NB_SITUATIONS}")
    e = np.array(ecarts)
    print(f"  Note réseau As - note 10 : moyenne {e.mean():+.3f}, As préféré dans {100 * (e > 0).mean():.0f} % des cas")
