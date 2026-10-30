import torch
from moteur import COULEURS
from regles import REGLES_STANDARD
from systeme import nb_atouts, plis_surs
from experience_coinche import SysCoinche, variante
from entrainer import creer_reseau, PALIERS
from generer_donnees import encoder
from rapide import afficher_rapide

_RESEAU = None   # chargé une seule fois par cœur de calcul


def reseau():
    global _RESEAU
    if _RESEAU is None:
        torch.set_num_threads(1)          # chaque cœur travaille seul
        _RESEAU = creer_reseau()
        _RESEAU.load_state_dict(torch.load("modele.pt", map_location="cpu"))
        _RESEAU.eval()
    return _RESEAU


def probabilites(main, on_entame):
    """Probabilités [80, ..., 160, capot] pour les 4 atouts, calculées d'un coup."""
    x = torch.tensor([encoder(main, c) + [on_entame] for c in COULEURS], dtype=torch.float32)
    with torch.no_grad():
        p = torch.sigmoid(reseau()(x)).numpy()
    return {c: p[i] for i, c in enumerate(COULEURS)}


class JoueurReseau(SysCoinche):
    """Votre système complet, mais l'ouvreur évalue sa main avec le réseau."""
    nom = "Réseau"
    seuil_reseau = 0.7     # probabilité de réussite exigée pour annoncer un palier

    def annoncer(self, main, joueur, contrat, regles):
        self.moi = joueur
        self.probas = None
        return super().annoncer(main, joueur, contrat, regles)

    def niveau(self, main, a):
        # Le capot d'entrée (toutes les cartes maîtresses) reste votre règle : 100 % de réussite
        if nb_atouts(main, a) >= 4 and plis_surs(main, a) == len(main):
            return 250
        if self.probas is None:
            premier = self.encheres[0][0] if self.encheres else self.moi
            on_entame = 1.0 if premier % 2 == self.moi % 2 else 0.0
            self.probas = probabilites(main, on_entame)
        niv = 0
        for palier, p in zip(PALIERS, self.probas[a]):
            if p >= self.seuil_reseau:
                niv = palier
        return niv


def joueur_reseau(seuil):
    class J(JoueurReseau):
        pass
    J.seuil_reseau, J.nom = seuil, f"Réseau{int(100 * seuil)}"
    return J


if __name__ == "__main__":
    reference = variante(4)   # votre système complet (marge 30, coinche seuil 4)
    print("=== Réseau (selon le seuil) contre votre système ===\n")
    for s in [0.5, 0.6, 0.7, 0.8, 0.9]:
        afficher_rapide(joueur_reseau(s), reference, 5000, REGLES_STANDARD)
