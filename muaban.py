import discord
import json
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from mcrcon import MCRcon

# ========= CONFIG =========
RCON_HOST = "127.0.0.1"
RCON_PORT = 25575
RCON_PASSWORD = "PASSWORD_RCON"
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MONEY_FILE = os.path.join(BASE_DIR, "money.json")
SHOP_FILE = os.path.join(BASE_DIR, "shop.json")
# ==========================

# ===== MONEY SYSTEM =====
def load_money():
    with open(MONEY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_money(data):
    with open(MONEY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_gold(user_id: int) -> int:
    data = load_money()
    return data.get(str(user_id), 0)

def remove_gold(user_id: int, amount: int):
    data = load_money()
    uid = str(user_id)
    data[uid] = data.get(uid, 0) - amount
    save_money(data)

# ===== MINECRAFT =====
def check_player_exists(mcname: str) -> bool:
    with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
        resp = mcr.command(f"essentials:seen {mcname}")
        return "never joined" not in resp.lower()

def give_item(mcname: str, item: str, amount: int):
    with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
        mcr.command(f"minecraft:give {mcname} minecraft:{item} {amount}")

# ===== MODAL =====
class MinecraftNameModal(Modal):
    def __init__(self, item, amount, price):
        super().__init__(title="Nhập tên Minecraft")
        self.item = item
        self.amount = amount
        self.price = price

        self.mcname = TextInput(
            label="Tên Minecraft",
            placeholder="VD: Steve",
            min_length=3,
            max_length=16
        )
        self.add_item(self.mcname)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        mcname = self.mcname.value

        if get_gold(user_id) < self.price:
            await interaction.response.send_message(
                "❌ Bạn không đủ gold!",
                ephemeral=True
            )
            return

        if not check_player_exists(mcname):
            await interaction.response.send_message(
                "❌ Tên Minecraft không tồn tại hoặc chưa từng vào server!",
                ephemeral=True
            )
            return

        give_item(mcname, self.item, self.amount)
        remove_gold(user_id, self.price)

        await interaction.response.send_message(
            f"✅ Đã gửi **{self.amount} {self.item}** cho **{mcname}**\n"
            "📦 Offline vẫn nhận được.",
            ephemeral=True
        )

# ===== SHOP VIEW =====
class ShopView(View):
    def __init__(self):
        super().__init__(timeout=60)
        with open(SHOP_FILE, "r", encoding="utf-8") as f:
            shop = json.load(f)

        for data in shop.values():
            self.add_item(ShopButton(data))

class ShopButton(Button):
    def __init__(self, data):
        super().__init__(
            label=f"{data['label']} – {data['price']} Gold",
            style=discord.ButtonStyle.green
        )
        self.data = data

    async def callback(self, interaction: discord.Interaction):
        if get_gold(interaction.user.id) < self.data["price"]:
            await interaction.response.send_message(
                "❌ Bạn không đủ gold!",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            MinecraftNameModal(
                self.data["item"],
                self.data["amount"],
                self.data["price"]
            )
        )

# ===== COG =====
class Muaban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="muaban", description="Shop mua đồ Minecraft")
    async def muaban(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🛒 SHOP MINECRAFT",
            description="Chọn món đồ bạn muốn mua",
            color=0x00ff99
        )

        with open(SHOP_FILE, "r", encoding="utf-8") as f:
            shop = json.load(f)

        for item in shop.values():
            embed.add_field(
                name=item["label"],
                value=f"💰 {item['price']} Gold",
                inline=False
            )

        await ctx.send(embed=embed, view=ShopView())

# ===== SETUP (QUAN TRỌNG) =====
async def setup(bot):
    await bot.add_cog(Muaban(bot))