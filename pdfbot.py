from pyrogram.types import InlineKeyboardMarkup , InlineKeyboardButton , CallbackQuery , ForceReply,Message,ReplyKeyboardMarkup, KeyboardButton,ReplyKeyboardRemove
from pyrogram import Client, filters

from functools import reduce
import os,re,random, threading,time

from cookies_nodb import Image_forms,Renm_msg,Photo_Options,Photo_Multi_Options,Pdf_Options,Pdf_Txt_Option,Pdf_Image_Option,Pdf_Multi_Options,Pdf_Refunc_Methods,Pdf_Trim_Msg,Txt_Trim_Msg,Renm_msg,Audio_Multi_Options,Other_Options,Main_Contract,Usage_Button,g_langs,Ex_Pdf_Limit,Ppf_Opts

from common_func_nodb import Pdf_Extract,Pdf_Page,Pdf_Trim,Pdf_Make,Pyrogram_Client,Check_File,Check_Dir,Pdf_Merge,Ocr_Func,Pdf_Margin,Upld_Dir_Func,Unlock_Pdf,Rmv_Dups,Zip_Extract,Grap_PicDir,Merge_Images_UP,Merge_Images_SBS,Blur_Func,Mp3_Conv,Media_Amplify,Media_Change,Media_Skip,Media_Compress,Media_Speed,Media_Trim,Upld_File,Send_Text_Res,Aud_Merge,Encode_Vid,Media_F_func,Send_TRes,Get_Name,Get_Msg,File_Dl,Pdf_Page_Num,Pdf_Compress,Multi_Op_Dl,Txt_Trim,Zip_Func,Txt_Merge,Google_Trans_Txt

from pypdf import PdfReader

Merge_Quee = {}
public_q =[]
Renm_L = []


#######

Bot_Token = '8016797331:AAEFGbZ9wWG5mI4Gomcxrskiis-yAzJEgog'
bot,Bot_Identifier = Pyrogram_Client(Bot_Token)

#####

Close_Loop = False

Public_Loop = False

main_dl_path = f'./downloads_{Bot_Identifier}/'


#### Bot Funcs ####

