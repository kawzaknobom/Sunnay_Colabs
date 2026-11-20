import nest_asyncio, os, asyncio, shutil
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

# كاشف وجه خفيف وسريع (YuNet) مع بديل تلقائي للجزء العلوي للرأس/الوجه
YUNET_PATH = os.getenv('YUNET_PATH', 'face_detection_yunet_2023mar.onnx')
yunet_detector = None

def _init_yunet():
    global yunet_detector
    if hasattr(cv2, "FaceDetectorYN") and os.path.exists(YUNET_PATH):
        try:
            yunet_detector = cv2.FaceDetectorYN.create(
                YUNET_PATH, "", (320, 320), score_threshold=0.55, nms_threshold=0.3, top_k=10
            )
            print("✅ YuNet face detector loaded!")
        except Exception as e:
            print(f"⚠️ YuNet init warning: {e}")

_init_yunet()

# النموذج الأول: متخصص في الوجه (يُفحص أولاً)
FACE_MODEL_ID = os.getenv('FACE_MODEL_ID', 'dima806/fairface_gender_image_detection')
# النموذج الثاني: متخصص في الجسد (يُفحص فقط إذا لم يطابق الوجه الجندر المطلوب)
BODY_MODEL_ID = os.getenv('BODY_MODEL_ID', 'NTQAI/pedestrian_gender_recognition')

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
    if os.path.isdir(Dir):
        shutil.rmtree(Dir, ignore_errors=True)

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

def refine_person_mask(combined_mask: np.ndarray, width: int, height: int) -> np.ndarray:
    """توسيع وتنعيم القناع لتقليل الفلتات على الحواف والحركة السريعة."""
    binary = (combined_mask > 0.15).astype(np.uint8) * 255
    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, close_kernel)
    dilated = cv2.dilate(closed, dilate_kernel, iterations=1)
    soft = cv2.GaussianBlur(dilated, (15, 15), 0).astype(np.float32) / 255.0
    return np.clip(soft, 0.0, 1.0)

