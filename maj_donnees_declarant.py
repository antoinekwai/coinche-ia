import glob
import time
import numpy as np

def detecter_role_attaque(s):
    """
    Détermine si le joueur est le Déclarant (1.0) ou le Soutien (0.5).
    s[236] vaut 1.0 (Attaque) ou 0.0 (Défense).
    Enchères :
      Moi : indices 249 à 256.
        s[249] = a parlé, s[253] = a parlé à l'atout, s[256] = a passé d'entrée
      Partenaire : indices 265 à 272.
        s[265] = a parlé, s[269] = a parlé à l'atout, s[272] = a passé d'entrée
    """
    if s[236] == 0.0:
        return 0.0 # Défense reste 0.0

    moi_passe_entree = (s[256] == 1.0)
    part_passe_entree = (s[272] == 1.0)
    moi_a_dit_atout = (s[253] == 1.0)
    part_a_dit_atout = (s[269] == 1.0)

    # Si j'ai passé d'entrée, je ne peux pas être l'ouvreur initial
    if moi_passe_entree and part_a_dit_atout:
        return 0.5
    # Si le partenaire a passé d'entrée, il ne peut pas être l'ouvreur
    if part_passe_entree and moi_a_dit_atout:
        return 1.0

    # Si un seul des deux a nommé l'atout
    if moi_a_dit_atout and not part_a_dit_atout:
        return 1.0
    if part_a_dit_atout and not moi_a_dit_atout:
        return 0.5

    # Si les deux ont soutenu à l'atout : comparer la première enchère
    # Celui qui a ouvert en premier a généralement la première annonce la plus basse (ex: 80 vs 100)
    val_premiere_moi = s[250]
    val_premiere_part = s[266]
    if val_premiere_moi < val_premiere_part and val_premiere_moi > 0:
        return 1.0
    elif val_premiere_part < val_premiere_moi and val_premiere_part > 0:
        return 0.5

    # Par défaut si indistinguable
    return 1.0

def mettre_a_jour_tous_les_blocs():
    fichiers = sorted(glob.glob("imitation_encheres/bloc_*.npz"))
    if not fichiers:
        print("Aucun fichier trouvé dans imitation_encheres/")
        return

    print(f"Mise à jour de la variable Déclarant dans les {len(fichiers)} blocs...")
    debut = time.time()
    total_decisions = 0
    nb_declarant = 0
    nb_soutien = 0
    nb_defense = 0

    for idx, f in enumerate(fichiers):
        data = np.load(f)
        S = data["S"]
        D = data["D"]
        C = data["C"]
        V = data["V"]

        # Mise à jour vectorisée de la colonne 236
        for i in range(len(S)):
            nouveau_role = detecter_role_attaque(S[i])
            S[i, 236] = nouveau_role
            if nouveau_role == 1.0:
                nb_declarant += 1
            elif nouveau_role == 0.5:
                nb_soutien += 1
            else:
                nb_defense += 1

        total_decisions += len(S)
        np.savez(f, S=S, D=D, C=C, V=V)
        print(f"  Bloc {idx:2d}/{len(fichiers)-1} mis à jour ({f})")

    print(f"\nTerminé en {time.time() - debut:.1f} secondes !")
    print(f"Total décisions traitées : {total_decisions}")
    print(f"  • Je suis Déclarant (1.0) : {nb_declarant} ({100*nb_declarant/total_decisions:.1f} %)")
    print(f"  • Mon Partenaire l'est (0.5) : {nb_soutien} ({100*nb_soutien/total_decisions:.1f} %)")
    print(f"  • En Défense (0.0) : {nb_defense} ({100*nb_defense/total_decisions:.1f} %)")

if __name__ == "__main__":
    mettre_a_jour_tous_les_blocs()
