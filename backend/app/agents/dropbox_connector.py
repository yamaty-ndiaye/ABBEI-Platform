import os
import tempfile
import dropbox
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Extensions utiles
EXTENSIONS_UTILES = {'.pdf', '.docx', '.doc', '.xlsx'}


def get_client() -> dropbox.Dropbox:
    """Retourne un client Dropbox authentifié"""
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

    def explorer(path):
        try:
            result = dbx.files_list_folder(path)
            while True:
                for entry in result.entries:
                    if isinstance(entry, dropbox.files.FileMetadata):
                        ext = Path(entry.name).suffix.lower()
                        if ext in EXTENSIONS_UTILES:
                            fichiers.append({
                                "nom": entry.name,
                                "chemin": entry.path_display,
                                "extension": ext,
                                "taille": entry.size
                            })
                    elif isinstance(entry, dropbox.files.FolderMetadata):
                        # Récursion manuelle dans chaque sous-dossier
                        explorer(entry.path_display)
                if not result.has_more:
                    break
                result = dbx.files_list_folder_continue(result.cursor)
        except dropbox.exceptions.ApiError as e:
            print(f"  ⚠️ Dossier inaccessible : {path} — {e}")

    explorer(chemin)
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
def generer_lien(dbx: dropbox.Dropbox, chemin_dropbox: str) -> str:
    """Génère un lien partagé vers un fichier Dropbox"""
    try:
        # Vérifier si un lien existe déjà
        liens = dbx.sharing_list_shared_links(path=chemin_dropbox)
        if liens.links:
            return liens.links[0].url
        # Sinon en créer un
        lien = dbx.sharing_create_shared_link_with_settings(chemin_dropbox)
        return lien.url
    except Exception as e:
        return None

if __name__ == "__main__":
    dbx = get_client()
    print("✅ Connecté à Dropbox")

    print("\n🔍 Listage des fichiers HABITAT 76...")
    fichiers = lister_fichiers_dropbox(
        dbx,
        "/ABBEI/ChantiersABBEI/HABITAT 76/Y-PE010Y-H76-MarchéEntretien"
    )
    print(f"✅ {len(fichiers)} fichiers trouvés")
    for f in fichiers[:5]:
        print(f"  {f['nom']} ({f['taille']} octets)")