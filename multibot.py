import nest_asyncio,os
nest_asyncio.apply()

#########################################################

Bot_Token = os.getenv('TOKEN')

########################################################

from pyrogram.types import InlineKeyboardMarkup , InlineKeyboardButton , CallbackQuery , ForceReply,Message,ReplyKeyboardMarkup, KeyboardButton,ReplyKeyboardRemove
from pyrogram import Client, filters

from functools import reduce
import os,re,random, threading,time

from cookies_nodb import Image_forms,Video_Forms,Audio_Forms,Video_Options,Audio_Options,Aud_Comp_Buttons,Amplify_Buttons,Speed_Buttons,Slow_Buttons,Media_Trim_Msg,Renm_msg,Photo_Options,Photo_Multi_Options,Photo_Blur_buttons,Color_button,Pdf_Options,Pdf_Txt_Option,Pdf_Image_Option,Pdf_Multi_Options,Pdf_Refunc_Methods,Pdf_Trim_Msg,Txt_Trim_Msg,Renm_msg,Audio_Multi_Options,Other_Options,Cbx_Option,Vid_Cov_Ops,Main_Contract,Usage_Button,g_langs,Epub_Opts,Get_Token_Text,LANGS_Modules,Tracs_Modules,Ex_Pdf_Limit,Ppf_Opts,Gemini_Tokens,Gemini_Users

from common_func_nodb import Color_Pic,Pdf_Extract,Pdf_Page,Pdf_Trim,Pdf_Make,Pyrogram_Client,Check_File,Check_Dir,Pdf_Merge,Ocr_Func,Pdf_Margin,Upld_Dir_Func,Color_Pdf,Txt_2_Pdf,Unlock_Pdf,Rmv_Dups,Zip_Extract,Grap_PicDir,Merge_Images_UP,Merge_Images_SBS,Blur_Func,Mp3_Conv,Media_Amplify,Media_Change,Media_Skip,Media_Compress,Media_Speed,Media_Trim,Upld_File,Send_Text_Res,Aud_Merge,Encode_Vid,Vid_Mon,Dur_Get,Media_F_func,Send_TRes,Get_Name,Get_Msg,File_Dl,Epub_Extract_Func,Pdf_Page_Num,Mute_Video,Sub_Aud,PPF2PDF,Mdx2PDf,Pdf_Compress,Multi_Op_Dl,Txt_Trim,upld2arch,delarch_file,Zip_Func,Vid_Merge,Aud_Scatter,Msg_Dur,Get_Stream_Dur,Music_Rmv,Gemini_Trans_Txt,Gemini_Transcribe,Txt_Merge,Google_Trans_Txt,Raw_Blur,Crop_Vid

from pypdf import PdfReader

Merge_Quee = {}
public_q , private_q,Admins = [],[],[1186940323,]
private_members = [6098039779,1236198543,2003751632,6440064616,1765196641,7775025243,1456992715,6736984940,680598818,664059060,7229383434,1649989266,958661686,6789860311,5750681123,518652142,6485236479,347299497,7874755060,5922418349,1332413869,6996798634,6157937003,340557636,6975606829,503844199,503844199,623925692,2033748922,684585017,8308746353,7543819495,1746181153,1416457274,569672553,1186940323,7007648648]
Renm_L = []

Blur_Dict = {}


#######

Bot_Token = '8016797331:AAEFGbZ9wWG5mI4Gomcxrskiis-yAzJEgog'
bot,Bot_Identifier = Pyrogram_Client(Bot_Token)

#####

Close_Loop = False

Public_Loop = False
Private_Loop = False

main_dl_path = f'./downloads_{Bot_Identifier}/'


#### Bot Funcs ####

