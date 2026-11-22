import nest_asyncio, os, asyncio, shutil, time, urllib.request
nest_asyncio.apply()

Bot_Token = os.getenv('TOKEN')

from pyrogram import Client, filters, idle
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton
import cv2, numpy as np
import torch
from PIL import Image
from ultralytics import YOLO
from transformers import AutoImageProcessor, AutoModelForImageClassification

# تحميل نموذج الـ Segmentation الأساسي
model = YOLO('yolov8m-seg.pt')

# كاشف وجه خفيف وسريع (YuNet) مع تحميل تلقائي من مستودع OpenCV الرسمي عند الحاجة
YUNET_PATH = os.getenv('YUNET_PATH', 'face_detection_yunet_2023mar.onnx')
YUNET_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_detection_yunet/face_detection_yunet_2023mar.onnx"
)
yunet_detector = None

def _ensure_yunet_file(path: str) -> bool:
    if os.path.exists(path) and os.path.getsize(path) > 100_000:
        return True
    try:
        print(f"⬇️ Downloading YuNet weights from OpenCV GitHub to '{path}'...")
        urllib.request.urlretrieve(YUNET_URL, path)
        if os.path.exists(path) and os.path.getsize(path) > 100_000:
            print(f"✅ YuNet downloaded successfully ({os.path.getsize(path)} bytes).")
            return True
        print(f"⚠️ YuNet download finished but file size is unexpectedly small: '{path}'.")
        return False
    except Exception as e:
        print(f"❌ YuNet download failed (reason: {e}).")
        return False

def _init_yunet():
    global yunet_detector
    if not hasattr(cv2, "FaceDetectorYN"):
        print("⚠️ OpenCV FaceDetectorYN is unavailable in this cv2 build.")
        return
    if not _ensure_yunet_file(YUNET_PATH):
        print(f"⚠️ YuNet detector skipped because weights are unavailable at '{YUNET_PATH}'.")
        return
    try:
        yunet_detector = cv2.FaceDetectorYN.create(
            YUNET_PATH, "", (320, 320), score_threshold=0.30, nms_threshold=0.3, top_k=15
        )
        print("✅ YuNet face detector loaded!")
    except Exception as e:
        yunet_detector = None
        print(f"⚠️ YuNet init warning: {e}")

_init_yunet()

# النموذج الأول: متخصص في الوجه (يُفحص أولاً عند وضوح الوجه أو الرأس)
FACE_MODEL_ID = os.getenv('FACE_MODEL_ID', 'dima806/fairface_gender_image_detection')
# النموذج الثاني: متخصص في الجسد (يُفحص عند عدم وضوح الوجه أو ضعف ثقة الوجه أو عدم المطابقة)
BODY_MODEL_ID = os.getenv('BODY_MODEL_ID', 'NTQAI/pedestrian_gender_recognition')

# عتبات ثقة متوسطة: حتى 4 عينات كل 0.5 ثانية؛ تكفي عينة واحدة مطابقة لاعتماد البلور
FACE_MIN_CONFIDENCE = float(os.getenv('FACE_MIN_CONFIDENCE', '0.52'))
BODY_MIN_CONFIDENCE = float(os.getenv('BODY_MIN_CONFIDENCE', '0.55'))
SAMPLE_INTERVAL_SEC = float(os.getenv('SAMPLE_INTERVAL_SEC', '0.5'))
MAX_SAMPLES_PER_TRACK = int(os.getenv('MAX_SAMPLES_PER_TRACK', '4'))

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

face_processor = None
face_model = None
face_init_error = None

body_processor = None
body_model = None
body_init_error = None

def _init_dual_models():
    global face_processor, face_model, face_init_error
    global body_processor, body_model, body_init_error

    try:
        face_processor = AutoImageProcessor.from_pretrained(FACE_MODEL_ID)
        fm = AutoModelForImageClassification.from_pretrained(FACE_MODEL_ID)
        fm.to(device)
        fm.eval()
        face_model = fm
        print(f"✅ Face model loaded on {device}: {FACE_MODEL_ID}")
    except Exception as e:
        face_init_error = str(e)
        print(f"⚠️ Face model init error: {face_init_error}")

    try:
        body_processor = AutoImageProcessor.from_pretrained(BODY_MODEL_ID)
        bm = AutoModelForImageClassification.from_pretrained(BODY_MODEL_ID)
        bm.to(device)
        bm.eval()
        body_model = bm
        print(f"✅ Body model loaded on {device}: {BODY_MODEL_ID}")
    except Exception as e:
        body_init_error = str(e)
        print(f"⚠️ Body model init error: {body_init_error}")

_init_dual_models()

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'
Audio_Forms = (".mp3", ".ogg", ".m4a", ".aac", ".flac", ".wav", ".wma", ".opus", ".3gpp")

