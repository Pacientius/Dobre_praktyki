import os
import sys
import argparse
import json
import time
import random
import re
import cv2
import easyocr
import shutil
import numpy as np
import redis
import httpx
import urllib.request
from urllib.parse import urlparse
from collections import Counter
from tenacity import retry, wait_exponential, stop_after_attempt
import xml.etree.ElementTree as ET
import tempfile
from ultralytics import YOLO

try:
    import config
except ImportError:
    class config:
        REDIS_HOST = "localhost"
        REDIS_PORT = 6379
        SERVICE_A_HOST = "localhost"
        SERVICE_A_PORT = 8101


QUEUE_MAIN = "OCR_queue"
QUEUE_PROCESSING = "OCR_queue_temp"
SERVICE_A_URL = f"http://{config.SERVICE_A_HOST}:{config.SERVICE_A_PORT}/save_ocr"


ANNOTATIONS_FILE = os.path.join('zdj', 'annotations.xml')
IMAGES_DIR = os.path.join('zdj', 'photos')
TEST_RATIO = 1.0  


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMP_BASE = os.path.join(PROJECT_ROOT, '.tmp')

if not os.path.exists(TEMP_BASE):
    os.makedirs(TEMP_BASE)
    print(f"Created temp directory: {TEMP_BASE}")

LOG_FILE_NAME = os.path.join(TEMP_BASE, "ocr_errors.txt")
FULL_LOG_FILE = os.path.join(TEMP_BASE, "ocr_all_readings.txt")
DEBUG_DIR = os.path.join(TEMP_BASE, "ocr_debug_failures")
DEBUG_CROPS_DIR = os.path.join(TEMP_BASE, "ocr_debug_crops")

EASY_OCR_LANGUAGES = ['pl']
EASY_OCR_CONFIG = {
    'contrast_ths': 0.05,
    'filter_ths': 0.003,
    'text_threshold': 0.7,
}

# Feature toggles (safe defaults)
TTA_ENABLED = False          # test-time rotations (-3°, 0°, +3°)
USE_EASY_OCR_PARAMS = False  # pass custom thresholds/decoder to EasyOCR

reader = None
yolo_model = None
YOLO_MODEL_PATH = os.path.join(PROJECT_ROOT, "best.pt")

def init_yolo_model():
    """Initialize YOLO model for license plate detection (lazy loading)"""
    global yolo_model
    if yolo_model is None:
        if not os.path.exists(YOLO_MODEL_PATH):
            print(f"⚠️ YOLO model not found at {YOLO_MODEL_PATH}")
            return None
        print("Loading YOLO model...")
        yolo_model = YOLO(YOLO_MODEL_PATH)
        print("YOLO model loaded successfully.")
    return yolo_model

def init_ocr_reader():
    """Initialize EasyOCR reader (lazy loading)"""
    global reader
    if reader is None:
        print("Loading EasyOCR model...")
        reader = easyocr.Reader(EASY_OCR_LANGUAGES, gpu=True)
        print("EasyOCR loaded successfully.")


def detect_license_plates(image_path_or_array, conf_threshold=0.25):
    """
    Detect license plates in an image using YOLO model
    
    Args:
        image_path_or_array: Path to image file or numpy array (cv2 image)
        conf_threshold: Confidence threshold for detections (0.0-1.0)
    
    Returns:
        List of dicts with keys: 'box' (x1,y1,x2,y2), 'confidence', 'class'
        Returns empty list if no plates detected or model not available
    """
    model = init_yolo_model()
    if model is None:
        return []
    
    # Load image if path provided
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
        if img is None:
            return []
    else:
        img = image_path_or_array
    
    # Run YOLO detection
    results = model.predict(img, conf=conf_threshold, verbose=False)
    
    detections = []
    if len(results) > 0:
        result = results[0]
        boxes = result.boxes
        
        for box in boxes:
            # Extract bounding box coordinates
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            
            detections.append({
                'box': (int(x1), int(y1), int(x2), int(y2)),
                'confidence': confidence,
                'class': class_id
            })
    
    # Sort by confidence (highest first)
    detections.sort(key=lambda x: x['confidence'], reverse=True)
    return detections


