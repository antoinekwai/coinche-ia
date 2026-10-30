import time
import numpy as np
import torch
import torch.nn as nn
from generer_donnees import encoder

PALIERS = [80, 90, 100, 110, 120, 130, 140, 150, 160]


def creer_reseau():
    return nn.Sequential(
        nn.Linear(33, 128), nn.ReLU(),
        nn.Linear(128, 128), nn.ReLU(),
        nn.Linear(128, len(PALIERS) + 1))


def preparer(tableau):
    x = torch.tensor(tableau[:, :33])
    pts = tableau[:, 33:34]
    cibles = [(pts >= p) for p in PALIERS] + [tableau[:, 34:35] > 0.5]
    y = torch.tensor(np.concatenate(cibles, axis=1).astype(np.float32))
    return x, y


def evaluer(reseau, main, atout, on_entame=1.0):
    """Probabilités [80, 90, ..., 160, capot] pour une main et un atout."""
    x = torch.tensor([encoder(main, atout) + [on_entame]], dtype=torch.float32)
    appareil = next(reseau.parameters()).device
    with torch.no_grad():
        return torch.sigmoid(reseau(x.to(appareil)))[0].cpu().numpy()


if __name__ == "__main__":
    appareil = "mps" if torch.backends.mps.is_available() else "cpu"
    tableau = np.load("donnees.npy")

    # Les 20 000 dernières donnes servent de test (jamais vues à l'entraînement)
    n_test = 4 * 20000
    x, y = preparer(tableau[:-n_test])
    xt, yt = preparer(tableau[-n_test:])
    x, y, xt, yt = x.to(appareil), y.to(appareil), xt.to(appareil), yt.to(appareil)

    reseau = creer_reseau().to(appareil)
    opt = torch.optim.Adam(reseau.parameters(), lr=1e-3)
    perte_fn = nn.BCEWithLogitsLoss()

    # Référence : un "réseau" qui répondrait toujours la moyenne
    moy = y.mean(0, keepdim=True).clamp(1e-4, 1 - 1e-4)
    base = perte_fn(torch.logit(moy).expand_as(yt), yt).item()
    print(f"Erreur de référence (sans rien apprendre) : {base:.4f}\n")

    debut = time.time()
    for epoque in range(1, 16):
        reseau.train()
        perm = torch.randperm(len(x)).to(appareil)
        for i in range(0, len(x), 2048):
            idx = perm[i:i + 2048]
            perte = perte_fn(reseau(x[idx]), y[idx])
            opt.zero_grad()
            perte.backward()
            opt.step()
        reseau.eval()
        with torch.no_grad():
            pt = perte_fn(reseau(xt), yt).item()
        print(f"  Époque {epoque:2} : erreur sur le test = {pt:.4f} ({time.time() - debut:.0f} s)")

    torch.save(reseau.state_dict(), "modele.pt")
    print("\nRéseau enregistré dans modele.pt\n")

    # Vérification : quand le réseau annonce p %, est-ce vrai p % du temps ? (palier 100)
    with torch.no_grad():
        p = torch.sigmoid(reseau(xt))[:, 2].cpu().numpy()
    reel = yt[:, 2].cpu().numpy()
    print("Prédit (100) | Réel   | Exemples")
    for bas in np.arange(0, 1, 0.1):
        m = (p >= bas) & (p < bas + 0.1)
        if m.sum():
            print(f"  {100*bas:3.0f}-{100*bas+10:3.0f} % | {100*reel[m].mean():5.1f} % | {m.sum():7}")

    # Quelques mains typiques de votre système (atout ♠)
    exemples = {
        "Votre 80 (V + 2 atouts + as)": [("V","♠"),("8","♠"),("7","♠"),("A","♥"),("8","♥"),("9","♦"),("7","♣"),("8","♣")],
        "Votre 90 (V, 9 + atout + as)": [("V","♠"),("9","♠"),("7","♠"),("A","♥"),("8","♥"),("9","♦"),("7","♣"),("8","♣")],
        "Votre 100 (4 atouts dont V, 9)": [("V","♠"),("9","♠"),("A","♠"),("7","♠"),("8","♥"),("9","♦"),("7","♣"),("8","♣")],
        "Main faible": [("R","♠"),("8","♠"),("D","♥"),("8","♥"),("9","♦"),("7","♦"),("7","♣"),("V","♣")],
    }
    print("\nMain                            | 80   90  100  110  120  130 | Conseil")
    for nom, main in exemples.items():
        probas = evaluer(reseau, main, "♠")
        gains = [v * (2 * q - 1) for v, q in zip(PALIERS, probas)]
        meilleur = max(range(len(PALIERS)), key=lambda i: gains[i])
        conseil = f"{PALIERS[meilleur]}" if gains[meilleur] > 0 else "passe"
        print(f"{nom:31} | " + " ".join(f"{100*q:3.0f}" for q in probas[:6]) + f" | {conseil}")
