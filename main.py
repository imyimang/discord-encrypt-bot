from cryptography.fernet import Fernet, InvalidToken
from discord.ext import commands,tasks
from itertools import cycle
import discord
import aiohttp
import os
import json
import base64


data = json.load(open("config.json", encoding="utf-8")) 


bot = commands.Bot(command_prefix=data["prefix"], intents=discord.Intents.all())


status = cycle(['安全加密機器人', '無日誌加解密檔案']) #機器人顯示的個人狀態,可自行更改


@tasks.loop(seconds=10)  # 每隔10秒更換一次機器人個人狀態
async def change_status():
    await bot.change_presence(activity=discord.Game(next(status)))


@bot.event
async def on_ready():
    slash = await bot.tree.sync()
    print(f"目前登入身份 --> {bot.user}")
    print(f"載入 {len(slash)} 個斜線指令")
    change_status.start()

#===================================================

@bot.tree.command(name="help", description="查看指令使用說明") 
async def help(ctx):
    await ctx.response.send_message(
        """# 指令說明\n
        - **/help** 查看指令說明
        - **/生成金鑰** 生成加密金鑰，如果已經有金鑰將會被覆蓋
        - **/設定金鑰** 設定你的解密金鑰(解密他人檔案時可以用到)
        - **/查詢金鑰** 查詢你當前預設的金鑰
        - **/加密** 用金鑰加密你的檔案(檔案最大15MB)，如果還沒有金鑰會先生成一個，optional_key為選填，如果填寫本次就會用該金鑰解密，沒有填寫就會用預設金鑰解密，預設金鑰可以用**/查詢金鑰**來查詢
        - **/解密** 用金鑰解密你的檔案(檔案最大20MB)，如果要解密其他金鑰加密的檔案請用**/設定金鑰**，optional_key為選填，如果填寫本次就會用該金鑰解密，沒有填寫就會用預設金鑰解密，預設金鑰可以用**/查詢金鑰**來查詢\n\n
        *made by* [*yimang*](https://github.com/imyimang/discord-encrypt-bot)\t
        [邀請機器人](https://discord.com/oauth2/authorize?client_id=1242337935022624788&permissions=551903332352&scope=bot)"""
        , ephemeral=True)



@bot.tree.command(name="生成金鑰", description="重新生成你的加密金鑰(先前加密的檔案將無法解密)") 
async def generate_key(ctx):
    try:
        key = Fernet.generate_key()
        if not os.path.exists("keys"):os.makedirs("keys")
        with open(f"keys/{ctx.user.id}.key", "wb") as key_file:
            key_file.write(key)
            key = key.decode('utf-8')
        await ctx.response.send_message(f"已重新生成加密金鑰，請妥善保管，遺失後將無法解密檔案:\n**{key}**", ephemeral=True)
    except Exception as e:
        await ctx.response.send_message(f"生成失敗:\n**{e}**", ephemeral=True)



@bot.tree.command(name="查詢金鑰", description="查詢你當前的加密金鑰") 
async def check_key(ctx):

    if not os.path.exists("keys"):os.makedirs("keys")
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
        key = bytes(key, 'utf-8')
        if is_valid_key(key):
            if not os.path.exists("keys"):os.makedirs("keys")
            with open(f"keys/{ctx.user.id}.key", "wb") as key_file:
                
                key_file.write(key)
            await ctx.response.send_message(f"已更改加密金鑰:\n**{key.decode('utf-8')}**", ephemeral=True)
        else:
             await ctx.response.send_message("請輸入有效的加密金鑰!", ephemeral=True)
             
    except Exception as e:
        await ctx.response.send_message(f"設定失敗:\n**{e}**", ephemeral=True)



