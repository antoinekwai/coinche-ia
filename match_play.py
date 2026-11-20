"""
match_play.py
Module d'Arbitrage Stratégique par Équité de Match (Match Play) :
Utilise les matrices de Bellman précalculées pour maximiser la probabilité
de gagner le match à 1000 points, sans AUCUNE règle en dur.
"""
import os
import numpy as np

OBJECTIF_MATCH = 1000
PAS_GRILLE = 20

# 1. CHARGEMENT EN CACHE DES MATRICES D'ÉQUITÉ DE MATCH
_V_SEC = None
_V_FFB = None

def charger_matrices():
    global _V_SEC, _V_FFB
    if _V_SEC is None:
        f_sec = "matrice_match_equity_sec.npy"
        if os.path.exists(f_sec):
            _V_SEC = np.load(f_sec)
        else:
            raise FileNotFoundError(f"Matrice {f_sec} manquante. Lancez solveur_match_play_bellman.py d'abord.")
    if _V_FFB is None:
        f_ffb = "matrice_match_equity_ffb.npy"
        if os.path.exists(f_ffb):
            _V_FFB = np.load(f_ffb)
        else:
            raise FileNotFoundError(f"Matrice {f_ffb} manquante. Lancez solveur_match_play_bellman.py d'abord.")

# 2. PROBABILITÉ DE VICTOIRE FINALE AVEC INTERPOLATION FLUIDE
def proba_victoire_match(score_nous, score_eux, bareme="contrat"):
    """Renvoie la probabilité (0.0 à 1.0) que notre camp gagne le match à 1000 points."""
    charger_matrices()
    V = _V_SEC if bareme == "contrat" else _V_FFB
    N = V.shape[0]

    # Bornes terminales directes
    if score_nous >= OBJECTIF_MATCH and score_nous > score_eux:
        return 1.0
    if score_eux >= OBJECTIF_MATCH and score_eux > score_nous:
        return 0.0

    # Coordonnées normalisées dans la grille (51 x 51)
    x = min(N - 1.0, max(0.0, score_nous / PAS_GRILLE))
    y = min(N - 1.0, max(0.0, score_eux / PAS_GRILLE))

    x0, y0 = int(np.floor(x)), int(np.floor(y))
    x1, y1 = min(N - 1, x0 + 1), min(N - 1, y0 + 1)

    dx = x - x0
    dy = y - y0

    # Interpolation bilinéaire pour une transition ultra-lisse (zéro à-coup)
    val = (V[x0, y0] * (1 - dx) * (1 - dy) +
           V[x1, y0] * dx * (1 - dy) +
           V[x0, y1] * (1 - dx) * dy +
           V[x1, y1] * dx * dy)
    return float(np.clip(val, 0.0, 1.0))

# 3. ÉVALUATION D'UNE DÉCISION D'ENCHÈRE EN TERMES DE P_WIN
def evaluer_decision_match_play(action, p_reussite, valeur_contrat, score_nous, score_eux,
                                 est_preneur=True, est_coinche=False, bareme="contrat"):
    """
    Calcule l'espérance de victoire finale E[P_win] d'une action d'enchère.
    """
    mult = 2 if est_coinche else 1

    if action == "passe":
        # En passe : on évalue la transition moyenne selon le barème
        if bareme == "contrat":
            # Barème sec : passe neutre ou don de petits points moyens si l'adversaire prend
            s1_futur = score_nous
            s2_futur = score_eux + 60
        else:
            # En FFB : la défense rapporte ~60 points de plis garantis !
            s1_futur = score_nous + 60
            s2_futur = score_eux + 170
        return proba_victoire_match(s1_futur, s2_futur, bareme)

    # Cas d'un contrat pris par notre camp
    if est_preneur:
        if bareme == "contrat":
            # Succès : +valeur * mult pour nous
            s1_succes = score_nous + (valeur_contrat * mult)
            s2_succes = score_eux
            # Chute : +valeur * mult pour l'adversaire
            s1_chute = score_nous
            s2_chute = score_eux + (valeur_contrat * mult)
        else:
            # Barème FFB
            # Succès : (arrondi ~100 + contrat) pour nous, ~60 pour eux si non coinché
            if est_coinche:
                s1_succes = score_nous + ((valeur_contrat + 100) * mult)
                s2_succes = score_eux
            else:
                s1_succes = score_nous + valeur_contrat + 100
                s2_succes = score_eux + 60
            # Chute FFB : 0 pour nous, 160 + contrat (* mult) pour eux !
            s1_chute = score_nous
            s2_chute = score_eux + ((160 + valeur_contrat) * mult)

        p_win_succes = proba_victoire_match(s1_succes, s2_succes, bareme)
        p_win_chute  = proba_victoire_match(s1_chute, s2_chute, bareme)
        return p_reussite * p_win_succes + (1.0 - p_reussite) * p_win_chute

    # Cas d'une Coinche sur contrat adverse (est_preneur = False)
    if action == "coinche":
        # p_reussite = probabilité de FAIRE CHUTER l'adversaire
        if bareme == "contrat":
            s1_chute_adv = score_nous + (valeur_contrat * 2)
            s2_chute_adv = score_eux
            s1_reussite_adv = score_nous
            s2_reussite_adv = score_eux + (valeur_contrat * 2)
        else:
            # En FFB : chute sous coinche = +500 pts pour nous, 0 pour eux !
            s1_chute_adv = score_nous + ((160 + valeur_contrat) * 2)
            s2_chute_adv = score_eux
            s1_reussite_adv = score_nous
            s2_reussite_adv = score_eux + ((valeur_contrat + 100) * 2)

        p_win_braquage = proba_victoire_match(s1_chute_adv, s2_chute_adv, bareme)
        p_win_punition = proba_victoire_match(s1_reussite_adv, s2_reussite_adv, bareme)
        return p_reussite * p_win_braquage + (1.0 - p_reussite) * p_win_punition

    return 0.5

# 4. ARBITRE D'ENCHÈRES DYNAMIQUE : CHOISIT L'ACTION QUI MAXIMISE P_WIN
def arbitrer_options_match_play(options_candidates, score_nous, score_eux, bareme="contrat"):
    """
    Prend en entrée une liste d'options :
    [ {"action": "80 ♠", "valeur": 80, "p_succes": 0.88, "type": "contrat"}, ... ]
    Renvoie le classement des options triées par espérance de victoire E[P_win] décroissante.
    """
    resultats = []
    for opt in options_candidates:
        act = opt["action"]
        val = opt.get("valeur", 80)
        p_suc = opt.get("p_succes", 0.5)
        type_opt = opt.get("type", "contrat")

        est_p = (type_opt == "contrat")
        est_c = (act == "coinche" or opt.get("coinche", False))

        p_win = evaluer_decision_match_play(
            act, p_suc, val, score_nous, score_eux,
            est_preneur=est_p, est_coinche=est_c, bareme=bareme
        )
        resultats.append({
            "action": act,
            "p_win": p_win,
            "p_win_pct": f"{p_win * 100.0:.2f} %",
            "valeur": val
        })

    resultats.sort(key=lambda x: x["p_win"], reverse=True)
    return resultats