Settings_Dict = {}
Base_Dl_Dir = './ProSeg_Work'

def odd_blur_size(val: int) -> int:
    val = max(3, int(val))
    return val if val % 2 == 1 else val + 1

def fmt_clock(seconds: float) -> str:
    sec = max(0, int(seconds))
    hrs = sec // 3600
    mins = (sec % 3600) // 60
    secs = sec % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"

def format_elapsed_min_sec(elapsed_sec: float) -> str:
    total_sec = max(0.0, float(elapsed_sec))
    mins = int(total_sec // 60)
    rem_sec = total_sec - (mins * 60)
    if mins > 0:
        return f"{mins} دقيقة و {rem_sec:.2f} ثانية ({total_sec:.2f} ثانية)"
    return f"0 دقيقة و {rem_sec:.2f} ثانية ({total_sec:.2f} ثانية)"

async def run_cmd(cmd: str):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {stderr.decode(errors='ignore')[-400:]}")

async def Create_Dir(Dir):
    os.makedirs(Dir, exist_ok=True)

async def Check_Dir(Dir):
    if Dir and os.path.exists(Dir):
        if os.path.isdir(Dir):
            shutil.rmtree(Dir, ignore_errors=True)
        else:
            try:
                os.remove(Dir)
            except OSError:
                pass

def Cleanup_Work_Dir(work_dir: str = Base_Dl_Dir):
    """حذف مجلد العمل بالكامل لضمان عدم بقاء أي ملفات مؤقتة."""
    if work_dir and os.path.exists(work_dir):
        if os.path.isdir(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)
        else:
            try:
                os.remove(work_dir)
            except OSError:
                pass

async def Mp3_Conv(File):
    base_no_ext, _ = os.path.splitext(File)
    Mp3_File = f"{base_no_ext}_Conv.mp3"
    await run_cmd(f'ffmpeg -y -i "{File}" -vn -q:a 2 "{Mp3_File}"')
    return Mp3_File

async def Media_Compress(file_path, Rate=None):
    base_no_ext, _ = os.path.splitext(file_path)
    if file_path.lower().endswith(Audio_Forms):
        bitrate = Rate or "192k"
        Res_File = f"{base_no_ext}_Comp.mp3"
        Cmd = f'ffmpeg -y -i "{file_path}" -b:a "{bitrate}" "{Res_File}"'
    else:
        Res_File = f"{base_no_ext}_Comp.mp4"
        Cmd = f'ffmpeg -y -i "{file_path}" -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k "{Res_File}"'
    await run_cmd(Cmd)
    return Res_File

async def Vid_Mk(Vid, Aud):
    base_no_ext, _ = os.path.splitext(Vid)
    Vid_Res = f"{base_no_ext}_Merged.mp4"
    if Aud and os.path.exists(Aud) and os.path.getsize(Aud) > 0:
        Cmd = (
            f'ffmpeg -y -i "{Vid}" -i "{Aud}" '
            f'-c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p '
            f'-c:a aac -b:a 128k -map 0:v:0 -map 1:a:0 -shortest "{Vid_Res}"'
        )
    else:
        Cmd = (
            f'ffmpeg -y -i "{Vid}" '
            f'-c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p "{Vid_Res}"'
        )
    await run_cmd(Cmd)
    return Vid_Res

def Pyrogram_Client(Bot_Token):
    Bot_Identifier = Bot_Token.split(':')[0]
    return Client(
        Bot_Identifier + '_session_seg_bot',
        api_id=Api_Id,
        api_hash=Api_Hash,
        bot_token=Bot_Token
    ), Bot_Identifier

async def get_seconds(clock_time):
    parts = clock_time.strip().split(':')
    if len(parts) == 3:
        hours, minutes, seconds = map(float, parts)
    elif len(parts) == 2:
        hours = 0.0
        minutes, seconds = map(float, parts)
    else:
        hours = 0.0
        minutes = 0.0
        seconds = float(parts[0])
    return (hours * 3600.0) + (minutes * 60.0) + seconds

def refine_person_mask(combined_mask: np.ndarray) -> np.ndarray:
    """توسيع وتنعيم القناع لتقليل الفلتات على الحواف والحركة السريعة."""
    binary = (combined_mask > 0.15).astype(np.uint8) * 255
    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, close_kernel)
    dilated = cv2.dilate(closed, dilate_kernel, iterations=1)
    soft = cv2.GaussianBlur(dilated, (15, 15), 0).astype(np.float32) / 255.0
    return np.clip(soft, 0.0, 1.0)

