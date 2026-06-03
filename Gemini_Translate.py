import nest_asyncio
nest_asyncio.apply()
import os

#########################################################

Bot_Token = os.getenv('TOKEN')

########################################################

from pyrogram.types import InlineKeyboardMarkup , InlineKeyboardButton , CallbackQuery , ForceReply,Message
from pyrogram import Client, filters,enums
from pyrogram import idle
from pyrogram.types import InlineKeyboardMarkup , InlineKeyboardButton , CallbackQuery ,Message,MessageEntity
from pyrogram.errors import FloodWait
from pyrogram.enums import MessageEntityType

from google import genai
from google.genai import types
from textwrap import wrap
import os,asyncio,shutil,re

def Pyrogram_Client(Bot_Token):
  Bot_Identifier = Bot_Token.split(':')[0]
  Session_file = Bot_Identifier+'_955hyh95|session_prm_bot'
  bot = Client(Session_file,api_id=Api_Id,api_hash=Api_Hash,bot_token=Bot_Token,in_memory=True)
  return bot,Bot_Identifier

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'
bot,Bot_Identifier = Pyrogram_Client(Bot_Token)

Gemini_Token_Pattern = "^AIzaSy.*"
T_linebreak = '\n\n ◾ــــــــــــــ◾ \n\n'

g_langs = [ 'العربية | ar','الإنجليزية | en','الفرنسية | fr','الألمانية | de','العبرية iw  |  iw','العبرية he | he','اليونانية | el','الأمهرية | am','الباسك | eu','البنغالية | bn','البرتغالية  | pt','البلغارية | bg','الكتالانية | ca','الشيروكية | chr','الكرواتية | hr','التشيكية | cs','الدنماركية | da','الهولندية | nl','الإستونية | et','الفلبينية | fil','الفنلندية | fi','الغوجاراتية | gu','الهندية |  hi','المجرية | hu','الأيسلندية | is ','الإندونيسية | id','الإيطالية | it','اليابانية | ja','الكانادا  | kn','الكورية | ko','اللاتفية | lv','الليتوانية | lt','الماليزية |  ms','المالايالامية | ml','الماراثية |  mr','النرويجية | no','البولندية | pl','الرومانية | ro','الروسية | ru','الصربية | sr','الصينية  | zh-cn','الصينية TW | zh-tw','السلوفاكية | sk','السلوفينية | sl','الإسبانية | es','السواحيلية | sw','السويدية | sv','التاميلية | ta','التيلوغوية | te','التايلاندية | th','التركية|  tr','الأوردية | ur','الأوكرانية | uk','الفيتنامية | vi' ,'الويلزية | cy','الأفريكانية | af', 'الأرمينية | hy','الألبانية | sq','الأذريبيجانية | az','البيلاروسية | be','البوسنية | bs','السبيونوية | ceb','الشيشوانية | ny','الكورسيكية | co', 'الهولندية | nl','الاسبرانتو | eo','الاستوانية | et','الفلبينية | tl','الزولو | zu ','يوروبا | yo','اليديشية | yi','xhosa | xh','الأوزبكية | uz ','أويغور | ug','طاجيكية | tg','السودانية | su','الصومالية | so','السنهالية | si','السندية | sd','شونا | sn','سيسوتو | st','الغيلية | gd','ساموا | sm','رومانية | ro','بنجابية | pa' ,'فارسية | fa','باشتو | ps','أوديا | or','نرويجية | no' ,'نيبالية | ne','ميانمارية | my','منغولية | mn','ماورية | mi','مالطية | mt','قيرغيزستانية | ky','كردية | ku','الخميرية | km','الكازخستانية | kk','الجاوية | jw','الأيرلندية | ga','الإندونيسية | id', 'الإيغبو | ig', 'المجرية | hu', 'همونغ | hmn','هاواي | haw','هاوسا | ha','الكريولية | ht' ,'الجورجية | ka','الجاليكية | gl','الفريزية | fy','لاوية | lo', 'لاتينية | la', 'ليتوانية | lt', 'لوكسمبورغية | lb','المقدونية | mk', 'الملغاشية | mg']


Gemini_dl_path = f'/content/Sunnay_Colabs/downloads_{Bot_Identifier}/'

