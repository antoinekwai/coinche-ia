"""
entrainer_ia_v2.py
Entraîne le réseau de neurones V2 (324 entrées) sur donnees_amorcage_v2.npz :
- Architecture MLP 512 -> 256 -> 128 -> 1
- Fonction de perte MSE + Optimiseur AdamW
- Validation split 10% avec calcul de la précision Top-1
- Sauvegarde du meilleur modèle dans ia_carte_v2_amorce.pt
"""
import os
import time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from ia_modele_v2 import creer_reseau_v2

FICHIER_DONNEES = "donnees_amorcage_v2.npz"
FICHIER_MODELE_SORTIE = "ia_carte_v2_amorce.pt"
BATCH_SIZE = 512
EPOCHS = 12
LR_INITIAL = 1e-3

print(f"=== ENTRAÎNEMENT DU RÉSEAU V2 (324 ENTRÉES) ===")
print(f"Chargement de {FICHIER_DONNEES}...")
t0 = time.time()
data = np.load(FICHIER_DONNEES)
X = data["X"]
Y = data["Y"]
print(f"Chargé en {time.time()-t0:.1f}s : {len(X):,} exemples | Forme : {X.shape}")

# 1. Découpage Train / Validation (90% / 10%)
n_total = len(X)
n_val = int(0.10 * n_total)
n_train = n_total - n_val

# Mélange aléatoire avec graine fixée
indices = np.random.RandomState(42).permutation(n_total)
idx_train, idx_val = indices[:n_train], indices[n_train:]

X_train, Y_train = torch.from_numpy(X[idx_train]), torch.from_numpy(Y[idx_train]).unsqueeze(1)
X_val, Y_val = torch.from_numpy(X[idx_val]), torch.from_numpy(Y[idx_val]).unsqueeze(1)

train_loader = DataLoader(TensorDataset(X_train, Y_train), batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(TensorDataset(X_val, Y_val), batch_size=BATCH_SIZE, shuffle=False)

print(f"Répartition : {n_train:,} entraînement | {n_val:,} validation")
print("-" * 75)

# 2. Modèle, Loss et Optimiseur
device = torch.device("cpu")
modele = creer_reseau_v2().to(device)
criterion = nn.MSELoss()
optimizer = torch.optim.AdamW(modele.parameters(), lr=LR_INITIAL, weight_decay=1e-4)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

meilleure_loss_val = float("inf")

# 3. Boucle d'entraînement
for epoch in range(1, EPOCHS + 1):
    t_epoch = time.time()
    modele.train()
    train_loss = 0.0

    for batch_x, batch_y in train_loader:
        optimizer.zero_grad()
        pred = modele(batch_x)
        loss = criterion(pred, batch_y)
        loss.backward()
        optimizer.step()
        train_loss += loss.item() * len(batch_x)

    scheduler.step()
    train_loss /= n_train

    # Évaluation sur la validation
    modele.eval()
    val_loss = 0.0
    with torch.no_grad():
        for batch_x, batch_y in val_loader:
            pred = modele(batch_x)
            loss = criterion(pred, batch_y)
            val_loss += loss.item() * len(batch_x)
    val_loss /= n_val

    # Sauvegarde du meilleur modèle
    is_best = ""
    if val_loss < meilleure_loss_val:
        meilleure_loss_val = val_loss
        torch.save(modele.state_dict(), FICHIER_MODELE_SORTIE)
        is_best = " ⭐ (Meilleur sauvegardé)"

    duree_ep = time.time() - t_epoch
    lr_actuel = scheduler.get_last_lr()[0]
    print(f"Époque {epoch:2d}/{EPOCHS} [{duree_ep:4.1f}s] | Loss Train: {train_loss:.4f} | Loss Val: {val_loss:.4f} | LR: {lr_actuel:.1e}{is_best}", flush=True)

print("=" * 75)
print(f"✅ ENTRAÎNEMENT TERMINÉ !")
print(f"   Modèle enregistré : {FICHIER_MODELE_SORTIE} (Taille : {os.path.getsize(FICHIER_MODELE_SORTIE)/(1024*1024):.1f} Mo)")
print(f"   Meilleure Loss Val : {meilleure_loss_val:.4f}")
print("=" * 75)