@bot.tree.command(name="加密", description="加密你的檔案") 
async def encrypt_command(ctx: discord.Interaction, the_file: discord.Attachment,optional_key:str = None):
    if the_file.size > 15728640:
        await ctx.response.send_message("檔案過大!檔案不可大於15MB", ephemeral=True)
        return
    
    if not os.path.exists("keys"):os.makedirs("keys")
    path = f"keys/{ctx.user.id}.key"

    if (not os.path.exists(path) or os.path.getsize(path)==0) and not optional_key:  
        key = Fernet.generate_key()
        with open(f"keys/{ctx.user.id}.key", "wb") as key_file:
            key_file.write(key)
            key = key.decode('utf-8')
        no_key = f"未找到已經存在的金鑰，已生成新的金鑰:\n**{key}**\n請妥善保管，遺失後將無法解密檔案\n\n"     
    else:no_key = ""

    try:
        if ctx.user == bot.user:return
        await ctx.response.defer(ephemeral=True)
        file_content = await read_file(the_file.url)
        encrypt_file(the_file.filename,file_content, ctx.user.id,optional_key)
        file = discord.File(f"temporary/{(the_file.filename)}.enc")
        await ctx.followup.send(content = f"{no_key}加密成功",file = file, ephemeral=True)

    except Exception as e:
        await ctx.followup.send(f"加密失敗:\n**{e}**", ephemeral=True)
        return
    os.remove(f'temporary/{the_file.filename}.enc')



@bot.tree.command(name="解密", description="解密你的檔案") 
async def decrypt_command(ctx: discord.Interaction,the_file: discord.Attachment,optional_key:str = None):
    if the_file.size > 20971520:
        await ctx.response.send_message("檔案過大!檔案不可大於15MB", ephemeral=True)
        return
    
    if not os.path.exists("keys"):os.makedirs("keys")
    path = f"keys/{ctx.user.id}.key"
    if (not os.path.exists(path) or os.path.getsize(path)==0) and not optional_key:
        await ctx.response.send_message("找不到解密金鑰", ephemeral=True)
        return
    
    try:
        if ctx.user == bot.user:return
        # 下載並儲存附件
        if not the_file.filename.endswith(".enc"):
            await ctx.response.send_message("解密失敗:\n**請提供正確的加密檔案(.enc結尾)**", ephemeral=True)
            return
        await ctx.response.defer(ephemeral=True)
        file_content = await read_file(the_file.url)
        print(f'{the_file.filename} 已下載')
        decrypt_file(the_file.filename, file_content, ctx.user.id, optional_key)
        
        file = discord.File(f"temporary/{the_file.filename[:-4]}")
        await ctx.followup.send(content = "解密成功",file = file, ephemeral=True)
    
    except Exception as e:
        if isinstance(e, InvalidToken):
            await ctx.followup.send(f"解密失敗:\n**解密金鑰錯誤**", ephemeral=True)
        else:
            await ctx.followup.send(f"解密失敗:\n**{e}**", ephemeral=True)
        return
    os.remove(f'temporary/{the_file.filename[:-4]}')

#===================================================

# 加載密鑰
def load_key(userid):
    return open(f"keys/{userid}.key", "rb").read()

# 加密文件
def encrypt_file(filename,file_content,userid,optional_key):
    if optional_key:
        key = bytes(optional_key, "utf-8")
    else:
        key = load_key(userid)
    f = Fernet(key)
    
    encrypted_data = f.encrypt(file_content)
    
    with open(f"temporary/{filename}" + ".enc", "wb") as file:
        file.write(encrypted_data)


# 解密文件
def decrypt_file(filename,file_content,userid,optional_key):
    if optional_key:
        key = bytes(optional_key, "utf-8")
    else:
        key = load_key(userid)
    f = Fernet(key)
    
    decrypted_data = f.decrypt(file_content)

    filename = f"temporary/{filename}"[:-4]
    with open(filename, "wb") as file:
        file.write(decrypted_data)


#下載檔案
async def read_file(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return(await response.read())
            

#檢測金鑰有效性
def is_valid_key(s):
    try:
        decoded_bytes = base64.urlsafe_b64decode(s)
        return len(decoded_bytes) == 32
    except:
        return False


bot.run(data["token"])