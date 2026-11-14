"""
etude_bicolore_reelle.py (Version 2 500 donnes massives)
Joue chaque donne réelle dans les DEUX sens :
- Sens 1 : Camp 0 joue dans son meilleur atout
- Sens 2 : Camp 1 joue dans son meilleur atout
Mesure les points réels faits de chaque côté sans AUCUNE simulation imaginaire.
"""
import time, json, random
import numpy as np
import torch
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, COULEURS, RANGS
from systeme_v2 import niveau_v2
from bot_mc_ia_v6 import BotMCIAv6, FICHIER_V6_RESEAU

NB_DONNES = 2500
FICHIER_SORTIE = "donnees_croisees_reelles.jsonl"
GRAINE_BASE = 400_000_000

print(f"=== ÉTUDE MASSIVE DES ENCHÈRES DISPUTÉES ({NB_DONNES:,} donnes réelles) ===")
print("Jeu réel des 2 camps dans leur atout respectif par le Réseau V2.")
print("-" * 75)

bot = BotMCIAv6(nb_simulations=1, fichier_reseau=FICHIER_V6_RESEAU)

def faire_jouer_donne(mains_init, atout, preneur):
    m = [list(mm) for mm in mains_init]
    hist = []
    prem = (preneur + 1) % 4
    pts_eq = [0, 0]
    contrat_fictif = {"valeur": 80, "atout": atout, "joueur": preneur, "coinche": 0, "capot": False}
    
    while len(hist) < 32:
        pli = []
        for step in range(4):
            j = (prem + step) % 4
            jbs = cartes_jouables(m[j], pli, atout, j, REGLES_STANDARD)
            c = bot.ia_v2.jouer_carte(m[j], jbs, pli, contrat_fictif, j, REGLES_STANDARD)
            m[j].remove(c)
            pli.append((j, c))
            hist.append((j, c))
        g = gagnant_pli(pli, atout)[0]
        prem = g
        p = sum(points(cc, atout) for _, cc in pli)
        if len(hist) == 32: p += REGLES_STANDARD["dix_de_der"]
        pts_eq[g % 2] += p
        
    return pts_eq

donnes_trouvees = 0
t0 = time.time()

with open(FICHIER_SORTIE, "w", encoding="utf-8") as f_out:
    for g in range(GRAINE_BASE, GRAINE_BASE + NB_DONNES * 8):
        if donnes_trouvees >= NB_DONNES:
            break

        random.seed(g); np.random.seed(g % 2**32); torch.manual_seed(g)
        mains = distribuer()
        
        coul_camp0 = max(COULEURS, key=lambda c: max(niveau_v2(mains[0], c), niveau_v2(mains[2], c)))
        coul_camp1 = max(COULEURS, key=lambda c: max(niveau_v2(mains[1], c), niveau_v2(mains[3], c)))
        
        niv_c0 = max(niveau_v2(mains[0], coul_camp0), niveau_v2(mains[2], coul_camp0))
        niv_c1 = max(niveau_v2(mains[1], coul_camp1), niveau_v2(mains[3], coul_camp1))
        
        if coul_camp0 != coul_camp1 and niv_c0 >= 80 and niv_c1 >= 80:
            donnes_trouvees += 1
            p0 = 0 if niveau_v2(mains[0], coul_camp0) >= niveau_v2(mains[2], coul_camp0) else 2
            p1 = 1 if niveau_v2(mains[1], coul_camp1) >= niveau_v2(mains[3], coul_camp1) else 3
            part0 = (p0 + 2) % 4
            part1 = (p1 + 2) % 4
            
            # SENS 1 : Camp 0 joue dans son atout
            pts_sens_0 = faire_jouer_donne(mains, coul_camp0, p0)
            pts_camp0 = pts_sens_0[0]
            
            # SENS 2 : Camp 1 joue dans son atout
            pts_sens_1 = faire_jouer_donne(mains, coul_camp1, p1)
            pts_camp1 = pts_sens_1[1]
            
            # Descripteurs détaillés Camp 0
            at_p0 = sum(1 for c in mains[p0] if c[1] == coul_camp0)
            at_part0 = sum(1 for c in mains[part0] if c[1] == coul_camp0)
            has_v0 = ('V', coul_camp0) in mains[p0]
            has_90 = ('9', coul_camp0) in mains[p0]
            as_ext0 = sum(1 for c in mains[p0] if c[0] == 'A' and c[1] != coul_camp0)
            as_part0 = sum(1 for c in mains[part0] if c[0] == 'A' and c[1] != coul_camp0)
            chicanes_0 = sum(1 for c in COULEURS if c != coul_camp0 and not any(carte[1] == c for carte in mains[p0]))
            
            rec = {
                "graine": g,
                # Camp 0
                "atout_0": coul_camp0, "niv_0": niv_c0, "pts_reels_0": pts_camp0,
                "atouts_preneur_0": at_p0, "atouts_part_0": at_part0, "atouts_tot_0": at_p0 + at_part0,
                "has_v_0": has_v0, "has_9_0": has_90, "as_ext_0": as_ext0, "as_part_0": as_part0,
                "chicanes_0": chicanes_0,
                # Camp 1
                "atout_1": coul_camp1, "niv_1": niv_c1, "pts_reels_1": pts_camp1,
                "atouts_tot_1": sum(1 for p in (1, 3) for c in mains[p] if c[1] == coul_camp1),
                "as_tot_1": sum(1 for p in (1, 3) for c in mains[p] if c[0] == 'A')
            }
            f_out.write(json.dumps(rec) + "\n")
            
            if donnes_trouvees % 500 == 0:
                print(f"  {donnes_trouvees:5d}/{NB_DONNES} donnes croisées jouées ({time.time()-t0:.1f}s)...", flush=True)

print("=" * 75)
print(f"✅ Terminé en {time.time()-t0:.1f}s ! {donnes_trouvees} donnes réelles enregistrées.")