def extract_body_and_face(frame: np.ndarray, mask_2d: np.ndarray, pad: int = 10):
    """إرجاع قصاصة الجسم الكامل وقصاصة الوجه/الرأس."""
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

    if yunet_detector is not None:
        try:
            yunet_detector.setInputSize((pw, ph))
            _, faces = yunet_detector.detect(body_crop)
            if faces is not None and len(faces) > 0:
                best = max(faces, key=lambda f: f[2] * f[3] * f[14])
                fx, fy, fw, fh = int(best[0]), int(best[1]), int(best[2]), int(best[3])
                pad_x = max(5, int(0.30 * fw))
                pad_top = max(6, int(0.35 * fh))
                pad_bot = max(5, int(0.20 * fh))
                gx1 = max(0, fx - pad_x)
                gy1 = max(0, fy - pad_top)
                gx2 = min(pw, fx + fw + pad_x)
                gy2 = min(ph, fy + fh + pad_bot)
                if gx2 - gx1 >= 16 and gy2 - gy1 >= 16:
                    face_crop = body_crop[gy1:gy2, gx1:gx2]
        except Exception:
            face_crop = None

    if face_crop is None:
        head_h = max(16, int(ph * 0.32))
        head_w = max(16, int(pw * 0.62))
        cx = pw // 2
        gx1 = max(0, cx - head_w // 2)
        gx2 = min(pw, cx + head_w // 2)
        gy2 = min(ph, head_h)
        if gx2 - gx1 >= 16 and gy2 >= 16:
            face_crop = body_crop[0:gy2, gx1:gx2]

    return {"body": body_crop, "face": face_crop}

def _label_to_gender(raw_label: str, idx: int) -> str:
    low = str(raw_label).strip().lower()
    if "female" in low or low in ("f", "woman", "women", "girl", "1"):
        return "female"
    if "male" in low or low in ("m", "man", "men", "boy", "0"):
        return "male"
    return "female" if idx == 1 else "male"

def _predict_single_model(crops: list, mdl, proc, tag: str) -> list:
    """تشغيل نموذج واحد على قائمة صور وإرجاع قائمة تسميات ('male' / 'female' / 'unknown')."""
    if mdl is None or proc is None:
        return ["unknown"] * len(crops)

    valid_indices = []
    pil_images = []
    for i, c in enumerate(crops):
        if c is not None and getattr(c, "size", 0) > 0:
            valid_indices.append(i)
            pil_images.append(Image.fromarray(cv2.cvtColor(c, cv2.COLOR_BGR2RGB)))

    out_labels = ["unknown"] * len(crops)
    if not pil_images:
        return out_labels

    try:
        inputs = proc(images=pil_images, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.inference_mode():
            outputs = mdl(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()
    except Exception as e:
        print(f"⚠️ {tag} inference error: {e}")
        return out_labels

    id2label = getattr(mdl.config, "id2label", {}) or {}
    female_cols = [i for i in range(probs.shape[1]) if _label_to_gender(id2label.get(i, str(i)), i) == "female"]
    male_cols = [i for i in range(probs.shape[1]) if _label_to_gender(id2label.get(i, str(i)), i) == "male"]

    for row_idx, orig_idx in enumerate(valid_indices):
        row = probs[row_idx]
        f_score = float(row[female_cols].sum()) if female_cols else 0.0
        m_score = float(row[male_cols].sum()) if male_cols else 0.0
        out_labels[orig_idx] = "female" if f_score >= m_score else "male"

    return out_labels

def classify_sequential_with_early_exit(samples: list, target_gender: str) -> list:
    """
    يفحص الوجه أولاً:
    - إذا أعطى الجندر المطلوب (مثلاً female) -> يتوقف فوراً ولا يشغّل نموذج الجسد.
    - إذا لم يعطِ الجندر المطلوب -> يشغّل نموذج الجسد؛ فإن أعطى المطلوب يعتمدة فوراً، وإلا يأخذ نتيجته.
    """
    if not samples:
        return []

    face_crops = [s.get("face") for s in samples]
    face_preds = _predict_single_model(face_crops, face_model, face_processor, "FaceModel")

    final_preds = list(face_preds)
    need_body_indices = []
    need_body_crops = []

    for i, f_lbl in enumerate(face_preds):
        if target_gender in ("female", "male"):
            if f_lbl == target_gender:
                print(f"⚡ Early-exit [Face={f_lbl}] -> {target_gender} (skip BodyModel)")
                continue
        else:
            if f_lbl != "unknown":
                continue

        b_crop = samples[i].get("body")
        if b_crop is not None and getattr(b_crop, "size", 0) > 0 and body_model is not None:
            need_body_indices.append(i)
            need_body_crops.append(b_crop)

    if need_body_crops:
        body_preds = _predict_single_model(need_body_crops, body_model, body_processor, "BodyModel")
        for idx, b_lbl in zip(need_body_indices, body_preds):
            f_lbl = face_preds[idx]
            if b_lbl != "unknown":
                final_preds[idx] = b_lbl
            elif f_lbl == "unknown":
                final_preds[idx] = "unknown"
            print(f"🔁 Fallback [Face={f_lbl} -> Body={b_lbl}] -> Final={final_preds[idx]}")

    return final_preds

async def Process_Video_Pro_Segmentation(file_path, replied, BlurRate, isfull, Ranges, gender_filter="all"):
    ksize = odd_blur_size(BlurRate)
    base_no_ext, _ = os.path.splitext(file_path)
    raw_out_path = f"{base_no_ext}_RawBlur.mp4"

    Aud = None
    try:
        Aud = await Mp3_Conv(file_path)
    except Exception:
        Aud = None

    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        raise ValueError("تعذر فتح ملف الفيديو.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 1:
        fps = 25.0
    progress_step = max(1, int(round(fps)))

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration_sec = total_frames / fps if total_frames > 0 else 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(raw_out_path, fourcc, fps, (width, height))

    ranges = []
    if not isfull and Ranges:
        for rng in Ranges.strip().split():
            if '-' in rng:
                s_str, e_str = rng.split('-', 1)
                start_f = int(await get_seconds(s_str) * fps)
                end_f = int(await get_seconds(e_str) * fps)
                if end_f >= start_f:
                    ranges.append((start_f, end_f))

    pre_roll_frames = max(4, int(round(fps * 0.25)))
    max_hold_frames = max(4, int(round(fps * 0.25)))

    last_alpha = np.zeros((height, width), dtype=np.float32)
    hold_counter = 0
    buffer = []

    track_gender_cache = {}
    recheck_interval = max(3, int(round(fps * 0.20)))
    any_gender_model_ready = (face_model is not None) or (body_model is not None)
    use_gender_filter = (gender_filter in ("male", "female")) and any_gender_model_ready

    def write_buffered_item(item):
        buf_frame, buf_alpha = item
        if np.any(buf_alpha > 0.01):
            blurred_frame = cv2.blur(buf_frame, (ksize, ksize))
            alpha_3c = buf_alpha[:, :, None]
            merged = (blurred_frame * alpha_3c + buf_frame * (1.0 - alpha_3c)).astype(np.uint8)
            out.write(merged)
        else:
            out.write(buf_frame)

    ret_num = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        ret_num += 1

        ispermit = True
        if not isfull:
            ispermit = any(start_f <= ret_num <= end_f for start_f, end_f in ranges)

        if ret_num % progress_step == 0 and duration_sec > 0:
            cur_sec = min(int(ret_num / fps), int(duration_sec))
            try:
                await replied.edit_text(f"🎬 جاري المعالجة... {cur_sec} من {int(duration_sec)} ثانية")
            except Exception:
                pass

        if ispermit:
            results = model.track(
                frame,
                persist=True,
                classes=[0],
                conf=0.28,
                iou=0.45,
                imgsz=640,
                retina_masks=True,
                tracker="bytetrack.yaml",
                verbose=False
            )

            current_mask = np.zeros((height, width), dtype=np.float32)
            if results and results[0].masks is not None:
                masks = results[0].masks.data.cpu().numpy()
                resized_masks = []
                for m in masks:
                    if m.shape != (height, width):
                        m = cv2.resize(m, (width, height), interpolation=cv2.INTER_LINEAR)
                    resized_masks.append(m.astype(np.float32))

                if use_gender_filter:
                    boxes = results[0].boxes
                    raw_ids = boxes.id.int().cpu().tolist() if (boxes is not None and boxes.id is not None) else []
                    track_ids = [raw_ids[i] if i < len(raw_ids) else None for i in range(len(resized_masks))]

                    mask_genders = ["unknown"] * len(resized_masks)
                    pending_indices = []
                    pending_samples = []

                    for idx, m in enumerate(resized_masks):
                        tid = track_ids[idx]
                        if tid is not None and tid in track_gender_cache:
                            mask_genders[idx] = track_gender_cache[tid]
                            if track_gender_cache[tid] != gender_filter and (ret_num % recheck_interval == 0):
                                sample = extract_body_and_face(frame, m)
                                if sample is not None:
                                    pending_indices.append(idx)
                                    pending_samples.append(sample)
                        else:
                            sample = extract_body_and_face(frame, m)
                            if sample is not None:
                                pending_indices.append(idx)
                                pending_samples.append(sample)

                    if pending_samples:
                        batch_preds = classify_sequential_with_early_exit(pending_samples, gender_filter)
                        for p_idx, g_label in zip(pending_indices, batch_preds):
                            mask_genders[p_idx] = g_label
                            tid = track_ids[p_idx]
                            if tid is not None:
                                if g_label == gender_filter or track_gender_cache.get(tid) != gender_filter:
                                    track_gender_cache[tid] = g_label
                            if g_label == gender_filter:
                                print(f"✅ Match at frame {ret_num} | tid={tid} -> {g_label}")

                    for idx, m in enumerate(resized_masks):
                        if mask_genders[idx] == gender_filter:
                            current_mask = np.maximum(current_mask, m)
                else:
                    for m in resized_masks:
                        current_mask = np.maximum(current_mask, m)

            if np.any(current_mask > 0.15):
                hold_counter = max_hold_frames
                alpha = refine_person_mask(current_mask, width, height)
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
        else:
            alpha = np.zeros((height, width), dtype=np.float32)
            last_alpha = alpha
            hold_counter = 0

        buffer.append((frame, alpha))

        while len(buffer) > pre_roll_frames + 1:
            write_buffered_item(buffer.pop(0))

    while buffer:
        write_buffered_item(buffer.pop(0))

    cap.release()
    out.release()

    final_vid = await Vid_Mk(raw_out_path, Aud)
    return final_vid

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
            "اختر الجندر المستهدف للبلور (الوجه أولاً ثم الجسد عند الحاجة):",
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

    try:
        vid_path = await message.download(file_name=os.path.join(user_dir, ""))
        blurred_vid = await Process_Video_Pro_Segmentation(
            vid_path,
            replied,
            cfg['BlurRate'],
            cfg['isfull'],
            cfg['Ranges'],
            cfg.get('Gender', 'all')
        )
        await replied.edit_text('✅ تمت العملية باحترافية تامة!')
        await message.reply_video(blurred_vid)
    except Exception as e:
        await replied.edit_text(f'❌ حدث خطأ: {str(e)}')
    finally:
        await Check_Dir(user_dir)

def main():
    os.makedirs(Base_Dl_Dir, exist_ok=True)
    bot.start()
    print("✅ Pro Segmentation Bot with Sequential Face->Body Early-Exit is ONLINE!")
    idle()
    bot.stop()

if __name__ == '__main__':
    main()