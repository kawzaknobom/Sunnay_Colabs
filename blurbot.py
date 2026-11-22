import nest_asyncio, os, sys, asyncio, shutil, time
from types import SimpleNamespace
nest_asyncio.apply()

# ultralytics/MiVOLO القديمان يستدعيان torch.load بلا weights_only=False، وهذا يفشل مع PyTorch >= 2.6.
# الأوزان هنا من مصادر موثوقة (ultralytics والمستودع الرسمي لـ MiVOLO)، لذا نعيد السلوك القديم.
os.environ.setdefault('TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD', '1')

Bot_Token = os.getenv('TOKEN')

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'
from pyrogram import Client, filters, idle
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton
from pyrogram.errors import FloodWait
import cv2, numpy as np
import torch
from ultralytics import YOLO

# تحميل نموذج الـ Segmentation الأساسي
model = YOLO('yolov8m-seg.pt')

# =====================================================================
# MiVOLO: نموذج واحد يفحص الوجه والجسد معاً (يحل محل نموذجي الوجه والجسد + YuNet)
# =====================================================================
MIVOLO_DIR = os.getenv('MIVOLO_DIR', '/content/MiVOLO')
if os.path.isdir(MIVOLO_DIR) and MIVOLO_DIR not in sys.path:
    sys.path.insert(0, MIVOLO_DIR)

MIVOLO_DETECTOR_WEIGHTS = os.getenv(
    'MIVOLO_DETECTOR_WEIGHTS', os.path.join(MIVOLO_DIR, 'models', 'yolov8x_person_face.pt')
)
MIVOLO_CHECKPOINT = os.getenv(
    'MIVOLO_CHECKPOINT', os.path.join(MIVOLO_DIR, 'models', 'mivolo_imbd.pth.tar')
)
MIVOLO_DEVICE = os.getenv('MIVOLO_DEVICE', 'cuda:0' if torch.cuda.is_available() else 'cpu')

# عتبات ثقة صارمة لتجنب الإيجابيات الكاذبة (False Positives)
FACE_MIN_CONFIDENCE = float(os.getenv('FACE_MIN_CONFIDENCE', '0.68'))    # عينة فيها وجه + جسد
FACE_HIGH_CONFIDENCE = float(os.getenv('FACE_HIGH_CONFIDENCE', '0.90'))  # وجه حاسم الثقة
BODY_MIN_CONFIDENCE = float(os.getenv('BODY_MIN_CONFIDENCE', '0.78'))    # جسد فقط (بدون وجه)
BODY_ONLY_WEIGHT = float(os.getenv('BODY_ONLY_WEIGHT', '0.65'))          # تخفيف وزن عينة الجسد فقط

SAMPLE_INTERVAL_SEC = float(os.getenv('SAMPLE_INTERVAL_SEC', '0.35'))
MAX_SAMPLES_PER_TRACK = int(os.getenv('MAX_SAMPLES_PER_TRACK', '12'))
MIN_CONFIRM_VOTES = int(os.getenv('MIN_CONFIRM_VOTES', '3'))
PROGRESS_EDIT_MIN_SEC = float(os.getenv('PROGRESS_EDIT_MIN_SEC', '4.0'))

mivolo_predictor = None
mivolo_init_error = None

def _init_mivolo():
    global mivolo_predictor, mivolo_init_error
    # نقاط تحقق MiVOLO القديمة تحتاج weights_only=False مع PyTorch >= 2.6 (الملفات موثوقة: من المستودع الرسمي)
    prev_flag = os.environ.get('TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD')
    os.environ['TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD'] = '1'
    try:
        for p in (MIVOLO_DETECTOR_WEIGHTS, MIVOLO_CHECKPOINT):
            if not os.path.exists(p):
                raise FileNotFoundError(f"ملف الأوزان غير موجود: {p}")
        from mivolo.predictor import Predictor
        cfg = SimpleNamespace(
            detector_weights=MIVOLO_DETECTOR_WEIGHTS,
            checkpoint=MIVOLO_CHECKPOINT,
            device=MIVOLO_DEVICE,
            with_persons=True,     # استخدام الجسد مع الوجه
            disable_faces=False,   # الوجه مفعّل (عند غيابه يعتمد على الجسد تلقائياً)
            draw=False,
        )
        mivolo_predictor = Predictor(cfg, verbose=False)
        print(f"✅ MiVOLO loaded on {MIVOLO_DEVICE}")
    except Exception as e:
        import traceback
        mivolo_predictor = None
        mivolo_init_error = f"{type(e).__name__}: {e}"
        print(f"⚠️ MiVOLO init error: {mivolo_init_error}")
        traceback.print_exc()
    finally:
        if prev_flag is None:
            os.environ.pop('TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD', None)
        else:
            os.environ['TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD'] = prev_flag

