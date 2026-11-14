"""
autopsier_ecarts_v3_v5.py (Version Radiographie Complète)
Trouve la 1re donne où v3 bat v5 au Pli 3, isole le pli de divergence,
et affiche la radiographie exacte des 40 mains imaginées par v3 vs v5 à cet instant !
"""
import random, numpy as np, torch
from collections import Counter
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte
from partie import phase_annonces
from test_mc_encheres import MCEncheres
from ia_joueur import JoueurIA
from benchmark_duel_pli3 import BotPli3_V3, BotPli3_V5
from detective_v3 import imaginer_v3
from detective_v5 import imaginer_v5

GRAINE_BASE = 85_000_000
NB_DONNES = 200

print("Recherche des donnes où v3 GAGNE et v5 CHUTE au Pli 3...")
trouvees = []

for g in range(GRAINE_BASE, GRAINE_BASE + NB_DONNES):
    random.seed(g); np.random.seed(g % 2**32); torch.manual_seed(g)
    mains = distribuer()
    donn = g % 4
    bots_e = [JoueurIA() for _ in range(4)]
    contrat = phase_annonces(mains, donn, bots_e, REGLES_STANDARD, afficher=False)
    if contrat is None: continue
    ench = list(bots_e[(donn+1)%4].encheres)
    camp = 0
    role = "attaque" if contrat["joueur"] % 2 == camp else "defense"
    atout = contrat["atout"]

    scores, historiques = {}, {}
    for nom, cls_b in [("v3", BotPli3_V3), ("v5", BotPli3_V5)]:
        random.seed(g * 10 + 7); np.random.seed((g * 10 + 7) % 2**32); torch.manual_seed(g * 10 + 7)
        m_c = [list(mm) for mm in mains]
        b = cls_b()
        adv = MCEncheres()
        hist, p_eq, pl_eq = [], [0,0], [0,0]
        prem = (donn + 1) % 4
        while len(hist) < 32:
            pli = []
            for step in range(4):
                j = (prem + step) % 4
                jbs = cartes_jouables(m_c[j], pli, atout, j, REGLES_STANDARD)
                if j % 2 == camp:
                    b.historique = list(hist); b.encheres = list(ench)
                    card = b.jouer_carte(m_c[j], jbs, pli, contrat, j, REGLES_STANDARD)
                else:
                    adv.historique = list(hist); adv.encheres = list(ench)
                    card = adv.jouer_carte(m_c[j], jbs, pli, contrat, j, REGLES_STANDARD)
                m_c[j].remove(card); pli.append((j, card)); hist.append((j, card))
            g_pli = gagnant_pli(pli, atout)[0]
            prem = g_pli
            p_eq[g_pli % 2] += sum(points(cc, atout) for _, cc in pli)
        bel = equipe_belote(mains, atout)
        _, reussi = decompte(contrat, p_eq, pl_eq, bel, REGLES_STANDARD)
        scores[nom] = reussi if role == "attaque" else (not reussi)
        historiques[nom] = hist

    if scores["v3"] and not scores["v5"]:
        trouvees.append((g, contrat, ench, mains, historiques["v3"], historiques["v5"], role))
        print(f"  -> Trouvé ! Graine {g} : Contrat {contrat['valeur']} {atout} ({role}) | v3 GAGNE, v5 CHUTE")
        break

if not trouvees:
    print("Aucune donne trouvée dans cette plage.")
    exit()

g, c, ench, mains, h_v3, h_v5, role = trouvees[0]
atout = c["atout"]
p_reel = c["joueur"]

print("\n" + "=" * 75)
print(f"AUTOPSIE DÉTAILLÉE DE LA GRAINE {g} (Contrat {c['valeur']} {atout} par J{p_reel})")
print("=" * 75)
print(f"Enchères réelles : {ench}")
print("\nMains réelles de départ :")
for j in range(4):
    at_main = [cc for cc in mains[j] if cc[1] == atout]
    as_main = [cc for cc in mains[j] if cc[0] == "A" and cc[1] != atout]
    role_j = " (Preneur)" if j == p_reel else (" (Partenaire)" if j == (p_reel+2)%4 else "")
    print(f"  Joueur {j}{role_j:<15} : {len(at_main)} atouts {[f'{r}{c_}' for r, c_ in at_main]} | {len(as_main)} As ext. {[f'{r}{c_}' for r, c_ in as_main]}")

