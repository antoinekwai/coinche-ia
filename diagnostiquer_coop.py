import random
from regles import REGLES_STANDARD
from moteur import distribuer
from partie import jouer_donne
from bot_mc_ia import BotMCIA
from bot_coop import BotCoop

NB = 600

def auditer_coop():
    regles = REGLES_STANDARD
    print(f"Audit comparatif donne par donne sur {NB} donnes...")
    
    gains_coop = []
    pertes_coop = []

    for num in range(NB):
        random.seed(333000 + num)
        mains = distribuer()
        donneur = num % 4

        # Table 1 : Coop en Sud/Nord
        j_coop = [BotCoop(), BotMCIA(), BotCoop(), BotMCIA()]
        r_coop = jouer_donne(donneur, j_coop, regles, mains=[list(m) for m in mains])

        # Table 2 : Base en Sud/Nord
        j_base = [BotMCIA(), BotMCIA(), BotMCIA(), BotMCIA()]
        r_base = jouer_donne(donneur, j_base, regles, mains=[list(m) for m in mains])

        if r_coop is None or r_base is None:
            continue

        score_coop = r_coop["scores"][0] - r_coop["scores"][1]
        score_base = r_base["scores"][0] - r_base["scores"][1]
        diff = score_coop - score_base

        if diff >= 50:
            gains_coop.append((num, diff, r_coop["contrat"], j_coop[0].historique))
        elif diff <= -50:
            pertes_coop.append((num, diff, r_coop["contrat"], j_coop[0].historique))

    print("\n" + "=" * 65)
    print(f"BILAN DES DONNES DE BASCULE SUR {NB} DONNES :")
    print(f"  🌟 Donnes où Coop GAGNE largement (>= +50 pts) : {len(gains_coop)} donnes")
    print(f"  ❌ Donnes où Coop PERD lourdement (<= -50 pts) : {len(pertes_coop)} donnes")
    print("=" * 65)

    if pertes_coop:
        print("\nEXAMEN D'UNE DONNE OÙ COOP A PERDU :")
        num, diff, c, hist = pertes_coop[0]
        print(f"Donne #{num} — Perte nette : {diff} pts sur contrat {c['valeur']} {c['atout']}")
        print("Les 3 premiers plis joués par Coop :")
        for p in range(min(3, len(hist)//4)):
            pli = hist[p*4 : p*4+4]
            print(f"  Pli {p+1} : " + "  ".join(f"J{j}:{r}{coul}" for j, (r, coul) in pli))

if __name__ == "__main__":
    auditer_coop()