_init_mivolo()

Audio_Forms = (".mp3", ".ogg", ".m4a", ".aac", ".flac", ".wav", ".wma", ".opus", ".3gpp")

Settings_Dict = {}
Base_Dl_Dir = './ProSeg_Work'

async def safe_edit_text(replied, text: str, last_edit_ref: list, force: bool = False):
    """تحديث رسالة التقدم بحد أدنى زمني ومعالجة FloodWait لتجنب حظر أو تأخير تيليجرام."""
    if replied is None:
        return
    now = time.monotonic()
    if not force and (now - last_edit_ref[0]) < PROGRESS_EDIT_MIN_SEC:
        return
    try:
        await replied.edit_text(text)
        last_edit_ref[0] = time.monotonic()
    except FloodWait as fw:
        await asyncio.sleep(min(float(fw.value) + 0.5, 15.0))
        try:
            await replied.edit_text(text)
            last_edit_ref[0] = time.monotonic()
        except Exception:
            pass
    except Exception:
        pass

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
    if not Bot_Token or ':' not in Bot_Token:
        raise ValueError("متغير البيئة TOKEN غير مضبوط بشكل صحيح.")
    if not Api_Id or not Api_Hash:
        raise ValueError("متغيرا البيئة API_ID و API_HASH مطلوبان للتشغيل.")
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

