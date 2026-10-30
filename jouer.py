import random
from regles import REGLES_STANDARD
from moteur import COULEURS, RANGS, distribuer, cartes_jouables, gagnant_pli, points, equipe_belote, decompte
from systeme_v2 import SysV2
from experience_reponse import reponse_variante
from ia_joueur import JoueurIA, FICHIER

# L'IA utilise le système recommandé complet
class BotIA(JoueurIA):
    nom = "IA"
    reponse = reponse_variante("court")


NOMS_JOUEURS = ["Vous (Sud)", "Ouest", "Partenaire (Nord)", "Est"]

def trier_main(main, atout=None):
    ordre_couleur = {"♠": 0, "♥": 1, "♣": 2, "♦": 3}
    ordre_rang = {"7": 0, "8": 1, "9": 2, "10": 3, "V": 4, "D": 5, "R": 6, "A": 7}
    return sorted(main, key=lambda c: (ordre_couleur.get(c[1], 9), ordre_rang.get(c[0], 0)))

def afficher_main_humain(main):
    cartes_triees = trier_main(main)
    lignes = [f"[{i+1}] {r}{c}" for i, (r, c) in enumerate(cartes_triees)]
    return "  ".join(lignes)

def demander_annonce(main, contrat, regles):
    print("\nVotre main :", afficher_main_humain(main))
    print("Options : tapez 'p' pour passer, 'c' pour coincher, ou une annonce ex: '80 C' (P, C, K, T pour ♠, ♥, ♦, ♣)")
    corresp = {"p": "♠", "c": "♥", "k": "♦", "t": "♣", "s": "♠", "h": "♥", "d": "♦", "c": "♣"}
    
    while True:
        rep = input("Votre décision > ").strip().lower()
        if rep in ("p", "passe", ""):
            return "passe"
        if rep in ("c", "coinche"):
            if contrat is not None and contrat["joueur"] % 2 != 0:
                return "coinche"
            print("Impossible de coincher maintenant.")
            continue
        
        morceaux = rep.split()
        if len(morceaux) == 2 and morceaux[0].isdigit():
            val = int(morceaux[0])
            c_char = morceaux[1][0]
            couleur = {"p": "♠", "h": "♥", "k": "♦", "t": "♣", "c": "♥", "d": "♦", "s": "♠"}.get(c_char)
            if couleur and val in range(80, 170, 10):
                mini = regles["annonce_min"] if contrat is None else contrat["valeur"] + regles["palier"]
                if mini <= val <= regles["annonce_max"]:
                    return (val, couleur)
        print("Format invalide. Exemples : 'p', '80 p' (pique), '90 c' (cœur), '100 k' (carreau), '80 t' (trèfle).")

def phase_annonces_interactive(mains, donneur, bots, regles):
    print("\n" + "="*50)
    print("--- NOUVELLE DONNE : PHASE D'ANNONCES ---")
    print("="*50)
    contrat = None
    j = (donneur + 1) % 4
    passes = 0
    encheres = []

    while True:
        for b in bots:
            if b is not None:
                b.encheres = encheres

        
        if j == 0: # Joueur Humain
            decision = demander_annonce(mains[0], contrat, regles)
        else: # Bot IA
            decision = bots[j].annoncer(mains[j], j, contrat, regles)

        if decision == "coinche" and contrat is not None and contrat["joueur"] % 2 != j % 2:
            contrat["coinche"] = 1
            encheres.append((j, "coinche"))
            print(f"👉 {NOMS_JOUEURS[j]} : COINCHE !")
            return contrat

        if isinstance(decision, tuple):
            valeur, couleur = decision
            capot = regles["capot_autorise"] and valeur == regles["valeur_capot"]
            contrat = {"valeur": valeur, "atout": couleur, "joueur": j, "coinche": 0, "capot": capot}
            passes = 0
            encheres.append((j, decision))
            nom_c = "CAPOT" if capot else valeur
            print(f"👉 {NOMS_JOUEURS[j]} : {nom_c} {couleur}")
        else:
            passes += 1
            encheres.append((j, "passe"))
            print(f"   {NOMS_JOUEURS[j]} : passe")

        if contrat is None and passes == 4:
            return None
        if contrat is not None and passes == 3:
            return contrat
        j = (j + 1) % 4

