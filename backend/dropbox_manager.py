import dropbox
import os
import re

# Central config
MIN_AUC_THRESHOLD = 0.95
FEEDBACK_WEIGHT_NAME = 'local_feedback_model.pth'

DROPBOX_CLUSTER_CREDS = [
    {
        'name': 'Account_01',
        'app_key': 'khk7l9vvlaylxcx',
        'app_secret': 'm459gltp6yaspic',
        'refresh_token': 'SIWvJLJuBnUAAAAAAAAAAfh2tA0b52XM3VMEjFlEABJmMWMfqr3yi945aNaNHo39'
    },
    {
        'name': 'Account_02',
        'app_key': 'rnoae6jj1bs66we',
        'app_secret': '4yjajvz9ajiax4h',
        'refresh_token': 'ZxSuV2l21AwAAAAAAAAAAdWblHU6TGAMmbrZj1rzSceha9PShqM4PsK7tNS_fO5i'
    }
]

class DropboxCluster:
    def __init__(self, creds_list):
        self.clients = []
        print(f"🔄 Initializing Dropbox Cluster...")
        for cred in creds_list:
            try:
                dbx = dropbox.Dropbox(
                    app_key=cred['app_key'],
                    app_secret=cred['app_secret'],
                    oauth2_refresh_token=cred['refresh_token']
                )
                dbx.users_get_current_account()
                self.clients.append({'name': cred['name'], 'dbx': dbx})
                print(f"   ✅ Connected to {cred['name']}")
            except Exception as e: 
                print(f"⚠️ Failed to connect to {cred['name']}: {e}")

    def download_all_models(self, download_dir='./downloaded_models'):
        if not os.path.exists(download_dir): os.makedirs(download_dir)
        model_files = []
        print(f"   🔍 Scanning Dropbox for Main Ensemble weights (AUC > {MIN_AUC_THRESHOLD})...")
        
        found_models = []
        for node in self.clients:
            try:
                files = node['dbx'].files_list_folder('').entries
                for entry in files:
                    if entry.name.endswith('.pth') and entry.name != FEEDBACK_WEIGHT_NAME:
                        match = re.search(r'_auc_([\d\.]+)\.pth', entry.name)
                        if match:
                            auc = float(match.group(1))
                            if auc > MIN_AUC_THRESHOLD:
                                found_models.append({'name': entry.name, 'path': entry.path_lower, 'auc': auc, 'dbx': node['dbx']})
            except Exception: pass
            
        # Sort by AUC descending and take the top 2
        found_models.sort(key=lambda x: x['auc'], reverse=True)
        best_models = found_models[:2]
        
        for model in best_models:
            local_path = os.path.join(download_dir, model['name'])
            if not os.path.exists(local_path):
                print(f"      ⬇️ Downloading {model['name']} (Elite Model - AUC: {model['auc']:.4f})...")
                try:
                    model['dbx'].files_download_to_file(local_path, model['path'])
                except Exception as e:
                    print(f"      ⚠️ Failed to download {model['name']}: {e}")
                    continue
            model_files.append(local_path)
            
        return sorted(list(set(model_files)))

    def upload_file(self, local_path, remote_name):
        for node in self.clients:
            try:
                with open(local_path, "rb") as f:
                    node['dbx'].files_upload(f.read(), f"/{remote_name}", mode=dropbox.files.WriteMode('overwrite'))
                return True
            except Exception as e: 
                print(f"⚠️ Upload failed on {node['name']}: {e}")
                continue
        return False

    def download_file(self, remote_name, local_path):
        for node in self.clients:
            try:
                node['dbx'].files_download_to_file(local_path, f"/{remote_name}")
                return True
            except Exception: continue
        return False

# Initialize a global instance
dbx_cluster = DropboxCluster(DROPBOX_CLUSTER_CREDS)