def extract_body_crop(frame: np.ndarray, mask_2d: np.ndarray, pad: int = 10):
    """
    قص الجسم الكامل للشخص اعتماداً على قناع YOLO. تُمرَّر القصاصة لاحقاً إلى MiVOLO
    (يكتشف الوجه والجسد بنفسه داخلها)، وتُرتَّب العينات حسب جودة المساحة وتنوّع الزمن.
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
    if pw < 20 or ph < 20:
        return None

    cx = 0.5 * (x1 + x2) / max(1.0, float(w))
    cy = 0.5 * (y1 + y2) / max(1.0, float(h))

    return {
        "body": frame[y1:y2, x1:x2].copy(),  # نسخة حتى لا يبقى الإطار الكامل محجوزاً في الذاكرة
        "quality_score": float(pw * ph),
        "center": (cx, cy),
    }

def _select_diverse_samples(track_list: list, max_keep: int) -> list:
    """
    اختيار عينات تمثّل المسار عبر الزمن وكذلك القصاصات الواضحة (أكبر مساحة)،
    لتجنب حصر جميع العينات في لحظة واحدة من الفيديو الطويل.
    """
    if len(track_list) <= max_keep:
        return track_list

    sorted_by_time = sorted(track_list, key=lambda x: x["frame_num"])
    id_to_pos = {id(item): idx for idx, item in enumerate(sorted_by_time)}
    n_slots = max_keep
    selected = []
    used_indices = set()

    for slot in range(n_slots):
        start_idx = (slot * len(sorted_by_time)) // n_slots
        end_idx = ((slot + 1) * len(sorted_by_time)) // n_slots
        if end_idx <= start_idx:
            end_idx = min(len(sorted_by_time), start_idx + 1)
        bucket = sorted_by_time[start_idx:end_idx]
        if bucket:
            best_in_bucket = max(bucket, key=lambda x: x["quality_score"])
            orig_pos = id_to_pos[id(best_in_bucket)]
            if orig_pos not in used_indices:
                selected.append(best_in_bucket)
                used_indices.add(orig_pos)

    if len(selected) < max_keep:
        remaining = [
            (i, item) for i, item in enumerate(sorted_by_time) if i not in used_indices
        ]
        remaining.sort(key=lambda pair: pair[1]["quality_score"], reverse=True)
        for i, item in remaining[: max_keep - len(selected)]:
            selected.append(item)
            used_indices.add(i)

    selected.sort(key=lambda x: x["frame_num"])
    return selected

def _box_iou(a, b) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    if inter <= 0.0:
        return 0.0
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    return inter / (area_a + area_b - inter + 1e-9)

def _predict_crop_mivolo(crop):
    """
    تشغيل MiVOLO على قصاصة شخص واحد. يرجع (label, confidence, has_face).
    - الشخص المستهدف = الجسد الذي تغطي مساحته معظم القصاصة.
    - has_face = هل وُجد وجه داخل صندوق هذا الجسد (فيُستخدم وجه+جسد معاً).
    """
    if mivolo_predictor is None or crop is None or getattr(crop, "size", 0) == 0:
        return "unknown", 0.0, False
    try:
        detected, _ = mivolo_predictor.recognize(crop)
        n = detected.n_objects
        if n == 0:
            return "unknown", 0.0, False

        res = detected.yolo_results
        ch, cw = crop.shape[:2]
        crop_box = (0.0, 0.0, float(cw), float(ch))
        xyxy = res.boxes.xyxy.cpu().numpy()
        cls_ids = res.boxes.cls.cpu().numpy().astype(int)

        persons, faces = [], []
        for i in range(n):
            g = detected.genders[i]
            s = detected.gender_scores[i]
            if g not in ("male", "female"):
                continue
            if s is None or (isinstance(s, np.ndarray) and s.size == 0):
                continue
            s_val = float(np.asarray(s).reshape(-1)[0]) if isinstance(s, np.ndarray) else float(s)
            item = (tuple(float(v) for v in xyxy[i]), g, s_val)
            name = str(res.names[int(cls_ids[i])]).lower()
            if name == "person":
                persons.append(item)
            elif name == "face":
                faces.append(item)

        if persons:
            bb, g, s = max(persons, key=lambda it: _box_iou(it[0], crop_box))
            has_face = any(
                bb[0] <= (fb[0] + fb[2]) / 2.0 <= bb[2] and bb[1] <= (fb[1] + fb[3]) / 2.0 <= bb[3]
                for fb, _, _ in faces
            )
            return g, s, has_face

        if faces:
            _, g, s = max(faces, key=lambda it: (it[0][2] - it[0][0]) * (it[0][3] - it[0][1]))
            return g, s, True
    except Exception as e:
        print(f"⚠️ MiVOLO inference error: {e}")
    return "unknown", 0.0, False

def classify_samples_mivolo(samples: list):
    """
    تقييم محافظ لكل عينة بنموذج MiVOLO (وجه+جسد معاً في نموذج واحد):
    - عينة فيها وجه: تُقبل بثقة >= FACE_MIN_CONFIDENCE، وتُعدّ "حاسمة" عند >= FACE_HIGH_CONFIDENCE.
    - عينة جسد فقط: تُقبل بثقة >= BODY_MIN_CONFIDENCE ويُخفَّف وزنها بـ BODY_ONLY_WEIGHT.
    الناتج بنفس صيغة النظام السابق: (label, confidence, is_strong_face).
    """
    results, debug_info = [], []
    for s in samples:
        lbl, conf, has_face = _predict_crop_mivolo(s.get("body"))
        dbg = {"src": "face+body" if has_face else "body", "mv": f"{lbl}:{conf:.2f}"}

        if lbl not in ("female", "male"):
            dbg["src"] = "none"
            results.append(("unknown", 0.0, False))
        elif has_face:
            if conf >= FACE_HIGH_CONFIDENCE:
                results.append((lbl, conf, True))
            elif conf >= FACE_MIN_CONFIDENCE:
                results.append((lbl, conf, False))
            else:
                results.append(("unknown", conf, False))
        else:
            if conf >= BODY_MIN_CONFIDENCE:
                results.append((lbl, conf * BODY_ONLY_WEIGHT, False))
            else:
                results.append(("unknown", conf, False))
        debug_info.append(dbg)
    return results, debug_info

def _finalize_track_decision(v: dict, target_gender: str):
    """
    حسم قرار المسار بعد تجميع وتصنيف عينات هذا الشخص عبر الفيديو.
    إذا ظهرت عينة واحدة على الأقل مطابقة للجندر المستهدف (target_gender)، تُعدّ نتيجة قاطعة لاعتماد كامل الـ Object.
    """
    f_votes = v["female_votes"]
    m_votes = v["male_votes"]
    f_weight = v["female_weight"]
    m_weight = v["male_weight"]
    is_untracked = bool(v.get("is_untracked", False))

    if target_gender == "female":
        if is_untracked:
            if f_votes >= 2 and f_weight > max(1.6, m_weight * 1.8):
                v["resolved_gender"] = "female"
                v["decision_reason"] = "untracked_confirmed_female"
            elif v["strong_face_female"] and f_weight >= 0.95 and m_weight == 0.0 and v["samples"] <= 2:
                v["resolved_gender"] = "female"
                v["decision_reason"] = "untracked_single_strong_female"
            elif (v["strong_face_male"] and f_weight == 0.0) or (m_weight > f_weight):
                v["resolved_gender"] = "male"
                v["decision_reason"] = "untracked_opposite_male"
            else:
                v["resolved_gender"] = "unknown"
                v["decision_reason"] = "untracked_insufficient_female_evidence"
        else:
            if v["strong_face_female"] and m_weight == 0.0:
                v["resolved_gender"] = "female"
                v["decision_reason"] = "strong_face_female"
            elif f_votes >= MIN_CONFIRM_VOTES and f_weight > max(1.8, m_weight * 1.8):
                v["resolved_gender"] = "female"
                v["decision_reason"] = "confirmed_target_female"
            elif f_votes >= 2 and f_weight > max(1.3, m_weight * 1.8):
                v["resolved_gender"] = "female"
                v["decision_reason"] = "final_weighted_female"
            elif (v["strong_face_male"] and f_weight == 0.0) or (m_votes >= 2 and m_weight > f_weight * 1.4) or (m_weight > f_weight):
                v["resolved_gender"] = "male"
                v["decision_reason"] = "confirmed_opposite_male"
            else:
                v["resolved_gender"] = "unknown"
                v["decision_reason"] = "insufficient_female_evidence"

    elif target_gender == "male":
        if is_untracked:
            if m_votes >= 2 and m_weight > max(1.6, f_weight * 1.8):
                v["resolved_gender"] = "male"
                v["decision_reason"] = "untracked_confirmed_male"
            elif v["strong_face_male"] and m_weight >= 0.95 and f_weight == 0.0 and v["samples"] <= 2:
                v["resolved_gender"] = "male"
                v["decision_reason"] = "untracked_single_strong_male"
            elif (v["strong_face_female"] and m_weight == 0.0) or (f_weight > m_weight):
                v["resolved_gender"] = "female"
                v["decision_reason"] = "untracked_opposite_female"
            else:
                v["resolved_gender"] = "unknown"
                v["decision_reason"] = "untracked_insufficient_male_evidence"
        else:
            if v["strong_face_male"] and f_weight == 0.0:
                v["resolved_gender"] = "male"
                v["decision_reason"] = "strong_face_male"
            elif m_votes >= MIN_CONFIRM_VOTES and m_weight > max(1.8, f_weight * 1.8):
                v["resolved_gender"] = "male"
                v["decision_reason"] = "confirmed_target_male"
            elif m_votes >= 2 and m_weight > max(1.3, f_weight * 1.8):
                v["resolved_gender"] = "male"
                v["decision_reason"] = "final_weighted_male"
            elif (v["strong_face_female"] and m_weight == 0.0) or (f_votes >= 2 and f_weight > m_weight * 1.4) or (f_weight > m_weight):
                v["resolved_gender"] = "female"
                v["decision_reason"] = "confirmed_opposite_female"
            else:
                v["resolved_gender"] = "unknown"
                v["decision_reason"] = "insufficient_male_evidence"
    else:
        v["resolved_gender"] = "unknown"
        v["decision_reason"] = "no_target"

    v["decided"] = True

def apply_local_roi_blur(frame: np.ndarray, alpha: np.ndarray, ksize: int) -> np.ndarray:
    """تطبيق البلور والمزج بأمان كامل على كامل الإطار أو المستطيل المحدد بدون أي عدم تطابق أبعاد."""
    if frame is None or getattr(frame, "size", 0) == 0 or alpha is None or getattr(alpha, "size", 0) == 0:
        return frame

    src_frame = np.ascontiguousarray(frame)
    if src_frame.ndim == 2:
        src_frame = cv2.cvtColor(src_frame, cv2.COLOR_GRAY2BGR)
    elif src_frame.ndim == 3 and src_frame.shape[2] == 4:
        src_frame = src_frame[:, :, :3]

    h, w = src_frame.shape[:2]
    a2d = np.asarray(alpha, dtype=np.float32)
    if a2d.ndim > 2:
        a2d = a2d[..., 0]
    a2d = np.ascontiguousarray(a2d)
    if a2d.shape[:2] != (h, w):
        a2d = cv2.resize(a2d, (w, h), interpolation=cv2.INTER_LINEAR)
    a2d = np.clip(a2d, 0.0, 1.0)

    ys, xs = np.where(a2d > 0.01)
    if len(xs) == 0 or len(ys) == 0:
        return src_frame

    pad = max(16, ksize // 2)
    x1 = max(0, int(xs.min()) - pad)
    y1 = max(0, int(ys.min()) - pad)
    x2 = min(w, int(xs.max()) + pad + 1)
    y2 = min(h, int(ys.max()) + pad + 1)
    if x2 <= x1 or y2 <= y1:
        return src_frame

    out_frame = src_frame.copy()
    roi_orig = np.ascontiguousarray(out_frame[y1:y2, x1:x2], dtype=np.float32)
    rh, rw = roi_orig.shape[:2]

    roi_blur = cv2.blur(roi_orig, (ksize, ksize)).astype(np.float32)
    if roi_blur.shape[:2] != (rh, rw):
        roi_blur = cv2.resize(roi_blur, (rw, rh), interpolation=cv2.INTER_LINEAR)

    roi_a = np.ascontiguousarray(a2d[y1:y2, x1:x2], dtype=np.float32)
    if roi_a.shape[:2] != (rh, rw):
        roi_a = cv2.resize(roi_a, (rw, rh), interpolation=cv2.INTER_LINEAR)

    # حساب كل قناة بشكل صريح لضمان عدم حدوث أي اختلاف في أبعاد المصفوفات
    for c in range(3):
        ch_orig = roi_orig[:, :, c]
        ch_blur = roi_blur[:, :, c]
        ch_out = ch_blur * roi_a + ch_orig * (1.0 - roi_a)
        out_frame[y1:y2, x1:x2, c] = np.clip(ch_out, 0.0, 255.0).astype(np.uint8)

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

        use_gender_filter = (gender_filter in ("male", "female")) and (mivolo_predictor is not None)

        # =====================================================================
        # المرحلة 1/3: استخراج جميع الـ Objects وتتبّعها وحفظ الأقنعة + القصاصات
        # =====================================================================
        frame_records = {}
        collected_samples = {}       # track_key -> list of sample dicts
        last_sample_frame = {}       # track_key -> last frame index sampled
        untracked_buckets = []       # list of dicts for tid < 0 proximity buckets
        next_untracked_id = -1000
        sample_interval_frames = max(1, int(round(fps * SAMPLE_INTERVAL_SEC)))
        max_pool_per_track = max(MAX_SAMPLES_PER_TRACK * 3, 24)
        last_edit_ref = [0.0]

        t_stage1_track = 0.0
        t_stage2_gender = 0.0
        t_stage3_blur = 0.0
        processed_frames_cnt = 0

        ret_num = 0
        pipeline_start = time.perf_counter()

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
                await safe_edit_text(
                    replied,
                    f"🔍 المرحلة 1/3 (استخراج وتتبع الـ Objects)... `{fmt_clock(cur_sec)}-{fmt_clock(duration_sec)}`",
                    last_edit_ref,
                )

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
            t_stage1_track += time.perf_counter() - t0_track

            if results and results[0].masks is not None:
                masks = results[0].masks.data.cpu().numpy()
                boxes = results[0].boxes
                raw_ids = boxes.id.int().cpu().tolist() if (boxes is not None and boxes.id is not None) else []

                records_this_frame = []
                for idx, m in enumerate(masks):
                    raw_tid = raw_ids[idx] if idx < len(raw_ids) else -1
                    bin_mask = (m > 0.30).astype(np.uint8)
                    is_untracked = raw_tid < 0
                    track_key = raw_tid

                    full_m = None
                    sample = None
                    if use_gender_filter or is_untracked:
                        full_m = cv2.resize(
                            bin_mask.astype(np.float32),
                            (width, height),
                            interpolation=cv2.INTER_NEAREST
                        )
                        sample = extract_body_crop(frame, full_m)

                    if is_untracked:
                        cx, cy = sample["center"] if sample is not None else (0.5, 0.5)
                        matched_bucket = None
                        for b in untracked_buckets:
                            dist = ((b["cx"] - cx) ** 2 + (b["cy"] - cy) ** 2) ** 0.5
                            if (ret_num - b["last_frame"]) <= int(round(fps * 1.5)) and dist <= 0.18:
                                matched_bucket = b
                                break
                        if matched_bucket is None:
                            matched_bucket = {
                                "key": next_untracked_id,
                                "cx": cx,
                                "cy": cy,
                                "last_frame": ret_num,
                            }
                            next_untracked_id -= 1
                            untracked_buckets.append(matched_bucket)
                        else:
                            matched_bucket["cx"] = cx
                            matched_bucket["cy"] = cy
                            matched_bucket["last_frame"] = ret_num
                        track_key = matched_bucket["key"]

                    records_this_frame.append((track_key, is_untracked, bin_mask))

                    if use_gender_filter and sample is not None:
                        last_f = last_sample_frame.get(track_key, -999999)
                        if (ret_num - last_f) >= sample_interval_frames:
                            sample["frame_num"] = ret_num
                            sample["sec"] = round(ret_num / fps, 2)
                            sample["is_untracked"] = is_untracked
                            pool = collected_samples.setdefault(track_key, [])
                            pool.append(sample)
                            if len(pool) > max_pool_per_track:
                                pool.sort(key=lambda x: x["quality_score"], reverse=True)
                                del pool[max_pool_per_track:]
                            last_sample_frame[track_key] = ret_num

                frame_records[ret_num] = records_this_frame

        # =====================================================================
        # المرحلة 2/3: فحص الجندر وفصل المقاطع المتناوبة (مثل ذكر -> أنثى -> ذكر) كـ Objects مستقلة
        # =====================================================================
        track_votes = {}
        approved_tids = set()
        split_boundaries = {}  # orig_tid -> list of (start_frame_num, sub_tid)
        split_tids = set()
        sample_logs = []

        if use_gender_filter:
            await safe_edit_text(
                replied,
                f"🧠 المرحلة 2/3 (فحص الجندر وفصل المقاطع لـ {len(collected_samples)} شخص/مسار)...",
                last_edit_ref,
                force=True,
            )

            t0_gender = time.perf_counter()

            # تصنيف جميع العينات المجمعة زمنياً لكل مسار أصلي أولاً
            ordered_items = []
            for orig_tid, pool in collected_samples.items():
                chron_pool = sorted(pool, key=lambda x: x["frame_num"])
                for s in chron_pool:
                    ordered_items.append((orig_tid, s))

            if ordered_items:
                all_samples = [s for _, s in ordered_items]
                all_preds, all_dbg = classify_samples_mivolo(all_samples)
                preds_by_tid = {}
                for (orig_tid, s), pred, dbg in zip(ordered_items, all_preds, all_dbg):
                    preds_by_tid.setdefault(orig_tid, []).append((s, pred, dbg))

                sub_pools = {}
                for orig_tid, items in preds_by_tid.items():
                    seg_idx = 0
                    cur_sub_tid = f"{orig_tid}_s{seg_idx}"
                    cur_gender = None
                    pending_gender = None
                    pending_count = 0
                    pending_start_frame = None
                    boundaries = [(0, cur_sub_tid)]

                    for s, (g_label, g_conf, is_strong_face), dbg in items:
                        f_num = int(s["frame_num"])
                        if g_label in ("male", "female"):
                            if cur_gender is None:
                                cur_gender = g_label
                                pending_gender = None
                                pending_count = 0
                            elif g_label == cur_gender:
                                pending_gender = None
                                pending_count = 0
                            else:
                                if pending_gender == g_label:
                                    pending_count += 1
                                else:
                                    pending_gender = g_label
                                    pending_count = 1
                                    pending_start_frame = f_num

                                # فصل مقطع جديد:
                                # - عند الدخول للجندر المستهدف: نبدأ مبكراً (وجه حاسم أو عينتان متتاليتان) حتى لا يفوت بداية الكلام.
                                # - عند الخروج من الجندر المستهدف: نطلب 3 عينات متتالية (أو وجه حاسم + عينة) حتى لا ينقطع الكلام بسبب فلتة عابرة.
                                entering_target = (g_label == gender_filter)
                                should_split = (
                                    (entering_target and (is_strong_face or pending_count >= 2))
                                    or ((not entering_target) and (pending_count >= 3 or (is_strong_face and pending_count >= 2)))
                                )
                                if should_split:
                                    seg_idx += 1
                                    cur_sub_tid = f"{orig_tid}_s{seg_idx}"
                                    split_frame = pending_start_frame if pending_start_frame is not None else f_num
                                    boundaries.append((split_frame, cur_sub_tid))
                                    cur_gender = g_label
                                    pending_gender = None
                                    pending_count = 0
                                    pending_start_frame = None

                        s_copy = dict(s)
                        s_copy["_pred"] = (g_label, g_conf, is_strong_face)
                        s_copy["_dbg"] = dbg
                        s_copy["_sub_tid"] = cur_sub_tid
                        sub_pools.setdefault(cur_sub_tid, []).append(s_copy)

                    if seg_idx > 0:
                        split_tids.add(orig_tid)
                        split_boundaries[orig_tid] = boundaries
                        print(f"✂️ [TRACK_SPLIT] tid={orig_tid} split into {len(boundaries)} segments: {boundaries}")

                selected_per_sub = {}
                for sub_tid, spool in sub_pools.items():
                    chosen = _select_diverse_samples(spool, MAX_SAMPLES_PER_TRACK)
                    selected_per_sub[sub_tid] = chosen
                    is_untracked = any(s.get("is_untracked", False) for s in chosen)
                    v = {
                        "female_votes": 0,
                        "male_votes": 0,
                        "female_weight": 0.0,
                        "male_weight": 0.0,
                        "strong_face_female": False,
                        "strong_face_male": False,
                        "samples": 0,
                        "is_untracked": is_untracked,
                        "decided": False,
                        "resolved_gender": None,
                        "decision_reason": None
                    }
                    total_for_sub = len(chosen)
                    for sample_obj in chosen:
                        g_label, g_conf, is_strong_face = sample_obj["_pred"]
                        dbg = sample_obj["_dbg"]
                        v["samples"] += 1

                        if g_label == "female":
                            v["female_votes"] += 1
                            v["female_weight"] += g_conf
                            if is_strong_face:
                                v["strong_face_female"] = True
                        elif g_label == "male":
                            v["male_votes"] += 1
                            v["male_weight"] += g_conf
                            if is_strong_face:
                                v["strong_face_male"] = True

                        entry = (
                            f"tid={sub_tid} f={sample_obj['frame_num']}({sample_obj['sec']}s) "
                            f"s#{v['samples']}/{total_for_sub} "
                            f"src={dbg['src']} MV={dbg['mv']} -> {g_label}:{g_conf:.2f} "
                            f"W=(F:{v['female_weight']:.2f}, M:{v['male_weight']:.2f})"
                        )
                        sample_logs.append(entry)
                        print(f"🧪 [STAGE2_SAMPLE] {entry}")

                    _finalize_track_decision(v, gender_filter)
                    track_votes[sub_tid] = v
                    if v["resolved_gender"] == gender_filter:
                        approved_tids.add(sub_tid)
                    print(
                        f"⏹️ [STAGE2_DECISION] tid={sub_tid} target={gender_filter} "
                        f"samples={v['samples']}/{MAX_SAMPLES_PER_TRACK} "
                        f"W=(F:{v['female_weight']:.2f}, M:{v['male_weight']:.2f}) -> {v['resolved_gender']} "
                        f"[{v['decision_reason']}, approved={sub_tid in approved_tids}]"
                    )

            t_stage2_gender = time.perf_counter() - t0_gender
            print(f"⚡ Stage 2 Approved ({gender_filter}): {sorted(approved_tids, key=lambda x: (0, x) if isinstance(x, int) else (1, str(x)))} | Total samples: {len(sample_logs)}")

            collected_samples.clear()

        def _resolve_effective_tid(orig_tid, frame_num: int):
            if orig_tid not in split_tids:
                return orig_tid
            active_sub = f"{orig_tid}_s0"
            for start_f, sub_id in split_boundaries.get(orig_tid, ()):
                if frame_num >= start_f:
                    active_sub = sub_id
                else:
                    break
            return active_sub

        # =====================================================================
        # المرحلة 3/3: تطبيق البلور على الأقنعة المعتمدة من أول ظهور للـ Object
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
            nonlocal t_stage3_blur
            t0 = time.perf_counter()
            buf_frame, buf_alpha = item
            if buf_frame.shape[1] != width or buf_frame.shape[0] != height:
                buf_frame = cv2.resize(buf_frame, (width, height), interpolation=cv2.INTER_LINEAR)
            if buf_alpha.shape[1] != width or buf_alpha.shape[0] != height:
                buf_alpha = cv2.resize(buf_alpha, (width, height), interpolation=cv2.INTER_LINEAR)

            if np.any(buf_alpha > 0.01):
                merged = apply_local_roi_blur(buf_frame, buf_alpha, ksize)
                if merged.shape[1] != width or merged.shape[0] != height:
                    merged = cv2.resize(merged, (width, height), interpolation=cv2.INTER_LINEAR)
                out.write(merged)
            else:
                out.write(buf_frame)
            t_stage3_blur += time.perf_counter() - t0

        ret_num = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            ret_num += 1
            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)

            if ret_num % progress_step == 0 and duration_sec > 0:
                cur_sec = min(ret_num / fps, duration_sec)
                await safe_edit_text(
                    replied,
                    f"🎬 المرحلة 3/3 (تطبيق البلور)... `{fmt_clock(cur_sec)}-{fmt_clock(duration_sec)}`",
                    last_edit_ref,
                )

            records = frame_records.get(ret_num)
            if records:
                combined_small = None
                for tid, _is_untracked, bin_mask in records:
                    eff_tid = _resolve_effective_tid(tid, ret_num) if use_gender_filter else tid
                    if (not use_gender_filter) or (eff_tid in approved_tids):
                        if bin_mask.ndim > 2:
                            bin_mask = bin_mask[..., 0]
                        if combined_small is None:
                            combined_small = bin_mask.astype(np.uint8).copy()
                        else:
                            if bin_mask.shape != combined_small.shape:
                                bin_mask_resized = cv2.resize(
                                    bin_mask.astype(np.uint8),
                                    (combined_small.shape[1], combined_small.shape[0]),
                                    interpolation=cv2.INTER_NEAREST
                                )
                            else:
                                bin_mask_resized = bin_mask.astype(np.uint8)
                            combined_small = np.maximum(combined_small, bin_mask_resized)

                if combined_small is not None and np.any(combined_small > 0):
                    current_mask = cv2.resize(
                        combined_small.astype(np.float32),
                        (width, height),
                        interpolation=cv2.INTER_LINEAR
                    )
                    hold_counter = max_hold_frames
                    alpha = refine_person_mask(current_mask)
                    if last_alpha.shape != alpha.shape:
                        last_alpha = cv2.resize(last_alpha, (width, height), interpolation=cv2.INTER_LINEAR)
                    alpha = np.maximum(alpha, last_alpha * 0.7)
                    last_alpha = alpha

                    buf_len = len(buffer)
                    lookback = min(pre_roll_frames, buf_len)
                    for i in range(1, lookback + 1):
                        idx = buf_len - i
                        back_weight = max(0.35, 1.0 - (i / (pre_roll_frames + 1)) * 0.65)
                        prev_f, prev_a = buffer[idx]
                        if prev_a.shape != alpha.shape:
                            prev_a = cv2.resize(prev_a, (width, height), interpolation=cv2.INTER_LINEAR)
                        updated_a = np.maximum(prev_a, alpha * back_weight)
                        buffer[idx] = (prev_f, updated_a)
                elif hold_counter > 0:
                    hold_counter -= 1
                    decay = (hold_counter + 1) / (max_hold_frames + 1)
                    if last_alpha.shape != (height, width):
                        last_alpha = cv2.resize(last_alpha, (width, height), interpolation=cv2.INTER_LINEAR)
                    alpha = last_alpha * decay
                    last_alpha = alpha
                else:
                    alpha = np.zeros((height, width), dtype=np.float32)
                    last_alpha = alpha
            elif hold_counter > 0:
                hold_counter -= 1
                decay = (hold_counter + 1) / (max_hold_frames + 1)
                if last_alpha.shape != (height, width):
                    last_alpha = cv2.resize(last_alpha, (width, height), interpolation=cv2.INTER_LINEAR)
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

        total_pipeline_elapsed = time.perf_counter() - pipeline_start

        if processed_frames_cnt > 0:
            print(
                f"📊 3-Stage Timing over {processed_frames_cnt} frames | "
                f"Stage1(YOLO): {t_stage1_track:.2f}s ({(t_stage1_track/processed_frames_cnt)*1000:.1f}ms/f) | "
                f"Stage2(Gender): {t_stage2_gender:.2f}s | "
                f"Stage3(Blur): {t_stage3_blur:.2f}s ({(t_stage3_blur/processed_frames_cnt)*1000:.1f}ms/f)"
            )

        final_vid = await Vid_Mk(raw_out_path, Aud)
        return final_vid, total_pipeline_elapsed
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
        "👋 أهلاً بك في بوت العزل الاحترافي (نظام 3 مراحل).\nاختر درجة البلور المطلوبة:",
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
            "اختر الجندر المستهدف للبلور (تصويت موزون صارم لتجنب التظليل الخاطئ):",
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

        if cfg['Gender'] != 'all' and mivolo_predictor is None:
            await message.reply_text(
                "⚠️ تنبيه: تعذر تهيئة نموذج MiVOLO؛ سيتم تطبيق البلور على الكل."
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
        import traceback
        traceback.print_exc()
        await replied.edit_text(f'❌ حدث خطأ: {str(e)}')
    finally:
        if upload_succeeded or not os.path.exists(user_dir):
            await Check_Dir(user_dir)
            if os.path.isdir(Base_Dl_Dir) and not os.listdir(Base_Dl_Dir):
                Cleanup_Work_Dir(Base_Dl_Dir)

def main():
    Cleanup_Work_Dir(Base_Dl_Dir)
    bot.start()
    print("✅ Pro Segmentation Bot (3-Stage Pipeline: YOLO -> Weighted Gender -> Blur) is ONLINE!")
    try:
        idle()
    finally:
        bot.stop()
        Cleanup_Work_Dir(Base_Dl_Dir)

if __name__ == '__main__':
    main()
