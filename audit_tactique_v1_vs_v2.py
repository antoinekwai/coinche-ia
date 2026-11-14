"""
audit_tactique_v1_vs_v2.py
Compare le bon sens tactique de l'ancien réseau (V1) et du nouveau (V2) sur 1 000 donnes :
1. Entame du preneur au Pli 1
2. Entame du partenaire au Pli 1
3. Poursuite de la purge au Pli 2
"""
import random
from regles import REGLES_STANDARD
from moteur import distribuer, cartes_jouables, gagnant_pli, COULEURS
from partie import phase_annonces
from ia_joueur import JoueurIA
from ia_modele_v2 import JoueurIA_V2
from bot_mc_ia_v6 import FICHIER_V6_RESEAU

NB_DONNES = 1000
GRAINE_BASE = 60_000_000

ia_v1 = JoueurIA()
ia_v2 = JoueurIA_V2(fichier=FICHIER_V6_RESEAU)

stats = {
    "V1": {
        "preneur_atout": 0, "preneur_as": 0, "preneur_autre": 0, "preneur_tot": 0,
        "partenaire_atout": 0, "partenaire_as": 0, "partenaire_autre": 0, "partenaire_tot": 0,
        "purge_continue": 0, "purge_abandonne": 0, "purge_tot": 0
    },
    "V2": {
        "preneur_atout": 0, "preneur_as": 0, "preneur_autre": 0, "preneur_tot": 0,
        "partenaire_atout": 0, "partenaire_as": 0, "partenaire_autre": 0, "partenaire_tot": 0,
        "purge_continue": 0, "purge_abandonne": 0, "purge_tot": 0
    }
}

print(f"=== AUDIT TACTIQUE COMPARATIF V1 vs V2 : {NB_DONNES} DONNES ===")
print("Analyse de l'instinct pur des deux réseaux (sans Monte-Carlo)")
print("-" * 75)

donnes_jouees = 0
for g in range(GRAINE_BASE, GRAINE_BASE + NB_DONNES * 2):
    if donnes_jouees >= NB_DONNES:
        break

    random.seed(g)
    mains_init = distribuer()
    donneur = g % 4
    joueurs_ench = [JoueurIA() for _ in range(4)]
    contrat = phase_annonces(mains_init, donneur, joueurs_ench, REGLES_STANDARD, afficher=False)
    if contrat is None:
        continue

    donnes_jouees += 1
    premier_parle = (donneur + 1) % 4
    encheres = list(joueurs_ench[premier_parle].encheres)
    atout = contrat["atout"]
    preneur = contrat["joueur"]
    partenaire = (preneur + 2) % 4
    entameur = (donneur + 1) % 4

    # Tester chaque modèle séparément sur la même donne
    for nom_m, bot in [("V1", ia_v1), ("V2", ia_v2)]:
        mains = [list(m) for m in mains_init]
        bot.historique = []
        bot.encheres = list(encheres)

        # 1. Analyse de l'entame au Pli 1
        jbs_entame = cartes_jouables(mains[entameur], [], atout, entameur, REGLES_STANDARD)
        c1 = bot.jouer_carte(mains[entameur], jbs_entame, [], contrat, entameur, REGLES_STANDARD)

        # Cas A : Le preneur entame
        if entameur == preneur:
            stats[nom_m]["preneur_tot"] += 1
            if c1[1] == atout:
                stats[nom_m]["preneur_atout"] += 1
            elif c1[0] == "A":
                stats[nom_m]["preneur_as"] += 1
            else:
                stats[nom_m]["preneur_autre"] += 1

        # Cas B : Le partenaire entame
        elif entameur == partenaire:
            a_atout = any(c[1] == atout for c in mains[entameur])
            if a_atout:
                stats[nom_m]["partenaire_tot"] += 1
                if c1[1] == atout:
                    stats[nom_m]["partenaire_atout"] += 1
                elif c1[0] == "A":
                    stats[nom_m]["partenaire_as"] += 1
                else:
                    stats[nom_m]["partenaire_autre"] += 1

        # 2. Dérouler le Pli 1 complet joué par ce modèle
        pli1 = [(entameur, c1)]
        mains[entameur].remove(c1)
        for step in range(1, 4):
            j = (entameur + step) % 4
            jbs = cartes_jouables(mains[j], pli1, atout, j, REGLES_STANDARD)
            bot.historique = list(pli1)
            cj = bot.jouer_carte(mains[j], jbs, pli1, contrat, j, REGLES_STANDARD)
            mains[j].remove(cj)
            pli1.append((j, cj))

        gagnant1 = gagnant_pli(pli1, atout)[0]
        camp_p = preneur % 2

        # 3. Pli 2 : Si le camp preneur a fait le pli 1 et a la main
        if gagnant1 % 2 == camp_p:
            advs = [(camp_p + 1) % 4, (camp_p + 3) % 4]
            atouts_adv = sum(1 for a in advs for c in mains[a] if c[1] == atout)
            a_atout_main = any(c[1] == atout for c in mains[gagnant1])

            if atouts_adv > 0 and a_atout_main:
                stats[nom_m]["purge_tot"] += 1
                jbs2 = cartes_jouables(mains[gagnant1], [], atout, gagnant1, REGLES_STANDARD)
                bot.historique = list(pli1)
                c2 = bot.jouer_carte(mains[gagnant1], jbs2, [], contrat, gagnant1, REGLES_STANDARD)
                if c2[1] == atout:
                    stats[nom_m]["purge_continue"] += 1
                else:
                    stats[nom_m]["purge_abandonne"] += 1

print("\n" + "=" * 75)
print("1. ENTAME DU PRENEUR AU PLI 1 :")
print("=" * 75)
for m in ["V1", "V2"]:
    tot = max(1, stats[m]["preneur_tot"])
    at = stats[m]["preneur_atout"]
    as_ = stats[m]["preneur_as"]
    aut = stats[m]["preneur_autre"]
    print(f"  {m} ({tot:3d} entames) : Atout {at:3d} ({100*at/tot:5.1f} %) | As franc {as_:3d} ({100*as_/tot:5.1f} %) | Autre {aut:3d} ({100*aut/tot:5.1f} %)")

print("\n" + "=" * 75)
print("2. ENTAME DU PARTENAIRE DU PRENEUR AU PLI 1 (avec >= 1 atout) :")
print("=" * 75)
for m in ["V1", "V2"]:
    tot = max(1, stats[m]["partenaire_tot"])
    at = stats[m]["partenaire_atout"]
    as_ = stats[m]["partenaire_as"]
    aut = stats[m]["partenaire_autre"]
    print(f"  {m} ({tot:3d} entames) : Atout au preneur {at:3d} ({100*at/tot:5.1f} %) | As franc {as_:3d} ({100*as_/tot:5.1f} %) | Autre {aut:3d} ({100*aut/tot:5.1f} %)")

print("\n" + "=" * 75)
print("3. POURSUITE DE LA PURGE AU PLI 2 (Camp preneur maître, atouts adverses vivants) :")
print("=" * 75)
for m in ["V1", "V2"]:
    tot = max(1, stats[m]["purge_tot"])
    cont = stats[m]["purge_continue"]
    ab = stats[m]["purge_abandonne"]
    print(f"  {m} ({tot:3d} cas) : Continue la purge {cont:3d} ({100*cont/tot:5.1f} %) | Abandonne la purge {ab:3d} ({100*ab/tot:5.1f} %)")
