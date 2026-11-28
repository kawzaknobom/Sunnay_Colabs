import nest_asyncio
nest_asyncio.apply()

import os
import json
import asyncio
import shutil
import subprocess
import gc

#########################################################

Bot_Token = os.getenv('TOKEN')
Admin_Id = int(os.getenv('Admin_Id', '0'))
Serv_Acc = os.environ['Service_Acc']
clean_string = Serv_Acc.replace("\xa0", " ")
data = json.loads(clean_string)
formatted_json = json.dumps(data, indent=2)
ServAcc_File = 'servac.json'
with open(ServAcc_File, 'w', encoding='utf-8') as f:
    f.write(formatted_json)

########################################################

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ForceReply, Message
from pyrogram import Client, filters
from pyrogram import idle

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'

def Pyrogram_Client(Bot_Token):
    Bot_Identifier = Bot_Token.split(':')[0]
    Session_file = Bot_Identifier + '_955hyh95|session_prm_bot'
    bot = Client(Session_file, api_id=Api_Id, api_hash=Api_Hash, bot_token=Bot_Token, in_memory=True)
    return bot, Bot_Identifier

bot, Bot_Identifier = Pyrogram_Client(Bot_Token)

ServAcc_Dir = f'/content/Sunnay_Colabs/ServAcc_{Bot_Identifier}/'
if not os.path.isdir(ServAcc_Dir):
    os.makedirs(ServAcc_Dir, exist_ok=True)

if len(os.listdir(ServAcc_Dir)) != 0:
    ServAcc_File = os.path.join(ServAcc_Dir, os.listdir(ServAcc_Dir)[0])
else:
    ServAcc_File = 'servac.json'

Global_Main_Queue = []
Public_Loop = False
processed_messages = set()

def Get_File(Dl_Dir, File_Ex):
    if not os.path.isdir(Dl_Dir):
        return None
    for file in os.listdir(Dl_Dir):
        if file.lower().endswith(File_Ex):
            return os.path.abspath(os.path.join(Dl_Dir, file))
    return None

def Ocr_Func(Ocr_Path):
    current_serv_acc = ServAcc_File if os.path.exists(ServAcc_File) else 'servac.json'
    Dir_Path = os.path.dirname(os.path.abspath(Ocr_Path)) + '/'
    abs_serv_acc = os.path.abspath(current_serv_acc)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_serv_acc

    Tahweel_Cmd = (
        f'tahweel "{Ocr_Path}" '
        f'--service-account-credentials "{abs_serv_acc}" '
        f'--pdf2image-thread-count 8 '
        f'--processor-max-workers 8 '
        f'--txt-page-separator 🟥'
    )
    p = subprocess.Popen(Tahweel_Cmd, cwd=Dir_Path, shell=True, env=os.environ)
    p.wait()

    Txt_File = Get_File(Dir_Path, 'txt')
    Docx_File = Get_File(Dir_Path, 'docx')
    return Txt_File, Docx_File

async def Create_Dir(Dir):
    if not os.path.isdir(Dir):
        os.makedirs(Dir, exist_ok=True)

async def Check_Dir(Dir):
    if os.path.isdir(Dir):
        shutil.rmtree(Dir)
    await Create_Dir(Dir)

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
                await A_reply.edit_text(f"تمت الإضافة للصف \n\n ترتيبك هو {elem} ☕")
            except Exception:
                pass

        C_Process = Global_Main_Queue[0]
        msg_list = C_Process.split('_')
        msg_type = msg_list[1]
        msg_id = int(msg_list[2])
        rp_msg_id = int(msg_list[-2])
        user_id = int(msg_list[-1])

        reply_msg = await bot.get_messages(user_id, rp_msg_id)
        File_Msg = await bot.get_messages(user_id, msg_id)
        Ocr_dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'

        try:
            try:
                await reply_msg.edit_text("جار العمل ☕...")
            except Exception:
                reply_msg = await File_Msg.reply("جار العمل ☕", reply_to_message_id=File_Msg.id)

            await Check_Dir(Ocr_dl_path)
            Ocr_File = await File_Msg.download(file_name=Ocr_dl_path)
            Txt_File, Docx_File = await asyncio.to_thread(Ocr_Func, Ocr_File)

            if msg_type == "doc":
                if Txt_File and os.path.exists(Txt_File):
                    await File_Msg.reply_document(Txt_File)
                if Docx_File and os.path.exists(Docx_File):
                    await File_Msg.reply_document(Docx_File)
            elif msg_type == "photo":
                if Txt_File and os.path.exists(Txt_File):
                    with open(Txt_File, 'r', encoding='utf-8') as tf:
                        txt_content = tf.read()
                    if txt_content.strip():
                        for i in range(0, len(txt_content), 4096):
                            await File_Msg.reply(txt_content[i:i + 4096])
                    await File_Msg.reply_document(Txt_File)

            try:
                await reply_msg.edit_text("تم العمل ☑️")
            except Exception:
                pass

        except Exception as err:
            err_text = str(err)[:3000]
            try:
                await reply_msg.edit_text(f"حدث خطأ أثناء المعالجة:\n`{err_text}`")
            except Exception:
                pass
        finally:
            if os.path.isdir(Ocr_dl_path):
                shutil.rmtree(Ocr_dl_path, ignore_errors=True)

        Global_Main_Queue.pop(0)

    gc.collect()
    Public_Loop = False

# ==================================================================== #

@bot.on_message(filters.command('start') & filters.private)
async def start_cmd(client, message):
    await message.reply('لبقية البوتات \n\n @sunnaybots')

@bot.on_message(filters.private & filters.incoming)
async def _telegram_file(client, message):
    global Global_Main_Queue

    if message.id in processed_messages:
        return
    processed_messages.add(message.id)

    if message.document:
        replied = await message.reply(f"تمت الإضافة لصف الانتظار ☕\nترتيبك في القائمة: {len(Global_Main_Queue) + 1}")
        Item = f"Ocr_doc_{message.id}_{replied.id}_{message.from_user.id}"
        Item_add(Item)

    elif message.photo:
        replied = await message.reply(f"تمت الإضافة لصف الانتظار ☕\nترتيبك في القائمة: {len(Global_Main_Queue) + 1}")
        Item = f"Ocr_photo_{message.id}_{replied.id}_{message.from_user.id}"
        Item_add(Item)

async def start_bot_async():
    try:
        await bot.start()
        if Admin_Id != 0:
            await bot.send_message(Admin_Id, 'OCR Bot Started with Global List Loop ✅')
        print("✅ OCR Bot (Global List Loop) is ONLINE!")
        await idle()
    finally:
        if bot.is_connected:
            await bot.stop()

if __name__ == '__main__':
    asyncio.run(start_bot_async())