Gemini_Dir = f'/content/Sunnay_Colabs/Gemini_{Bot_Identifier}/'

if not os.path.isdir(Gemini_Dir):
   os.mkdir(Gemini_Dir)

if len(os.listdir(Gemini_Dir)) != 0 :
   Gemini_File = os.listdir(Gemini_Dir)[0]
   Gemini_Tokens = open(Gemini_Dir+Gemini_File,'r').read().split(' ')
else :
    Gemini_File = ''



Gemini_Model = 'gemini-2.5-flash-lite'
#Gemini_Model = 'gemini-2.5-pro'


async def Check_File(File):
  if os.path.isfile(File):
      os.remove(File)

async def Create_Dir(Dir):
  if not os.path.isdir(Dir):
    os.makedirs(Dir, exist_ok=True)

async def Check_Dir(Dir):
  if os.path.isdir(Dir):
      shutil.rmtree(Dir)
  await Create_Dir(Dir)

async def Wrap_Text(text,num):
 if '\n' in text : 
  text= text.replace('\n','§')
 Text_list = wrap(text,num)
 for No,part in enumerate(Text_list) : 
  if '§' in part :
   Text_list[No] = part.replace('§','\n')
 return Text_list 

async def Rmv_Trans(Res):
  Res_Lines = Res.split('\n')
  for No,line in enumerate(Res_Lines) :
    if any(x in line for x in (  'ترجم', 'translat')):
     Res_Lines.pop(No)
  Res = '\n'.join(Res_Lines)
  return Res

async def Grap_Lang(Sym): 
  for lang in g_langs :
    if Sym in lang : 
      F_L = lang.split('|')[0].strip()
      break
  return F_L

async def Gemini_Trans_Txt(TxtFile,lang_sy='ar'):
  mainDir = '/'.join(TxtFile.split('/')[:-1]) + '/'
  Res_Name = mainDir +  TxtFile.split('/')[-1].split('.')[0]
  Txt_File = Res_Name + '_Translated.txt'
  await Check_File(Txt_File)
  Text = open(TxtFile,'r').read()
  await Gemini_CTxt(TxtFile,Txt_File,Text,lang_sy,0,10000)
  return Txt_File
  
async def Gemini_CTxt(TxtFile,Txt_File,Text,lang_sy,Req_Count=0,Limit=20000):
  with open(Txt_File,'a') as f : 
    if len(Text) > Limit : 
      Textlist = await Wrap_Text(Text,Limit)
      for Num,part in enumerate(Textlist) : 
        mainDir = '/'.join(TxtFile.split('/')[:-1]) + '/'
        Res_Name = mainDir +  TxtFile.split('/')[-1].split('.')[0]
        Txt_Part = Res_Name + f'_P0000{Num}.txt'
        open(Txt_Part,'a').write(part)
        Res_Text,Req_Count = await Gemini_BTxt(Txt_Part,Req_Count,lang_sy)
        if Res_Text == 'ERROR' :
          New_Limit = Limit-5000
          if New_Limit != 0 :
            return await Gemini_CTxt(TxtFile,Txt_File,Text,lang_sy,Req_Count,New_Limit)
          else : 
           mainDir = '/'.join(TxtFile.split('/')[:-1]) + '/'
           Res_Name = mainDir +  TxtFile.split('/')[-1].split('.')[0]
           Rest_File = Res_Name + f'_Res.txt'
           with open(Rest_File,'a') as Rf : 
             for sec in Textlist[Num:]:
               Rf.write(sec)
           raise ValueError('انتهت توكنات اليوم 🌿')
        f.write(Res_Text)
        os.remove(Txt_Part)
    else : 
      Res_Text,Req_Count = await Gemini_BTxt(TxtFile,Req_Count,lang_sy)
      if Res_Text == 'ERROR' :
          New_Limit = Limit-5000
          if New_Limit != 0 :
            return await Gemini_CTxt(TxtFile,Txt_File,Text,lang_sy,Req_Count,New_Limit)
          else : 
           raise ValueError('انتهت توكنات اليوم 🌿')
      f.write(Res_Text)
      

