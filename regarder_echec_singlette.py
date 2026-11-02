import random
from regles import REGLES_STANDARD
from moteur import distribuer, COULEURS
from partie import jouer_donne
from bot_mc_ia import BotMCIA
from bot_coop import BotCoop
from systeme_v2 import niveau_v2

def trouver_donne_divergente():
    regles = REGLES_STANDARD
    
    for graine in range(888000, 890000):
        random.seed(graine)
        mains = distribuer()
        donneur = graine % 4

        coul_att = max(COULEURS, key=lambda c: niveau_v2(mains[1], c))
        niv_att = niveau_v2(mains[1], coul_att)
        if niv_att < 110: continue

        # Sud en défense avec singlette + atout
        main_sud = mains[0]
        if not any(c[1] == coul_att for c in main_sud): continue
        cotes = [c for c in COULEURS if c != coul_att]
        singl = [c for c in cotes if sum(1 for x in main_sud if x[1] == c) == 1 and not any(x == ("A", c) for x in main_sud)]
        if not singl: continue

        # Table 1 : Convention singlette (BotCoop)
        j1 = [BotCoop(), BotMCIA(), BotCoop(), BotMCIA()]
        r1 = jouer_donne(donneur, j1, regles, mains=mains)

        # Table 2 : Jeu libre (BotMCIA)
        j2 = [BotMCIA(), BotMCIA(), BotMCIA(), BotMCIA()]
        r2 = jouer_donne(donneur, j2, regles, mains=mains)

        diff = (r1["scores"][0] - r1["scores"][1]) - (r2["scores"][0] - r2["scores"][1])

        # On cherche une donne où la convention a lourdement chuté face au jeu libre
        if diff <= -100:
            print("="*65)
            print(f"DONNE TROUVÉE (Graine {graine}) : Perte nette de {diff} pts avec la singlette")
            print(f"Contrat adverse : {r1['contrat']['valeur']} {r1['contrat']['atout']} par Ouest")
            print("\nMains de départ :")
            print(f"  Vous (Sud) : {' '.join(r+c for r,c in mains[0])} (Singlette: {singl[0]})")
            print(f"  Ouest      : {' '.join(r+c for r,c in mains[1])}")
            print(f"  Nord       : {' '.join(r+c for r,c in mains[2])}")
            print(f"  Est        : {' '.join(r+c for r,c in mains[3])}")
            
            print("\nTable 1 (Avec convention singlette) :")
            print(f"  Pli 1 : {' '.join(f'J{j}:{r}{c}' for j,(r,c) in j1[0].historique[:4])}")
            print(f"  Pli 2 : {' '.join(f'J{j}:{r}{c}' for j,(r,c) in j1[0].historique[4:8])}")
            print(f"  Score : Vous {r1['scores'][0]} - {r1['scores'][1]} Eux (Contrat {'RÉUSSI' if r1['reussi'] else 'CHUTÉ'})")

            print("\nTable 2 (Sans convention, jeu libre) :")
            print(f"  Pli 1 : {' '.join(f'J{j}:{r}{c}' for j,(r,c) in j2[0].historique[:4])}")
            print(f"  Pli 2 : {' '.join(f'J{j}:{r}{c}' for j,(r,c) in j2[0].historique[4:8])}")
            print(f"  Score : Vous {r2['scores'][0]} - {r2['scores'][1]} Eux (Contrat {'RÉUSSI' if r2['reussi'] else 'CHUTÉ'})")
            print("="*65)
            break

if __name__ == "__main__":
    trouver_donne_divergente()
