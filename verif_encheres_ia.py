from regles import REGLES_STANDARD
from ia_joueur import JoueurIA, FICHIER
from systeme_corrige import SysCorrige
from experience_coinche import variante
from joueur_reseau import joueur_reseau
from rapide import afficher_rapide


def avec_ia(classe, nom, **reglages):
    """Même système d'annonces que `classe`, mais jeu de la carte par l'IA."""
    attributs = {"nom": nom, "jouer_carte": JoueurIA.jouer_carte,
                 "fichier": FICHIER, "epsilon": 0.0, "memoire": None}
    attributs.update(reglages)
    return type(nom, (classe,), attributs)


if __name__ == "__main__":
    regles, nb = REGLES_STANDARD, 15000
    ref = JoueurIA            # système corrigé (marge 30, coinche 4), jeu de la carte IA

    print("=== 1. Audace d'ouverture (réseau, seuil de réussite exigé) ===")
    for s in (0.7, 0.8, 0.9):
        afficher_rapide(avec_ia(joueur_reseau(s), f"IA-Réseau{int(100 * s)}"), ref, nb, regles)

    print("=== 2. Système d'origine contre système corrigé ===")
    afficher_rapide(avec_ia(variante(4), "IA-Origine"), ref, nb, regles)

    print("=== 3. Plafond de la marge ===")
    afficher_rapide(avec_ia(SysCorrige, "IA-Plafond140", plafond=140), ref, nb, regles)

    print("=== 4. Marge et coinche (nouvelle IA) ===")
    for m in (20, 40):
        afficher_rapide(avec_ia(SysCorrige, f"IA-Marge{m}", marge=m), ref, nb, regles)
    for s in (3, 5):
        afficher_rapide(avec_ia(SysCorrige, f"IA-Coinche{s}", seuil=s), ref, nb, regles)
