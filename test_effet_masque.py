import numpy as np
import torch
from regles import REGLES_STANDARD
from systeme_v2 import SysV2
from ia_joueur import JoueurIA, charger
from ia_encodage import encoder_situation, encoder_carte
from rapide import afficher_rapide

# Version A : avec le filtre de non-dominance (Valet protégé)
class IA_Protegee(JoueurIA):
    nom = "IA-AvecMasque"
    # Utilise la nouvelle méthode de JoueurIA dans ia_joueur.py

# Version B : l'IA d'origine 100% réseau pur (sans aucun filtre)
class IA_Pure(JoueurIA):
    nom = "IA-SansMasque"

    def jouer_carte(self, main, jouables, pli, contrat, joueur, regles):
        if len(jouables) == 1:
            return jouables[0]

        s = encoder_situation(main, pli, self.historique, contrat, joueur, regles, self.encheres)
        cartes = np.stack([encoder_carte(c, contrat["atout"]) for c in jouables])
        x = np.concatenate([np.repeat(s[None, :], len(jouables), axis=0), cartes], axis=1)

        with torch.no_grad():
            notes = charger(self.fichier)(torch.from_numpy(x)).squeeze(1).numpy()
        k = int(notes.argmax())

        return jouables[k]

if __name__ == "__main__":
    regles = REGLES_STANDARD
    print("=== DUEL : IA avec protection du Valet vs IA 100% réseau pur (15 000 donnes) ===")
    afficher_rapide(IA_Protegee, IA_Pure, 15000, regles, graine=123456)
