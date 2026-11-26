import nest_asyncio, os, asyncio, gc, time
nest_asyncio.apply()

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

#########################################################

Bot_Token = os.getenv('TOKEN')
Admin_Id = int(os.getenv('Admin_Id', '0'))

F5_ARABIC_REPO = os.getenv('F5_ARABIC_REPO', 'IbrahimSalah/Arabic-F5-TTS-v2').strip()
F5_ARABIC_CKPT = os.getenv('F5_ARABIC_CKPT', 'model_547500_8_18.pt').strip()
F5_ARABIC_VOCAB = os.getenv('F5_ARABIC_VOCAB', 'vocab.txt').strip()
F5_ARABIC_CFG = os.getenv('F5_ARABIC_CFG', 'F5TTS_Base_8_18.yaml').strip()
F5_REPO_REF_WAV = os.getenv('F5_REPO_REF_WAV', 'reference.wav').strip()

DEFAULT_REF_TEXT = (
    "لَا يَمُرُّ يَوْمٌ إِلَّا وَأَسْتَقْبِلُ عِدَّةَ رَسَائِلَ، "
    "تَتَضَمَّنُ أَسْئِلَةً مُلِحَّةْ."
)
NFE_STEP = int(os.getenv('F5_NFE_STEP', '64'))
CFG_STRENGTH = float(os.getenv('F5_CFG_STRENGTH', '2.5'))
TTS_SPEED = float(os.getenv('F5_SPEED', '0.9'))
USE_REPO_REF_ALWAYS = os.getenv('USE_REPO_REF_ALWAYS', '1').strip() == '1'
HF_TOKEN = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_HUB_TOKEN') or None

########################################################

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ForceReply, Message
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, MessageTooLong
from pyrogram import idle

import yaml
import torch
import numpy as np
import soundfile as sf
from huggingface_hub import hf_hub_download
from f5_tts.infer.utils_infer import (
    load_model,
    load_vocoder,
    infer_process,
    preprocess_ref_audio_text,
)
from f5_tts.model import DiT

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'

Global_Main_Queue = []
Public_Loop = False

User_Voice_Samples = {}
User_Sample_Msg_Ids = {}

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def load_arabic_f5_tts(
    repo_id: str,
    device: str,
    ckpt_filename: str,
    vocab_filename: str,
    cfg_filename: str,
    ref_wav_filename: str,
    token=None,
):
    """تحميل ملفات Arabic-F5-TTS-v2 والـ Vocoder والنموذج."""
    vocab_file_path = hf_hub_download(repo_id=repo_id, filename=vocab_filename, token=token)
    ckpt_file_path = hf_hub_download(repo_id=repo_id, filename=ckpt_filename, token=token)
    config_file_path = hf_hub_download(repo_id=repo_id, filename=cfg_filename, token=token)
    repo_ref_wav_path = hf_hub_download(repo_id=repo_id, filename=ref_wav_filename, token=token)

    with open(config_file_path, "r", encoding="utf-8") as f:
        loaded_yaml = yaml.safe_load(f) or {}

    model_cfg = dict(
        dim=1024,
        depth=22,
        heads=18,
        ff_mult=2,
        text_dim=512,
        conv_layers=8,
    )
    mel_spec_type = "vocos"

    model_section = loaded_yaml.get("model", {})
    if isinstance(model_section, dict):
        mel_spec_type = model_section.get("mel_spec", {}).get("mel_spec_type", mel_spec_type)
        arch = model_section.get("arch", {})
        if isinstance(arch, dict) and arch:
            model_cfg.update({
                k: v for k, v in arch.items()
                if k in ("dim", "depth", "heads", "ff_mult", "text_dim", "conv_layers")
            })

    vocoder = load_vocoder(is_local=False, device=device)
    ema_model = load_model(
        DiT,
        model_cfg,
        ckpt_path=ckpt_file_path,
        mel_spec_type=mel_spec_type,
        vocab_file=vocab_file_path,
        device=device,
    )
    return ema_model, vocoder, mel_spec_type, repo_ref_wav_path


