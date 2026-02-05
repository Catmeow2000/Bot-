import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
import random, json, asyncio, os

# ================= CONFIG =================
TOKEN = "MTQ2NzgzMTU2MTU0OTM4NTg3MA.G04X9m.BtJ5b43kEWd9xBIx5KScy1xGZn9rABFgZLIbLw"
MONEY_FILE = "money.json"

USER_IDS = [1105723916149854218, 704560980255965245]  # danh sách ID có quyền sử dụng lệnh

# ================= DICE EMOJI =================
DICE_EMOJI = {
    1: "⚀",
    2: "⚁",
    3: "⚂",
    4: "⚃",
    5: "⚄",
    6: "⚅"
}

# ================= INTENTS =================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# ================= MONEY =================
if not os.path.exists(MONEY_FILE):
    with open(MONEY_FILE, "w") as f:
        json.dump({}, f)

def load_money():
    with open(MONEY_FILE, "r") as f:
        return json.load(f)

def save_money(data):
    with open(MONEY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_money(uid):
    data = load_money()
    return data.get(str(uid), 0)

def add_money(uid, amt):
    data = load_money()
    data[str(uid)] = data.get(str(uid), 0) + amt
    save_money(data)

def remove_money(uid, amt):
    data = load_money()
    data[str(uid)] = max(0, data.get(str(uid), 0) - amt)
    save_money(data)

# ================= ADMIN CHECK =================
def is_admin(interaction: discord.Interaction) -> bool:
    if not interaction.guild:
        return False
    member = interaction.guild.get_member(interaction.user.id)
    if not member:
        return False
    return member.guild_permissions.administrator

# ================= BET MODAL =================
class BetModal(Modal):
    def __init__(self, choice, view):
        super().__init__(title=f"Cược {choice}")
        self.choice = choice
        self.view = view
        self.amount = TextInput(label="Nhập tiền cược", placeholder="Ví dụ: 100")
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            bet = int(self.amount.value)
        except:
            return await interaction.response.send_message("❌ Phải nhập số", ephemeral=True)

        if bet <= 0 or get_money(interaction.user.id) < bet:
            return await interaction.response.send_message("❌ Không đủ tiền", ephemeral=True)

        self.view.bets[interaction.user.id] = {"choice": self.choice, "money": bet}
        await interaction.response.send_message(
            f"✅ Đã cược **{bet} gold** vào **{self.choice}**",
            ephemeral=True
        )

# ================= VIEW =================
class TaiXiuView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.bets = {}
        choices = [("Tài","tai"),("Xỉu","xiu"),("Chẵn","chan"),("Lẻ","le")]
        for i in range(3, 19):
            choices.append((f"Số {i}", str(i)))

        for label, cid in choices:
            btn = Button(label=label, style=discord.ButtonStyle.secondary)
            btn.callback = self.make_callback(cid)
            self.add_item(btn)

    def make_callback(self, choice):
        async def callback(interaction: discord.Interaction):
            await interaction.response.send_modal(BetModal(choice, self))
        return callback

# ================= ĐĂNG KÝ LỆNH SLASH VÀ SỰ KIỆN =================
def setup(bot: commands.Bot):
    @bot.tree.command(name="help", description="Hướng dẫn bot")
    async def help_cmd(interaction: discord.Interaction):
        embed = discord.Embed(title="📘 BOT TÀI XỈU", color=0x00ffff)
        embed.add_field(
            name="🎲 Cách chơi",
            value=(
                "• Tài (11–18)\n"
                "• Xỉu (3–10)\n"
                "• Chẵn (Tổng chẵn) / Lẻ (Tổng lẻ)\n"
                "• Số (3–18)\n\n"
                "💰 Thắng x3 – Thua mất cược"
            ),
            inline=False
        )
        embed.add_field(
            name="📜 Lệnh",
            value=(
                "/taixiu – chơi\n"
                "/balance – xem tiền\n"
                "/givemoney – admin thêm tiền\n"
                "/takemoney – admin trừ tiền\n"
                "/help – hướng dẫn"
            ),
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="balance", description="Xem số tiền")
    async def balance(interaction: discord.Interaction):
        # Đọc dữ liệu mới nhất từ file money.json
        data = load_money()  # hoặc: json.load(open(MONEY_FILE, "r"))
        balance_amount = data.get(str(interaction.user.id), 0)
        
        # Hiển thị số tiền trong embed/response
        await interaction.response.send_message(
            f"💰 Bạn có **{balance_amount} gold**",
            ephemeral=True
        )

    @bot.tree.command(name="givemoney", description="Admin cho tiền")
    @app_commands.describe(userid="ID người nhận", amount="Số tiền")
    async def givemoney(interaction: discord.Interaction, userid: str, amount: int):
        if interaction.user.id not in USER_IDS:
            return await interaction.response.send_message("❌ Bạn không có quyền dùng lệnh này", ephemeral=True)
        if not userid.isdigit() or amount <= 0:
            return await interaction.response.send_message("❌ Dữ liệu không hợp lệ", ephemeral=True)

        add_money(int(userid), amount)
        await interaction.response.send_message(f"✅ Đã cộng **{amount} gold** cho ID `{userid}`")

    @bot.tree.command(name="takemoney", description="Admin trừ tiền")
    @app_commands.describe(userid="ID người bị trừ", amount="Số tiền")
    async def takemoney(interaction: discord.Interaction, userid: str, amount: int):
        if interaction.user.id not in USER_IDS:
            return await interaction.response.send_message("❌ Bạn không có quyền dùng lệnh này", ephemeral=True)
        if not userid.isdigit() or amount <= 0:
            return await interaction.response.send_message("❌ Dữ liệu không hợp lệ", ephemeral=True)

        remove_money(int(userid), amount)
        await interaction.response.send_message(f"✅ Đã trừ **{amount} gold** của ID `{userid}`")

    @bot.tree.command(name="taixiu", description="Chơi tài xỉu")
    async def taixiu(interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎲 TÀI XỈU CAT BOT - TÀI TRỢ YUMI",
            description="**Chọn Tài (11-18), Xỉu (3-10), Chẵn/Lẻ hoặc số cụ thể (3-18) để đặt cược.**\n\n" +
    "Sau khi chọn, nhập số gold bạn muốn cược không giới hạn .\n\n" +
    "**Tỉ lệ trả thưởng:**\n" +
    "• Tài / Xỉu / Chẵn / Lẻ: **1:1**\n" +
    "• Số cụ thể (3-18): **1:10**\n\n" +
    "• Nếu bot dừng, hãy sử dụng lại lệnh *(không cược)* để tiếp tục ván chơi\n" +
    "⏳ **Trò chơi sẽ bắt đầu ngay lập tức và đếm ngược 45 giây**",
            color=0xff9900
        )

        view = TaiXiuView()
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()

        # 🎲 Đếm ngược 45 giây với hiệu ứng xúc xắc
        for t in range(45, 0, -1):
            d1 = random.randint(1,6)
            d2 = random.randint(1,6)
            d3 = random.randint(1,6)

            embed.clear_fields()
            embed.add_field(
                name="🎲 Xúc xắc đang quay",
                value=f"{DICE_EMOJI[d1]}  {DICE_EMOJI[d2]}  {DICE_EMOJI[d3]}",
                inline=False
            )
            embed.set_footer(text=f"⏳ Còn {t} giây")
            await msg.edit(embed=embed)
            await asyncio.sleep(1)

        # 🎯 Kết quả thật
        dice = [random.randint(1,6) for _ in range(3)]
        total = sum(dice)
        result_text = "TÀI" if total >= 11 else "XỈU"
        result = "tai" if total >= 11 else "xiu"

        win, lose = [], []

        for uid, data in view.bets.items():
            bet = data["money"]
            remove_money(uid, bet)

            choice = data["choice"]
            ok = False
            # Xử lý Tài/Xỉu
            if choice == result:
                ok = True
            # Xử lý Chẵn/Lẻ
            if choice == "chan" and total % 2 == 0:
                ok = True
            if choice == "le" and total % 2 == 1:
                ok = True
            # Xử lý chọn số chính xác
            if choice.isdigit() and int(choice) == total:
                ok = True

            if ok:
                add_money(uid, bet * 3)
                win.append(f"<@{uid}> +{bet*3}")
            else:
                lose.append(f"<@{uid}> -{bet}")

        res = discord.Embed(title="?? KẾT QUẢ TÀI XỈU", color=0x00ffcc)
        res.add_field(
            name="🎲 Xúc xắc",
            value=f"{DICE_EMOJI[dice[0]]}  {DICE_EMOJI[dice[1]]}  {DICE_EMOJI[dice[2]]}",
            inline=False
        )
        res.add_field(name="➕ Tổng", value=str(total), inline=True)
        res.add_field(name="🔥 Kết quả", value=f"**{result_text}**", inline=True)
        res.add_field(name="✅ Thắng", value="\n".join(win) or "Không ai", inline=False)
        res.add_field(name="❌ Thua", value="\n".join(lose) or "Không ai", inline=False)

        await msg.edit(embed=res, view=None)

    @bot.event
    async def on_ready():
        await bot.tree.sync()
        print("✅ Bot online & slash command đã sync")

    print("✅ Đã load module tài xỉu")