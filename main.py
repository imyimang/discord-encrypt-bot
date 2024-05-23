from cryptography.fernet import Fernet
from discord.ext import commands,tasks
from itertools import cycle
import discord
import aiohttp
import os
import json


data = json.load(open("config.json", encoding="utf-8")) 



bot = commands.Bot(command_prefix=data["prefix"], intents=discord.Intents.all())


status = cycle(['安全加密機器人', '無日誌加解密檔案']) #機器人顯示的個人狀態(可自行更改,要刪除這行也可以)


@tasks.loop(seconds=10)  # 每隔10秒更換一次機器人個人狀態
async def change_status():
    await bot.change_presence(activity=discord.Game(next(status)))


@bot.event
async def on_ready():
    slash = await bot.tree.sync()
    print(f"目前登入身份 --> {bot.user}")
    print(f"載入 {len(slash)} 個斜線指令")
    change_status.start()



@bot.tree.command(name="help", description="查看指令使用說明") 
async def help(ctx):
    await ctx.response.send_message("# 指令說明\n* **/help** 查看指令說明\n* **/生成金鑰** 生成加密金鑰，如果已經有金鑰將會被覆蓋\n* **/設定金鑰** 設定你的解密金鑰(解密他人檔案時可以用到)\n* **/查詢金鑰** 查詢你當前預設的金鑰\n* **/加密** 用金鑰加密你的檔案(檔案最大15MB)，如果還沒有金鑰會先生成一個，optional_key為選填，如果填寫本次就會用該金鑰解密，沒有填寫就會用預設金鑰解密，預設金鑰可以用**/查詢金鑰**來查詢\n* **/解密** 用金鑰解密你的檔案(檔案最大15MB)，如果要解密其他金鑰加密的檔案請用**/設定金鑰**，optional_key為選填，如果填寫本次就會用該金鑰解密，沒有填寫就會用預設金鑰解密，預設金鑰可以用**/查詢金鑰**來查詢\n\n *made by* [*yimang*](https://github.com/imyimang/discord-encrypt-bot)\n[邀請機器人](https://discord.com/oauth2/authorize?client_id=1242337935022624788&permissions=551903332352&scope=bot)", ephemeral=True)



@bot.tree.command(name="生成金鑰", description="重新生成你的加密金鑰(先前加密的檔案將無法解密)") 
async def generate_key(ctx):
    try:
        key = Fernet.generate_key()
        with open(f"keys/{ctx.user.id}.key", "wb") as key_file:
            key_file.write(key)
            key = key.decode('utf-8')
        await ctx.response.send_message(f"已重新生成加密金鑰，請妥善保管，遺失後將無法解密檔案:\n**{key}**", ephemeral=True)
    except Exception as e:
        await ctx.response.send_message(f"生成失敗:\n**{e}**", ephemeral=True)



@bot.tree.command(name="查詢金鑰", description="查詢你當前的加密金鑰") 
async def check_key(ctx):

    path = f"keys/{ctx.user.id}.key"
    if not os.path.exists(path) or os.path.getsize(path)==0:
        await ctx.response.send_message(f"並無已生成的金鑰，請使用/加密 或 /生成金鑰來獲取金鑰", ephemeral=True)
        return
    
    try:
        with open(path, "rb") as file:
            data = file.read()
            key = data.decode('utf-8')
        await ctx.response.send_message(f"你的金鑰是:\n**{key}**", ephemeral=True)
    except Exception as e:
        await ctx.response.send_message(f"查詢失敗:\n**{e}**", ephemeral=True)



@bot.tree.command(name="設定金鑰", description="重新設定你的加密金鑰(先前加密的檔案將無法解密)") 
async def set_key(ctx, key:str):
    try:
        with open(f"keys/{ctx.user.id}.key", "wb") as key_file:
            msg_2 = bytes(key, 'utf-8')
            key_file.write(msg_2)
        await ctx.response.send_message(f"已更改加密金鑰:\n**{msg_2.decode('utf-8')}**", ephemeral=True)
    
    except Exception as e:
        await ctx.response.send_message(f"設定失敗:\n**{e}**", ephemeral=True)



