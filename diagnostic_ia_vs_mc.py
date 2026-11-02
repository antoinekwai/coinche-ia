import random
from collections import defaultdict
from regles import REGLES_STANDARD
from moteur import distribuer, gagnant_pli, cartes_jouables
from partie import jouer_donne
from systeme_v2 import SysV2
from ia_joueur import JoueurIA
from test_mc_encheres import MCEncheres

NB_DONNES = 1500

def analyser_swings():
    regles = REGLES_STANDARD
    print(f"Lancement de {NB_DONNES} donnes en duplicate (IA vs MC-Enchères)...")
    
    swings_mc_gagne = []  # Donnes où MC bat l'IA
    swings_ia_gagne = []  # Donnes où l'IA bat MC
    
    stats = defaultdict(lambda: {"mc_pts": 0, "ia_pts": 0, "cas": 0})
    
    for num in range(NB_DONNES):
        random.seed(900000 + num)
        mains = distribuer()
        donneur = num % 4
        
        # Table 1 : IA en 0 et 2 (Sud/Nord), MC en 1 et 3 (Ouest/Est)
        j_t1 = [JoueurIA(), MCEncheres(), JoueurIA(), MCEncheres()]
        r1 = jouer_donne(donneur, j_t1, regles, mains=mains)
        
        # Table 2 : Inversion des places (MC en 0 et 2, IA en 1 et 3)
        j_t2 = [MCEncheres(), JoueurIA(), MCEncheres(), JoueurIA()]
        r2 = jouer_donne(donneur, j_t2, regles, mains=mains)
        
        if r1 is None or r2 is None:
            continue
            
        c = r1["contrat"]
        val = c["valeur"]
        atout = c["atout"]
        coinche = c.get("coinche", 0) > 0
        
        # Score net pour l'équipe (0 et 2)
        # Table 1 : IA est en (0 et 2)
        score_ia_t1 = r1["scores"][0] - r1["scores"][1]
        score_mc_t2 = r2["scores"][0] - r2["scores"][1]
        
        # Différence nette sur la donne
        # diff > 0 => IA a mieux joué ; diff < 0 => MC a mieux joué
        diff = (score_ia_t1 - score_mc_t2) / 2.0
        
        if abs(diff) > 0:
            camp_contrat = "Attaque" if c["joueur"] % 2 == 0 else "Défense"
            cat_val = "80-90" if val <= 90 else ("100-110" if val <= 110 else "120+")
            
            # Identifier le premier pli où les coups divergent
            hist1 = j_t1[0].historique
            hist2 = j_t2[0].historique
            pli_divergence = 8
            for p in range(len(hist1)):
                if hist1[p][1] != hist2[p][1]:
                    pli_divergence = (p // 4) + 1
                    break

            info = {
                "num": num,
                "diff": diff,
                "val": val,
                "atout": atout,
                "coinche": coinche,
                "camp": camp_contrat,
                "cat_val": cat_val,
                "pli_div": pli_divergence,
                "mains": mains,
                "r1": r1,
                "r2": r2
            }
            
            if diff < 0:
                swings_mc_gagne.append(info)
                stats["Total"]["mc_pts"] += abs(diff)
                stats[f"Camp: {camp_contrat}"]["mc_pts"] += abs(diff)
                stats[f"Niveau: {cat_val}"]["mc_pts"] += abs(diff)
                stats[f"Coinché: {'Oui' if coinche else 'Non'}"]["mc_pts"] += abs(diff)
                stats[f"Divergence: Pli {pli_divergence}"]["mc_pts"] += abs(diff)
            else:
                swings_ia_gagne.append(info)
                stats["Total"]["ia_pts"] += diff
                stats[f"Camp: {camp_contrat}"]["ia_pts"] += diff
                stats[f"Niveau: {cat_val}"]["ia_pts"] += diff
                stats[f"Coinché: {'Oui' if coinche else 'Non'}"]["ia_pts"] += diff
                stats[f"Divergence: Pli {pli_divergence}"]["ia_pts"] += diff
                
        if (num + 1) % 250 == 0:
            print(f"  {num + 1}/{NB_DONNES} donnes analysées...")

    print("\n" + "="*65)
    print("=== BILAN DU DIAGNOSTIC : OÙ MC-ENCHÈRES BAT-IL L'IA ? ===")
    print("="*65)
    print(f"Sur {NB_DONNES} donnes :")
    print(f"  • Donnes identiques (écart = 0) : {NB_DONNES - len(swings_mc_gagne) - len(swings_ia_gagne)}")
    print(f"  • Donnes où l'IA gagne          : {len(swings_ia_gagne)} donnes (+{sum(x['diff'] for x in swings_ia_gagne):.0f} pts)")
    print(f"  • Donnes où MC gagne            : {len(swings_mc_gagne)} donnes ({sum(x['diff'] for x in swings_mc_gagne):.0f} pts)")
    print(f"  👉 Bilan net pour MC            : {-(sum(x['diff'] for x in swings_ia_gagne) + sum(x['diff'] for x in swings_mc_gagne)) / NB_DONNES:.2f} pts/donne")

    print("\n--- RÉPARTITION DES POINTS GAGNÉS PAR CATÉGORIE ---")
    print(f"{'Catégorie':<28} | {'Points MC':<10} | {'Points IA':<10} | {'Solde net'}")
    for cat in sorted(stats.keys()):
        if cat == "Total": continue
        mc_p = stats[cat]["mc_pts"]
        ia_p = stats[cat]["ia_pts"]
        solde = mc_p - ia_p
        signe = f"+{solde:.0f} pour MC" if solde > 0 else f"+{-solde:.0f} pour IA"
        print(f"{cat:<28} | {mc_p:<10.0f} | {ia_p:<10.0f} | {signe}")

    # Afficher la pire donne de l'IA
    if swings_mc_gagne:
        pire = min(swings_mc_gagne, key=lambda x: x["diff"])
        print("\n" + "="*65)
        print(f"EXEMPLE TYPE : LA PIRE DONNE DE L'IA (Perte nette : {pire['diff']} pts)")
        print(f"Contrat : {pire['val']} {pire['atout']} ({pire['camp']}) — Coinché: {pire['coinche']}")
        print(f"Première divergence de jeu au Pli {pire['pli_div']}")
        print("="*65)

if __name__ == "__main__":
    analyser_swings()
