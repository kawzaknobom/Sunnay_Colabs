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
MAX_SAMPLES_PER_TRACK = int(os.getenv('MAX_SAMPLES_PER_TRACK', '8'))
MIN_CONFIRM_VOTES = int(os.getenv('MIN_CONFIRM_VOTES', '3'))

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
        mivolo_predictor = None
        mivolo_init_error = str(e)
        print(f"⚠️ MiVOLO init error: {mivolo_init_error}")
    finally:
        if prev_flag is None:
            os.environ.pop('TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD', None)
        else:
            os.environ['TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD'] = prev_flag

_init_mivolo()

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
    (يكتشف الوجه والجسد بنفسه داخلها)، وتُرتَّب العينات حسب مساحة القصاصة.
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

    return {
        "body": frame[y1:y2, x1:x2].copy(),  # نسخة حتى لا يبقى الإطار الكامل محجوزاً في الذاكرة
        "quality_score": float(pw * ph),
    }

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
            if g not in ("male", "female") or s is None:
                continue
            item = (tuple(float(v) for v in xyxy[i]), g, float(s))
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
    حسم قرار المسار بعد تجميع وتصنيف كل عينات هذا الشخص عبر الفيديو.
    """
    f_votes = v["female_votes"]
    m_votes = v["male_votes"]
    f_weight = v["female_weight"]
    m_weight = v["male_weight"]

    if target_gender == "female":
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

        use_gender_filter = (gender_filter in ("male", "female")) and (mivolo_predictor is not None)

        # =====================================================================
        # المرحلة 1/3: استخراج جميع الـ Objects وتتبّعها وحفظ الأقنعة + القصاصات
        # =====================================================================
        frame_records = {}
        collected_samples = {}       # tid -> list of sample dicts
        last_sample_frame = {}       # tid -> last frame index sampled
        sample_interval_frames = max(1, int(round(fps * SAMPLE_INTERVAL_SEC)))

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
                try:
                    await replied.edit_text(
                        f"🔍 المرحلة 1/3 (استخراج وتتبع الـ Objects)... `{fmt_clock(cur_sec)}-{fmt_clock(duration_sec)}`"
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
            t_stage1_track += time.perf_counter() - t0_track

            if results and results[0].masks is not None:
                masks = results[0].masks.data.cpu().numpy()
                boxes = results[0].boxes
                raw_ids = boxes.id.int().cpu().tolist() if (boxes is not None and boxes.id is not None) else []

                records_this_frame = []
                for idx, m in enumerate(masks):
                    tid = raw_ids[idx] if idx < len(raw_ids) else -1
                    bin_mask = (m > 0.30).astype(np.uint8)
                    records_this_frame.append((tid, bin_mask))

                    if use_gender_filter:
                        last_f = last_sample_frame.get(tid, -999999)
                        if (ret_num - last_f) >= sample_interval_frames:
                            full_m = cv2.resize(
                                bin_mask.astype(np.float32),
                                (width, height),
                                interpolation=cv2.INTER_NEAREST
                            )
                            sample = extract_body_crop(frame, full_m)
                            if sample is not None:
                                sample["frame_num"] = ret_num
                                sample["sec"] = round(ret_num / fps, 2)
                                track_list = collected_samples.setdefault(tid, [])
                                track_list.append(sample)
                                # الاحتفاظ بأعلى MAX_SAMPLES_PER_TRACK عينة جودة (الأولوية للقصاصات الأكبر مساحة)
                                if len(track_list) > MAX_SAMPLES_PER_TRACK:
                                    track_list.sort(key=lambda x: x["quality_score"], reverse=True)
                                    del track_list[MAX_SAMPLES_PER_TRACK:]
                                last_sample_frame[tid] = ret_num

                frame_records[ret_num] = records_this_frame

        # =====================================================================
        # المرحلة 2/3: فحص الجندر للـ Objects المستخرجة عبر النماذج الموزونة
        # =====================================================================
        track_votes = {}
        approved_tids = set()
        sample_logs = []

        if use_gender_filter:
            try:
                await replied.edit_text(
                    f"🧠 المرحلة 2/3 (فحص الجندر بدقة لـ {len(collected_samples)} شخص/مسار)..."
                )
            except Exception:
                pass

            t0_gender = time.perf_counter()

            # تجميع كل العينات المختارة لكل المسارات لتشغيلها دفعة واحدة (Batch) بأعلى سرعة ودقة
            flat_tids = []
            flat_samples = []
            for tid, s_list in collected_samples.items():
                track_votes[tid] = {
                    "female_votes": 0,
                    "male_votes": 0,
                    "female_weight": 0.0,
                    "male_weight": 0.0,
                    "strong_face_female": False,
                    "strong_face_male": False,
                    "samples": 0,
                    "decided": False,
                    "resolved_gender": None,
                    "decision_reason": None
                }
                # ترتيب عينات المسار زمنياً لوضوح السجل
                s_list.sort(key=lambda x: x["frame_num"])
                for s in s_list:
                    flat_tids.append(tid)
                    flat_samples.append(s)

            if flat_samples:
                batch_preds, batch_dbg = classify_samples_mivolo(flat_samples)

                for tid, sample_obj, (g_label, g_conf, is_strong_face), dbg in zip(
                    flat_tids, flat_samples, batch_preds, batch_dbg
                ):
                    v = track_votes[tid]
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
                        f"tid={tid} f={sample_obj['frame_num']}({sample_obj['sec']}s) "
                        f"s#{v['samples']}/{len(collected_samples[tid])} "
                        f"src={dbg['src']} MV={dbg['mv']} -> {g_label}:{g_conf:.2f} "
                        f"W=(F:{v['female_weight']:.2f}, M:{v['male_weight']:.2f})"
                    )
                    sample_logs.append(entry)
                    print(f"🧪 [STAGE2_SAMPLE] {entry}")

            # حسم القرار النهائي لكل مسار بناءً على كامل عيناته عبر الفيديو
            for tid, v in track_votes.items():
                _finalize_track_decision(v, gender_filter)
                if v["resolved_gender"] == gender_filter:
                    approved_tids.add(tid)
                print(
                    f"⏹️ [STAGE2_DECISION] tid={tid} target={gender_filter} "
                    f"samples={v['samples']}/{MAX_SAMPLES_PER_TRACK} "
                    f"W=(F:{v['female_weight']:.2f}, M:{v['male_weight']:.2f}) -> {v['resolved_gender']} "
                    f"[{v['decision_reason']}, approved={tid in approved_tids}]"
                )

            t_stage2_gender = time.perf_counter() - t0_gender
            print(f"⚡ Stage 2 Approved ({gender_filter}): {sorted(approved_tids)} | Total samples: {len(sample_logs)}")

            # تحرير قصاصات الصور من الذاكرة قبل بدء المرحلة الثالثة
            collected_samples.clear()

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

            if ret_num % progress_step == 0 and duration_sec > 0:
                cur_sec = min(ret_num / fps, duration_sec)
                try:
                    await replied.edit_text(
                        f"🎬 المرحلة 3/3 (تطبيق البلور)... `{fmt_clock(cur_sec)}-{fmt_clock(duration_sec)}`"
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