def jouer_manche_interactive(mains, contrat, premier, bots, regles):
    atout = contrat["atout"]
    pts_eq = [0, 0]
    plis_eq = [0, 0]
    historique = []

    print("\n" + "="*50)
    print(f"--- JEU DE LA CARTE (Atout : {atout} | Contrat : {contrat['valeur']} par {NOMS_JOUEURS[contrat['joueur']]}) ---")
    print("="*50)

    for num in range(1, 9):
        print(f"\n--- Pli {num}/8 ---")
        pli = []
        for i in range(4):
            j = (premier + i) % 4
            jouables = cartes_jouables(mains[j], pli, atout, j, regles)
            
            if j == 0: # Humain
                print(f"Pli en cours : " + "  ".join(f"{NOMS_JOUEURS[jj]}: {r}{c}" for jj, (r, c) in pli) if pli else "Vous entamez le pli.")
                jouables_triees = trier_main(jouables, atout)
                print("Cartes jouables : " + "  ".join(f"[{k+1}] {r}{c}" for k, (r, c) in enumerate(jouables_triees)))
                
                while True:
                    rep = input(f"Votre choix (1 à {len(jouables_triees)}) > ").strip()
                    if rep.isdigit() and 1 <= int(rep) <= len(jouables_triees):
                        carte = jouables_triees[int(rep) - 1]
                        break
                    print("Choix invalide.")
            else: # Bot IA
                bots[j].historique = historique
                carte = bots[j].jouer_carte(mains[j], jouables, pli, contrat, j, regles)
                if carte not in jouables:
                    carte = jouables[0]
                print(f"{NOMS_JOUEURS[j]} joue : {carte[0]}{carte[1]}")

            mains[j].remove(carte)
            pli.append((j, carte))
            historique.append((j, carte))

        gagnant, c_gagnante = gagnant_pli(pli, atout)
        eq = gagnant % 2
        plis_eq[eq] += 1
        pts_pli = sum(points(c, atout) for _, c in pli)
        if num == 8:
            pts_pli += regles["dix_de_der"]
        pts_eq[eq] += pts_pli
        print(f"==> Pli remporté par {NOMS_JOUEURS[gagnant]} avec {c_gagnante[0]}{c_gagnante[1]} (+{pts_pli} pts)")
        premier = gagnant

    return pts_eq, plis_eq

def partie_interactive():
    regles = REGLES_STANDARD
    bots = [None, BotIA(), BotIA(), BotIA()]
    scores = [0, 0] # [Equipe Nous (0+2), Equipe Eux (1+3)]
    donneur = 0

    while max(scores) < regles["score_objectif"]:
        mains = distribuer()
        copie_mains = [m[:] for m in mains]
        contrat = phase_annonces_interactive(mains, donneur, bots, regles)

        if contrat is None:
            print("\nTout le monde passe ! On redistribue...")
            donneur = (donneur + 1) % 4
            continue

        atout = contrat["atout"]
        belote = equipe_belote(copie_mains, atout)
        if belote is not None:
            camp_belote = "Votre équipe" if belote == 0 else "L'équipe adverse"
            print(f"🔔 Belote annoncée pour {camp_belote} !")

        pts_eq, plis_eq = jouer_manche_interactive(mains, contrat, (donneur + 1) % 4, bots, regles)
        marque, reussi = decompte(contrat, pts_eq, plis_eq, belote, regles)

        scores[0] += marque[0]
        scores[1] += marque[1]

        statut = "RÉUSSI" if reussi else "CHUTÉ"
        print("\n" + "#"*45)
        print(f"FIN DE LA DONNE : Contrat {contrat['valeur']} {atout} {statut} !")
        print(f"Points cartes : Vous {pts_eq[0]} - {pts_eq[1]} Eux")
        print(f"Points marqués cette donne : Vous +{marque[0]} | Eux +{marque[1]}")
        print(f"SCORE TOTAL : VOUS {scores[0]} - {scores[1]} EUX (Objectif : {regles['score_objectif']})")
        print("#"*45)

        donneur = (donneur + 1) % 4
        input("\nAppuyez sur Entrée pour la donne suivante...")

    gagnant = "VOUS avez gagné !" if scores[0] >= regles["score_objectif"] else "Les BOTS ont gagné !"
    print("\n" + "🏆"*20)
    print(f"FIN DE PARTIE : {gagnant} ({scores[0]} à {scores[1]})")
    print("🏆"*20 + "\n")

if __name__ == "__main__":
    partie_interactive()