def extract_body_and_face(frame: np.ndarray, mask_2d: np.ndarray, pad: int = 10):
    """
    إرجاع قصاصة الجسم الكامل وقصاصة الوجه إذا تم اكتشافه عبر YuNet،
    مع توفير قصاصة رأس احتياطية عند تعذر اكتشاف الوجه عبر YuNet.
    """
    h, w = mask_2d.shape
    ys, xs = np.where(mask_2d > 0.15)
    if len(xs) == 0 or len(ys) == 0:
        return None

    x1 = max(0, int(xs.min()) - pad)
    y1 = max(0, int(ys.min()) - pad)
    x2 = min(w, int(xs.max()) + pad)
    y2 = min(h, int(ys.max()) + pad)
    pw, ph = x2 - x1, y2 - y1
    if pw < 16 or ph < 16:
        return None

    body_crop = frame[y1:y2, x1:x2]
    face_crop = None
    face_detected = False
    yunet_score = 0.0

    if yunet_detector is not None:
        try:
            yunet_detector.setInputSize((pw, ph))
            _, faces = yunet_detector.detect(body_crop)
            if faces is not None and len(faces) > 0:
                best = max(faces, key=lambda f: f[2] * f[3] * max(0.01, float(f[14])))
                det_score = float(best[14])
                yunet_score = det_score
                fx, fy, fw, fh = int(best[0]), int(best[1]), int(best[2]), int(best[3])
                if fw >= 14 and fh >= 14 and det_score >= 0.30:
                    pad_x = max(4, int(0.30 * fw))
                    pad_top = max(5, int(0.35 * fh))
                    pad_bot = max(4, int(0.20 * fh))
                    gx1 = max(0, fx - pad_x)
                    gy1 = max(0, fy - pad_top)
                    gx2 = min(pw, fx + fw + pad_x)
                    gy2 = min(ph, fy + fh + pad_bot)
                    if gx2 - gx1 >= 14 and gy2 - gy1 >= 14:
                        face_crop = body_crop[gy1:gy2, gx1:gx2]
                        face_detected = True
        except Exception:
            face_crop = None
            face_detected = False

    fallback_head_crop = None
    head_h = max(16, int(ph * 0.32))
    head_w = max(16, int(pw * 0.62))
    cx = pw // 2
    gx1 = max(0, cx - head_w // 2)
    gx2 = min(pw, cx + head_w // 2)
    gy2 = min(ph, head_h)
    if gx2 - gx1 >= 16 and gy2 >= 16:
        fallback_head_crop = body_crop[0:gy2, gx1:gx2]

    return {
        "body": body_crop,
        "face": face_crop,
        "fallback_head": fallback_head_crop,
        "face_detected": face_detected,
        "yunet_score": yunet_score
    }

def _label_to_gender(raw_label: str, idx: int) -> str:
    low = str(raw_label).strip().lower()
    if "female" in low or low in ("f", "woman", "women", "girl", "1"):
        return "female"
    if "male" in low or low in ("m", "man", "men", "boy", "0"):
        return "male"
    return "female" if idx == 1 else "male"

def _predict_single_model(crops: list, mdl, proc, tag: str):
    if mdl is None or proc is None:
        return [("unknown", 0.0)] * len(crops)

    valid_indices = []
    pil_images = []
    for i, c in enumerate(crops):
        if c is not None and getattr(c, "size", 0) > 0:
            valid_indices.append(i)
            pil_images.append(Image.fromarray(cv2.cvtColor(c, cv2.COLOR_BGR2RGB)))

    results_out = [("unknown", 0.0)] * len(crops)
    if not pil_images:
        return results_out

    try:
        inputs = proc(images=pil_images, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.inference_mode():
            outputs = mdl(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()
    except Exception as e:
        print(f"⚠️ {tag} inference error: {e}")
        return results_out

    id2label = getattr(mdl.config, "id2label", {}) or {}
    female_cols = [i for i in range(probs.shape[1]) if _label_to_gender(id2label.get(i, str(i)), i) == "female"]
    male_cols = [i for i in range(probs.shape[1]) if _label_to_gender(id2label.get(i, str(i)), i) == "male"]

    for row_idx, orig_idx in enumerate(valid_indices):
        row = probs[row_idx]
        f_score = float(row[female_cols].sum()) if female_cols else 0.0
        m_score = float(row[male_cols].sum()) if male_cols else 0.0
        total = f_score + m_score
        if total <= 1e-6:
            results_out[orig_idx] = ("unknown", 0.0)
            continue

        f_norm = f_score / total
        m_norm = m_score / total
        if f_norm >= m_norm:
            results_out[orig_idx] = ("female", f_norm)
        else:
            results_out[orig_idx] = ("male", m_norm)

    return results_out

def classify_sequential_with_debug(samples: list, target_gender: str):
    """
    فحص متسلسل بعتبات متوسطة مع أولوية مطلقة للجندر المستهدف (وخصوصاً female):
    إذا أعطى نموذج الوجه أو نموذج الجسد الجندر المستهدف بنسبة معقولة (> 0.50)، يُقدَّم ويُعتمد فوراً.
    """
    if not samples:
        return [], []

    final_preds = ["unknown"] * len(samples)
    debug_info = [
        {
            "src": "none",
            "face_det": bool(s.get("face_detected")),
            "yn": round(float(s.get("yunet_score", 0.0)), 2),
            "f": None,
            "b": None,
        }
        for s in samples
    ]

    face_check_indices = []
    face_check_crops = []
    direct_body_indices = []
    direct_body_crops = []

    for i, s in enumerate(samples):
        if face_model is not None:
            if s.get("face_detected") and s.get("face") is not None:
                face_check_indices.append(i)
                face_check_crops.append(s["face"])
                debug_info[i]["src"] = "face"
            elif s.get("fallback_head") is not None:
                face_check_indices.append(i)
                face_check_crops.append(s["fallback_head"])
                debug_info[i]["src"] = "head"
            elif s.get("body") is not None and getattr(s.get("body"), "size", 0) > 0 and body_model is not None:
                direct_body_indices.append(i)
                direct_body_crops.append(s["body"])
                debug_info[i]["src"] = "body"
        elif body_model is not None:
            b_crop = s.get("body")
            if b_crop is not None and getattr(b_crop, "size", 0) > 0:
                direct_body_indices.append(i)
                direct_body_crops.append(b_crop)
                debug_info[i]["src"] = "body"

    face_preds_map = {}
    need_body_from_face_indices = []
    need_body_from_face_crops = []

    if face_check_crops:
        face_results = _predict_single_model(face_check_crops, face_model, face_processor, "FaceModel")
        for idx, (f_lbl, f_conf) in zip(face_check_indices, face_results):
            face_preds_map[idx] = (f_lbl, f_conf)
            debug_info[idx]["f"] = f"{f_lbl}:{f_conf:.2f}"

            # أولوية للجندر المستهدف إذا أعطاه نموذج الوجه فوق 0.50 أو تجاوز العتبة المتوسطة
            if target_gender in ("female", "male") and f_lbl == target_gender and f_conf > 0.50:
                final_preds[idx] = f_lbl
                continue

            is_confident = f_conf >= FACE_MIN_CONFIDENCE
            matches_target = (f_lbl == target_gender) if target_gender in ("female", "male") else (f_lbl != "unknown")

            if is_confident and matches_target:
                final_preds[idx] = f_lbl
            else:
                b_crop = samples[idx].get("body")
                if b_crop is not None and getattr(b_crop, "size", 0) > 0 and body_model is not None:
                    need_body_from_face_indices.append(idx)
                    need_body_from_face_crops.append(b_crop)
                    debug_info[idx]["src"] = f"{debug_info[idx]['src']}+body"
                else:
                    final_preds[idx] = f_lbl if is_confident else "unknown"

    all_body_indices = direct_body_indices + need_body_from_face_indices
    all_body_crops = direct_body_crops + need_body_from_face_crops

    if all_body_crops:
        body_results = _predict_single_model(all_body_crops, body_model, body_processor, "BodyModel")
        for idx, (b_lbl, b_conf) in zip(all_body_indices, body_results):
            debug_info[idx]["b"] = f"{b_lbl}:{b_conf:.2f}"
            f_lbl, f_conf = face_preds_map.get(idx, ("unknown", 0.0))

            # تقديم الجندر المستهدف دائماً إذا أعطاه أي من النموذجين بنسبة > 0.50
            if target_gender in ("female", "male"):
                if b_lbl == target_gender and b_conf > 0.50:
                    final_preds[idx] = b_lbl
                    continue
                if f_lbl == target_gender and f_conf > 0.50:
                    final_preds[idx] = f_lbl
                    continue

            if idx in face_preds_map:
                if b_lbl != "unknown" and b_conf >= BODY_MIN_CONFIDENCE and (
                    (target_gender in ("female", "male") and b_lbl == target_gender)
                    or (f_conf < FACE_MIN_CONFIDENCE and b_conf > f_conf)
                ):
                    final_preds[idx] = b_lbl
                else:
                    final_preds[idx] = f_lbl if (f_lbl != "unknown" and f_conf >= FACE_MIN_CONFIDENCE) else "unknown"
            else:
                if b_lbl != "unknown" and b_conf >= BODY_MIN_CONFIDENCE:
                    final_preds[idx] = b_lbl
                else:
                    final_preds[idx] = "unknown"

    return final_preds, debug_info

def _finalize_incomplete_track(tid: int, v: dict, target_gender: str):
    """
    حسم قرار الـ track غير المكتمل (الذي لم يصل إلى MAX_SAMPLES_PER_TRACK ولم يجد الجندر المطلوب)
    بالاعتماد على الجندر المخالف الذي وُجد فعلاً أثناء ظهوره.
    """
    if v["decided"]:
        return

    opposite_gender = "male" if target_gender == "female" else ("female" if target_gender == "male" else None)

    if opposite_gender and v.get(opposite_gender, 0) > 0:
        v["resolved_gender"] = opposite_gender
        v["decision_reason"] = "opposite_gender_early_exit"
    elif v.get("female", 0) > 0 and v.get("male", 0) == 0:
        v["resolved_gender"] = "female"
        v["decision_reason"] = "observed_female_early_exit"
    elif v.get("male", 0) > 0 and v.get("female", 0) == 0:
        v["resolved_gender"] = "male"
        v["decision_reason"] = "observed_male_early_exit"
    else:
        v["resolved_gender"] = "unknown"
        v["decision_reason"] = "no_target_before_exit"

    v["decided"] = True

def apply_local_roi_blur(frame: np.ndarray, alpha: np.ndarray, ksize: int) -> np.ndarray:
    """تطبيق البلور والمزج على المستطيل المحيط بالقناع فقط لتسريع المعالجة."""
    ys, xs = np.where(alpha > 0.01)
    if len(xs) == 0 or len(ys) == 0:
        return frame

    h, w = frame.shape[:2]
    pad = max(16, ksize // 2)
    x1 = max(0, int(xs.min()) - pad)
    y1 = max(0, int(ys.min()) - pad)
    x2 = min(w, int(xs.max()) + pad + 1)
    y2 = min(h, int(ys.max()) + pad + 1)

    out_frame = frame.copy()
    roi = out_frame[y1:y2, x1:x2]
    roi_alpha = alpha[y1:y2, x1:x2, None]
    blurred_roi = cv2.blur(roi, (ksize, ksize))
    out_frame[y1:y2, x1:x2] = (blurred_roi * roi_alpha + roi * (1.0 - roi_alpha)).astype(np.uint8)
    return out_frame

async def Process_Video_Pro_Segmentation(file_path, replied, BlurRate, isfull, Ranges, gender_filter="all"):
    ksize = odd_blur_size(BlurRate)
    base_no_ext, _ = os.path.splitext(file_path)
    raw_out_path = f"{base_no_ext}_RawBlur.avi"

    Aud = None
    try:
        Aud = await Mp3_Conv(file_path)
    except Exception:
        Aud = None

    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        raise ValueError("تعذر فتح ملف الفيديو.")

    out = None
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 1:
            fps = 25.0
        progress_step = max(1, int(round(fps)))

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration_sec = total_frames / fps if total_frames > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        ranges = []
        if not isfull and Ranges:
            for rng in Ranges.strip().split():
                if '-' in rng:
                    s_str, e_str = rng.split('-', 1)
                    start_f = int(await get_seconds(s_str) * fps)
                    end_f = int(await get_seconds(e_str) * fps)
                    if end_f >= start_f:
                        ranges.append((start_f, end_f))

        any_gender_model_ready = (face_model is not None) or (body_model is not None)
        use_gender_filter = (gender_filter in ("male", "female")) and any_gender_model_ready

        # =====================================================================
        # المرحلة الأولى: رصد الفيديو وحفظ الأقنعة + حتى 4 فحوصات كل 0.5 ثانية
        # =====================================================================
        frame_records = {}
        track_votes = {}
        approved_tids = set()
        sample_logs = []
        sample_interval_frames = max(1, int(round(fps * SAMPLE_INTERVAL_SEC)))

        t_track_sum = 0.0
        t_gender_sum = 0.0
        t_blur_sum = 0.0
        processed_frames_cnt = 0

        ret_num = 0
        blur_inspect_start = time.perf_counter()

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            ret_num += 1

            ispermit = True
            if not isfull:
                ispermit = any(start_f <= ret_num <= end_f for start_f, end_f in ranges)

            if ret_num % progress_step == 0 and duration_sec > 0:
                cur_sec = min(ret_num / fps, duration_sec)
                try:
                    await replied.edit_text(
                        f"🔍 المرحلة 1/2 (الرصد والفحص كل {SAMPLE_INTERVAL_SEC}ث حتى {MAX_SAMPLES_PER_TRACK} مرات)... `{fmt_clock(cur_sec)}-{fmt_clock(duration_sec)}`"
                    )
                except Exception:
                    pass

            if not ispermit:
                continue

            processed_frames_cnt += 1
            t0_track = time.perf_counter()
            results = model.track(
                frame,
                persist=True,
                classes=[0],
                conf=0.25,
                iou=0.45,
                imgsz=512,
                retina_masks=False,
                tracker="bytetrack.yaml",
                verbose=False
            )
            t_track_sum += time.perf_counter() - t0_track

            if results and results[0].masks is not None:
                masks = results[0].masks.data.cpu().numpy()
                boxes = results[0].boxes
                raw_ids = boxes.id.int().cpu().tolist() if (boxes is not None and boxes.id is not None) else []

                records_this_frame = []
                pending_tids = []
                pending_samples = []

                for idx, m in enumerate(masks):
                    tid = raw_ids[idx] if idx < len(raw_ids) else -1
                    bin_mask = (m > 0.30).astype(np.uint8)
                    records_this_frame.append((tid, bin_mask))

                    if use_gender_filter:
                        if tid not in track_votes:
                            track_votes[tid] = {
                                "female": 0,
                                "male": 0,
                                "samples": 0,
                                "last_sample_f": -999999,
                                "decided": False,
                                "resolved_gender": None,
                                "decision_reason": None
                            }

                        v = track_votes[tid]
                        # يستمر في الفحص طالما لم يُحسم بعد ولم يتجاوز الحد الأقصى للعينات
                        if (
                            not v["decided"]
                            and v["samples"] < MAX_SAMPLES_PER_TRACK
                            and (ret_num - v["last_sample_f"]) >= sample_interval_frames
                        ):
                            full_m = cv2.resize(bin_mask.astype(np.float32), (width, height), interpolation=cv2.INTER_NEAREST)
                            sample = extract_body_and_face(frame, full_m)
                            if sample is not None:
                                pending_tids.append(tid)
                                pending_samples.append(sample)
                                v["last_sample_f"] = ret_num

                frame_records[ret_num] = records_this_frame

                if use_gender_filter and pending_samples:
                    t0_g = time.perf_counter()
                    batch_preds, batch_dbg = classify_sequential_with_debug(pending_samples, gender_filter)
                    sec_now = round(ret_num / fps, 2)
                    for tid, g_label, dbg in zip(pending_tids, batch_preds, batch_dbg):
                        v = track_votes[tid]
                        if v["decided"]:
                            continue
                        v["samples"] += 1
                        if g_label in ("female", "male"):
                            v[g_label] += 1

                        # 1) إذا وُجد الجندر المطلوب: يُعتمد فوراً ويتوقف الفحص لهذا الـ tid
                        if g_label == gender_filter:
                            approved_tids.add(tid)
                            v["resolved_gender"] = gender_filter
                            v["decision_reason"] = "target_gender_found"
                            v["decided"] = True
                        # 2) إذا اكتمل الحد الأقصى للعينات دون إيجاد الجندر المطلوب: يُحسم بما وُجد
                        elif v["samples"] >= MAX_SAMPLES_PER_TRACK:
                            v["resolved_gender"] = g_label if g_label in ("female", "male") else (
                                "female" if v["female"] > v["male"] else ("male" if v["male"] > v["female"] else "unknown")
                            )
                            v["decision_reason"] = "max_samples_reached"
                            v["decided"] = True

                        entry = (
                            f"tid={tid} f={ret_num}({sec_now}s) s#{v['samples']}/{MAX_SAMPLES_PER_TRACK} "
                            f"src={dbg['src']} yn={dbg['yn']} F={dbg['f']} B={dbg['b']} -> {g_label} "
                            f"[approved={tid in approved_tids}, decided={v['decided']}, reason={v['decision_reason']}]"
                        )
                        sample_logs.append(entry)
                        print(f"🧪 [SAMPLE_DEBUG] {entry}")
                    t_gender_sum += time.perf_counter() - t0_g

        # حسم أي track لم يكمل العينات بسبب اختفائه أو نهاية المرحلة الأولى
        if use_gender_filter:
            for tid, v in track_votes.items():
                if not v["decided"]:
                    _finalize_incomplete_track(tid, v, gender_filter)
                    print(
                        f"⏹️ [EARLY_EXIT_RESOLVED] tid={tid} target={gender_filter} "
                        f"samples={v['samples']}/{MAX_SAMPLES_PER_TRACK} "
                        f"votes=(F:{v['female']}, M:{v['male']}) -> {v['resolved_gender']} "
                        f"[{v['decision_reason']}, approved={tid in approved_tids}]"
                    )

            print(f"⚡ Approved ({gender_filter}, max={MAX_SAMPLES_PER_TRACK}): {sorted(approved_tids)} | Votes: {track_votes}")
            print(f"📋 Total samples logged: {len(sample_logs)}")

        # =====================================================================
        # المرحلة الثانية: تطبيق البلور على الأقنعة المحفوظة من أول ظهور للـ object
        # =====================================================================
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(raw_out_path, fourcc, fps, (width, height))
        if not out.isOpened():
            raise RuntimeError("تعذر فتح VideoWriter لكتابة الفيديو المؤقت.")

        pre_roll_frames = max(4, int(round(fps * 0.25)))
        max_hold_frames = max(4, int(round(fps * 0.25)))

        last_alpha = np.zeros((height, width), dtype=np.float32)
        hold_counter = 0
        buffer = []

        def write_buffered_item(item):
            nonlocal t_blur_sum
            t0 = time.perf_counter()
            buf_frame, buf_alpha = item
            if buf_frame.shape[1] != width or buf_frame.shape[0] != height:
                buf_frame = cv2.resize(buf_frame, (width, height), interpolation=cv2.INTER_LINEAR)
            if buf_alpha.shape[1] != width or buf_alpha.shape[0] != height:
                buf_alpha = cv2.resize(buf_alpha, (width, height), interpolation=cv2.INTER_LINEAR)

            if np.any(buf_alpha > 0.01):
                merged = apply_local_roi_blur(buf_frame, buf_alpha, ksize)
                out.write(merged)
            else:
                out.write(buf_frame)
            t_blur_sum += time.perf_counter() - t0

        ret_num = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            ret_num += 1

            if ret_num % progress_step == 0 and duration_sec > 0:
                cur_sec = min(ret_num / fps, duration_sec)
                try:
                    await replied.edit_text(
                        f"🎬 المرحلة 2/2 (تطبيق البلور)... `{fmt_clock(cur_sec)}-{fmt_clock(duration_sec)}`"
                    )
                except Exception:
                    pass

            records = frame_records.get(ret_num)
            if records:
                combined_small = None
                for tid, bin_mask in records:
                    if (not use_gender_filter) or (tid in approved_tids):
                        if combined_small is None:
                            combined_small = bin_mask.copy()
                        else:
                            combined_small = np.maximum(combined_small, bin_mask)

                if combined_small is not None and np.any(combined_small > 0):
                    current_mask = cv2.resize(
                        combined_small.astype(np.float32),
                        (width, height),
                        interpolation=cv2.INTER_LINEAR
                    )
                    hold_counter = max_hold_frames
                    alpha = refine_person_mask(current_mask)
                    alpha = np.maximum(alpha, last_alpha * 0.7)
                    last_alpha = alpha

                    buf_len = len(buffer)
                    lookback = min(pre_roll_frames, buf_len)
                    for i in range(1, lookback + 1):
                        idx = buf_len - i
                        back_weight = max(0.35, 1.0 - (i / (pre_roll_frames + 1)) * 0.65)
                        prev_f, prev_a = buffer[idx]
                        updated_a = np.maximum(prev_a, alpha * back_weight)
                        buffer[idx] = (prev_f, updated_a)
                elif hold_counter > 0:
                    hold_counter -= 1
                    decay = (hold_counter + 1) / (max_hold_frames + 1)
                    alpha = last_alpha * decay
                    last_alpha = alpha
                else:
                    alpha = np.zeros((height, width), dtype=np.float32)
                    last_alpha = alpha
            elif hold_counter > 0:
                hold_counter -= 1
                decay = (hold_counter + 1) / (max_hold_frames + 1)
                alpha = last_alpha * decay
                last_alpha = alpha
            else:
                alpha = np.zeros((height, width), dtype=np.float32)
                last_alpha = alpha

            buffer.append((frame, alpha))
            while len(buffer) > pre_roll_frames + 1:
                write_buffered_item(buffer.pop(0))

        while buffer:
            write_buffered_item(buffer.pop(0))

        out.release()
        out = None

        if not os.path.exists(raw_out_path) or os.path.getsize(raw_out_path) == 0:
            raise RuntimeError("فشل إنشاء ملف الفيديو المؤقت أو أنه فارغ.")

        blur_inspect_elapsed = time.perf_counter() - blur_inspect_start

        if processed_frames_cnt > 0:
            print(
                f"📊 Avg/frame over {processed_frames_cnt} frames | "
                f"track: {(t_track_sum/processed_frames_cnt)*1000:.1f}ms | "
                f"gender: {(t_gender_sum/processed_frames_cnt)*1000:.1f}ms | "
                f"blur+write: {(t_blur_sum/processed_frames_cnt)*1000:.1f}ms"
            )

        final_vid = await Vid_Mk(raw_out_path, Aud)
        return final_vid, blur_inspect_elapsed
    finally:
        if cap is not None:
            cap.release()
        if out is not None:
            out.release()

bot, Bot_Identifier = Pyrogram_Client(Bot_Token)

def get_user_cfg(user_id: int) -> dict:
    if user_id not in Settings_Dict:
        Settings_Dict[user_id] = {'BlurRate': '', 'isfull': True, 'Ranges': '', 'Gender': 'all'}
    return Settings_Dict[user_id]

@bot.on_message(filters.command('start') & filters.private)
async def command_start(client, message):
    user_id = message.from_user.id
    Settings_Dict[user_id] = {'BlurRate': '', 'isfull': True, 'Ranges': '', 'Gender': 'all'}
    await message.reply_text(
        "👋 أهلاً بك في بوت العزل الاحترافي.\nاختر درجة البلور المطلوبة:",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("11"), KeyboardButton("31")],
            [KeyboardButton("109"), KeyboardButton("185")],
            [KeyboardButton("261"), KeyboardButton("491")]
        ], resize_keyboard=True)
    )

@bot.on_message(filters.private & filters.incoming & filters.text)
async def _text_handler(client, message):
    user_id = message.from_user.id
    cfg = get_user_cfg(user_id)
    text = message.text.strip()

    if text == "إلغاء":
        cfg['isfull'] = True
        cfg['Ranges'] = ''
        await message.reply_text(
            "تم الإلغاء والعودة إلى وضع الفيديو الكامل.",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("Full Vid"), KeyboardButton("Ranges")]
            ], resize_keyboard=True)
        )
        return

    if text in ['11', '31', '109', '185', '261', '491']:
        cfg['BlurRate'] = text
        await message.reply_text(
            "اختر الجندر المستهدف للبلور (الوجه الواضح أولاً ثم الجسد عند الحاجة أو ضعف الثقة):",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("الكل"), KeyboardButton("إناث فقط"), KeyboardButton("ذكور فقط")]
            ], resize_keyboard=True)
        )
    elif text in ['الكل', 'إناث فقط', 'ذكور فقط']:
        if text == 'الكل':
            cfg['Gender'] = 'all'
        elif text == 'إناث فقط':
            cfg['Gender'] = 'female'
        else:
            cfg['Gender'] = 'male'

        if cfg['Gender'] != 'all' and not ((face_model is not None) or (body_model is not None)):
            await message.reply_text(
                "⚠️ تنبيه: تعذر تهيئة نموذجي الجندر؛ سيتم تطبيق البلور على الكل."
            )

        await message.reply_text(
            "اختر نمط المعالجة:",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("Full Vid"), KeyboardButton("Ranges")]
            ], resize_keyboard=True)
        )
    elif text == 'Full Vid':
        cfg['isfull'] = True
        await message.reply_text("✅ تم الحفظ. أرسل الفيديو الآن للمعالجة!")
    elif text == 'Ranges':
        cfg['isfull'] = False
        await message.reply_text(
            "أرسل الآن النطاقات الزمنية في رسالة واحدة مباشرة:\nمثال:\n`00:00-00:49 1:20-1:31`",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("إلغاء")]], resize_keyboard=True)
        )
    elif not cfg['isfull'] and '-' in text:
        cfg['Ranges'] = text
        await message.reply_text(
            "✅ تم حفظ جميع النطاقات بنجاح. أرسل الفيديو الآن!",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("Full Vid"), KeyboardButton("Ranges")]
            ], resize_keyboard=True)
        )
    else:
        await message.reply_text("⚠️ يرجى اختيار درجة البلور أو الجندر أو نمط المعالجة الصحيح من الأزرار.")

