import nest_asyncio, os, asyncio, gc, time
nest_asyncio.apply()

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

#########################################################

Bot_Token = os.getenv('TOKEN')
Admin_Id = int(os.getenv('Admin_Id', '0'))

FASIH_TTS_REPO = os.getenv('FASIH_TTS_REPO', 'NightPrince/Fasih-TTS-V1').strip()
FASIH_LANGUAGE = os.getenv('FASIH_LANGUAGE', 'ar').strip()
FASIH_TEMPERATURE = float(os.getenv('FASIH_TEMPERATURE', '0.65'))
FASIH_REP_PENALTY = float(os.getenv('FASIH_REP_PENALTY', '2.0'))
FASIH_SPLIT_TEXT = os.getenv('FASIH_SPLIT_TEXT', '0').strip() == '1'
FASIH_SAMPLE_RATE = int(os.getenv('FASIH_SAMPLE_RATE', '24000'))
MP3_BITRATE = os.getenv('MP3_BITRATE', '192k').strip()
USE_REPO_REF_ALWAYS = os.getenv('USE_REPO_REF_ALWAYS', '1').strip() == '1'
HF_TOKEN = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_HUB_TOKEN') or None

########################################################

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ForceReply, Message
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, MessageTooLong
from pyrogram import idle

import torch
import numpy as np
import soundfile as sf
from huggingface_hub import snapshot_download
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'

Global_Main_Queue = []
Public_Loop = False

User_Voice_Samples = {}
User_Sample_Msg_Ids = {}

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def load_fasih_tts(repo_id: str, device: str, token=None):
    """تحميل نموذج Fasih-TTS-V1 وملف speaker_latents.pt."""
    model_dir = snapshot_download(repo_id=repo_id, token=token)
    config = XttsConfig()
    config.load_json(f"{model_dir}/config.json")

    model = Xtts.init_from_config(config)
    model.load_checkpoint(
        config,
        checkpoint_path=f"{model_dir}/model.pth",
        vocab_path=f"{model_dir}/vocab.json",
        use_deepspeed=False,
    )
    model.to(device).eval()

    latents = torch.load(f"{model_dir}/speaker_latents.pt", map_location=device)
    return model, latents


print(f"🔄 جاري تحميل نموذج {FASIH_TTS_REPO} على: {DEVICE}...")
FASIH_MODEL, FASIH_LATENTS = load_fasih_tts(FASIH_TTS_REPO, DEVICE, token=HF_TOKEN)
print("✅ تم تحميل نموذج Fasih-TTS-V1 بنجاح!")