print(f"🔄 جاري تحميل نموذج {F5_ARABIC_REPO} ({F5_ARABIC_CKPT}) على: {DEVICE}...")
F5_MODEL, F5_VOCODER, F5_MEL_TYPE, REPO_REF_WAV_PATH = load_arabic_f5_tts(
    F5_ARABIC_REPO,
    DEVICE,
    ckpt_filename=F5_ARABIC_CKPT,
    vocab_filename=F5_ARABIC_VOCAB,
    cfg_filename=F5_ARABIC_CFG,
    ref_wav_filename=F5_REPO_REF_WAV,
    token=HF_TOKEN,
)
print("✅ تم تحميل نموذج Arabic-F5-TTS-v2 بنجاح!")


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


def synthesize_f5_sync(text: str, speaker_wav_path: str, output_wav_path: str) -> str:
    """توليد الصوت عبر Arabic-F5-TTS-v2 بالإعدادات المضبوطة."""
    abs_output_wav = os.path.abspath(output_wav_path)
    base_dir = os.path.dirname(abs_output_wav)
    os.makedirs(base_dir, exist_ok=True)

    using_repo_ref = USE_REPO_REF_ALWAYS or not speaker_wav_path or not os.path.exists(speaker_wav_path)
    active_ref = REPO_REF_WAV_PATH if using_repo_ref else speaker_wav_path
    ref_text_to_use = DEFAULT_REF_TEXT if using_repo_ref else ""

    abs_speaker_wav = os.path.abspath(active_ref)
    ref_audio, resolved_ref_text = preprocess_ref_audio_text(abs_speaker_wav, ref_text_to_use)

    clean_text = " ".join(text.split()).strip()
    if not clean_text:
        raise ValueError("النص فارغ بعد التنظيف.")

    audio_wave, sample_rate, _ = infer_process(
        ref_audio=ref_audio,
        ref_text=resolved_ref_text,
        gen_text=clean_text,
        model_obj=F5_MODEL,
        vocoder=F5_VOCODER,
        mel_spec_type=F5_MEL_TYPE,
        nfe_step=NFE_STEP,
        cfg_strength=CFG_STRENGTH,
        speed=TTS_SPEED,
        show_info=lambda _: None,
        device=DEVICE,
    )

    wave_np = np.asarray(audio_wave, dtype=np.float32)
    if np.isnan(wave_np).any() or np.isinf(wave_np).any():
        raise RuntimeError("النموذج أخرج قيم NaN أو Inf.")

    peak = float(np.max(np.abs(wave_np))) if wave_np.size > 0 else 0.0
    if peak > 1.0:
        wave_np = wave_np / peak * 0.95

    sf.write(abs_output_wav, wave_np, sample_rate)
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
                await reply_msg.edit_text("جارِ توليد الصوت عبر Arabic-F5-TTS-v2 الآن ☕...")
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

            output_wav_path = os.path.join(task_dl_path, f"f5_ar_{text_msg_id}.wav")

            await reply_msg.edit_text("🎙️ جارِ تحويل النص إلى صوت...")
            await asyncio.to_thread(
                synthesize_f5_sync,
                input_text,
                speaker_wav or "",
                output_wav_path
            )

            if not os.path.exists(output_wav_path) or os.path.getsize(output_wav_path) == 0:
                raise RuntimeError("فشل إنشاء الملف الصوتي الناتج.")

            await reply_msg.edit_text("📤 جارِ إرسال المقطع الصوتي...")
            await text_msg.reply_audio(
                output_wav_path,
                caption="✅ تم توليد الصوت عبر Arabic-F5-TTS-v2 بنجاح"
            )

            if os.path.exists(output_wav_path):
                os.remove(output_wav_path)
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
        "أهلاً بك في بوت تحويل النص إلى صوت (Arabic-F5-TTS-v2) 🎙️\n\n"
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
            await bot.send_message(Admin_Id, 'Arabic-F5-TTS-v2 Bot Started ✅')
        print("✅ Arabic-F5-TTS-v2 Bot (Global List Loop) is ONLINE!")
        await idle()
    finally:
        if bot.is_connected:
            await bot.stop()

if __name__ == '__main__':
    asyncio.run(start_bot_async())