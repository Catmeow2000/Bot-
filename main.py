import discord
from discord.ext import commands
import taixiu
import diemdanh
import muaban

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user}")

    # ❌ KHÔNG await vì setup KHÔNG async
    taixiu.setup(bot)

    # ✅ diemdanh là async → phải await
    await diemdanh.setup(bot)
    await muaban.setup(bot)

    await bot.tree.sync()
    print("✅ Slash commands đã sync")

bot.run("")