@bot.tree.command(name="加密", description="加密你的檔案") 
async def encrypt_command(ctx: discord.Interaction, the_file: discord.Attachment,optional_key:str = None):
    if the_file.size > 15728640:
        await ctx.response.send_message("檔案過大!檔案不可大於15MB", ephemeral=True)
        return
    
    path = f"keys/{ctx.user.id}.key"

    if (not os.path.exists(path) or os.path.getsize(path)==0) and not optional_key:  
        key = Fernet.generate_key()
        with open(f"keys/{ctx.user.id}.key", "wb") as key_file:
            key_file.write(key)
            key = key.decode('utf-8')
        no_key = f"未找到已經存在的金鑰，已生成新的金鑰:\n**{key}**\n請妥善保管，遺失後將無法解密檔案\n\n"     
    else:
        no_key = ""

    try:
        if ctx.user == bot.user:
            return

        await ctx.response.defer(ephemeral=True)
        await download_file(the_file.url, the_file.filename)
        print(f'{the_file.filename} 已下載')
        if optional_key:
            encrypt_file(the_file.filename, ctx.user.id,optional_key)
        else:
            encrypt_file(the_file.filename, ctx.user.id,None)
        file = discord.File(f"{str(the_file.filename)}.enc")
        await ctx.followup.send(content = f"{no_key}加密成功",file = file, ephemeral=True)

    except Exception as e:
        await ctx.followup.send(f"加密失敗:\n**{e}**")
    os.remove(the_file.filename)
    os.remove(f"{the_file.filename}.enc")




@bot.tree.command(name="解密", description="解密你的檔案") 
async def decrypt_command(ctx: discord.Interaction,the_file: discord.Attachment,optional_key:str = None):
    if the_file.size > 15728640:
        await ctx.response.send_message("檔案過大!檔案不可大於15MB", ephemeral=True)
        return
    
    path = f"keys/{ctx.user.id}.key"
    if (not os.path.exists(path) or os.path.getsize(path)==0) and not optional_key:
        await ctx.response.send_message("找不到解密金鑰", ephemeral=True)
        return
    
    try:
        if ctx.user == bot.user:
            return
        # 下載並儲存附件
        if not the_file.filename.endswith(".enc"):
            await ctx.response.send_message("解密失敗:\n**請提供正確的加密檔案(.enc結尾)**", ephemeral=True)
            return
        await ctx.response.defer(ephemeral=True)
        await download_file(the_file.url, the_file.filename)
        print(f'{the_file.filename} 已下載')
        if optional_key:
            decrypt_file(the_file.filename, ctx.user.id,optional_key)
        else:
            decrypt_file(the_file.filename, ctx.user.id,None)
        file_name = str(the_file.filename)
        file_name = file_name[:-4]
        file = discord.File(file_name)
        await ctx.followup.send(content = "解密成功",file = file, ephemeral=True)

    except Exception as e:
        await ctx.followup.send(f"解密失敗:\n**{e}**")
    os.remove(the_file.filename)
    os.remove(file_name)





# 加載密鑰
def load_key(userid):
    return open(f"keys/{userid}.key", "rb").read()

# 加密文件
def encrypt_file(filename,userid,optional_key):
    if optional_key:
        key = optional_key
        key = bytes(key, 'utf-8')
    else:
        key = load_key(userid)
    f = Fernet(key)
    
    with open(filename, "rb") as file:
        file_data = file.read()


        
    encrypted_data = f.encrypt(file_data)
    
    with open(filename + ".enc", "wb") as file:
        file.write(encrypted_data)



# 解密文件
def decrypt_file(filename,userid,optional_key):
    if optional_key:
        key = optional_key
        key = bytes(key, 'utf-8')
    else:
        key = load_key(userid)
    f = Fernet(key)
    
    with open(filename, "rb") as file:
        encrypted_data = file.read()

        
    decrypted_data = f.decrypt(encrypted_data)
    
    with open(filename[:-4], "wb") as file:
        file.write(decrypted_data)




#下載檔案
async def download_file(url, filename):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(filename, 'wb') as f:
                    f.write(await response.read())




bot.run(data["token"])