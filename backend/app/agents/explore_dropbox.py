import os
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

CHANTIERS_PATH = os.getenv("CHANTIERS_PATH")

# Mots clés dans les noms de dossiers ciblés
DOSSIERS_CIBLES = [
    "GestionBonsCdes",
    "Facturation",
    "BON FACTURES",
    "BONS ANNULES",
    "BT finis"
]

# Extensions utiles
EXTENSIONS_UTILES = {'.pdf', '.docx', '.doc', '.xlsx', '.xls'}


def explorer_chantiers(chemin: str):
    """Parcourt uniquement les dossiers ciblés dans ChantiersABBEI"""
    
    fichiers_trouves = []
    compteur_dossiers = 0

    path = Path(chemin)

    # Niveau 1 : bailleurs (HABITAT 76, LOGEAL...)
    for bailleur in path.iterdir():
        if not bailleur.is_dir():
            continue

        # Niveau 2 : chantiers (PE010Y-H76-MarchéEntretien...)
        for chantier in bailleur.iterdir():
            if not chantier.is_dir():
                continue

            # Niveau 3 : on cherche les dossiers ciblés par mot clé
            for sous_dossier in chantier.iterdir():
                if not sous_dossier.is_dir():
                    continue

                if any(cible in sous_dossier.name for cible in DOSSIERS_CIBLES):
                    compteur_dossiers += 1
                    print(f"  ✅ {bailleur.name} / {chantier.name} / {sous_dossier.name}")

                    for fichier in sous_dossier.rglob('*'):
                        if fichier.is_file() and fichier.suffix.lower() in EXTENSIONS_UTILES:
                            fichiers_trouves.append({
                                "bailleur": bailleur.name,
                                "chantier": chantier.name,
                                "dossier": sous_dossier.name,
                                "fichier": fichier.name,
                                "chemin": str(fichier),
                                "extension": fichier.suffix.lower()
                            })

    print(f"\n  → {compteur_dossiers} dossiers ciblés parcourus")
    return fichiers_trouves


def afficher_rapport(fichiers):
    """Affiche le rapport final"""
    
    print("\n" + "="*50)
    print("RAPPORT INVENTAIRE CIBLÉ")
    print("="*50)
    
    stats = defaultdict(int)
    for f in fichiers:
        stats[f["extension"]] += 1
    
    print(f"\n📊 TOTAL FICHIERS UTILES : {len(fichiers)}")
    for ext, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {ext:10} → {count} fichiers")
    
    bailleurs = defaultdict(int)
    for f in fichiers:
        bailleurs[f["bailleur"]] += 1
    
    print(f"\n📁 FICHIERS PAR BAILLEUR :")
    for bailleur, count in sorted(bailleurs.items(), key=lambda x: -x[1])[:15]:
        print(f"  {bailleur:40} → {count} fichiers")


if __name__ == "__main__":
    print("🔍 Exploration des chantiers ABBEI...")
    fichiers_chantiers = explorer_chantiers(CHANTIERS_PATH)
    afficher_rapport(fichiers_chantiers)
    print(f"\n✅ Inventaire terminé : {len(fichiers_chantiers)} fichiers à indexer")