async def run_command(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode(), stderr.decode()


async def convert_sample_to_wav(input_audio_path, output_wav_path):
    """تحويل العينة الصوتية إلى WAV نظيف (24kHz mono)."""
    cmd = f'ffmpeg -i "{input_audio_path}" -ac 1 -ar 24000 -sample_fmt s16 "{output_wav_path}" -y'
    await run_command(cmd)
    return os.path.exists(output_wav_path) and os.path.getsize(output_wav_path) > 0


async def convert_wav_to_mp3(input_wav_path: str, output_mp3_path: str, bitrate: str = "192k") -> bool:
    """تحويل ملف WAV الناتج إلى صيغة MP3 قبل الإرسال."""
    cmd = f'ffmpeg -i "{input_wav_path}" -codec:a libmp3lame -b:a {bitrate} -ar {FASIH_SAMPLE_RATE} "{output_mp3_path}" -y'
    _, stderr = await run_command(cmd)
    if not (os.path.exists(output_mp3_path) and os.path.getsize(output_mp3_path) > 0):
        raise RuntimeError(f"فشل تحويل الصوت إلى MP3: {stderr.strip()}")
    return True


def synthesize_fasih_sync(text: str, speaker_wav_path: str, output_wav_path: str) -> str:
    """توليد الصوت عبر Fasih-TTS-V1 وحفظه كملف WAV بمعدل 24kHz."""
    abs_output_wav = os.path.abspath(output_wav_path)
    base_dir = os.path.dirname(abs_output_wav)
    os.makedirs(base_dir, exist_ok=True)

    clean_text = " ".join(text.split()).strip()
    if not clean_text:
        raise ValueError("النص فارغ بعد التنظيف.")

    if not USE_REPO_REF_ALWAYS and speaker_wav_path and os.path.exists(speaker_wav_path):
        gpt_cond_latent, speaker_embedding = FASIH_MODEL.get_conditioning_latents(
            audio_path=[os.path.abspath(speaker_wav_path)]
        )
    else:
        gpt_cond_latent = FASIH_LATENTS["gpt_cond_latent"]
        speaker_embedding = FASIH_LATENTS["speaker_embedding"]

    with torch.inference_mode():
        out = FASIH_MODEL.inference(
            clean_text,
            FASIH_LANGUAGE,
            gpt_cond_latent,
            speaker_embedding,
            temperature=FASIH_TEMPERATURE,
            repetition_penalty=FASIH_REP_PENALTY,
            enable_text_splitting=FASIH_SPLIT_TEXT,
        )

    raw_wav = out["wav"]
    if hasattr(raw_wav, "detach"):
        raw_wav = raw_wav.detach().cpu().numpy()
    elif hasattr(raw_wav, "cpu"):
        raw_wav = raw_wav.cpu().numpy()

    wave_np = np.squeeze(np.asarray(raw_wav, dtype=np.float32))
    if wave_np.size == 0 or np.isnan(wave_np).any() or np.isinf(wave_np).any():
        raise RuntimeError("النموذج أخرج موجة صوتية فارغة أو تحتوي على قيم NaN/Inf.")

    peak = float(np.max(np.abs(wave_np)))
    if peak > 1.0:
        wave_np = wave_np / peak * 0.95

    sf.write(abs_output_wav, wave_np, samplerate=FASIH_SAMPLE_RATE)
    return abs_output_wav


def Pyrogram_Client(Bot_Token):
    Bot_Identifier = Bot_Token.split(':')[0]
    Session_file = Bot_Identifier + '_955hyh95|session_prm_bot'
    bot = Client(Session_file, api_id=Api_Id, api_hash=Api_Hash, bot_token=Bot_Token, in_memory=True)
    return bot, Bot_Identifier


bot, Bot_Identifier = Pyrogram_Client(Bot_Token)
dl_path = f'./downloads_{Bot_Identifier}/'

# ==================== نظام الـ Global List Loop ==================== #

def Item_add(Item):
    global Global_Main_Queue, Public_Loop
    Global_Main_Queue.append(Item)
    if not Public_Loop:
        Public_Loop = True
        asyncio.create_task(Multi_loop_async())


async def Multi_loop_async():
    global Global_Main_Queue, Public_Loop
    Public_Loop = True

    while len(Global_Main_Queue) > 0:
        for elem in range(1, len(Global_Main_Queue)):
            try:
                A_Reply_List = Global_Main_Queue[elem].split('_')
                A_rp_msg_id = int(A_Reply_List[-2])
                A_user_id = int(A_Reply_List[-1])
                A_reply = await bot.get_messages(A_user_id, A_rp_msg_id)
                await A_reply.edit_text(f"تمت الإضافة للصف \n\n ترتيبك هو {elem} ☕ ")
            except Exception:
                pass

        C_Process = Global_Main_Queue[0]
        msg_list = C_Process.split('_')
        text_msg_id = int(msg_list[1])
        sample_msg_id = int(msg_list[2])
        rp_msg_id = int(msg_list[-2])
        user_id = int(msg_list[-1])

        reply_msg = await bot.get_messages(user_id, rp_msg_id)
        text_msg = await bot.get_messages(user_id, text_msg_id)

        try:
            try:
                await reply_msg.edit_text("جارِ توليد الصوت عبر Fasih-TTS-V1 الآن ☕...")
            except Exception:
                reply_msg = await text_msg.reply("جارِ العمل ☕", reply_to_message_id=text_msg.id)

            speaker_wav = User_Voice_Samples.get(user_id)
            if not USE_REPO_REF_ALWAYS and (not speaker_wav or not os.path.exists(speaker_wav)):
                sample_msg = await bot.get_messages(user_id, sample_msg_id)
                if sample_msg and (sample_msg.voice or sample_msg.audio):
                    task_dir = f'./tts_work_{user_id}_{text_msg_id}_{Bot_Identifier}/'
                    os.makedirs(task_dir, exist_ok=True)
                    raw_dl = await sample_msg.download(file_name=task_dir)
                    restored_wav = os.path.join(task_dir, "restored_ref.wav")
                    await convert_sample_to_wav(raw_dl, restored_wav)
                    speaker_wav = restored_wav
                    User_Voice_Samples[user_id] = speaker_wav
                else:
                    raise ValueError("لم يتم العثور على عينة صوتية صالحة. أرسل عينة صوتية أولاً.")

            input_text = (text_msg.text or "").strip()
            if not input_text:
                raise ValueError("الرسالة النصية فارغة.")

            task_dl_path = f'./tts_work_{user_id}_{text_msg_id}_{Bot_Identifier}/'
            os.makedirs(task_dl_path, exist_ok=True)

            output_wav_path = os.path.join(task_dl_path, f"fasih_ar_{text_msg_id}.wav")
            output_mp3_path = os.path.join(task_dl_path, f"fasih_ar_{text_msg_id}.mp3")

            await reply_msg.edit_text("🎙️ جارِ تحويل النص إلى صوت...")
            await asyncio.to_thread(
                synthesize_fasih_sync,
                input_text,
                speaker_wav or "",
                output_wav_path
            )

            if not os.path.exists(output_wav_path) or os.path.getsize(output_wav_path) == 0:
                raise RuntimeError("فشل إنشاء الملف الصوتي الناتج.")

            await reply_msg.edit_text("🔄 جارِ تحويل المقطع إلى صيغة MP3...")
            await convert_wav_to_mp3(output_wav_path, output_mp3_path, bitrate=MP3_BITRATE)

            await reply_msg.edit_text("📤 جارِ إرسال ملف MP3...")
            await text_msg.reply_audio(
                output_mp3_path,
                caption="✅ تم توليد الصوت وتحويله إلى MP3 بنجاح"
            )

            for temp_file in (output_wav_path, output_mp3_path):
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            try:
                os.rmdir(task_dl_path)
            except OSError:
                pass

            await reply_msg.edit_text('تمت العملية بنجاح ☑️')

        except Exception as err:
            err_text = str(err)[:3000]
            try:
                await reply_msg.edit_text(f"حدث خطأ أثناء المعالجة:\n`{err_text}`")
            except Exception:
                pass

        Global_Main_Queue.pop(0)

    gc.collect()
    if DEVICE == "cuda":
        torch.cuda.empty_cache()
    Public_Loop = False

# ==================================================================== #

@bot.on_message(filters.command('start') & filters.private)
async def start_cmd(client, message):
    await message.reply(
        "أهلاً بك في بوت تحويل النص إلى صوت (Fasih-TTS-V1) 🎙️\n\n"
        "أرسل **النص** العربي المشكول الذي تريد تحويله إلى صوت.\n\n"
        "لبقية البوتات \n\n @sunnaybots"
    )

@bot.on_message(filters.private & filters.incoming & (filters.voice | filters.audio))
async def receive_voice_sample(client, message):
    user_id = message.from_user.id
    status_msg = await message.reply("⏳ جارِ استقبال وتجهيز العينة الصوتية...")

    try:
        samples_dir = os.path.join(dl_path, "samples", str(user_id))
        os.makedirs(samples_dir, exist_ok=True)

        downloaded_file = await message.download(file_name=samples_dir + "/")
        clean_wav_path = os.path.join(samples_dir, "reference_voice.wav")

        ok = await convert_sample_to_wav(downloaded_file, clean_wav_path)
        if os.path.exists(downloaded_file) and downloaded_file != clean_wav_path:
            os.remove(downloaded_file)

        if not ok:
            await status_msg.edit_text("❌ تعذر تحويل العينة الصوتية.")
            return

        User_Voice_Samples[user_id] = clean_wav_path
        User_Sample_Msg_Ids[user_id] = message.id

        await status_msg.edit_text(
            "✅ تم حفظ العينة الصوتية.\n"
            "أرسل الآن **النص** المشكول الذي تريد تحويله إلى صوت."
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ حدث خطأ أثناء حفظ العينة:\n`{str(e)[:1000]}`")

@bot.on_message(filters.private & filters.incoming & filters.text & ~filters.command(['start']))
async def receive_text_for_tts(client, message):
    global Global_Main_Queue
    user_id = message.from_user.id

    if not USE_REPO_REF_ALWAYS and (user_id not in User_Voice_Samples or not os.path.exists(User_Voice_Samples[user_id])):
        await message.reply("⚠️ أرسل عينة صوتية أولاً ثم أرسل النص.")
        return

    replied = await message.reply(f"تمت الإضافة لصف الانتظار ☕\nترتيبك في القائمة: {len(Global_Main_Queue) + 1}")
    sample_msg_id = User_Sample_Msg_Ids.get(user_id, 0)
    Item = f"TTS_{message.id}_{sample_msg_id}_{replied.id}_{user_id}"
    Item_add(Item)

async def start_bot_async():
    if not os.path.exists(dl_path):
        os.makedirs(dl_path)
    try:
        await bot.start()
        if Admin_Id != 0:
            await bot.send_message(Admin_Id, 'Fasih-TTS-V1 Bot Started ✅')
        print("✅ Fasih-TTS-V1 Bot (Global List Loop) is ONLINE!")
        await idle()
    finally:
        if bot.is_connected:
            await bot.stop()

if __name__ == '__main__':
    asyncio.run(start_bot_async())