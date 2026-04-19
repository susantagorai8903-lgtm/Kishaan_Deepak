"""
paddy-disease-classification.py
---------------------------------
Training script for the paddy-disease HOG + Logistic Regression classifier.

Usage
-----
    # Train on all images in dataset/
    python paddy-disease-classification.py

    # Limit total images (faster dev run)
    python paddy-disease-classification.py --max-images 500

    # Run a quick prediction on a single image
    python paddy-disease-classification.py --predict path/to/leaf.jpg

Dataset layout expected
------------------------
    dataset/
        Bacterial_Leaf_Blight/
            img001.jpg
            img002.png
            ...
        Brown_Spot/
            ...
        ...

Trained artefact saved to
--------------------------
    models/paddy_disease_model.pkl
    (a tuple: sklearn Pipeline, LabelEncoder)

NOTE: Do NOT change HOG parameters here without retraining and updating
      config.py to match, or inference will produce garbage predictions.
"""

import argparse
import os
import random

import cv2
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from skimage.feature import hog

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "dataset")
MODEL_PATH = os.path.join(BASE_DIR, "models", "paddy_disease_model.pkl")

# ── HOG parameters — must stay in sync with config.py ────────────────────────
HOG_ORIENTATIONS    = 9
HOG_PIXELS_PER_CELL = (8, 8)
HOG_CELLS_PER_BLOCK = (2, 2)
HOG_BLOCK_NORM      = "L2-Hys"
IMG_SIZE            = (128, 128)


# ═════════════════════════════════════════════════════════════════════════════
#  Dataset loading
# ═════════════════════════════════════════════════════════════════════════════

def load_dataset(data_dir: str, max_images: int | None = None):
    """
    Walk *data_dir* and load images + string labels.

    Parameters
    ----------
    data_dir   : str            Root directory (each sub-folder = one class).
    max_images : int | None     If set, randomly sample this many images total.

    Returns
    -------
    images : np.ndarray   Shape (N, 128, 128, 3) — BGR, uint8.
    labels : np.ndarray   Shape (N,) — string class names.
    paths  : list[str]    Corresponding file paths (for debug messages).
    """
    images, labels, paths = [], [], []

    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"Dataset directory not found: {data_dir}")

    all_items = []
    for class_name in os.listdir(data_dir):
        class_dir = os.path.join(data_dir, class_name)
        if not os.path.isdir(class_dir):
            continue
        for fname in os.listdir(class_dir):
            if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                all_items.append((os.path.join(class_dir, fname), class_name))

    if not all_items:
        return np.array(images), np.array(labels), paths

    if max_images and max_images < len(all_items):
        random.seed(42)
        all_items = random.sample(all_items, max_images)

    for idx, (img_path, class_name) in enumerate(all_items, 1):
        img = cv2.imread(img_path)
        if img is None:
            print(f"  ⚠  Skipping unreadable image: {img_path}")
            continue
        try:
            img = cv2.resize(img, IMG_SIZE)
        except Exception as exc:
            print(f"  ⚠  Resize failed {img_path}: {exc}")
            continue
        images.append(img)
        labels.append(class_name)
        paths.append(img_path)
        if idx % 200 == 0:
            print(f"  Loaded {idx}/{len(all_items)} images …")

    return np.array(images), np.array(labels), paths


# ═════════════════════════════════════════════════════════════════════════════
#  HOG feature extraction
# ═════════════════════════════════════════════════════════════════════════════

def extract_features(images: np.ndarray, paths: list[str] | None = None) -> np.ndarray:
    """
    Compute HOG feature vectors for every image in *images*.

    If HOG extraction fails for an image, a zero vector of the correct length
    is inserted so the dataset index stays aligned.
    """
    # Compute expected feature length from a blank image
    _blank = np.zeros(IMG_SIZE, dtype=np.uint8)
    feat_len = len(
        hog(_blank, orientations=HOG_ORIENTATIONS,
            pixels_per_cell=HOG_PIXELS_PER_CELL,
            cells_per_block=HOG_CELLS_PER_BLOCK,
            block_norm=HOG_BLOCK_NORM)
    )

    features = []
    for idx, img in enumerate(images):
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            feat = hog(
                gray,
                orientations   = HOG_ORIENTATIONS,
                pixels_per_cell= HOG_PIXELS_PER_CELL,
                cells_per_block = HOG_CELLS_PER_BLOCK,
                block_norm      = HOG_BLOCK_NORM,
            )
            features.append(feat)
        except Exception as exc:
            src = (paths[idx] if paths and idx < len(paths) else f"index {idx}")
            print(f"  ⚠  HOG failed for {src}: {exc}.  Using zero vector.")
            features.append(np.zeros(feat_len))

    return np.array(features)