def Callback_Add(CallbackQuery):
  Quee = private_q if CallbackQuery.from_user.id in private_members else public_q
  replied = CallbackQuery.edit_message_text(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ")
  Item = CallbackQuery.data + f'_{replied.id}_{CallbackQuery.from_user.id}'
  Item_add(Item)

def Item_add(Item):
  User_Id = int(Item.split("_")[-1])
  Quee = private_q if User_Id in private_members else public_q
  Quee.append(Item)
  loop_name = "Private_Loop" if User_Id in private_members else "Public_Loop"
  if not globals()[loop_name] :	
    globals()[loop_name] = True
    Type = "PrivateQ" if User_Id in private_members else "MainQ"
    Multi_loop(Type)
    
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
        
        elif message.audio or message.voice :
          Word = 'الصوتيات'
          Cmd = '/A_Finish'
          C_Cmd = '/A_Clear'
        
        elif message.video :
          Word = 'الفيديوهات'
          Cmd = '/V_Finish'
          C_Cmd = '/V_Clear'

        elif message.document : 
          if message.document.file_name.lower().endswith(Image_forms) : 
            Word = 'الصور'
            if method == 'IMerge' :
              Cmd = '/IM_Finish'
              C_Cmd = '/IM_Clear'
            else :
              Cmd = '/IP_Finish'
              C_Cmd = '/IP_Clear'
          elif message.document.file_name.lower().endswith(Audio_Forms) : 
            Word = 'الصوتيات'
            Cmd = '/A_Finish'
            C_Cmd = '/A_Clear'
          elif message.document.file_name.lower().endswith(Video_Forms) : 
            Word = 'الفيديوهات'
            Cmd = '/V_Finish'
            C_Cmd = '/V_Clear'
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

def New_Member(message):
   CHOOSE_UR_BUTTONS = []
   for option in Usage_Button :
    CHOOSE_UR_BUTTONS.append([InlineKeyboardButton(option[0],callback_data=option[1]+'_'+str(message.id))])
   CHOOSE_UR_BUTTONS = Rmv_Dups(CHOOSE_UR_BUTTONS)
   message.reply(text = Main_Contract,reply_markup = InlineKeyboardMarkup(CHOOSE_UR_BUTTONS))
    

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

def Multi_loop(Type):
  Multi_Q = public_q if Type == "MainQ" else private_q
  dl_path = f'./downloads_{Type}_{Bot_Identifier}/'
  for obj in range (0,len(Multi_Q)) :
   if Type == "MainQ" : 
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
    bot.send_message(-1001655903083,C_Process)
    msg_list = C_Process.split('_')
    msg_id = msg_list[1]
    dl_path = f'./downloads_{Type}_{msg_id}_{Bot_Identifier}/'
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
        
      elif process in ['PMerge','AMerge','VMerge','IMerge','PMake','Montaj','Zip','SubAud','TMerge'] : 
        
        Files_Ids = msg_list[1:-2]
        if process == 'IMerge' :
          Files_Ids = msg_list[1:-3]
        Process_List = Multi_Op_Dl(bot,dl_path,Files_Ids,user_id)
        if process == 'PMerge' : 
          Res_File = Pdf_Merge(Process_List)
        elif process == 'TMerge':
          Res_File = Txt_Merge(Process_List)
            
        elif process == 'AMerge' :
          mergtxt = Process_List[0].split('.')[0] + '.txt'
          for File_Elm in Process_List :
            mp3_path = Mp3_Conv(File_Elm)
            open(mergtxt,'a').write(f"file '{mp3_path}' \n")
          Res_File = Aud_Merge(mergtxt)
        
        elif process == 'VMerge' :
          mergtxt = Process_List[0].split('.')[0] + '.txt'
          for File_Elm in Process_List :
            Main_Dir = ('.' if File_Elm[0] == '.' else '' ) + ('/'.join(File_Elm.split('/')[:-1])) + '/'
            New_Name = f"Vid_{random.randint(0,1000)}.mp4"
            New_File = Main_Dir+New_Name
            os.rename(File_Elm,New_File)
            open(mergtxt,'a').write(f"file '{New_File}' \n")
          Res_File = Vid_Merge(mergtxt)

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
         
        elif process == 'Montaj' :
          for item in Process_List :
            if item.lower().endswith(Image_forms):
              Img = item 
            else :
              Aud = item 
          Mp3_Path = Mp3_Conv(Aud)
          Res_File,Thumbnail = Vid_Mon(Img,Mp3_Path)
        
        elif process == 'SubAud' :
          for item in Process_List :
            if item.lower().endswith(Video_Forms):
              Vid = item 
            else :
              Aud = item 
          Res_File = Sub_Aud(Vid,Aud)

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
           if File.lower().endswith(('pdf','ppt','pptx','mdx')) :

            if File.lower().endswith(('ppt','pptx')) :
              File = PPF2PDF(File)
            elif File.lower().endswith(('mdx')) :
              File = Mdx2PDf(File)
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
          if File.lower().endswith('.epub'):
            Txt_File = Epub_Extract_Func(File)
            Upld_File(Txt_File,File_Msg)
          else :
            if File.lower().endswith(('.pdf','ppt','pptx','mdx')):
                  if File.lower().endswith(('ppt','pptx')) :
                    File = PPF2PDF(File)
                  elif File.lower().endswith(('mdx')) :
                    File = Mdx2PDf(File)
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
              elif File.lower().endswith(('ppt','pptx')) :
                File = PPF2PDF(File)
              elif File.lower().endswith(('mdx')) :
                 File = Mdx2PDf(File)
              Txt_File,Docx_File = Ocr_Func(File)
            
            if process == 'Trans' :
              Trans_Model = msg_list[3]
              if Trans_Model == 'Gemini' :
               try:
                Txt_File = Gemini_Trans_Txt(Txt_File,Rate)
               except Exception as err :
                 TxtFile = Txt_File.split('.')[0] + '_Translated.txt'
                 Rest_File = Txt_File.split('.')[0] + '_Translated_Rest.txt'
                 File_Msg.reply_document(TxtFile)
                 File_Msg.reply_document(Rest_File)
              
              elif Trans_Model == 'GTrans' : 
                Txt_File = Google_Trans_Txt(Txt_File,Rate)

              #else :
               # pass
                #Txt_File = Txt_Trans_Func(Txt_File,Rate)
            if File.lower().endswith(Image_forms):
              Send_Text_Res(File_Msg,open(Txt_File,'r').read())
            else :
              File_Msg.reply_document(Txt_File)
              if process == 'Ocr' :
                File_Msg.reply_document(Docx_File)
         
         elif process == 'ToArch' :
           upld2arch(File,File_Msg)

         elif process == 'Trac' :
          if msg_list[2] == 'Gemini' :
              Txt_File = Gemini_Transcribe(File)
          elif msg_list[2] == 'Wit' :
          	
              Stream_Dur = Dur_Get(File_Msg,File)
              Txt_File = Media_F_func(File,Stream_Dur,True if Type == 'MainQ' else False)
          elif msg_list[2] == 'Whisper' :
            pass
            # Txt_File = whisper_transcribe(File)
          Send_TRes(File_Msg,Txt_File)
        
         elif process == 'Mute' :
            Muted_Vid = Mute_Video(File)
            Upld_File(Muted_Vid,File_Msg)
  
         elif process == 'Frag':
            Parts_Dir = Aud_Scatter(File,int(Rate)*60)
            for file in sorted(os.listdir(Parts_Dir)):
              Res_File = Mp3_Conv(Parts_Dir+file)
              Upld_File(Res_File,File_Msg)
              
         elif process == 'MRMV' : 
            streamdur = Get_Stream_Dur(File)
            Prv_Members = private_members
            if streamdur > 120 and user_id not in Prv_Members :
                File_Msg.reply(f"المقطع يتجاوز الحد المسموح به 2 دقيقة  ☕️ ")
            else :
                Res_File = Music_Rmv(File_Msg,File,streamdur)

            """
            elif process ==  'TxtPdf' : 
              if File.lower().endswith('.txt'):
                Pdf_File = Txt_2_Pdf(File)
                File_Msg.reply_document(Pdf_File)
              elif File.lower().endswith(('cbz','cbr','zip','rar')) :
                File_Msg.reply('الميزة معطلة')
                
                Extract_Dir = Zip_Extract(File)
                Img_List = Grap_PicDir(Extract_Dir)
                if len(Img_List) != 0 :
                  Pdf_File = Pdf_Make(Img_List)
                  File_Msg.reply_document(Pdf_File)
                else : 
                  File_Msg.reply('لا توجد صورة في الملف ❌')
            """
            
  
         elif process in ('Color','Blur','Crop','Amplify','Compress','Speeden','Slowen','Marg','Unlock','2Pdf','Renm','Silence','Change','Convert') :
              if process == 'Color' :
                if File.lower().endswith(Image_forms): 
                  Res_File = Color_Pic(File,Rate)
                else :
                  Res_File = Color_Pdf(File,Rate)
              
              elif process == 'Crop' :
                Crop_Mode = Rate
                Res_File = Crop_Vid(File,Crop_Mode)

              elif process == 'Blur' :
                key = f"{user_id}_{File_Msg.id}"
                if File.lower().endswith(Image_forms): 
                  Res_File = Blur_Func(File,int(Rate))
                else : 
                 Blur_File = Blur_Dict[key]
                 Res_File = Raw_Blur(File,int(Rate),Blur_File)


                # if len(msg_list) == 5 : 
                #   Res_File = Blur_Func(File,int(Rate))
                # elif len(msg_list) == 6 : 
                #   if msg_list[3] == 'dfull' : 
                #     Res_File = Blur_Func(File,int(Rate))
                #   else :
                #     Ranges = msg_list[3]
                #     Res_File = Raw_Blur(File,int(Rate),Ranges)
              
              elif process == 'Renm':
               Ext = File.split('.')[-1]
               Res_File = f"{dl_path}{Rate.replace('|',' ')}.{Ext}"
               Cmd = f'mv "{File}" "{Res_File}"'
               os.system(Cmd)

              elif process == '2Pdf' : 
                if File.lower().endswith(('ppt','pptx')) :
                  Res_File = PPF2PDF(File)
                elif File.lower().endswith(('mdx')) :
                 Res_File = Mdx2PDf(File)
                elif File.lower().endswith('txt') :
                  Res_File = Txt_2_Pdf(File)
              elif process == 'Marg' :
               if File.lower().endswith(('ppt','pptx')) :
                File = PPF2PDF(File)
               elif File.lower().endswith(('mdx')) :
                File = Mdx2PDf(File)
               if Pdf_Page_Num(File) < Ex_Pdf_Limit : 
                Res_File = Pdf_Margin(File)
               else :
                  File_Msg.reply(f'حد الملف {Ex_Pdf_Limit} ميغا')
              elif process == 'Unlock' :
               if File.lower().endswith(('ppt','pptx')) :
                Res_File = PPF2PDF(File)
               elif File.lower().endswith(('mdx')) :
                Res_File = Mdx2PDf(File)
               else :
                if Pdf_Page_Num(File) < Ex_Pdf_Limit : 
                  Res_File = Unlock_Pdf(File)
                else :
                    File_Msg.reply(f'حد الملف {Ex_Pdf_Limit} صفحة')
              elif process == 'Amplify' : 
                Res_File = Media_Amplify(File,Rate)
              elif process == 'Compress' :
                if File.lower().endswith('pdf'):
                  Res_File = Pdf_Compress(bot,dl_path,File)
                else :
                  Res_File = Media_Compress(File,Rate)
              elif process == 'Speeden' : 
                Res_File = Media_Speed(File,Rate)
              elif process == 'Slowen' : 
               Res_File = Media_Speed(File,Rate)
              elif process == 'Change' : 
               Res_File = Media_Change(File)
              
              elif process == 'Convert' : 
               if File.lower().endswith(Audio_Forms) :
                Res_File = Mp3_Conv(File)
               else :
                if Rate == '2mp3':
                  Res_File = Mp3_Conv(File)
                else :
                  Res_File = Encode_Vid(File)

              elif process == 'Silence' : 
                Res_File = Media_Skip(File)
              Upld_File(Res_File,File_Msg)
              
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
        return Multi_loop(Type)
    else :
      loop_name = "Public_Loop" if Type == "MainQ" else "Private_Loop"
      if globals()[loop_name] :	
        globals()[loop_name] = False

###### Bot Funcs #####

@bot.on_message(filters.command('clear') & filters.text & filters.private)
def _telegram_file(client, message):
 admins = Admins
 if message.from_user.id in admins :
   private_q.clear()
   message.reply('تم الحذف')

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
      Quee = private_q if User_Id in private_members else public_q
      replied = Replied_Msg.edit_text(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ")
      Key = f'{Method}_{message.from_user.id}'
      Msgs_ids = '_'.join(Merge_Quee[Key][1])
      Item = f"{Method}_{Msgs_ids}_{replied.id}_{message.from_user.id}"
      del Merge_Quee[Key]
      Item_add(Item)
      
      
@bot.on_message(filters.command('add_token') & filters.private)
def command1(bot,message):
 User_Id = message.from_user.id
 message.reply_text(Get_Token_Text,reply_markup=ForceReply(True),reply_to_message_id=message.id)

@bot.on_message(filters.command('start') & filters.private)
def command1(bot,message):
   User_Id = message.from_user.id
   message.reply('لبقية البوتات \n\n @sunnay6626')
   #My_Db.Insert_User(message.from_user.id)
  
######## Admin Funcs ###$

@bot.on_message(filters.command('users') & filters.text & filters.private)
def _telegram_file(client, message):
 admins = Admins
 if message.from_user.id in admins :
   Bot_Members = private_members
   Members_String = ""
   Buttons = []
   for Member in Bot_Members :
     try :
       Member_Name = "=U | " + bot.get_users(int(Member)).first_name + ' 👉 ' 
       Members_String += Member_Name
     except :
       Members_String += "=U | "
     try :
       Member_Name = '@' + bot.get_users(int(Member)).username + ' 👉 ' 
       Members_String += Member_Name
     except :
       pass
     try :
       Member_Name = bot.get_users(int(Member)).first_name
       Buttons.append([InlineKeyboardButton(Member_Name, url=f"tg://openmessage?user_id={Member}")])
     except :
       Buttons.append([InlineKeyboardButton(Member, url=f"tg://openmessage?user_id={Member}")])
     Members_String +=  f'`{Member}`'  + '\n'
   msgusers = ' 🟥 قائمة المستخدمين \n\n' + Members_String
   message.reply(msgusers,reply_markup=InlineKeyboardMarkup(Buttons))
   
@bot.on_message(filters.command('adduser') & filters.text & filters.private)
def _telegram_file(client, message):
 admins = Admins
 if message.from_user.id in admins :
  msg_str_list = message.text.split(' ')
  if len(msg_str_list) == 2 :
   userid = int(msg_str_list[1])
   private_members.append(userid)
  else : 
    del msg_str_list[0]
    for usid in msg_str_list : 
      private_members.append(usid)
  message.reply('تمت التعبئة')


@bot.on_message(filters.command('deluser') & filters.text & filters.private)
def _telegram_file(client, message):
 admins = Admins
 if message.from_user.id in admins :
  msg_str_list = message.text.split(' ')
  if len(msg_str_list) == 2:
   userid = int(msg_str_list[1])
   private_members.remove(userid)
  else : 
    del msg_str_list[0]
    for usid in msg_str_list : 
      private_members.remove(usid)
  message.reply('تمت التعبئة')

#####

@bot.on_message(filters.private & filters.incoming & (filters.photo | filters.audio | filters.voice | filters.video | filters.document ))
def _telegram_file(client, message):
    
  User_Id = message.from_user.id
  Zip_Key = f'Zip_{User_Id}'
  Montaj_Key = f'Montaj_{User_Id}'
  IMerge_Key = f'IMerge_{User_Id}'
  Pmake_Key = f'PMake_{User_Id}'
  AMerge_Key = f'AMerge_{User_Id}'
  VMerge_Key = f'VMerge_{User_Id}'
  SubAud_Key = f'SubAud_{User_Id}'
  PMerge_Key = f'PMerge_{User_Id}'
  TMerge_Key = f'TMerge_{User_Id}'
  if Zip_Key in list(Merge_Quee.keys()):
    Universal_Concat(message,Merge_Quee,Zip_Key)
    return
  else :
    if Montaj_Key in list(Merge_Quee.keys()) or SubAud_Key in list(Merge_Quee.keys()) :
      Key = (Montaj_Key if Montaj_Key in list(Merge_Quee.keys()) else SubAud_Key)
      if (message.voice or message.photo or message.audio) or (message.document.file_name.lower().endswith(Image_forms+Audio_Forms)) :
        Merge_Quee[Key][1].append(str(message.id))
        Replied_Id = Merge_Quee[Key][0][0]
        Replied_Msg = Get_Msg(bot,User_Id,Replied_Id)
        
        Quee = private_q if User_Id in private_members else public_q
        replied = Replied_Msg.edit_text(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ")
        Msgs_ids = '_'.join(Merge_Quee[Key][1])
        Item = f"{Key.split('_')[0]}_{Msgs_ids}_{replied.id}_{User_Id}"
        del Merge_Quee[Key]
        Item_add(Item)
        return None
      
    elif IMerge_Key in list(Merge_Quee.keys()):
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
    elif AMerge_Key in list(Merge_Quee.keys()):
     if message.audio or message.voice or message.document.file_name.lower().endswith(Audio_Forms) :
      Universal_Concat(message,Merge_Quee,AMerge_Key)
      return
    elif VMerge_Key in list(Merge_Quee.keys()):
     if message.video or message.document.file_name.lower().endswith(Video_Forms) :
      Universal_Concat(message,Merge_Quee,VMerge_Key)
      return
    elif TMerge_Key in list(Merge_Quee.keys()):
     if message.document.file_name.lower().endswith('txt') :
      Universal_Concat(message,Merge_Quee,TMerge_Key)
      return

  if message.photo : 
      Options =  Photo_Options + Pdf_Image_Option
  
  elif message.audio or message.voice : 
      Options = Audio_Options

  elif message.video : 
   Options = Video_Options
   
  elif message.document : 
   
   if message.document.file_name.lower().endswith(Image_forms) : 
      Options = Photo_Options + Pdf_Image_Option
     
   elif message.document.file_name.lower().endswith(Video_Forms) : 
     Options = Video_Options
     
   elif message.document.file_name.lower().endswith(Audio_Forms) : 
     
      Options = Audio_Options
   
   elif message.document.file_name.lower().endswith(('pdf','ppt','pptx','mdx')) : 
       if message.document.file_name.lower().endswith('pdf'):
        Options = Pdf_Options
       else :
         Options = Ppf_Opts
   
   elif message.document.file_name.lower().endswith('txt') : 
     
     Options = Pdf_Txt_Option
   
   elif message.document.file_name.lower().endswith(('cbz','cbr','zip','rar')) : 
     
     Options = Cbx_Option
   
   elif message.document.file_name.lower().endswith('epub'): 
     Options = Epub_Opts
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
  Prv_Members = private_members
  User_Id = CallbackQuery.from_user.id
  Quee = private_q if User_Id in private_members else public_q
  Callback_List = CallbackQuery.data.split('_')
  Method = Callback_List[0]
  Msg_Id = Callback_List[1]
  if not Msg_Id in ('SBS','UD'):
    file_msg = Get_Msg(bot,User_Id,Msg_Id)
  if Method == 'Yes':
    prv_users = private_members
    if User_Id not in prv_users :
     pass
    CallbackQuery.edit_message_text("أهلا بك 🌿 ")
  
  elif Method == 'No':
    CallbackQuery.edit_message_text("شكراً لك على صدقك🌿 ")
  elif Method == 'DelArch':
    Replied = CallbackQuery.edit_message_text("جار الحذف 🌿")
    Arch_Url = CallbackQuery.message.text
    File_Name = Arch_Url.split('/')[-1]
    delarch_file(File_Name)
    Replied.edit_text("تم الحذف 🌿")

  elif Method in ('Trans','Trac'):
   
   if Method == 'Trac':
    if len(Callback_List) == 3 :
      if Callback_List[2] == 'Gemini':
       if User_Id not in Prv_Members : 
        CallbackQuery.edit_message_text(f"هذه الميزة خاصة  ☕ ")
        return
       if not User_Id in Gemini_Users :
        CallbackQuery.edit_message_text(f"هذه الميزة معطلة  ☕ ")
       else : 
         Callback_Add(CallbackQuery)
      else :
        Callback_Add(CallbackQuery)
    
    elif len(Callback_List) == 2 :
      CHOOSE_UR_Mod = "اختر النموذج "
      Tracs_BUTTONS = []
      for Mod in Tracs_Modules : 
        Data = f"{CallbackQuery.data}_{Mod[1]}"
        Tracs_BUTTONS.append([InlineKeyboardButton(Mod[0],callback_data=Data)])
      CallbackQuery.edit_message_text(text = CHOOSE_UR_Mod,reply_markup = InlineKeyboardMarkup(Tracs_BUTTONS))

   elif Method == 'Trans':
    if len(Callback_List) == 4 :
      if Callback_List[3] == 'Gemini':
       if not User_Id in Gemini_Users :
        CallbackQuery.edit_message_text(f"هذه الميزة معطلة  ☕ ")
       else : 
         Callback_Add(CallbackQuery)
      else :
        Callback_Add(CallbackQuery)
    
    elif len(Callback_List) == 3 :
      CHOOSE_UR_Mod = "اختر النموذج "
      LANGS_BUTTONS = []
      for Mod in LANGS_Modules : 
        Data = f"{CallbackQuery.data}_{Mod[1]}"
        LANGS_BUTTONS.append([InlineKeyboardButton(Mod[0],callback_data=Data)])
      CallbackQuery.edit_message_text(text = CHOOSE_UR_Mod,reply_markup = InlineKeyboardMarkup(LANGS_BUTTONS))
    else :
      CHOOSE_UR_LANG = "اختر اللغة المراد الترجمة إليها"
      LANGS_BUTTONS = []
      for lang in g_langs : 
        
        Rom_Num = int(len(g_langs)/3)
        Data = f"{CallbackQuery.data}_{lang.split('|')[-1].strip()}"
        if g_langs.index(lang) > Rom_Num-1 :
         LANGS_BUTTONS[g_langs.index(lang)%Rom_Num].append(InlineKeyboardButton(lang.split('|')[0],callback_data=Data))
        else : 
         LANGS_BUTTONS.append([InlineKeyboardButton(lang.split('|')[0],callback_data=Data)])
      CallbackQuery.edit_message_text(text = CHOOSE_UR_LANG,reply_markup = InlineKeyboardMarkup(LANGS_BUTTONS))
      
  elif Method in ('Montaj','SubAud'):
      #Clear_Dict(Merge_Quee,User_Id)
      Key = f'{Method}_{User_Id}'
      if Method == 'Montaj' :
       if Key in list(Merge_Quee.keys()):
        del Merge_Quee[Key]
       Merge_Quee[Key] = [[],[Callback_List[-1]]]
       if file_msg.document :
         if file_msg.document.file_name.lower().endswith(Image_forms):
           Word = 'الصوتية'
         else :
           Word = 'الصورة'
       elif file_msg.photo :
         Word = 'الصوتية'
       else :
         Word = 'الصورة'
       M_Text = f'الآن أرسل {Word} 🌿'
       Replied = CallbackQuery.edit_message_text(M_Text)
       Merge_Quee[Key][0].append(Replied.id)
      
      elif Method == 'SubAud' :
       if Key in list(Merge_Quee.keys()):
        del Merge_Quee[Key]
       Merge_Quee[Key] = [[],[Callback_List[-1]]]
       M_Text = f'الآن أرسل الصوتية 🌿'
       Replied = CallbackQuery.edit_message_text(M_Text)
       Merge_Quee[Key][0].append(Replied.id)

  elif Method in ('PMake','IMerge','PMerge','AMerge','VMerge','VMerge','Zip','TMerge') :
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
      
    elif Method == 'AMerge':
    
      Word = 'الصوتيات'
      Cmd = '/A_Finish'
      C_Cmd = '/A_Clear'
    
    elif Method == 'VMerge' :
      if User_Id not in Prv_Members : 
        CallbackQuery.edit_message_text(f"هذه الميزة خاصة  ☕ ")
        return
      Word = 'الفيديوهات'
      Cmd = '/V_Finish'
      C_Cmd = '/V_Clear'

    #Clear_Dict(Merge_Quee,User_Id)
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
  
     
  elif Method == 'Crop' :
    key = f'{User_Id}_{file_msg.id}'
    callback_dict[key] = CallbackQuery.data.strip()
    CallbackQuery.message.delete()
    Text = 'اختر نمط الـCrop \n\n سيتم بتر الجزء المختار من المقطع'
    Buttons = [
          [KeyboardButton("RightHalf"), KeyboardButton("LeftHalf")],
          [KeyboardButton("UpperHalf"), KeyboardButton("LowerHalf")],
          [KeyboardButton("RightThird"), KeyboardButton("LeftThird")],
          [KeyboardButton("UpperThird"), KeyboardButton("LowerThird")]]
    replied = file_msg.reply_text(text = Text,reply_markup = ReplyKeyboardMarkup(Buttons, resize_keyboard=True))


  elif Method in ['Color','Blur','Crop','Amplify','Compress','Speeden','Slowen','Convert'] :
   if len(Callback_List) > 2 : 
     if Callback_List[-1] == '2mp4' :
       if file_msg.document :
        if file_msg.document.file_name.lower().endswith('mp4'):
          replied = CallbackQuery.edit_message_text(f"جار العمل ☕")
          File = File_Dl(file_msg,main_dl_path)
          Upld_File(File,file_msg)
          os.remove(File)
          replied.edit_text('تم ✅')
        else :
          Callback_Add(CallbackQuery)
       
     elif Callback_List[-1] == '2ogg' :
        replied = CallbackQuery.edit_message_text(f"جار العمل ☕")
        File = File_Dl(file_msg,main_dl_path)
        if file_msg.document :

          if file_msg.document.file_name.lower().endswith(Video_Forms):
            File = Mp3_Conv(File)
        
        elif file_msg.video :

          File = Mp3_Conv(File)
        
        file_msg.reply_voice(File)
        os.remove(File)
        replied.edit_text('تم ✅')

     else :
      if not Method == 'Blur' :
        Callback_Add(CallbackQuery)
      else : 
        if file_msg.photo : 
          Callback_Add(CallbackQuery)
        elif file_msg.video : 
          key = f'{User_Id}_{file_msg.id}'
          callback_dict[key] = CallbackQuery.data.strip()
          CallbackQuery.message.delete()
          Text = 'اختر نمط البلور'
          Buttons = [
                [KeyboardButton("Ranges"), KeyboardButton("Full Vid")]
            ]
          replied = file_msg.reply_text(text = Text,reply_markup = ReplyKeyboardMarkup(Buttons, resize_keyboard=True))

        elif file_msg.document : 
          if file_msg.document.file_name.lower().endswith(Image_forms) :
            Callback_Add(CallbackQuery)
          elif file_msg.document.file_name.lower().endswith(Video_Forms) :
            key = f'{User_Id}_{file_msg.id}'
            callback_dict[key] = CallbackQuery.data.strip()
            CallbackQuery.message.delete()
            Text = 'اختر نمط البلور'
            Buttons = [
                [KeyboardButton("Ranges"), KeyboardButton("Full Vid")]
            ]
            replied = file_msg.reply_text(text = Text,reply_markup = ReplyKeyboardMarkup(Buttons, resize_keyboard=True))   

   else : 
    CHOOSE_UR_BUTTONS = []
    CHOOSE_UR_Option = "اختر ما تريد "
    if Method == 'Color':
      Buttons = Color_button
    elif Method == 'Blur':
      Buttons = Photo_Blur_buttons
    elif Method == 'Amplify':
      Buttons = Amplify_Buttons
    
    elif Method in ('Compress','Convert'):
     
     if Method == 'Convert':
       if file_msg.document :
        if file_msg.document.file_name.lower().endswith(Audio_Forms):
         Callback_Add(CallbackQuery)
         return
        else :
          Buttons = Vid_Cov_Ops
       elif file_msg.audio or file_msg.voice :
         if file_msg.voice :
           Buttons = Vid_Cov_Ops[1:-1]
         else :
          Buttons = Vid_Cov_Ops[:-2]
        #  Callback_Add(CallbackQuery)
        #  return
       else :
          if file_msg.video :
              Buttons = Vid_Cov_Ops[:-1]
     
     elif Method == 'Compress':
      if file_msg.document :
        if file_msg.document.file_name.lower().endswith(Video_Forms):
          Callback_Add(CallbackQuery)
          return
        elif file_msg.document.file_name.lower().endswith(Audio_Forms):
          Buttons = Aud_Comp_Buttons
        elif file_msg.document.file_name.lower().endswith('pdf'):
          replied = CallbackQuery.edit_message_text(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ")
          File_Id = Callback_List[-1]
          Item = f"{Method}_{File_Id}_{replied.id}_{User_Id}"
          Item_add(Item)
          return 
      elif file_msg.video : 
        Callback_Add(CallbackQuery)
        return
      else :
        Buttons = Aud_Comp_Buttons
    elif Method == 'Speeden':
      Buttons = Speed_Buttons
    elif Method == 'Slowen':
      Buttons = Slow_Buttons
    for method in Buttons : 
       Text = method[0]
       Data = CallbackQuery.data + '_' + method[1]
       CHOOSE_UR_BUTTONS.append([InlineKeyboardButton(Text,callback_data=Data)])
    
    CallbackQuery.edit_message_text(text = CHOOSE_UR_Option,reply_markup = InlineKeyboardMarkup(CHOOSE_UR_BUTTONS))
    
  elif Method in ('Trim','Renm','Frag'):
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
       else :
         Text = Media_Trim_Msg
     else :
       Text = Media_Trim_Msg
   elif Method == 'Frag' :
     Text = "الآن أرسل عدد الدقائق لكل قطعة صوتية"
   file_msg.reply_text(Text,reply_markup=ForceReply(True),reply_to_message_id=file_msg.id)
  
  elif Method in ('Ocr','2Pdf','Det','Ex','Marg','Unlock','Change','Silence','Details','Mute','ToArch','MRMV') :
    if Method == 'ToArch' and User_Id not in Prv_Members : 
        CallbackQuery.edit_message_text(f"هذه الميزة خاصة  ☕ ")
        return
    if Method == 'MRMV' and User_Id not in Prv_Members and Msg_Dur(file_msg) > 120 :
       CallbackQuery.edit_message_text(f"المقطع يتجاوز الحد المسموح به 2 دقيقة  ☕️ ")
       return
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
    Gemini_Token_Pattern = "^AIzaSy.*"
    # if re.search(Gemini_Token_Pattern,Msg_Text) :
    #   Gemini_Token = Msg_Text.strip()
    #   GTokens = Gemini_Tokens
    #   if Gemini_Token in GTokens : 
    #      reply_msg.reply('التوكن موجود بالفعل ، استعمل غيره 🌿')
    #   else : 
    #       tokentext = f"{User_Id}_{Gemini_Token}_#gtokens"
    #       bot.send_message(-1001655903083,tokentext)
    #       reply_msg.reply('تمت إضافة التوكن لقاعدة البيانات ✅')
    #   reply_msg.delete()
    # else :
    ReplyMsg_Text = reply_msg.text
    reply_msg.delete()
    Quee = private_q if User_Id in private_members else public_q
    replied = file_msg.reply(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ")
    Pdf_Trim_Pattern = r"^\d+(?:[,-/]\d+(?:-\d+)?)*$"
    Media_Trim_Pattern = r"\d{,2}:\d{2}"
    if 'عدد الدقائق' in ReplyMsg_Text :
        Process = 'Frag'
        Text = Msg_Text
    
    elif User_Id in Renm_L :
      Process = 'Renm'
      Text = Msg_Text.replace(' ','|')
      Renm_L.remove(User_Id)

    elif re.search(Pdf_Trim_Pattern,Msg_Text) or re.search(Media_Trim_Pattern,Msg_Text) or '~' in Msg_Text  :
        Process = 'Trim'
        Text = Msg_Text.strip()
        if ' ' in Text:
          Text = Msg_Text.replace(' ','|')

    Item = f"{Process}_{file_id}_{Text}_{replied.id}_{User_Id}"
    Item_add(Item)

##############

@bot.on_message(filters.private & filters.incoming & filters.text)
def _telegram_file(client, message):
  User_Id = message.from_user.id
  Callback_Keys = list(callback_dict.keys())
  if any(str(User_Id) in key for key in Callback_Keys) :
    for Key in Callback_Keys :
      if str(User_Id) in Key :
        key = Key
    CallbackList = callback_dict[key].split('_')
    process = CallbackList[0]
    file_id = CallbackList[1]
    
    if process == 'Blur' :
      if key not in list(Blur_Dict.keys()) :
        Blur_Dict[key] = {'isfull':True,'MainBlur':'','RightHalf':'','LeftHalf':'','UpperHalf':'','LowerHalf':'','RightThird':'','LeftThird':'','UpperThird':'','LowerThird':'','RightThirdLeft':'','LeftThirdLeft':'','UpperThirdLeft':'','LowerThirdLeft':'','FullFrame':'','RightHalfK':False,"LeftHalfK":False,"UpperHalfK":False,"LowerHalfK":False,"RightThirdK":False,"LeftThirdK":False,"UpperThirdK":False,"LowerThirdK":False,"RightThirdLeftK":False,"LeftThirdLeftK":False,"UpperThirdLeftK":False,"LowerThirdLeftK":False,"FullFrameK":False}
      
      if Blur_Dict[key]['RightHalfK'] or Blur_Dict[key]['LeftHalfK'] or Blur_Dict[key]['UpperHalfK'] or Blur_Dict[key]['LowerHalfK'] or Blur_Dict[key]['RightThirdK'] or Blur_Dict[key]['LeftThirdK'] or Blur_Dict[key]['UpperThirdK'] or Blur_Dict[key]['LowerThirdK'] or Blur_Dict[key]['RightThirdLeftK'] or Blur_Dict[key]['LeftThirdLeftK'] or Blur_Dict[key]['UpperThirdLeftK'] or Blur_Dict[key]['LowerThirdLeftK'] or Blur_Dict[key]['FullFrameK']  :
        
        if Blur_Dict[key]['RightHalfK'] :
          Blur_Dict[key]['RightHalf'] = message.text
          Blur_Dict[key]['RightHalfK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['LeftHalfK'] :
          Blur_Dict[key]['LeftHalf'] = message.text
          Blur_Dict[key]['LeftHalfK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['UpperHalfK'] :
          Blur_Dict[key]['UpperHalf'] = message.text
          Blur_Dict[key]['UpperHalfK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['LowerHalfK'] :
          Blur_Dict[key]['LowerHalf'] = message.text
          Blur_Dict[key]['LowerHalfK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['RightThirdK'] :
          Blur_Dict[key]['RightThird'] = message.text
          Blur_Dict[key]['RightThirdK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['LeftThirdK'] :
          Blur_Dict[key]['LeftThird'] = message.text
          Blur_Dict[key]['LeftThirdK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['UpperThirdK']:
          Blur_Dict[key]['UpperThird'] = message.text
          Blur_Dict[key]['UpperThirdK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['LowerThirdK'] :
          Blur_Dict[key]['LowerThird'] = message.text
          Blur_Dict[key]['LowerThirdK'] = False
          message.reply('تم التلقيم')
        
        elif Blur_Dict[key]['RightThirdLeftK'] :
          Blur_Dict[key]['RightThirdLeft'] = message.text
          Blur_Dict[key]['RightThirdLeftK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['LeftThirdLeftK'] :
          Blur_Dict[key]['LeftThirdLeft'] = message.text
          Blur_Dict[key]['LeftThirdLeftK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['UpperThirdLeftK']:
          Blur_Dict[key]['UpperThirdLeft'] = message.text
          Blur_Dict[key]['UpperThirdLeftK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['LowerThirdLeftK'] :
          Blur_Dict[key]['LowerThirdLeft'] = message.text
          Blur_Dict[key]['LowerThirdLeftK'] = False
          message.reply('تم التلقيم')
        
        elif Blur_Dict[key]['FullFrameK'] :
          Blur_Dict[key]['FullFrame'] = message.text
          Blur_Dict[key]['FullFrameK'] = False
          message.reply('تم التلقيم')
        


      if message.text in ['Full Vid','Ranges'] :
        if message.text == 'Full Vid' :
          Text = 'اختر نمط البلور'
        elif message.text == 'Ranges' :
          Blur_Dict[key]['isfull'] = False
          Text = 'اختر المدى مع ما يناسب '
        Buttons = [
          [KeyboardButton("FullFrame")],
          [KeyboardButton("RightHalf"), KeyboardButton("LeftHalf")],
          [KeyboardButton("UpperHalf"), KeyboardButton("LowerHalf")],
          [KeyboardButton("RightThird"), KeyboardButton("LeftThird")],
          [KeyboardButton("UpperThird"), KeyboardButton("LowerThird")],
          [KeyboardButton("RightThirdLeft"), KeyboardButton("LeftThirdLeft")],
          [KeyboardButton("UpperThirdLeft"), KeyboardButton("LowerThirdLeft")]
          ]
        if message.text == 'Ranges' :
          Buttons += [[KeyboardButton("✔️")]]
        replied = message.reply_text(text = Text,reply_markup = ReplyKeyboardMarkup(Buttons,resize_keyboard=True))
        
      
      elif message.text in ['RightHalf','LeftHalf','UpperHalf','LowerHalf','RightThird','LeftThird','UpperThird','LowerThird','RightThirdLeft','LeftThirdLeft','UpperThirdLeft','LowerThirdLeft','FullFrame'] :
        if Blur_Dict[key]['isfull'] :
          Blur_Dict[key]['MainBlur'] = message.text
          Item = callback_dict[key]
          Quee = private_q if User_Id in private_members else public_q
          replied = message.reply(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ",reply_markup=ReplyKeyboardRemove())
          Item = Item + f'_{replied.id}_{User_Id}'
          Item_add(Item)
          callback_dict.pop(key)
        else : 
          Text = f'''الآن أرسل نطاقات الـ {message.text} بهذه الصورة
            hh:mm:ss-hh:mm:ss
            ويمكنك إرسال أكثر من مدى بهذه الصورة بترك مسافة بين كل مدى
            hh:mm:ss-hh:mm:ss hh:mm:ss-hh:mm:ss hh:mm:ss-hh:mm:ss
            '''
          Blur_Dict[key][message.text+'K'] = True
          message.reply(Text)
      
      elif message.text == '✔️' :
          Item = callback_dict[key]
          Quee = private_q if User_Id in private_members else public_q
          replied = message.reply(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ",reply_markup=ReplyKeyboardRemove())
          Item = Item + f'_{replied.id}_{User_Id}'
          Item_add(Item)
          callback_dict.pop(key)

    elif process == 'Crop' :
      Crop_Mode = message.text 
      Item = callback_dict[key]
      Quee = private_q if User_Id in private_members else public_q
      replied = message.reply(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ",reply_markup=ReplyKeyboardRemove())
      Item = Item + f'_{Crop_Mode}_{replied.id}_{User_Id}'
      Item_add(Item)
      callback_dict.pop(key)



def main():
    try:
        bot.start()
        print("✅ Blur Bot is ONLINE!")
        idle()
    finally:
        if bot.is_connected:
            bot.stop()

main()