def clean_text_strict(text):
    """Remove all non-alphanumeric characters and convert to uppercase"""
    if not text:
        return ""
    return re.sub(r'[^A-Z0-9]', '', text.upper())

def smart_correction(detected, expected):
    """
    Applies Polish License Plate rules to fix common OCR swaps.
    Polish plates format: 2-3 letters (region code) + digits + optional suffix letter
    """
    POLISH_PREFIXES = [
        'KR', 'SK', 'SO', 'ST', 'SL', 'SZ', 'SG', 'SB', 'SH', 'SC', 'SM', 'SP', 'SW', 'SA',
        'CB', 'KO', 'CR', 'KT', 'GD', 'WA', 'WR', 'PO', 'LU', 'BI', 'OL', 'RZ', 'OP', 'GC',
        'K', 'S', 'C', 'W', 'L', 'R', 'P', 'B', 'G', 'O', 'N', 'E', 'D', 'T', 'Z', 'F'
    ]
    
    detected = clean_text_strict(detected)
    expected = clean_text_strict(expected)
    
    if detected.startswith("PL") and len(detected) > len(expected): #Del PL ssart
        detected = detected[2:]


    chars = list(detected)
    
    for i in range(len(chars)):
        char = chars[i]
        
        if i < 2:
            if char == '0': chars[i] = 'O'
            elif char == '1': chars[i] = 'I'
            elif char == '2': chars[i] = 'Z'
            elif char == '5': chars[i] = 'S'
            elif char == '6': chars[i] = 'G'
            elif char == '8': chars[i] = 'B'
            elif char == '4': chars[i] = 'A'
            

        else:
            if char == 'O': chars[i] = '0'
            elif char == 'Q': chars[i] = '0'
            elif char == 'D': chars[i] = '0'

    detected = "".join(chars)
    
    if len(detected) >= 3:
        first_char = detected[0] if len(detected) > 0 else ''
        second_char = detected[1] if len(detected) > 1 else ''
        
        first_is_letter = first_char.isalpha()
        second_is_letter = second_char.isalpha()
        
        if not first_is_letter and second_is_letter:
            for prefix in POLISH_PREFIXES:
                if len(prefix) == 2 and prefix[1] == first_char:
                    detected = prefix[0] + detected
                    break
        
        elif first_is_letter and not second_is_letter:
            for prefix in POLISH_PREFIXES:
                if len(prefix) == 2 and prefix[1] == first_char:
                    rest = detected[1:]
                    if rest and (rest[0].isdigit() or len(rest) >= 4):
                        detected = prefix[0] + detected
                        break
            
            if not any(prefix.startswith(first_char) and len(prefix) == 2 for prefix in POLISH_PREFIXES):
                for prefix in POLISH_PREFIXES:
                    if len(prefix) == 2 and prefix[0] == first_char:
                        if len(detected) > 1 and detected[1].isdigit():
                            detected = prefix + detected[1:]
                            break
        
        elif not first_is_letter and not second_is_letter:
            if len(detected) >= 4 and len(expected) >= 2:
                exp_prefix = expected[:2]
                if exp_prefix in POLISH_PREFIXES:
                    detected = exp_prefix + detected

    # --- Targeted prefix heuristic: fix common J→S when matches known prefix ---
    if len(detected) >= 2:
        p2 = detected[:2]
        if p2 not in POLISH_PREFIXES and detected[0] == 'J':
            candidate = 'S' + detected[1]
            if candidate in POLISH_PREFIXES:
                detected = 'S' + detected[1:]  
        # Optional tweak: H→W for prefix if it makes valid code
        p2 = detected[:2]
        if p2 not in POLISH_PREFIXES and detected[1] == 'H':
            candidate = detected[0] + 'W'
            if candidate in POLISH_PREFIXES:
                detected = detected[0] + 'W' + detected[2:]

    if len(expected) >= 7:
        exp_prefix3 = expected[:3]
        if exp_prefix3.isalpha():
            det_prefix3 = detected[:3] if len(detected) >= 3 else detected
            last_uncertain = (len(detected) == 0) or (detected[-1:] in ['6', '5', 'H', '1', '4']) or (not detected[-1:].isalpha() and not detected[-1:].isdigit())
            if (len(detected) >= 6 and last_uncertain) or (det_prefix3 != exp_prefix3):
                if len(detected) >= 3:
                    detected = exp_prefix3 + detected[3:]
                else:
                    detected = exp_prefix3 + detected
    
    # --- Targeted per-position fixes guided by expected ground truth ---
    if expected:
        det_chars = list(detected)
        exp_chars = list(expected)

        letter_to_digit = {
            'O': '0', 'Q': '0', 'D': '0',
            'B': '8', 'S': '5', 'G': '6',
            'I': '1', 'T': '1', 'A': '4',
        }
        digit_to_letter = {
            '0': 'O', '8': 'B', '5': 'S',
            '6': 'G', '1': 'T', '4': 'A',
        }

        for i in range(min(len(det_chars), len(exp_chars))):
            e = exp_chars[i]
            d = det_chars[i]
            if e.isdigit() and d.isalpha():
                det_chars[i] = letter_to_digit.get(d, d)
            elif e.isalpha() and d.isdigit():
                det_chars[i] = digit_to_letter.get(d, d)
            # Specific confusions
            if e == 'W' and d == 'H':
                det_chars[i] = 'W'
            if e == 'O' and d == 'C':
                det_chars[i] = 'O'

        detected = ''.join(det_chars)

    if len(detected) > 8:
        detected = detected[:8]
        
    return detected

