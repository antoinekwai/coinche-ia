from regles import REGLES_STANDARD
VARIANTE_CHUTE_160 = dict(REGLES_STANDARD, valeur_chute=160)
from systeme_v2 import SysV2
from experience_reponse import reponse_variante
from ia_joueur import JoueurIA, FICHIER
from rapide import afficher_rapide

class SysRecommande(SysV2):
    nom = "Système Recommandé"
    reponse = reponse_variante("court")

def avec_ia(classe, nom, **reglages):
    attributs = {"nom": nom, "jouer_carte": JoueurIA.jouer_carte,
                 "fichier": FICHIER, "epsilon": 0.0, "memoire": None}
    attributs.update(reglages)
    return type(nom, (classe,), attributs)

if __name__ == "__main__":
    regles = VARIANTE_CHUTE_160
    nb = 15000
    ref = avec_ia(SysRecommande, "IA-Recommandé")

    print("\n=======================================================")
    print("=== ÉTUDE DE LA VARIANTE : CHUTE À 160 POINTS FIXES ===")
    print("=======================================================\n")
    
    print("=== 1. Quelle marge dans les enchères disputées quand la chute coûte 160 ? ===")
    for m in (0, 10, 20, 30, 40):
        afficher_rapide(avec_ia(SysRecommande, f"Marge{m}", marge=m), ref, nb, regles)

    print("\n=== 2. Quel seuil de coinche contre 80 quand la chute rapporte 160 (320 coinché) ? ===")
    for s in (2, 3, 4, 5):
        afficher_rapide(avec_ia(SysRecommande, f"Coinche{s}", seuil=s), ref, nb, regles)
