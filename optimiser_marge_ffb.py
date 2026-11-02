from regles import VARIANTE_POINTS_FAITS
from systeme_v2 import SysV2
from experience_reponse import reponse_variante
from ia_joueur import JoueurIA
from rapide import afficher_rapide

# Barème FFB avec objectif 1500 points
REGLES_FFB = dict(VARIANTE_POINTS_FAITS, score_objectif=1500)

def bot_ffb(nom, marge):
    class Bot(JoueurIA):
        pass
    Bot.nom = nom
    Bot.marge = marge
    Bot.seuil = 4
    Bot.reponse = reponse_variante("court")
    return Bot

if __name__ == "__main__":
    nb = 12000
    ref = bot_ffb("Ref-Marge10", marge=10)
    print("=== OPTIMISATION DE LA MARGE EN BARÈME FFB (12 000 donnes en duplicate) ===")
    print("Référence : Marge 10\n")
    
    for m in (0, 20, 30):
        afficher_rapide(bot_ffb(f"Marge{m}", m), ref, nb, REGLES_FFB)
