from regles import REGLES_STANDARD
from systeme_v2 import SysV2
from experience_reponse import reponse_variante
from ia_joueur import JoueurIA
from partie import jouer_donne

class Bot(JoueurIA):
    nom = "Bot"
    reponse = reponse_variante("court")

if __name__ == "__main__":
    contrats = 0
    chutes = 0
    coinches = 0
    coinches_chutees = 0

    print("Simulation de 2 000 donnes entre 4 IA...")
    for i in range(2000):
        r = jouer_donne(i % 4, [Bot() for _ in range(4)], REGLES_STANDARD)
        if r is None: continue
        contrats += 1
        c = r["contrat"]
        reussi = r["reussi"]
        
        if not reussi:
            chutes += 1
        if c.get("coinche", 0) > 0:
            coinches += 1
            if not reussi:
                coinches_chutees += 1

    print(f"\nSur {contrats} contrats joués :")
    print(f"  • Contrats réussis : {contrats - chutes} ({100*(contrats-chutes)/contrats:.1f} %)")
    print(f"  • Contrats CHUTÉS  : {chutes} ({100*chutes/contrats:.1f} %)")
    print(f"  • Contrats coinchés : {coinches} ({100*coinches/contrats:.1f} %)")
    print(f"  • Chutes sur coinche : {coinches_chutees}/{coinches} ({100*coinches_chutees/max(1, coinches):.1f} %)")
