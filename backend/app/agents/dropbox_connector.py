import os
import tempfile
import dropbox
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Extensions utiles
EXTENSIONS_UTILES = {'.pdf', '.docx', '.doc', '.xlsx'}

# Dossiers ciblés dans ChantiersABBEI
DOSSIERS_CIBLES = [
    "gestionbonscdes",
    "facturation",
    "bon factures",
    "bons annules",
    "bt finis"
]


def get_client() -> dropbox.Dropbox:
    token = os.getenv("DROPBOX_TOKEN")
    app_key = os.getenv("DROPBOX_APP_KEY")
    app_secret = os.getenv("DROPBOX_APP_SECRET")
    
    if app_key and app_secret:
        return dropbox.Dropbox(
            oauth2_access_token=token,
            app_key=app_key,
            app_secret=app_secret
        )
    return dropbox.Dropbox(token)


def lister_fichiers_dropbox(dbx: dropbox.Dropbox, chemin: str) -> list:
    """Liste récursivement tous les fichiers utiles depuis un chemin Dropbox"""
    fichiers = []
    
    try:
        result = dbx.files_list_folder(chemin, recursive=True)
        
        while True:
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    ext = Path(entry.name).suffix.lower()
                    if ext in EXTENSIONS_UTILES:
                        # Vérifier si le fichier est dans un dossier ciblé
                        chemin_lower = entry.path_lower
                        if any(cible in chemin_lower for cible in DOSSIERS_CIBLES):
                            fichiers.append({
                                "nom": entry.name,
                                "chemin": entry.path_display,
                                "extension": ext,
                                "taille": entry.size
                            })
            
            if not result.has_more:
                break
            result = dbx.files_list_folder_continue(result.cursor)
            
    except dropbox.exceptions.ApiError as e:
        print(f"❌ Erreur Dropbox : {e}")
    
    return fichiers


def telecharger_fichier(dbx: dropbox.Dropbox, chemin_dropbox: str) -> str:
    """Télécharge un fichier Dropbox dans /tmp/ et retourne le chemin local"""
    ext = Path(chemin_dropbox).suffix.lower()
    
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        _, response = dbx.files_download(chemin_dropbox)
        with open(tmp_path, 'wb') as f:
            f.write(response.content)
        return tmp_path
    except Exception as e:
        os.unlink(tmp_path)
        raise e


def telecharger_batch(dbx: dropbox.Dropbox, fichiers: list, taille_batch: int = 100) -> list:
    """Télécharge les fichiers par batch et retourne les chemins locaux"""
    resultats = []
    
    for i in range(0, len(fichiers), taille_batch):
        batch = fichiers[i:i + taille_batch]
        print(f"  → Batch {i//taille_batch + 1} : {len(batch)} fichiers")
        
        for fichier in batch:
            try:
                tmp_path = telecharger_fichier(dbx, fichier["chemin"])
                resultats.append({
                    "tmp_path": tmp_path,
                    "nom": fichier["nom"],
                    "chemin_dropbox": fichier["chemin"],
                    "extension": fichier["extension"]
                })
            except Exception as e:
                print(f"  ❌ {fichier['nom']}: {e}")
                continue
    
    return resultats


if __name__ == "__main__":
    dbx = get_client()
    print("✅ Connecté à Dropbox")
    
    # Test — lister les fichiers HABITAT 76
    print("\n🔍 Listage des fichiers HABITAT 76...")
    fichiers = lister_fichiers_dropbox(
        dbx, 
        "/ABBEI/ChantiersABBEI/HABITAT 76/Y-PE010Y-H76-MarchéEntretien"
    )
    print(f"✅ {len(fichiers)} fichiers trouvés")
    for f in fichiers[:5]:
        print(f"  {f['nom']} ({f['taille']} octets)")