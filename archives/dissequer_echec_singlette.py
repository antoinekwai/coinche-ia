import random
from regles import REGLES_STANDARD
from moteur import distribuer, COULEURS, cartes_jouables
from partie import jouer_donne, phase_annonces
from bot_mc_ia import BotMCIA
from bot_coop import BotCoop

def inspecter_echecs(nb_exemples=3):
    regles = REGLES_STANDARD
    trouves = 0

    print("Recherche de donnes réelles où l'entame singlette a fait perdre la défense...\n")

    for graine in range(777000, 800000):
        random.seed(graine)
        mains = distribuer()
        donneur = graine % 4

        # Enchères réelles
        j_test = [BotMCIA(), BotMCIA(), BotMCIA(), BotMCIA()]
        contrat = phase_annonces(mains, donneur, j_test, regles, afficher=False)
        if contrat is None:
            continue

        # Condition : Adversaire preneur, contrat >= 100, Sud à l'entame au Pli 1
        preneur = contrat["joueur"]
        if preneur % 2 == 0 or contrat["valeur"] < 100:
            continue

        premier = (donneur + 1) % 4
        if premier != 0:
            continue

        atout = contrat["atout"]
        main_sud = mains[0]
        nb_atouts_sud = sum(1 for c in main_sud if c[1] == atout)
        if nb_atouts_sud == 0 or ("V", atout) in main_sud:
            continue

        cotes = [c for c in COULEURS if c != atout]
        singlettes = [c for c in cotes if sum(1 for x in main_sud if x[1] == c) == 1 and not any(x == ("A", c) for x in main_sud)]
        if not singlettes:
            continue

        # Table 1 : Sud et Nord jouent avec BotCoop (Convention)
        j_coop = [BotCoop(), BotMCIA(), BotCoop(), BotMCIA()]
        r_coop = jouer_donne(donneur, j_coop, regles, mains=[list(m) for m in mains])

        # Table 2 : Sud et Nord jouent avec BotMCIA (Jeu libre sans convention)
        j_base = [BotMCIA(), BotMCIA(), BotMCIA(), BotMCIA()]
        r_base = jouer_donne(donneur, j_base, regles, mains=[list(m) for m in mains])

        if r_coop is None or r_base is None:
            continue

        score_coop = r_coop["scores"][0] - r_coop["scores"][1]
        score_base = r_base["scores"][0] - r_base["scores"][1]
        perte = score_base - score_coop

        # Si la convention a fait perdre le contrat ou des points significatifs
        if perte >= 100:
            trouves += 1
            print("=" * 70)
            print(f"EXEMPLE {trouves} (Graine {graine}) : PERTE NETTE DE {perte} POINTS")
            print("=" * 70)
            nom_preneur = ["Sud", "Ouest", "Nord", "Est"][preneur]
            print(f"Contrat adverse : {contrat['valeur']} {contrat['atout']} par {nom_preneur}")
            print(f"Singlette de Sud : {singlettes[0]}")
            print("\nMains initiales :")
            noms = ["Sud (Vous)", "Ouest", "Nord (Part.)", "Est"]
            for p in range(4):
                cartes_str = " ".join(f"{r}{c}" for r, c in mains[p])
                print(f"  {noms[p]:14} : {cartes_str}")

            print("\n--- TABLE 1 : Avec convention singlette (BotCoop) ---")
            for num in range(1, 9):
                pli = j_coop[0].historique[(num-1)*4 : num*4]
                detail = " ".join(f"{noms[j]}:{r}{c}" for j, (r, c) in pli)
                print(f"  Pli {num} : {detail}")
            statut_coop = "RÉUSSI" if r_coop["reussi"] else "CHUTÉ"
            print(f"  Résultat : Contrat adverse {statut_coop} | Score : Sud {r_coop['scores'][0]} — Eux {r_coop['scores'][1]}")

            print("\n--- TABLE 2 : Jeu libre (BotMCIA) ---")
            for num in range(1, 9):
                pli = j_base[0].historique[(num-1)*4 : num*4]
                detail = " ".join(f"{noms[j]}:{r}{c}" for j, (r, c) in pli)
                print(f"  Pli {num} : {detail}")
            statut_base = "RÉUSSI" if r_base["reussi"] else "CHUTÉ"
            print(f"  Résultat : Contrat adverse {statut_base} | Score : Sud {r_base['scores'][0]} — Eux {r_base['scores'][1]}")
            print("\n")

            if trouves >= nb_exemples:
                break

if __name__ == "__main__":
    inspecter_echecs()
