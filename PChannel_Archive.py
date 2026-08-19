import nest_asyncio
nest_asyncio.apply()
import os

#########################################################


Api_Id = os.environ['Api_Id']
Api_Hash = os.environ['Api_Hash']
Session_String = os.environ['Session_String']
Channel_User = os.environ['Channel_User']

#########################################################


from pyrogram import Client,idle

import asyncio,shutil


Token_Identifier = Session_String.split('-')[0]
Session_file = Token_Identifier +'_session_bot'

bot = Client(Session_file,api_id=Api_Id,api_hash=Api_Hash,session_string=Session_String)

def Create_Dir(Dir):
  if not os.path.isdir(Dir):
    Mkdir_Cmd = f'mkdir -p "{Dir}"'
    os.system(Mkdir_Cmd)
      
def Check_Dir(Dir):
  if os.path.isdir(Dir):
      shutil.rmtree(Dir)
  Create_Dir(Dir)


def Insert_Txt(File,Msg):
  T_linebreak = '\n\n ◾ــــــــــــــ◾ \n\n'
  with open(File,'a') as f : 
   if Msg.text :
      Text = Msg.text
   else :
     if Msg.sticker : 
       return
     else :
      if Msg.chat.username :
        Link = f"« https://t.me/{Msg.chat.username}/{Msg.id} »"
      else : 
        Link = f"« https://t.me/c/{str(Msg.chat.id)[4:]}/{Msg.id} »"
      if Msg.caption == None : 
        Text = Link 
      else : 
        Text = Link +  '\n' + Msg.caption 
   f.write(Text+T_linebreak)

async def Channel_Arc(Channel_Id) :

      Arch_Dir = f'./Arch_Dir_{Channel_Id}/'
      Check_Dir(Arch_Dir)
      Arch_File = Arch_Dir +  f'Archive_{Channel_Id}.txt'
      Msgs_List = []
      async for Msg in bot.get_chat_history(Channel_Id) :
        Msgs_List.append(Msg)
      for Msg in reversed(Msgs_List):
        Insert_Txt(Arch_File,Msg)
      await bot.send_document("me",Arch_File,caption=Channel_Id)
      Check_Dir(Arch_Dir)
  

##############


def main():
    try:
        bot.start()
        asyncio.run(Channel_Arc(Channel_User))
        print("✅ تمت الأرشفة")
        idle()
    finally:
        if bot.is_connected:
            bot.stop()

main()