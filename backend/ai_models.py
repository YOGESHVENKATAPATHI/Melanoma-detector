import os
import cv2
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import albumentations as A
from albumentations.pytorch import ToTensorV2
import timm
from datetime import datetime

from dropbox_manager import dbx_cluster, FEEDBACK_WEIGHT_NAME

class Config:
    MODEL_NAME = 'coatnet_0_rw_224' 
    FEEDBACK_MODEL_NAME = 'mobilenetv3_small_050'
    IMG_SIZE = 224
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # 🛡️ SELECTIVE ENSEMBLING THRESHOLD
    MIN_AUC_THRESHOLD = 0.95 
    
    # Active Learning Config (Local Temporary Paths)
    FEEDBACK_DIR = './user_feedback_images'
    FEEDBACK_CSV = 'feedback_log.csv'
    
    # LOWERED LEARNING RATE to prevent gradient explosion on tiny datasets
    LR = 1e-4 
    BATCH_SIZE = 4
    
    # 🚀 UPDATED: Side-car model now controls 60% of the final decision!
    FUSION_WEIGHT = 0.80 

os.makedirs(Config.FEEDBACK_DIR, exist_ok=True)

class MelanomaClassifier(nn.Module):
    def __init__(self, model_name):
        super().__init__()
        # Use timm to create model but turn off pretrained to avoid downloading in API unless needed
        # Or keep pretrained=False if we are loading weights anyway
        self.model = timm.create_model(model_name, pretrained=False, num_classes=1)
    def forward(self, x): return self.model(x)

def get_transforms(is_train=False):
    if is_train:
        return A.Compose([
            A.Resize(Config.IMG_SIZE, Config.IMG_SIZE),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.5),
            A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.1, rotate_limit=45, p=0.5),
            A.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
            ToTensorV2(),
        ])
    return A.Compose([
        A.Resize(Config.IMG_SIZE, Config.IMG_SIZE),
        A.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
        ToTensorV2(),
    ])