# Trouver le pli de divergence
pli_div = None
for pli_num in range(1, 9):
    p_v3 = h_v3[(pli_num-1)*4 : pli_num*4]
    p_v5 = h_v5[(pli_num-1)*4 : pli_num*4]
    if p_v3 != p_v5:
        pli_div = pli_num
        break

print(f"\n⚡ PREMIER PLI DE DIVERGENCE : PLI {pli_div}")
p_v3 = h_v3[(pli_div-1)*4 : pli_div*4]
p_v5 = h_v5[(pli_div-1)*4 : pli_div*4]
print(f"  Pli joué par v3 : " + " ".join(f"J{j}:{cc[0]}{cc[1]}" for j, cc in p_v3))
print(f"  Pli joué par v5 : " + " ".join(f"J{j}:{cc[0]}{cc[1]}" for j, cc in p_v5))

# Identifier qui a divergé
hist_avant_div = h_v3[:(pli_div-1)*4]
pli_en_cours_div = []
joueur_qui_diverge = None
for k in range(4):
    if p_v3[k] != p_v5[k]:
        joueur_qui_diverge = p_v3[k][0]
        break
    pli_en_cours_div.append(p_v3[k])

print(f"\n👉 C'est Joueur {joueur_qui_diverge} qui prend une décision différente !")
c_v3 = [cc for j, cc in p_v3 if j == joueur_qui_diverge][0]
c_v5 = [cc for j, cc in p_v5 if j == joueur_qui_diverge][0]
print(f"   • v3 a choisi : {c_v3[0]}{c_v3[1]}")
print(f"   • v5 a choisi : {c_v5[0]}{c_v5[1]}")

# Radiographie des 40 mains imaginées par v3 vs v5 à cet instant précis
mains_moment = [list(mm) for mm in mains]
for j_h, c_h in hist_avant_div + pli_en_cours_div:
    mains_moment[j_h].remove(c_h)

main_j = mains_moment[joueur_qui_diverge]
hist_moment = hist_avant_div + pli_en_cours_div

print("\n" + "=" * 75)
print(f"RADIOGRAPHIE DES 40 MAINS IMAGINÉES PAR CHAQUE DÉTECTIVE À CET INSTANT :")
print("=" * 75)

for nom_det, fn_det in [("Détective v3 (Aléatoire + Rejeu)", imaginer_v3), ("Détective v5 (Guidé)", imaginer_v5)]:
    print(f"\n--- {nom_det} ---")
    atouts_adversaire = []
    valet_adv = 0
    neuf_adv = 0
    as_adv = []
    
    # Observer l'adversaire principal (le preneur si on défend, ou le défenseur fort)
    j_observe = p_reel if joueur_qui_diverge != p_reel else (joueur_qui_diverge + 1) % 4
    
    for i in range(40):
        random.seed(g * 1000 + i * 7)
        m_sim = fn_det(main_j, joueur_qui_diverge, hist_moment, ench, atout, REGLES_STANDARD)
        p_at = [cc for cc in m_sim[j_observe] if cc[1] == atout]
        atouts_adversaire.append(len(p_at))
        valet_adv += int(('V', atout) in m_sim[j_observe])
        neuf_adv += int(('9', atout) in m_sim[j_observe])
        as_adv.append(sum(1 for cc in m_sim[j_observe] if cc[0] == 'A' and cc[1] != atout))
        
    dist_at = Counter(atouts_adversaire)
    dist_str = ", ".join(f"{k} atouts: {v}/40" for k, v in sorted(dist_at.items()))
    print(f"Joueur {j_observe} (observé dans les simulations) :")
    print(f"  • Atouts restants en main : moyenne = {np.mean(atouts_adversaire):.2f} [{dist_str}]")
    print(f"  • Valet d'atout en main  : {valet_adv}/40 ({100*valet_adv/40:.0f} %)")
    print(f"  • Neuf d'atout en main   : {neuf_adv}/40 ({100*neuf_adv/40:.0f} %)")
    print(f"  • As extérieurs          : moyenne = {np.mean(as_adv):.2f}")