async def Gemini_BTxt(TxtFile,Req_Count,lang_sy='ar',Api_Index=0) : 
  Gemini_Apis = globals()['Gemini_Tokens']
  client = genai.Client(api_key=Gemini_Apis[Api_Index])
  F_L = await Grap_Lang(lang_sy)
  Translate_Prompt = f"""
ترجم هذا الملف النصي بأكمله بدقة إلى {F_L}  👇
  
  """ 
  try : 
    file = client.files.upload(file=TxtFile)
    response = client.models.generate_content(model=Gemini_Model, contents=[Translate_Prompt, file])
    Res = await Rmv_Trans(response.text)
    Res = Res + T_linebreak + open(TxtFile,'r').read() + T_linebreak
    Req_Count += 1
    return Res,Req_Count
  except Exception as err : 
    Req_Count+=1
    New_Index = Api_Index+1 
    if New_Index < len(Gemini_Apis):
      if Req_Count%15 == 0 :
        await asyncio.sleep(60)
      return await Gemini_BTxt(TxtFile,Req_Count,lang_sy,New_Index)
    else :
      return 'ERROR',Req_Count
      #raise ValueError('انتهت توكنات اليوم 🌿')

async def Get_Msg(bot,Chat_id,msg_id):
  try : 
     msg = await bot.get_messages(int(Chat_id),int(msg_id))
     return msg
  except FloodWait as e :
      await asyncio.sleep(e.value)
      return await Get_Msg(bot,Chat_id,msg_id)
  except Exception as err : 
      pass

@bot.on_message(filters.private & filters.incoming)
async def _telegram_file(client, message):
  if message.text :
     if re.search(Gemini_Token_Pattern,message.text) :
        open(Gemini_Dir+'gemini.txt','w').write(message.text)
        await message.reply('تم تلقيم التوكنات')
        globals()['Gemini_File'] = 'gemini.txt'
        globals()['Gemini_Tokens'] = message.text.split(' ')
        return
     elif len(globals()['Gemini_File']) == 0 : 
            await message.reply('قم بإرسال توكن Gemini')
            return 

  if message.document : 
        if len(globals()['Gemini_File']) == 0 : 
            await message.reply('قم بإرسال توكن Gemini')
            return

  CHOOSE_UR_LANG = "اختر اللغة المراد الترجمة إليها"
  LANGS_BUTTONS = []
  for lang in g_langs : 
        Rom_Num = int(len(g_langs)/3)
        Data = f"{message.id}_{lang.split('|')[-1].strip()}"
        if g_langs.index(lang) > Rom_Num-1 :
         LANGS_BUTTONS[g_langs.index(lang)%Rom_Num].append(InlineKeyboardButton(lang.split('|')[0],callback_data=Data))
        else : 
         LANGS_BUTTONS.append([InlineKeyboardButton(lang.split('|')[0],callback_data=Data)])
  await message.reply(text = CHOOSE_UR_LANG,reply_markup = InlineKeyboardMarkup(LANGS_BUTTONS))
      


@bot.on_callback_query()
async def callback_query(CLIENT,CallbackQuery):
  User_Id = CallbackQuery.from_user.id
  Callback_List = CallbackQuery.data.split('_')
  msg_id = int(Callback_List[0])
  lang = Callback_List[1]
  Msg = await Get_Msg(bot,User_Id,msg_id)
  Replied = await CallbackQuery.edit_message_text(" جار العمل  ")
  if Msg.text :
    await Check_Dir(Gemini_dl_path)
    open(Gemini_dl_path+'text.txt','w').write(Msg.text)
    Res = await Gemini_Trans_Txt(Gemini_dl_path+'text.txt',lang)
    await Msg.reply_document(Res)
    await Check_Dir(Gemini_dl_path)
    await Replied.edit_text(" تم  ")
  
  elif Msg.document :
    if Msg.document.file_name.lower().endswith('txt') :
        txt = await Msg.download(file_name=Gemini_dl_path)
        Res = await Gemini_Trans_Txt(txt,lang)
        await Msg.reply_document(Res)
        await Check_Dir(Gemini_dl_path)
        await Replied.edit_text(" تم  ")





Gemini_Trans_Txt

def main():
    try:
        bot.start()
        print("✅ Gemini Bot is ONLINE!")
        idle()
    finally:
        if bot.is_connected:
            bot.stop()

main()