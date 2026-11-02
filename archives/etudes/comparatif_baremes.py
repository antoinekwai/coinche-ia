from regles import REGLES_STANDARD
from systeme_v2 import SysV2
from experience_reponse import reponse_variante
from ia_joueur import JoueurIA
from partie import jouer_donne

# Définition directe des variantes pour éviter les soucis d'import
VARIANTE_CHUTE_160 = dict(REGLES_STANDARD, valeur_chute=160)
VARIANTE_POINTS_FAITS = dict(REGLES_STANDARD, mode_score="contrat_plus_points")

def tester_bareme(nom, regles, marge=30, seuil=4):
    class Bot(JoueurIA):
        pass
    Bot.nom = "Bot"
    Bot.marge = marge
    Bot.seuil = seuil
    Bot.reponse = reponse_variante("court")

    contrats = chutes = coinches = coinches_chutees = 0

    for i in range(2000):
        r = jouer_donne(i % 4, [Bot() for _ in range(4)], regles)
        if r is None:
            continue
        contrats += 1
        c = r["contrat"]
        reussi = r["reussi"]

        if not reussi:
            chutes += 1
        if c.get("coinche", 0) > 0:
            coinches += 1
            if not reussi:
                coinches_chutees += 1

    taux_chute = 100 * chutes / contrats
    taux_coinche = 100 * coinches / contrats
    taux_succes_coinche = 100 * coinches_chutees / max(1, coinches)

    print(f"{nom:<32} | {contrats - chutes:4d} ({100-taux_chute:4.1f}%) | {chutes:4d} ({taux_chute:4.1f}%) | {coinches:4d} ({taux_coinche:4.1f}%) | {taux_succes_coinche:4.1f}%")

if __name__ == "__main__":
    print(f"{'Barème & Réglages':<32} | {'Réussis':<12} | {'Chutés':<12} | {'Coinchés':<12} | {'Chute s/ Coinche'}")
    print("-" * 85)

    # 1. Barème actuel standard (contrat sec, marge 30)
    tester_bareme("1. Standard (Contrat sec, M30)", REGLES_STANDARD, marge=30, seuil=4)

    # 2. Chute à 160 (marge adaptée à 20)
    tester_bareme("2. Chute à 160 (Marge 20)", VARIANTE_CHUTE_160, marge=20, seuil=4)

    # 3. Barème Officiel FFB (contrat + points faits, marge 20)
    tester_bareme("3. Officiel FFB (Pts faits, M20)", VARIANTE_POINTS_FAITS, marge=20, seuil=4)
