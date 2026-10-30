from rapport_outils import nouveau_document
from rapport_s1 import page_titre, section_en_bref
from rapport_s2 import section_methode
from rapport_s3 import section_mains
from rapport_s4 import section_annonces
from rapport_s5 import section_coinche, section_capot
from rapport_s7 import section_carte, section_limites
from rapport_s9 import section_bareme
from rapport_annexe import annexe_fiche

if __name__ == "__main__":
    doc = nouveau_document()
    page_titre(doc)
    section_en_bref(doc)
    section_methode(doc)
    section_mains(doc)
    section_annonces(doc)
    section_coinche(doc)
    section_capot(doc)
    section_carte(doc)
    section_limites(doc)
    section_bareme(doc)
    doc.add_page_break() 
    annexe_fiche(doc)
    doc.save("rapport_coinche.docx")
    print("rapport_coinche.docx créé")