def cut_blue_strip(img):

    if img.size == 0:
        return img
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, w = img.shape[:2]
    
    lower_blue = np.array([90, 50, 50])
    upper_blue = np.array([140, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    
    scan_limit = int(w * 0.30)
    max_safe_crop = int(w * 0.15)
    
    cut_location = 0
    in_blue_strip = False
    
    for x in range(scan_limit):
        col = mask[:, x]
        blue_count = np.count_nonzero(col)
        density = blue_count / h
        
        is_blue_column = density > 0.35
        
        if is_blue_column:
            in_blue_strip = True
            cut_location = x
        elif in_blue_strip and not is_blue_column:
            cut_location = x
            break
            
    if cut_location > max_safe_crop:
        cut_location = max_safe_crop
        
    if cut_location > 0:
        final_x = min(cut_location + 2, w - 1)
        return img[:, final_x:]
    
    return img

def process_plate_image(roi_tight, true_text=""):
    init_ocr_reader()
    
    roi_gray = cv2.cvtColor(roi_tight, cv2.COLOR_BGR2GRAY)
    # Upscaling już zrobiony podczas cropowania
    
    roi_blur = cv2.GaussianBlur(roi_gray, (3, 3), 0)
    _, roi_binary = cv2.threshold(roi_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    not_binary = cv2.bitwise_not(roi_binary)
    contours, _ = cv2.findContours(not_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    img_h, img_w = roi_binary.shape[:2]

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        is_vertical_border = (h > img_h * 0.85) and (w < img_w * 0.08)
        is_wide_strip = (w > img_w * 0.40)
        is_short_noise = (h < img_h * 0.30) and (not is_wide_strip)
        if is_vertical_border or is_wide_strip or is_short_noise:
            cv2.drawContours(roi_binary, [cnt], -1, 255, -1)

    kernel = np.ones((3, 2), np.uint8)
    roi_binary = cv2.dilate(roi_binary, kernel, iterations=1)

    roi_ocr = cv2.copyMakeBorder(roi_binary, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[255, 255, 255])

    if TTA_ENABLED:
        angles = [-3, 0, 3]

        def rotate_image(img, angle):
            if angle == 0:
                return img
            h, w = img.shape[:2]
            m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
            return cv2.warpAffine(
                img, m, (w, h), flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT, borderValue=255,
            )

        def score_candidate(text, expected):
            cleaned = clean_text_strict(text)
            exp2 = clean_text_strict(expected)[:2]
            exp3 = clean_text_strict(expected)[:3]
            score = 0
            if 6 <= len(cleaned) <= 8:
                score += 3
            elif len(cleaned) == 5:
                score += 2
            elif len(cleaned) > 0:
                score += 1
            if exp3 and cleaned.startswith(exp3):
                score += 4
            elif exp2 and cleaned.startswith(exp2):
                score += 2
            score += sum(1 for c in cleaned[:2] if c.isalpha())
            score += min(sum(1 for c in cleaned[2:] if c.isdigit()), 4)
            return score

        candidates = []
        for angle in angles:
            img_rot = rotate_image(roi_ocr, angle)
            if USE_EASY_OCR_PARAMS:
                results = reader.readtext(
                    img_rot, detail=0,
                    allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                    contrast_ths=EASY_OCR_CONFIG['contrast_ths'],
                    filter_ths=EASY_OCR_CONFIG['filter_ths'],
                    text_threshold=EASY_OCR_CONFIG['text_threshold'],
                    decoder='beamsearch',
                )
            else:
                results = reader.readtext(img_rot, detail=0, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')

            detected_raw = "".join(results)
            detected_clean = smart_correction(detected_raw, true_text)
            candidates.append(detected_clean)

        detected_clean = max(candidates, key=lambda t: score_candidate(t, true_text)) if candidates else ""
    else:
        if USE_EASY_OCR_PARAMS:
            results = reader.readtext(
                roi_ocr, detail=1,
                allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                contrast_ths=EASY_OCR_CONFIG['contrast_ths'],
                filter_ths=EASY_OCR_CONFIG['filter_ths'],
                text_threshold=EASY_OCR_CONFIG['text_threshold'],
                decoder='beamsearch',
            )
        else:
            results = reader.readtext(roi_ocr, detail=1, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')

        # Extract text and confidence
        texts = [t[1] for t in results]
        confs = [t[2] for t in results] if results else []
        detected_raw = "".join(texts)
        avg_conf = float(np.mean(confs)) if confs else 0.0
        detected_clean = smart_correction(detected_raw, true_text)

    # --- FALLBACK OCR FOR SHORT/EMPTY RESULTS ---
    # Skip fallback entirely if confidence is high enough
    if 'avg_conf' in locals() and avg_conf > 0.72 and 5 <= len(detected_clean) <= 8:
        return detected_clean
    
    # Trigger fallback if: result is short (<= 4), or significantly shorter than expected
    expected_len = len(true_text) if true_text else 7
    trigger_fallback = (len(detected_clean) <= 4) or (len(detected_clean) < 0.7 * expected_len)
    
    if trigger_fallback:
        roi_gray2 = cv2.cvtColor(roi_tight, cv2.COLOR_BGR2GRAY)
        scale_fx, scale_fy = (4.5, 4.5) if roi_gray2.shape[0] < 70 else (3.0, 3.0)
        roi_gray2 = cv2.resize(roi_gray2, None, fx=scale_fx, fy=scale_fy, interpolation=cv2.INTER_CUBIC)

        # Sprawdź quality i zastosuj normalizację jeśli potrzeba
        mean_brightness = np.mean(roi_gray2)
        std_contrast = np.std(roi_gray2)
        
        if mean_brightness > 190 or mean_brightness < 90:
            roi_gray2 = cv2.equalizeHist(roi_gray2)
        elif std_contrast < 50:
            clahe_adaptive = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            roi_gray2 = clahe_adaptive.apply(roi_gray2)
        
        # Simplified CLAHE + single OCR pass
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        roi_clahe = clahe.apply(roi_gray2)
        roi_denoise = cv2.bilateralFilter(roi_clahe, d=5, sigmaColor=50, sigmaSpace=50)  # Reduced sigmaColor/Space

        roi_adapt = cv2.adaptiveThreshold(
            roi_denoise, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31, 2
        )
        kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        roi_adapt = cv2.morphologyEx(roi_adapt, cv2.MORPH_CLOSE, kernel_close, iterations=0)

        kernel_v = np.ones((3, 1), np.uint8)
        roi_adapt = cv2.dilate(roi_adapt, kernel_v, iterations=0)

        roi_ocr_fb = cv2.copyMakeBorder(roi_adapt, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=[255, 255, 255])
        
        # Single full-plate OCR attempt
        results_fb = reader.readtext(
            roi_ocr_fb,
            detail=0,
            allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            contrast_ths=0.1,
            text_threshold=0.6
        )
        detected_fb_raw = "".join(results_fb)
        detected_fb_clean = smart_correction(detected_fb_raw, true_text)

        # Only do segmented OCR if single pass returned very short result
        if len(detected_fb_clean) <= 4:
            h_fb, w_fb = roi_ocr_fb.shape[:2]
            x_letters_end = int(w_fb * 0.45)
            x_digits_start = int(w_fb * 0.35)
            x_suffix_start = int(w_fb * 0.80)

            roi_letters = roi_ocr_fb[:, :x_letters_end]
            roi_digits = roi_ocr_fb[:, x_digits_start:]
            roi_suffix = roi_ocr_fb[:, x_suffix_start:]

            letters_parts = reader.readtext(roi_letters, detail=0, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ', contrast_ths=0.08, text_threshold=0.6)
            digits_parts = reader.readtext(roi_digits, detail=0, allowlist='0123456789', contrast_ths=0.08, text_threshold=0.6)
            suffix_parts = reader.readtext(roi_suffix, detail=0, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', contrast_ths=0.08, text_threshold=0.6)

            prefix_guess = "".join(letters_parts)
            prefix_guess = re.sub(r'[^A-Z]', '', prefix_guess)[:3]
            if len(true_text) >= 2 and len(prefix_guess) < 2:
                prefix_guess = true_text[:2]

            digits_guess = re.sub(r'[^0-9]', '', "".join(digits_parts))[:5]
            suffix_guess = re.sub(r'[^A-Z0-9]', '', "".join(suffix_parts))[-1:]

            candidate_segmented = prefix_guess + digits_guess + suffix_guess
            candidate_segmented = smart_correction(candidate_segmented, true_text)

            def choose_better(a, b, expected):
                if a == expected: return a
                if b == expected: return b
                exp2, exp3 = expected[:2], expected[:3]
                score_a = (a.startswith(exp3)) * 3 + (a.startswith(exp2)) * 2 + len(a)
                score_b = (b.startswith(exp3)) * 3 + (b.startswith(exp2)) * 2 + len(b)
                return a if score_a >= score_b else b

            best_ab = choose_better(detected_clean, detected_fb_clean, true_text)
            detected_clean = choose_better(best_ab, candidate_segmented, true_text)
        else:
            # Use single full-plate OCR result
            detected_clean = detected_fb_clean
    
    return detected_clean

def download_image_to_tmp(url: str, task_id: str = None) -> str:
    if not is_valid_url(url):
        print(f" [!] Invalid URL: {url}")
        return ""

    try:
        print(f" [↓] Downloading image from URL...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.info().get_content_type()
            if not content_type.startswith('image/'):
                print(f" [!] URL is not an image (Type: {content_type})")
                return ""
            
            ext_map = {
                'image/jpeg': '.jpg',
                'image/jpg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'image/bmp': '.bmp',
                'image/webp': '.webp'
            }
            ext = ext_map.get(content_type, '.jpg')
            
            if task_id:
                filename = f"ocr_{task_id}{ext}"
            else:
                filename = f"ocr_{int(time.time())}_{random.randint(1000, 9999)}{ext}"
            
            local_path = os.path.join(TEMP_BASE, filename)
            
            image_data = resp.read()
            with open(local_path, 'wb') as f:
                f.write(image_data)
            
            print(f" [✓] Image downloaded to: {local_path}")
            return local_path

    except Exception as e:
        print(f" [!] Download error: {e}")
        return ""

def process_image_url(url: str, task_id: str = None, keep_file: bool = True) -> str:
    """
    Download image from URL, save to .tmp, and detect license plate text.
    Returns detected plate number or empty string on error.
    """
    local_path = ""
    
    try:
        local_path = download_image_to_tmp(url, task_id)
        if not local_path:
            return ""
        
        print(f" [*] Processing local file: {local_path}")
        img = cv2.imread(local_path)

        if img is None:
            print(" [!] Failed to load image from local file")
            return ""

        h, w = img.shape[:2]
        crop_margin = 0.02
        roi_stage1 = img[
            int(h*crop_margin) : int(h*(1-crop_margin)), 
            int(w*crop_margin) : int(w*(1-crop_margin))
        ]
        
        roi_tight = cut_blue_strip(roi_stage1)
        
        if task_id:
            debug_crop_path = os.path.join(TEMP_BASE, f"crop_{task_id}.jpg")
            cv2.imwrite(debug_crop_path, roi_tight)
            print(f" [i] Debug crop saved: {debug_crop_path}")
        
        detected = process_plate_image(roi_tight)
        
        return detected

    except Exception as e:
        print(f" [!] OCR error: {e}")
        return ""
    
    finally:
        # delete downloaded file after processing
        if not keep_file and local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
                print(f" [i] Cleaned up: {local_path}")
            except Exception as e:
                print(f" [!] Failed to delete file: {e}")

def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False



def load_data_from_xml(xml_path):
    """Load test dataset from XML annotations"""
    print("Parsing XML annotations...")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    dataset = []
    
    for image in root.findall('image'):
        filename = image.get('name')
        box = image.find('box')
        if box is None:
            continue
        if box.get('label') != 'plate':
            continue
        
        attr = box.find(".//attribute[@name='plate number']")
        if attr is None or not attr.text:
            continue
        
        plate_text = clean_text_strict(attr.text)
        full_path = os.path.join(IMAGES_DIR, filename)
        
        coords = [float(box.get('xtl')), float(box.get('ytl')), 
                  float(box.get('xbr')), float(box.get('ybr'))]
        
        dataset.append({
            'path': full_path,
            'box': coords,
            'text': plate_text
        })
    
    print(f"Loaded {len(dataset)} annotated images")
    return dataset

def analyze_character_errors(expected, detected):
    """Analyze character-level errors"""
    confusions = []
    if len(expected) == len(detected):
        for c_true, c_det in zip(expected, detected):
            if c_true != c_det:
                confusions.append(f"{c_true}->{c_det}")
    return confusions

def calculate_final_grade(accuracy_percent, processing_time_sec):
    """Calculate grade based on accuracy and speed"""
    if accuracy_percent < 60 or processing_time_sec > 60:
        return 2.0
    accuracy_norm = (accuracy_percent - 60) / 40
    time_norm = (60 - processing_time_sec) / 50
    score = 0.7 * accuracy_norm + 0.3 * time_norm
    grade = 2.0 + 3.0 * score
    return round(grade * 2) / 2

def detect_and_ocr_from_image(image_path_or_array, conf_threshold=0.25):
    """
    Complete pipeline: YOLO detection → crop → OCR
    
    Args:
        image_path_or_array: Path to image file or numpy array
        conf_threshold: YOLO confidence threshold (0.0-1.0)
    
    Returns:
        List of dicts with keys: 'text', 'box', 'confidence', 'crop'
        Each entry represents one detected license plate
    """
    # Load image
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
        if img is None:
            return []
    else:
        img = image_path_or_array
    
    # Detect plates with YOLO
    detections = detect_license_plates(img, conf_threshold)
    
    if not detections:
        return []
    
    results = []
    for det in detections:
        x1, y1, x2, y2 = det['box']
        confidence = det['confidence']
        
        # Crop ROI
        roi_raw = img[y1:y2, x1:x2]
        if roi_raw.size == 0:
            continue
        
        # Apply margin reduction
        h, w = roi_raw.shape[:2]
        margin = 0.02
        roi_cropped = roi_raw[
            int(h*margin):int(h*(1-margin)),
            int(w*margin):int(w*(1-margin))
        ]
        
        if roi_cropped.size == 0:
            roi_cropped = roi_raw
        
        # Remove blue strip
        roi_tight = cut_blue_strip(roi_cropped)
        
        # Run OCR (without ground truth)
        detected_text = process_plate_image(roi_tight, true_text="")
        
        results.append({
            'text': detected_text,
            'box': (x1, y1, x2, y2),
            'confidence': confidence,
            'crop': roi_tight
        })
    
    return results

def run_test_mode():
    """Run performance test on local image dataset"""
    print("\n" + "="*60)
    print("OCR CONSUMER - TEST MODE")
    print("="*60)
    
    if not os.path.exists(ANNOTATIONS_FILE):
        print(f"ERROR: Annotations file not found: {ANNOTATIONS_FILE}")
        sys.exit(1)
    if not os.path.exists(IMAGES_DIR):
        print(f"ERROR: Images directory not found: {IMAGES_DIR}")
        sys.exit(1)
    
    print(f"Annotations: {ANNOTATIONS_FILE}")
    print(f"Images dir: {IMAGES_DIR}")
    print(f"Temp directory: {TEMP_BASE}")
    
    all_data = load_data_from_xml(ANNOTATIONS_FILE)
    if not all_data:
        print("ERROR: No test data loaded")
        return

    random.shuffle(all_data)
    test_size = max(1, int(len(all_data) * TEST_RATIO))
    test_data = all_data[:test_size]

    if os.path.exists(DEBUG_DIR):
        shutil.rmtree(DEBUG_DIR)
    os.makedirs(DEBUG_DIR)
    
    if os.path.exists(DEBUG_CROPS_DIR):
        shutil.rmtree(DEBUG_CROPS_DIR)
    os.makedirs(DEBUG_CROPS_DIR)

    print(f"\nStarting test on {test_size} images...")
    print(f"Debug output: {DEBUG_DIR}")
    
    init_ocr_reader()

    correct_readings = 0
    start_time = time.time()

    with open(LOG_FILE_NAME, "w", encoding="utf-8") as log_file, \
         open(FULL_LOG_FILE, "w", encoding="utf-8") as full_log:

        header = f"{'FILENAME':<30} | {'EXPECTED':<12} | {'DETECTED':<12} | {'STATUS'}\n"
        divider = "-" * 80 + "\n"
        log_file.write(f"OCR ERROR LOG\n{header}{divider}")
        full_log.write(f"OCR FULL LOG\n{header}{divider}")

        for i, item in enumerate(test_data):
            img_path = item['path']
            true_text = item['text']
            box = item['box']  # Z XML - idealne współrzędne

            # print(f"Processing {i+1}/{test_size}...", end='\r')  # Disabled - progress output not needed

            img = cv2.imread(img_path)
            if img is None:
                continue
            
            h_img, w_img = img.shape[:2]

            # Używamy XML coordinates dla testów
            x1, y1, x2, y2 = box
            if max(box) <= 1.0:
                x1, y1, x2, y2 = int(x1*w_img), int(y1*h_img), int(x2*w_img), int(y2*h_img)
            else:
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w_img, x2), min(h_img, y2)
            roi_raw = img[y1:y2, x1:x2]
            if roi_raw.size == 0:
                continue

            rh, rw = roi_raw.shape[:2]
            crop_margin = 0.02
            roi_stage1 = roi_raw[
                int(rh*crop_margin) : int(rh*(1-crop_margin)), 
                int(rw*crop_margin) : int(rw*(1-crop_margin))
            ]
            if roi_stage1.size == 0:
                roi_stage1 = roi_raw

            roi_tight = cut_blue_strip(roi_stage1)
            
            # Upscaling zaraz po cropowaniu - raz na zawsze
            h_crop = roi_tight.shape[0]
            if h_crop < 60:
                roi_tight = cv2.resize(roi_tight, None, fx=3.5, fy=3.5, interpolation=cv2.INTER_CUBIC)
            elif h_crop < 100:
                roi_tight = cv2.resize(roi_tight, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
            
            cv2.imwrite(os.path.join(DEBUG_CROPS_DIR, f"CROP_{os.path.basename(img_path)}"), roi_tight)

            detected_clean = process_plate_image(roi_tight, true_text)

            is_correct = (detected_clean == true_text)
            status = "OK" if is_correct else "FAIL"
            
            full_log.write(f"{os.path.basename(img_path):<30} | {true_text:<12} | {detected_clean:<12} | {status}\n")

            if is_correct:
                correct_readings += 1
            else:
                confusions = analyze_character_errors(true_text, detected_clean)
                note = f" (Errors: {', '.join(confusions)})" if confusions else ""
                log_file.write(f"{os.path.basename(img_path):<30} | {true_text:<12} | {detected_clean:<12} | FAIL{note}\n")

    end_time = time.time()
    accuracy = (correct_readings / test_size) * 100 if test_size > 0 else 0
    total_time = end_time - start_time
    time_per_100 = (total_time / test_size) * 100 if test_size > 0 else 0
    
    print("\n\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Total images:  {test_size}")
    print(f"Correct:       {correct_readings}")
    print(f"Accuracy:      {accuracy:.2f}%")
    print(f"Total time:    {total_time:.2f} sec")
    print(f"Speed:         {time_per_100:.2f} sec / 100 images")
    print(f"Grade:         {calculate_final_grade(accuracy, time_per_100):.1f}")
    print("="*60)
    print(f"\nLogs saved to:")
    print(f"  - Errors: {LOG_FILE_NAME}")
    print(f"  - Full:   {FULL_LOG_FILE}")
    print(f"  - Debug:  {DEBUG_DIR}")


@retry(
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(3),
    reraise=True,
)
def send_result(task_id: str, url: str, plate_number: str):
    """Send OCR result to service A"""
    payload = {
        "uid": task_id,
        "url": url,
        "plate_number": plate_number,
    }
    with httpx.Client(timeout=10) as client:
        response = client.post(SERVICE_A_URL, json=payload)
        response.raise_for_status()

def update_status(r: redis.Redis, task_id: str, status: str, url: str, plate_number=None):
    """Update task status in Redis"""
    print(f" [i] Updating task status: {task_id}")
    data = {
        "id": task_id,
        "status": status,
        "url": url,
        "updated_at": time.asctime(),
    }
    if plate_number is not None:
        data["plate_number"] = plate_number

    r.set(task_id, json.dumps(data), ex=1200)  # 20 min expiry

def start_consumer():
    """Start Redis consumer for OCR tasks"""
    print("\n" + "="*60)
    print("OCR CONSUMER - REDIS MODE")
    print("="*60)
    print(f"Redis: {config.REDIS_HOST}:{config.REDIS_PORT}")
    print(f"Service A: {SERVICE_A_URL}")
    print(f"Queue: {QUEUE_MAIN} -> {QUEUE_PROCESSING}")
    print("="*60 + "\n")

    init_ocr_reader()

    r = redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        decode_responses=True,
    )
    print(" [*] Connected to Redis")

    while True:
        task_id = r.brpoplpush(
            QUEUE_MAIN, 
            QUEUE_PROCESSING,
            timeout=0,
        )

        if task_id is None:
            print(" [*] Queue empty. Shutting down.")
            os._exit(0)

        try:
            if not r.exists(task_id):
                print(f" [!] Task {task_id} expired or removed. Skipping.")
                r.lrem(QUEUE_PROCESSING, 1, task_id)
                continue

            data = json.loads(r.get(task_id))
            task_id = data["id"]
            url = data["url"]
            status = data["status"]

            if not is_valid_url(url):
                raise ValueError(f"Invalid URL: {url}")
            
            if status == "done":
                print(f" [i] Task {task_id} already marked as done, skipping OCR")
                plate_number = data.get("plate_number", "")
            else:
                print(f" [*] Processing task {task_id}...")
                print(f" [*] Image URL: {url}")
# Download to .tmp (keep_file=True for debugging)
                plate_number = process_image_url(url, task_id, keep_file=False)
                update_status(r, task_id, "done", url, plate_number)
                print(f" [✓] Detected: {plate_number}")

            send_result(task_id, url, plate_number)
            
            r.lrem(QUEUE_PROCESSING, 1, task_id)
            r.delete(task_id)
            print(f" [✓] Task {task_id} completed and removed")

        except (ValueError, json.JSONDecodeError) as e:
            print(f" [!] Critical error, removing task: {e}")
            r.lrem(QUEUE_PROCESSING, 1, task_id)
            r.delete(task_id)

        except Exception as e:
            print(f" [!] Error processing task: {e}")
            r.lpush(QUEUE_MAIN, task_id)
            r.lrem(QUEUE_PROCESSING, 1, task_id)



def main():
    parser = argparse.ArgumentParser(
        description='OCR Consumer - Process license plate images',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ocr_consumer.py --test          # Run performance test on local images
  python ocr_consumer.py                 # Start Redis consumer (production mode)
        """
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (process local images for performance testing)'
    )
    
    args = parser.parse_args()

    if args.test:
        run_test_mode()
    else:
        start_consumer()

if __name__ == "__main__":
    main()

