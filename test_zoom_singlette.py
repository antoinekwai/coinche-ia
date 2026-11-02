import os
import random
import multiprocessing as mp
from regles import REGLES_STANDARD
from moteur import distribuer, COULEURS, cartes_jouables
from partie import jouer_donne
from bot_mc_ia import BotMCIA
from bot_coop import BotCoop
from etude_atout import resume

NB_CAS = 500
GRAINE = 777000

def evaluer_donne_defense_propre(graine):
    random.seed(graine)
    mains = distribuer()
    donneur = graine % 4
    regles = REGLES_STANDARD

    # On fait jouer les enchères normales
    j_test = [BotMCIA(), BotMCIA(), BotMCIA(), BotMCIA()]
    # Simulation des enchères
    from partie import phase_annonces
    contrat = phase_annonces(mains, donneur, j_test, regles, afficher=False)
    
    if contrat is None:
        return None

    # CONDITION 1 : L'adversaire a le contrat (Ouest joueur 1 ou Est joueur 3)
    preneur = contrat["joueur"]
    if preneur % 2 == 0:
        return None # C'est notre camp qui a pris, on passe !

    # CONDITION 2 : Contrat consistant (>= 100)
    if contrat["valeur"] < 100:
        return None

    atout = contrat["atout"]
    # CONDITION 3 : Sud est à l'entame (joueur qui parle juste après le donneur = entameur du pli 1)
    premier = (donneur + 1) % 4
    if premier != 0:
        return None # Sud n'a pas l'entame au Pli 1

    # CONDITION 4 : Sud a une singlette (non-As) et au moins 1 atout (mais pas les maîtres d'atout !)
    main_sud = mains[0]
    nb_atouts_sud = sum(1 for c in main_sud if c[1] == atout)
    if nb_atouts_sud == 0 or ("V", atout) in main_sud:
        return None # Pas de singlette sans atout, ou si on a le Valet on purge !

    cotes = [c for c in COULEURS if c != atout]
    singlettes = [c for c in cotes if sum(1 for x in main_sud if x[1] == c) == 1 and not any(x == ("A", c) for x in main_sud)]
    if not singlettes:
        return None

    # Nous avons une VRAIE donne de défense à la singlette !
    # Table 1 : Sud et Nord jouent avec BotCoop (convention)
    j_coop = [BotCoop(), BotMCIA(), BotCoop(), BotMCIA()]
    r_coop = jouer_donne(donneur, j_coop, regles, mains=[list(m) for m in mains])

    # Table 2 : Sud et Nord jouent avec BotMCIA (jeu libre)
    j_base = [BotMCIA(), BotMCIA(), BotMCIA(), BotMCIA()]
    r_base = jouer_donne(donneur, j_base, regles, mains=[list(m) for m in mains])

    if r_coop is None or r_base is None:
        return None

    # Score net pour NOTRE camp (défense = équipe 0)
    score_coop = r_coop["scores"][0] - r_coop["scores"][1]
    score_base = r_base["scores"][0] - r_base["scores"][1]

    # Gain de la convention par rapport au jeu libre
    return score_coop - score_base

if __name__ == "__main__":
    print(f"Test rigoureux de {NB_CAS} vraies donnes de défense avec entame singlette...")
    cas = []
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        for diff in pool.imap_unordered(evaluer_donne_defense_propre, range(GRAINE, GRAINE + 40000), chunksize=25):
            if diff is not None:
                cas.append(diff)
                if len(cas) % 50 == 0:
                    print(f"  {len(cas)}/{NB_CAS} cas vérifiés...", flush=True)
                if len(cas) >= NB_CAS:
                    break

    n, m, marge = resume(cas)
    print("\n" + "=" * 65)
    print(f"RÉSULTAT NET DE LA CONVENTION SINGLETTE EN DÉFENSE ({n} cas réels) :")
    print(f"  👉 Écart par donne pour la défense : {m:+.1f} ± {marge:.1f} points")
    print("=" * 65)
