"""
benchmark_arbitrage_defensif.py
Mesure appariée : arbitrage As-10 ANCIEN (toujours la plus haute de la séquence)
contre CORRIGÉ (plus basse sur pli perdu à coup sûr). Adversaire : MC-Enchères.
Usage : python3 benchmark_arbitrage_defensif.py rapide 200
        python3 benchmark_arbitrage_defensif.py v6 600
"""
import sys, time, random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte
from partie import phase_annonces
from test_mc_encheres import MCEncheres
from ia_joueur import JoueurIA
from ia_modele_v2 import JoueurIA_V2
from bot_mc_ia_v6 import BotMCIAv6

MOTEUR = sys.argv[1] if len(sys.argv) > 1 else "rapide"
NB_DONNES = int(sys.argv[2]) if len(sys.argv) > 2 else 200
PREMIERE_GRAINE = 90_000_000
VARIANTES = {"ancien": False, "corrige": True}

def creer_bot(defensif):
    if MOTEUR == "v6":
        b = BotMCIAv6()
        assert hasattr(b, "ia_v2"), "BotMCIAv6 n'a pas d'attribut ia_v2"
        b.ia_v2.arbitrage_defensif = defensif
    else:
        b = JoueurIA_V2(fichier="ia_carte_v2_champion.pt")
        b.arbitrage_defensif = defensif
    return b

print(f"=== ARBITRAGE DÉFENSIF ({MOTEUR}) : {NB_DONNES} donnes appariées vs MC-Enchères ===", flush=True)
res = {v: {"marque": [], "pts": [], "ok": [], "sec": [], "hist": []} for v in VARIANTES}
donnes = 0
t_debut = time.time()

for graine in range(PREMIERE_GRAINE, PREMIERE_GRAINE + NB_DONNES * 3):
    if donnes >= NB_DONNES:
        break
    random.seed(graine); np.random.seed(graine % 2**32); torch.manual_seed(graine)
    mains_init = distribuer()
    donneur = graine % 4
    joueurs_ench = [JoueurIA() for _ in range(4)]
    contrat = phase_annonces(mains_init, donneur, joueurs_ench, REGLES_STANDARD, afficher=False)
    if contrat is None:
        continue
    donnes += 1
    encheres = list(joueurs_ench[(donneur + 1) % 4].encheres)
    camp = 0
    role_attaque = (contrat["joueur"] % 2 == camp)
    val, atout = contrat["valeur"], contrat["atout"]
    mult = {0: 1, 1: 2, 2: 3}.get(contrat.get("coinche", 0), 1)

    for nom, defensif in VARIANTES.items():
        s = graine * 10 + 7
        random.seed(s); np.random.seed(s % 2**32); torch.manual_seed(s)
        mains = [list(m) for m in mains_init]
        bot = creer_bot(defensif)
        adv = MCEncheres()
        hist, p_eq, pl_eq = [], [0, 0], [0, 0]
        prem = (donneur + 1) % 4
        t0 = time.time()
        while len(hist) < 32:
            pli = []
            for k in range(4):
                j = (prem + k) % 4
                jbs = cartes_jouables(mains[j], pli, atout, j, REGLES_STANDARD)
                acteur = bot if j % 2 == camp else adv
                acteur.historique = list(hist)
                acteur.encheres = list(encheres)
                c = acteur.jouer_carte(mains[j], jbs, pli, contrat, j, REGLES_STANDARD)
                mains[j].remove(c)
                pli.append((j, c))
                hist.append((j, c))
            gagnant = gagnant_pli(pli, atout)[0]
            prem = gagnant
            p = sum(points(c, atout) for _, c in pli)
            if len(hist) == 32:
                p += REGLES_STANDARD["dix_de_der"]
            p_eq[gagnant % 2] += p
            pl_eq[gagnant % 2] += 1

        bel = equipe_belote(mains_init, atout)
        _, reussi = decompte(contrat, p_eq, pl_eq, bel, REGLES_STANDARD)
        gagne = reussi if role_attaque else not reussi
        r = res[nom]
        r["marque"].append((val * mult) if gagne else (-val * mult))
        r["pts"].append(p_eq[camp])
        r["ok"].append(gagne)
        r["sec"].append(time.time() - t0)
        r["hist"].append(tuple(hist))

    if donnes % 50 == 0:
        e = np.array(res["corrige"]["marque"], float) - np.array(res["ancien"]["marque"], float)
        print(f"  {donnes:5d}/{NB_DONNES} | {(time.time()-t_debut)/60:5.1f} min | écart marque corrigé-ancien : {e.mean():+.2f}", flush=True)

A = np.array(res["ancien"]["marque"], float)
C = np.array(res["corrige"]["marque"], float)
e = C - A
n = len(e)
marge = 1.96 * e.std(ddof=1) / np.sqrt(n) if n > 1 else 0.0
diff = [i for i in range(n) if res["ancien"]["hist"][i] != res["corrige"]["hist"][i]]

print("\n" + "=" * 70)
print(f"RÉSULTATS ({MOTEUR}) SUR {n} DONNES APPARIÉES")
print("=" * 70)
for nom in VARIANTES:
    r = res[nom]
    print(f"{nom:<8} | Pts faits {np.mean(r['pts']):6.1f} | Succès {100*np.mean(r['ok']):5.1f}% | "
          f"Marque {np.mean(r['marque']):+7.1f} | {np.mean(r['sec']):.2f} s/donne")
print("-" * 70)
print(f"ÉCART DE MARQUE (corrigé - ancien) : {e.mean():+.2f} ± {marge:.2f} pts/donne (IC 95 %)")
print(f"Donnes où le jeu a changé : {len(diff)} / {n} ({100*len(diff)/max(n,1):.1f} %)")
if diff:
    ed = e[diff]
    print(f"  Sur ces donnes : écart moyen {ed.mean():+.1f} | corrigé meilleur {int((ed>0).sum())} | "
          f"pire {int((ed<0).sum())} | égal {int((ed==0).sum())}")