def Callback_Add(CallbackQuery):
  Quee = public_q
  replied = CallbackQuery.edit_message_text(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ")
  Item = CallbackQuery.data + f'_{replied.id}_{CallbackQuery.from_user.id}'
  Item_add(Item)

def Item_add(Item):
  User_Id = int(Item.split("_")[-1])
  Quee = public_q
  Quee.append(Item)
  loop_name = "Public_Loop"
  if not globals()[loop_name] :	
    globals()[loop_name] = True
    Multi_loop()
    
def Pdf_Cases(Case,File,Msg):
  if any(x in Case for x in ('-','/')):
    if '-' in Case : 
      Sep =  '-' 
    elif '/' in Case : 
      Sep =  '/' 
    point_list = Case.split(Sep) 
    Start = int(point_list[0])
    End = int(point_list[1])
    Pdf_File = Pdf_Trim(File,Start,End)
    cap =  ( f"`{Start}` to `{End}`")
    Upld_File(Pdf_File,Msg,cap)
  else : 
    Pdf_File = Pdf_Page(File,int(Case))
    Extract_Dir = Pdf_Extract(Pdf_File)
    Msgs_List = Upld_Dir_Func(Extract_Dir,Msg)
 
def Universal_Concat(message,Merge_Quee,Method):
      User_Id = message.from_user.id
      Merge_Quee[Method][1].append(str(message.id))
      method = Method.split('_')[0]
      if method == 'Zip' :
        Word = 'الملفات'
        Cmd = '/Z_Finish'
        C_Cmd = '/Z_Clear'
      else :
        if message.photo : 
          Word = 'الصور'
          if method == 'IMerge' :
            Cmd = '/IM_Finish'
            C_Cmd = '/IM_Clear'
          else :
            Cmd = '/IP_Finish'
            C_Cmd = '/IP_Clear'
        

        elif message.document : 
          if message.document.file_name.lower().endswith(Image_forms) : 
            Word = 'الصور'
            if method == 'IMerge' :
              Cmd = '/IM_Finish'
              C_Cmd = '/IM_Clear'
            else :
              Cmd = '/IP_Finish'
              C_Cmd = '/IP_Clear'
          elif message.document.file_name.lower().endswith(('pdf','ppt','pptx','mdx')) : 
            Word = 'الملفات'
            Cmd = '/P_Finish'
            C_Cmd = '/P_Clear'
          
          elif message.document.file_name.lower().endswith('txt') : 
            Word = 'الملفات'
            Cmd = '/T_Finish'
            C_Cmd = '/T_Clear'
            
      M_Text = f"""
      ▪️عدد {Word} 👈 {len(Merge_Quee[Method][1])} ملفاً
      ▪️بعد الانتهاء اضغط الأمر 
      {Cmd}
      ▪️لإلغاء عملية الدمج ، اضغط الأمر 
      {C_Cmd}
      """
      Replied_Msg = Get_Msg(bot,User_Id,Merge_Quee[Method][0][0])
      Replied_Msg.edit_text(M_Text)

###### Main Loop ####

def reload_loop(process):
      if process in public_q :
        msg_list = process.split('_')
        rp_msg_id = int(msg_list[-2])
        user_id = int(msg_list[-1])
        reply_msg = Get_Msg(bot,user_id,rp_msg_id)
        File_Msg = Get_Msg(bot,user_id,msg_list[1])
        try : 
            reply_msg.edit_text("لقد تخطيت الحد الزمني الأقصى للطلب ( 30 دقيقة )")
        except :
          reply_msg.delete()
          reply_msg = File_Msg.reply("لقد تخطيت الحد الزمني الأقصى للطلب ( 30 دقيقة )")
        del public_q[0]
        thread = threading.Thread(target=Multi_loop, args=["MainQ"])
        thread.start()

def Multi_loop():
  Multi_Q = public_q
  dl_path = f'./downloads_{Bot_Identifier}/'
  for obj in range (0,len(Multi_Q)) :
   timer = threading.Timer(1800, reload_loop, args=[public_q[0]])
   timer.start()

   for elem in range (1,len(Multi_Q)) :
        try :
         A_Reply_List = Multi_Q[elem].split('_')
         A_rp_msg_id = A_Reply_List[-2]
         A_user_id = A_Reply_List[-1]
         A_reply = Get_Msg(bot,A_user_id,A_rp_msg_id)
         A_reply.edit_text(f"تمت الإضافة للصف \n\n ترتيبك هو {elem} ☕ ")
        except :
          pass
   try :
    C_Process = Multi_Q[0]
    msg_list = C_Process.split('_')
    msg_id = msg_list[1]
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    process = msg_list[0]
    rp_msg_id = int(msg_list[-2])
    user_id = int(msg_list[-1])
    reply_msg = Get_Msg(bot,user_id,rp_msg_id)
    File_Msg = Get_Msg(bot,user_id,msg_id)
    File_Name = Get_Name(File_Msg)
    if any(x in File_Name for x in ('أحمد السيد','أحمد_السيد','احمد_السيد','احمد السيد')) :
        reply_msg.edit_text('آسف ، لا أخدم لـ [أحمد السيد](https://telegra.ph/من-هو-أحمد-السيد-03-26) 🌿',disable_web_page_preview=True)
    else :
      try : 
        reply_msg.edit_text(f"جار العمل  ☕")
      except :
        reply_msg.delete()
        reply_msg = File_Msg.reply('جار العمل ☕')
      if process == 'Det' :
        if File_Msg.audio :
          Size = File_Msg.audio.file_size
        elif File_Msg.voice :
          Size = File_Msg.voice.file_size
        elif File_Msg.video :
          Size = File_Msg.video.file_size
        elif File_Msg.document :
          Size = File_Msg.document.file_size
        Details =  f"اسم الملف : \n {File_Name} \n حجم الملف : \n {round(int(Size)/(1024*1024),2)} ميغا بايت  "
        reply_msg.reply(Details)
        
      elif process in ['PMerge','IMerge','PMake','Zip','TMerge'] : 
        
        Files_Ids = msg_list[1:-2]
        if process == 'IMerge' :
          Files_Ids = msg_list[1:-3]
        Process_List = Multi_Op_Dl(bot,dl_path,Files_Ids,user_id)
        if process == 'PMerge' : 
          Res_File = Pdf_Merge(Process_List)
        elif process == 'TMerge':
          Res_File = Txt_Merge(Process_List)
            

        elif process == 'IMerge' :
         if len(Process_List) < 11 :
          if msg_list[-3] == 'SBS':
            Merge_Mode = Merge_Images_SBS
          else : 
            Merge_Mode = Merge_Images_UP
          Res_File = reduce(Merge_Mode,Process_List)
          File_Msg.reply_document(Res_File)
         else :
           File_Msg.reply('غير مسموح بأكثر من عشر صور ')
          
        elif process == 'PMake' : 
         Res_File = Pdf_Make(Process_List)
        elif process == 'Zip' :
          Res_File = Zip_Func(dl_path)
         
        Upld_File(Res_File,File_Msg)
        if process == 'Zip' :
          os.remove(Res_File)
      
      else :
       Rate = msg_list[2]
       if not (File_Msg.photo or File_Msg.video or File_Msg.audio or File_Msg.voice or (File_Msg.document and not File_Msg.document.file_name.lower().endswith(('pdf','ppt','pptx','mdx'))) or (File_Msg.document and File_Msg.document.file_name.lower().endswith(('pdf','ppt','pptx','mdx')) and int(int(File_Msg.document.file_size)/(1024*1024)) <= 500 )) :
        File_Msg.reply(f'حد الملف {Ex_Pdf_Limit} ميغا')
       else : 
         File = File_Dl(File_Msg,dl_path)
         if process == 'Trim' :
           if '|' in Rate : 
              Rate = Rate.replace('|',' ')
           if File.lower().endswith(('pdf')) :

            if any(x in Rate for x in [',','،']):
             if ',' in Rate : 
                splitor = ','
             else : 
                splitor = '،'
             Cases = Rate.split(splitor)
             for Case in Cases : 
               Pdf_Cases(Case,File,File_Msg)
            else : 
             Pdf_Cases(Rate,File,File_Msg)

           elif File.lower().endswith('txt'):
             Phrase_List = Rate.split('~')
             Start_ph = Phrase_List[0]
             End_ph = Phrase_List[-1]
             Res_File = Txt_Trim(File,Start_ph,End_ph)
             Upld_File(Res_File,File_Msg)

           else :
    
             if ' ' in Rate : 
               Parts = Rate.split(" ")
               for part in Parts : 
                Res_File = Media_Trim(File,part)
                start = part.split('-')[0]
                End = part.split('-')[1]
                cap =  ( f"`{start}` to `{End}`")
                Upld_File(Res_File,File_Msg,cap)
             else :
               Res_File = Media_Trim(File,Rate)
               start = Rate.split('-')[0]
               End = Rate.split('-')[1]
               cap =  ( f"`{start}` to `{End}`")
               Upld_File(Res_File,File_Msg)
                    
         elif process == 'Ex':
          
            if File.lower().endswith(('.pdf')):
                  Extract_Dir = Pdf_Extract(File)
                  Msgs_List = Upld_Dir_Func(Extract_Dir,File_Msg)
            elif File.lower().endswith(('cbz','cbr','zip','rar')) :
              Extract_Dir = Zip_Extract(File)
              Msgs_List = Upld_Dir_Func(Extract_Dir,File_Msg)

         elif process in ['Ocr','Trans']:
            
            if File.lower().endswith('txt'):
              Txt_File = File
            else :
              if File.endswith('PDF'):
                os.rename(File,File.lower())
                File = File.lower()
              Txt_File,Docx_File = Ocr_Func(File)
          

            if File.lower().endswith(Image_forms):
              Send_Text_Res(File_Msg,open(Txt_File,'r').read())
            else :
              File_Msg.reply_document(Txt_File)
              if process == 'Ocr' :
                File_Msg.reply_document(Docx_File)
         
  
         elif process in ('Compress','Marg','Unlock','Renm') :
              
              if process == 'Renm':
               Ext = File.split('.')[-1]
               Res_File = f"{dl_path}{Rate.replace('|',' ')}.{Ext}"
               Cmd = f'mv "{File}" "{Res_File}"'
               os.system(Cmd)

              elif process == 'Marg' :
               if Pdf_Page_Num(File) < Ex_Pdf_Limit : 
                Res_File = Pdf_Margin(File)
               else :
                  File_Msg.reply(f'حد الملف {Ex_Pdf_Limit} ميغا')
              elif process == 'Unlock' :
               
                if Pdf_Page_Num(File) < Ex_Pdf_Limit : 
                  Res_File = Unlock_Pdf(File)
                else :
                    File_Msg.reply(f'حد الملف {Ex_Pdf_Limit} صفحة')
              elif process == 'Compress' :
                if File.lower().endswith('pdf'):
                  Res_File = Pdf_Compress(bot,dl_path,File)
              
      try :
        reply_msg.edit_text('تمت  ☑️')
      except :
        pass
      Check_Dir(dl_path)
   except Exception as err :
       try : 
        reply_msg.edit_text(err)
       except : 
         pass
   if C_Process in Multi_Q : 
    globals()['Close_Loop'] = False
    del Multi_Q[0]
   else :
    globals()['Close_Loop'] = True
    break
  if not globals()['Close_Loop'] :
    if len(Multi_Q) != 0 :
        return Multi_loop()
    else :
      loop_name = "Public_Loop"
      if globals()[loop_name] :	
        globals()[loop_name] = False

###### Bot Funcs #####

@bot.on_message((filters.command('P_Clear') | filters.command('IM_Clear') | filters.command('A_Clear') | filters.command('V_Clear') | filters.command('IP_Clear') | filters.command('Z_Clear') | filters.command('T_Clear') ) & filters.private)
def command1(bot,message):
  
   User_Id = message.from_user.id
   if message.text.strip() == '/P_Clear' : 
     Method = 'PMerge'
     Key = f'{Method}_{User_Id}'
     
   elif message.text.strip() == '/IM_Clear': 
     Method = 'IMerge'
     Key = f'{Method}_{User_Id}'
    
   elif message.text.strip() == '/IP_Clear': 
    Method = 'PMake'
    Key = f'{Method}_{User_Id}'
    
   elif message.text.strip() == '/A_Clear':
     Method = 'AMerge'
     Key = f'{Method}_{User_Id}'
    
   elif message.text.strip() == '/V_Clear':
     Method = 'VMerge'
     Key = f'{Method}_{User_Id}'

   elif message.text.strip() == '/T_Clear':
     Method = 'TMerge'
     Key = f'{Method}_{User_Id}'

   elif message.text.strip() == '/Z_Clear':
     Method = 'Zip'
     Key = f'{Method}_{User_Id}'

   Reply_Id = Merge_Quee[Key][0][0]
   Replied_Msg = Get_Msg(bot,User_Id,Reply_Id)
   Replied_Msg.edit_text('تم الإلغاء ✅')
   del Merge_Quee[Key]


@bot.on_message((filters.command('P_Finish') | filters.command('IM_Finish') | filters.command('A_Finish') | filters.command('V_Finish') | filters.command('IP_Finish') | filters.command('Z_Finish') | filters.command('T_Finish') ) & filters.private)
def command1(bot,message):
  
   User_Id = message.from_user.id
   if message.text.strip() == '/P_Finish' : 
     Method = 'PMerge'
     Key = f'{Method}_{User_Id}'
     
   elif message.text.strip() == '/IM_Finish': 
     Method = 'IMerge'
     Key = f'{Method}_{User_Id}'
    
   elif message.text.strip() == '/IP_Finish': 
    Method = 'PMake'
    Key = f'{Method}_{User_Id}'
    
   elif message.text.strip() == '/A_Finish':
     Method = 'AMerge'
     Key = f'{Method}_{User_Id}'

   elif message.text.strip() == '/V_Finish':
     Method = 'VMerge'
     Key = f'{Method}_{User_Id}'

   elif message.text.strip() == '/T_Finish':
     Method = 'TMerge'
     Key = f'{Method}_{User_Id}'
   
   elif message.text.strip() == '/Z_Finish':
     Method = 'Zip'
     Key = f'{Method}_{User_Id}'

   Replied_Msg_id = Merge_Quee[Key][0][0]
   Replied_Msg = Get_Msg(bot,User_Id,Replied_Msg_id)
   if len(Merge_Quee[Key][1]) < 2 and not Method in ('PMake','Zip') :
        Replied_Msg.edit_text("لقد أرسلت ملفاً واحداً فقط !")
        return
   else :
     if Method == 'IMerge':
        Replied_Msg.delete()
        MERGE_MODE_IMAGE = "اختر نمط الدمج "
        Merge_Modes = [['أفقياً','SBS'],['رأسياً','UD']]
        MERGE_MODE_Buttons = []
        for Mod in Merge_Modes : 
         MERGE_MODE_Buttons.append([InlineKeyboardButton(Mod[0],callback_data=f'IMerge_{Mod[1]}_{message.from_user.id}')])
        message.reply(text = MERGE_MODE_IMAGE,reply_markup = InlineKeyboardMarkup(MERGE_MODE_Buttons))
     else :
      Quee = public_q 
      replied = Replied_Msg.edit_text(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ")
      Key = f'{Method}_{message.from_user.id}'
      Msgs_ids = '_'.join(Merge_Quee[Key][1])
      Item = f"{Method}_{Msgs_ids}_{replied.id}_{message.from_user.id}"
      del Merge_Quee[Key]
      Item_add(Item)
      

@bot.on_message(filters.command('start') & filters.private)
def command1(bot,message):
   User_Id = message.from_user.id
   message.reply('لبقية البوتات \n\n @sunnay6626')
   #My_Db.Insert_User(message.from_user.id)
  
#####

@bot.on_message(filters.private & filters.incoming & (filters.photo | filters.audio | filters.voice | filters.video | filters.document ))
def _telegram_file(client, message):
    
  User_Id = message.from_user.id
  Zip_Key = f'Zip_{User_Id}'
  IMerge_Key = f'IMerge_{User_Id}'
  Pmake_Key = f'PMake_{User_Id}'
  PMerge_Key = f'PMerge_{User_Id}'
  TMerge_Key = f'TMerge_{User_Id}'
  if Zip_Key in list(Merge_Quee.keys()):
    Universal_Concat(message,Merge_Quee,Zip_Key)
    return
  else :
      
    if IMerge_Key in list(Merge_Quee.keys()):
     if message.photo or message.document.file_name.lower().endswith(Image_forms):
      Universal_Concat(message,Merge_Quee,IMerge_Key)
      return
    elif PMerge_Key in list(Merge_Quee.keys()):
     if message.document.file_name.lower().endswith('pdf'):
      Universal_Concat(message,Merge_Quee,PMerge_Key)
      return
    elif Pmake_Key in list(Merge_Quee.keys()):
     if message.photo or message.document.file_name.lower().endswith(Image_forms):
      Universal_Concat(message,Merge_Quee,Pmake_Key)
      return
    elif TMerge_Key in list(Merge_Quee.keys()):
     if message.document.file_name.lower().endswith('txt') :
      Universal_Concat(message,Merge_Quee,TMerge_Key)
      return

  if message.photo : 
      Options =  Photo_Options + Pdf_Image_Option
   
  elif message.document : 
   
   if message.document.file_name.lower().endswith(Image_forms) : 
      Options = Photo_Options + Pdf_Image_Option
   
   elif message.document.file_name.lower().endswith(('pdf','ppt','pptx','mdx')) : 
       if message.document.file_name.lower().endswith('pdf'):
        Options = Pdf_Options
       else :
         Options = Ppf_Opts
   
   elif message.document.file_name.lower().endswith('txt') : 
     
     Options = Pdf_Txt_Option
   
   else :
     Options = Other_Options
     
  CHOOSE_UR_BUTTONS = []
  CHOOSE_UR_Option = "اختر ما تريد "
  for Index,option in enumerate(Options) : 
    if Index > 6 : 
      CHOOSE_UR_BUTTONS[(Index-1)%6].append(InlineKeyboardButton(option[0],callback_data=option[1]+'_'+str(message.id)))
    else : 
     CHOOSE_UR_BUTTONS.append([InlineKeyboardButton(option[0],callback_data=option[1]+'_'+str(message.id))])
     
  CHOOSE_UR_BUTTONS = Rmv_Dups(CHOOSE_UR_BUTTONS)
  message.reply(text = CHOOSE_UR_Option,reply_markup = InlineKeyboardMarkup(CHOOSE_UR_BUTTONS))
 
#####################################

callback_dict = {}

@bot.on_callback_query()
def callback_query(CLIENT,CallbackQuery):
  User_Id = CallbackQuery.from_user.id
  Quee = public_q
  Callback_List = CallbackQuery.data.split('_')
  Method = Callback_List[0]
  Msg_Id = Callback_List[1]
  if not Msg_Id in ('SBS','UD'):
    file_msg = Get_Msg(bot,User_Id,Msg_Id)
  if Method == 'Yes':
    CallbackQuery.edit_message_text("أهلا بك 🌿 ")

  elif Method in ('PMake','PMerge','IMerge','Zip','TMerge') :
    if Method == 'PMerge':
      Word = 'الملفات'
      Cmd = '/P_Finish'
      C_Cmd = '/P_Clear'
    elif Method == 'Zip':
      Word = 'الملفات'
      Cmd = '/Z_Finish'
      C_Cmd = '/Z_Clear'
    elif Method == 'TMerge':
      Word = 'الملفات'
      Cmd = '/T_Finish'
      C_Cmd = '/T_Clear'
    elif Method == 'IMerge':
     if Msg_Id in ('SBS','UD') :
      replied = CallbackQuery.edit_message_text(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ")
      Key = f'IMerge_{User_Id}'
      Msgs_ids = '_'.join(Merge_Quee[Key][1])
      Item = f"IMerge_{Msgs_ids}_{Msg_Id}_{replied.id}_{User_Id}"
      Item_add(Item)
      del Merge_Quee[Key]
      return
     else :
      Word = 'الصور'
      Cmd = '/IM_Finish'
      C_Cmd = '/IM_Clear'
    
    elif Method == 'PMake':
      Word = 'الصور'
      Cmd = '/IP_Finish'
      C_Cmd = '/IP_Clear'
      
    Key = f'{Method}_{User_Id}'
    if Key in list(Merge_Quee.keys()):
     del Merge_Quee[Key]
    Merge_Quee[Key] = [[],[Callback_List[-1]]]
    M_Text = f"""
      ▪️عدد {Word} 👈 {len(Merge_Quee[Key][1])} ملفاً
      ▪️بعد الانتهاء اضغط الأمر 
      {Cmd}
      ▪️لإلغاء عملية الدمج ، اضغط الأمر 
      {C_Cmd}
      """
    Replied = CallbackQuery.edit_message_text(M_Text)
    Merge_Quee[Key][0].append(Replied.id)
  

  elif Method in ['Compress'] :           
        if file_msg.document.file_name.lower().endswith('pdf'):
          replied = CallbackQuery.edit_message_text(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ")
          File_Id = Callback_List[-1]
          Item = f"{Method}_{File_Id}_{replied.id}_{User_Id}"
          Item_add(Item)      
    
  elif Method in ('Trim','Renm'):
   bot.delete_messages(User_Id,CallbackQuery.message.id)
   if Method == 'Renm' :
     Renm_L.append(User_Id)
     Text = Renm_msg
   elif Method == 'Trim' :
     if file_msg.document :
       if file_msg.document.file_name.lower().endswith(('pdf','ppt','pptx','mdx')):
         Text = Pdf_Trim_Msg
       elif file_msg.document.file_name.lower().endswith('txt'):
        Text = Txt_Trim_Msg
   
   file_msg.reply_text(Text,reply_markup=ForceReply(True),reply_to_message_id=file_msg.id)
  
  elif Method in ('Ocr','2Pdf','Det','Ex','Marg','Unlock') :
   
    replied = CallbackQuery.edit_message_text(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ")
    File_Id = Callback_List[-1]
    Item = f"{Method}_{File_Id}_{replied.id}_{User_Id}"
    Item_add(Item)
 
##################################

@bot.on_message(filters.private & filters.reply)
def refunc(client,message):
   if (message.reply_to_message.reply_markup) and isinstance(message.reply_to_message.reply_markup, ForceReply)  :
    User_Id = message.from_user.id
    Msg_Text = message.text
    reply_id = message.reply_to_message_id
    reply_msg = Get_Msg(bot,User_Id,reply_id)
    file_id = reply_msg.reply_to_message_id
    file_msg = Get_Msg(bot,User_Id,file_id)
    message.delete()
  
    ReplyMsg_Text = reply_msg.text
    reply_msg.delete()
    Quee = public_q
    replied = file_msg.reply(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ")
    Pdf_Trim_Pattern = r"^\d+(?:[,-/]\d+(?:-\d+)?)*$"
    
    if User_Id in Renm_L :
      Process = 'Renm'
      Text = Msg_Text.replace(' ','|')
      Renm_L.remove(User_Id)

    elif re.search(Pdf_Trim_Pattern,Msg_Text) or '~' in Msg_Text  :
        Process = 'Trim'
        Text = Msg_Text.strip()
        if ' ' in Text:
          Text = Msg_Text.replace(' ','|')

    Item = f"{Process}_{file_id}_{Text}_{replied.id}_{User_Id}"
    Item_add(Item)

##############

bot.run()