@bot.on_message(filters.private & filters.incoming & filters.video)
async def _video_handler(client, message):
    user_id = message.from_user.id
    cfg = get_user_cfg(user_id)
    if not cfg['BlurRate']:
        await message.reply_text('⚠️ يرجى إعادة ضبط الإعدادات بالضغط على: /start')
        return

    user_dir = os.path.join(Base_Dl_Dir, f"{Bot_Identifier}_{user_id}")
    await Create_Dir(user_dir)
    replied = await message.reply_text('🚀 جاري تحميل الفيديو ومعالجة النطاقات المحددة بدقة...')

    upload_succeeded = False
    try:
        vid_path = await message.download(file_name=os.path.join(user_dir, ""))
        blurred_vid, blur_inspect_elapsed = await Process_Video_Pro_Segmentation(
            vid_path,
            replied,
            cfg['BlurRate'],
            cfg['isfull'],
            cfg['Ranges'],
            cfg.get('Gender', 'all')
        )
        time_str = format_elapsed_min_sec(blur_inspect_elapsed)
        await replied.edit_text(
            f"✅ تمت العملية باحترافية تامة!\n⏱️ وقت الفحص والبلور: `{time_str}`"
        )
        await message.reply_video(blurred_vid)
        upload_succeeded = True
    except Exception as e:
        await replied.edit_text(f'❌ حدث خطأ: {str(e)}')
    finally:
        if upload_succeeded or not os.path.exists(user_dir):
            await Check_Dir(user_dir)
            if os.path.isdir(Base_Dl_Dir) and not os.listdir(Base_Dl_Dir):
                Cleanup_Work_Dir(Base_Dl_Dir)

def main():
    Cleanup_Work_Dir(Base_Dl_Dir)
    bot.start()
    print("✅ Pro Segmentation Bot (Medium Thresholds + Target Priority + Max 4 Samples) is ONLINE!")
    try:
        idle()
    finally:
        bot.stop()
        Cleanup_Work_Dir(Base_Dl_Dir)

if __name__ == '__main__':
    main()