class FeedbackDataset(Dataset):
    def __init__(self, df, transform=None):
        self.df = df
        self.transform = transform
    def __len__(self): return len(self.df)
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        local_img_path = os.path.join(Config.FEEDBACK_DIR, row['image_name'])
        if not os.path.exists(local_img_path):
            dbx_cluster.download_file(row['image_name'], local_img_path)
            
        img = cv2.imread(local_img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if self.transform:
            img = self.transform(image=img)['image']
        return img, torch.tensor(row['target'], dtype=torch.float32)

def load_ensemble_model(model_path):
    model = MelanomaClassifier(Config.MODEL_NAME).to(Config.DEVICE)
    try:
        ckpt = torch.load(model_path, map_location=Config.DEVICE)
        state_dict = ckpt['model_state_dict'] if (isinstance(ckpt, dict) and 'model_state_dict' in ckpt) else ckpt
        clean_state_dict = {k.replace('module.', ''): (v.float() if torch.is_tensor(v) else v) for k, v in state_dict.items()}
        model.load_state_dict(clean_state_dict)
        model.eval() 
        return model
    except Exception as e: 
        print(f"Failed to load model {model_path}: {e}")
        return None

def initialize_feedback_model():
    model = MelanomaClassifier(Config.FEEDBACK_MODEL_NAME).to(Config.DEVICE)
    print("   🔍 Checking Cluster for existing Side-Car model...")
    if dbx_cluster.download_file(FEEDBACK_WEIGHT_NAME, f"./{FEEDBACK_WEIGHT_NAME}"):
        model.load_state_dict(torch.load(f"./{FEEDBACK_WEIGHT_NAME}", map_location=Config.DEVICE))
        print("   ✅ Clustered Side-Car Model Loaded & Synced!")
    else:
        print("   ℹ️ No custom feedback model found in cluster. Initializing fresh.")
    return model

def apply_surgical_hair_removal(image_rgb):
    lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
    l_channel, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    cl = clahe.apply(l_channel)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    blackhat = cv2.morphologyEx(cl, cv2.MORPH_BLACKHAT, kernel)
    _, mask = cv2.threshold(blackhat, 10, 255, cv2.THRESH_BINARY)
    return cv2.inpaint(image_rgb, mask, 3, cv2.INPAINT_TELEA)

# Global models (loaded once)
LOADED_MODELS = []
MODEL_NAMES = []
FEEDBACK_MODEL = None

def init_models():
    global FEEDBACK_MODEL, LOADED_MODELS, MODEL_NAMES
    model_paths = dbx_cluster.download_all_models()
    for path in model_paths:
        model = load_ensemble_model(path)
        if model is not None:
            LOADED_MODELS.append(model)
            MODEL_NAMES.append(os.path.basename(path))
    FEEDBACK_MODEL = initialize_feedback_model()

def predict_lesion(image_rgb):
    try:
        global FEEDBACK_MODEL
        if image_rgb is None: return None, None, "⚠️ Please provide an image."
        
        # 🛡️ THE SAFETY NET: Check if we actually have models to predict with
        if not LOADED_MODELS and not os.path.exists(f"./{FEEDBACK_WEIGHT_NAME}"):
            return None, None, f"⚠️ ERROR: No models found with AUC > {Config.MIN_AUC_THRESHOLD} and no Side-Car trained."

        cleaned_image = apply_surgical_hair_removal(image_rgb)
        transform = get_transforms(is_train=False)
        img_tensor = transform(image=cleaned_image)['image'].unsqueeze(0).to(Config.DEVICE)
        
        probabilities = []
        breakdown_text = []

        # 1. Run Main Core (Only if loaded)
        if LOADED_MODELS:
            for model, name in zip(LOADED_MODELS, MODEL_NAMES):
                with torch.no_grad():
                    if torch.cuda.is_available():
                        with torch.amp.autocast('cuda'):
                            logits = model(img_tensor).squeeze(1)
                    else:
                        logits = model(img_tensor).squeeze(1)
                    prob = torch.sigmoid(logits).item()
                    probabilities.append(prob)
                    breakdown_text.append(f"Main Core ({name}): {prob:.4f}")
            
            ensemble_prob = float(np.mean(probabilities))
        else:
            ensemble_prob = 0.0 # Fallback if only the side-car exists
            breakdown_text.append("Main Core: OFF (No elite models found)")

        final_prob = ensemble_prob
        
        # 2. Run Side-Car Feedback Override (If trained)
        if os.path.exists(f"./{FEEDBACK_WEIGHT_NAME}"):
            FEEDBACK_MODEL.eval()
            with torch.no_grad():
                if torch.cuda.is_available():
                    with torch.amp.autocast('cuda'):
                        logits = FEEDBACK_MODEL(img_tensor).squeeze(1)
                else:
                    logits = FEEDBACK_MODEL(img_tensor).squeeze(1)
                feedback_prob = torch.sigmoid(logits).item()
                
            # FUSION MATH
            if LOADED_MODELS:
                final_prob = (ensemble_prob * (1.0 - Config.FUSION_WEIGHT)) + (feedback_prob * Config.FUSION_WEIGHT)
            else:
                final_prob = feedback_prob
                
            breakdown_text.append("--- FUSION OVERRIDE ---")
            breakdown_text.append(f"Clustered Feedback Model: {feedback_prob:.4f} (Weight: {Config.FUSION_WEIGHT*100}%)")
            breakdown_text.append(f"Adjusted Final Score: {final_prob:.4f}")

        pred_class = "Malignant" if final_prob >= 0.5 else "Benign"
        breakdown_text.insert(0, f"🌟 FINAL VERDICT: {pred_class} 🌟\n")

        return cleaned_image, final_prob, pred_class, "\n".join(breakdown_text)
        
    except Exception as e:
        error_msg = f"⚠️ CRITICAL ERROR DURING PREDICTION:\n{str(e)}"
        print(error_msg)
        return None, None, None, error_msg

def process_feedback(image_rgb, image_name, actual_diagnosis):
    true_label = 1 if actual_diagnosis == "Malignant" else 0

    local_img_path = os.path.join(Config.FEEDBACK_DIR, image_name)
    cv2.imwrite(local_img_path, cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))

    dbx_cluster.download_file(Config.FEEDBACK_CSV, f"./{Config.FEEDBACK_CSV}")
    if not os.path.exists(f"./{Config.FEEDBACK_CSV}"):
        pd.DataFrame(columns=['image_name', 'target', 'source']).to_csv(f"./{Config.FEEDBACK_CSV}", index=False)
        
    new_data = pd.DataFrame([{'image_name': image_name, 'target': true_label, 'source': 'USER_FEEDBACK'}])
    new_data.to_csv(f"./{Config.FEEDBACK_CSV}", mode='a', header=not os.path.exists(f"./{Config.FEEDBACK_CSV}"), index=False)
    
    dbx_cluster.upload_file(local_img_path, image_name)
    dbx_cluster.upload_file(f"./{Config.FEEDBACK_CSV}", Config.FEEDBACK_CSV)
    return f"☁️ ✅ Data Synced to Cluster! Explicit true label saved as {'Malignant' if true_label == 1 else 'Benign'}."

def train_feedback_sidecar():
    global FEEDBACK_MODEL
    if not dbx_cluster.download_file(Config.FEEDBACK_CSV, f"./{Config.FEEDBACK_CSV}"):
        return "⚠️ Could not find feedback data in the cluster."
        
    df = pd.read_csv(f"./{Config.FEEDBACK_CSV}")
    if len(df) < 2: return "⚠️ Need at least 2 clustered feedback images to begin training."

    loader = DataLoader(FeedbackDataset(df, transform=get_transforms(is_train=True)), batch_size=Config.BATCH_SIZE, shuffle=True)
    criterion = nn.BCEWithLogitsLoss()
    
    FEEDBACK_MODEL.train()
    optimizer = optim.AdamW(FEEDBACK_MODEL.parameters(), lr=Config.LR, weight_decay=1e-3)
    
    scaler = torch.amp.GradScaler('cuda') if torch.cuda.is_available() else None
    
    for epoch in range(5):
        for images, labels in loader:
            images, labels = images.to(Config.DEVICE), labels.to(Config.DEVICE)
            if torch.cuda.is_available():
                with torch.amp.autocast('cuda'):
                    outputs = FEEDBACK_MODEL(images).squeeze(1)
                    loss = criterion(outputs, labels)
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
            else:
                outputs = FEEDBACK_MODEL(images).squeeze(1)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
            optimizer.zero_grad()

    torch.save(FEEDBACK_MODEL.state_dict(), f"./{FEEDBACK_WEIGHT_NAME}")
    dbx_cluster.upload_file(f"./{FEEDBACK_WEIGHT_NAME}", FEEDBACK_WEIGHT_NAME)
    
    return f"☁️ 🚀 SUCCESS! Side-Car Model trained and pushed to Dropbox Cluster."