# ═════════════════════════════════════════════════════════════════════════════
#  Training
# ═════════════════════════════════════════════════════════════════════════════

def train(max_images: int | None = None) -> None:
    """Load the dataset, train the model, print metrics, and save the artefact."""
    print("Loading dataset …")
    X, y, paths = load_dataset(DATA_DIR, max_images=max_images)
    print(f"Loaded {len(X)} images.")

    if len(X) == 0:
        print("No images found.  Place images in dataset/<ClassName>/ folders.")
        return

    print("Extracting HOG features …")
    X_feat = extract_features(X, paths)

    encoder = LabelEncoder()
    y_enc   = encoder.fit_transform(y)

    unique, counts = np.unique(y, return_counts=True)
    print("\nClass distribution:")
    for cls, cnt in zip(unique, counts):
        print(f"  {cls}: {cnt}")

    if len(unique) < 2:
        print("Need at least 2 classes.  Exiting.")
        return

    X_train, X_test, y_train, y_test = train_test_split(
        X_feat, y_enc, test_size=0.2, random_state=42
    )

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf",    LogisticRegression(
            multi_class="auto",
            solver     ="lbfgs",
            max_iter   =1000,
            C          =1.0,
            random_state=42,
        )),
    ])

    print("\nTraining Logistic Regression …")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(f"\nAccuracy: {accuracy_score(y_test, y_pred):.4f}")

    try:
        test_labels = np.unique(y_test)
        print("\nClassification Report:\n",
              classification_report(
                  y_test, y_pred,
                  labels      =test_labels,
                  target_names=encoder.inverse_transform(test_labels),
              ))
    except Exception as exc:
        print(f"⚠  Could not generate classification report: {exc}")
        print(classification_report(y_test, y_pred, zero_division=0))

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump((model, encoder), MODEL_PATH)
    print(f"\n✅  Model saved → {MODEL_PATH}")


# ═════════════════════════════════════════════════════════════════════════════
#  Single-image prediction helper (for quick CLI testing)
# ═════════════════════════════════════════════════════════════════════════════

def predict_single(image_path: str) -> str:
    """
    Load the saved model and predict the disease class for one image.

    Parameters
    ----------
    image_path : str    Path to a PNG / JPEG leaf image.

    Returns
    -------
    str — predicted class name.
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}.  Run training first.")

    model, encoder = joblib.load(MODEL_PATH)

    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    img  = cv2.resize(img, IMG_SIZE)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    feat = hog(
        gray,
        orientations   = HOG_ORIENTATIONS,
        pixels_per_cell= HOG_PIXELS_PER_CELL,
        cells_per_block = HOG_CELLS_PER_BLOCK,
        block_norm      = HOG_BLOCK_NORM,
    )
    pred = model.predict([feat])[0]
    return encoder.inverse_transform([pred])[0]


# ═════════════════════════════════════════════════════════════════════════════
#  CLI
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train paddy-disease classifier.")
    parser.add_argument(
        "--max-images", type=int, default=None,
        help="Limit total images sampled from the dataset (useful for quick tests).",
    )
    parser.add_argument(
        "--predict", type=str, default=None,
        help="Path to a single leaf image to classify using the saved model.",
    )
    args, _ = parser.parse_known_args()

    if args.predict:
        try:
            label = predict_single(args.predict)
            print(f"Predicted disease: {label}")
        except Exception as exc:
            print(f"Prediction failed: {exc}")
    else:
        train(max_images=args.max_images)
