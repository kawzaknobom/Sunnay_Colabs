import nest_asyncio, os, asyncio, shutil
nest_asyncio.apply()

Bot_Token = os.getenv('TOKEN')

from pyrogram import Client, filters, idle
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton
import cv2, numpy as np
from ultralytics import YOLO

# تحميل نموذج تجزئة الأنمي المخصص
model = YOLO('Anime-yolov8-seg.pt')

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'
Audio_Forms = (".mp3", ".ogg", ".m4a", ".aac", ".flac", ".wav", ".wma", ".opus", ".3gpp")

Settings_Dict = {}
Base_Dl_Dir = './AnimeSeg_Work'

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
        Bot_Identifier + '_session_anime_seg_bot',
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

def refine_anime_mask(combined_mask: np.ndarray) -> np.ndarray:
    """توسيع وتنعيم القناع لتغطية الشعر والأطراف والحركة السريعة في الأنمي."""
    binary = (combined_mask > 0.22).astype(np.uint8) * 255
    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))
    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (35, 35))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, close_kernel)
    dilated = cv2.dilate(closed, dilate_kernel, iterations=1)
    soft = cv2.GaussianBlur(dilated, (17, 17), 0).astype(np.float32) / 255.0
    return np.clip(soft, 0.0, 1.0)

async def Process_Video_Pro_Segmentation(file_path, replied, BlurRate, isfull, Ranges):
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
        fps = 24.0
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

    # عدد الفريمات التي نرجع للخلف لتغطيتها قبل ظهور الشخصية (~0.25 ثانية)
    pre_roll_frames = max(4, int(round(fps * 0.25)))
    # عدد الفريمات التي نحتفظ فيها بالقناع بعد اختفائه مؤقتاً (~0.25 ثانية)
    max_hold_frames = max(4, int(round(fps * 0.25)))

    last_alpha = np.zeros((height, width), dtype=np.float32)
    hold_counter = 0
    buffer = []

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
                await replied.edit_text(f"🎬 جاري المعالجة باستخدام نموذج الأنمي... {cur_sec} من {int(duration_sec)} ثانية")
            except Exception:
                pass

        if ispermit:
            results = model.track(
                frame,
                persist=True,
                conf=0.28,
                iou=0.5,
                imgsz=640,
                retina_masks=True,
                tracker="bytetrack.yaml",
                verbose=False
            )

            current_mask = np.zeros((height, width), dtype=np.float32)
            if results and results[0].masks is not None:
                masks = results[0].masks.data.cpu().numpy()
                for m in masks:
                    if m.shape != (height, width):
                        m = cv2.resize(m, (width, height), interpolation=cv2.INTER_LINEAR)
                    current_mask = np.maximum(current_mask, m)

            if np.any(current_mask > 0.22):
                hold_counter = max_hold_frames
                alpha = refine_anime_mask(current_mask)
                alpha = np.maximum(alpha, last_alpha * 0.7)
                last_alpha = alpha

                # توسيع القناع للخلف على الفريمات السابقة في الـ buffer لتفادي ظهور بداية الدخول
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
        Settings_Dict[user_id] = {'BlurRate': '', 'isfull': True, 'Ranges': ''}
    return Settings_Dict[user_id]

@bot.on_message(filters.command('start') & filters.private)
async def command_start(client, message):
    user_id = message.from_user.id
    Settings_Dict[user_id] = {'BlurRate': '', 'isfull': True, 'Ranges': ''}
    await message.reply_text(
        "👋 أهلاً بك في بوت عزل الأنمي الاحترافي.\nاختر درجة البلور المطلوبة:",
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
        await message.reply_text("⚠️ يرجى اختيار درجة البلور أو نمط المعالجة الصحيح من الأزرار.")

@bot.on_message(filters.private & filters.incoming & filters.video)
async def _video_handler(client, message):
    user_id = message.from_user.id
    cfg = get_user_cfg(user_id)
    if not cfg['BlurRate']:
        await message.reply_text('⚠️ يرجى إعادة ضبط الإعدادات بالضغط على: /start')
        return

    user_dir = os.path.join(Base_Dl_Dir, f"{Bot_Identifier}_{user_id}")
    await Create_Dir(user_dir)
    replied = await message.reply_text('🚀 جاري تحميل الفيديو ومعالجة شخصيات الأنمي بدقة واحترافية...')

    try:
        vid_path = await message.download(file_name=os.path.join(user_dir, ""))
        blurred_vid = await Process_Video_Pro_Segmentation(
            vid_path, replied, cfg['BlurRate'], cfg['isfull'], cfg['Ranges']
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
    print("✅ Anime Segmentation Bot with Model is ONLINE!")
    idle()
    bot.stop()

if __name__ == '__main__':
    main()