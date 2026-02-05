import json
import os
import asyncio
from datetime import datetime
import discord
from discord.ext import commands
from discord import app_commands

class DiemDanh(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # File lưu dữ liệu điểm danh và tiền
        self.data_file = "diemdanh_data.json"
        self.money_file = "money.json"
        # Khóa để tránh xung đột ghi file
        self.lock = asyncio.Lock()

    @app_commands.command(name="diemdanh", description="Điểm danh hàng ngày nhận 1000 gold")
    async def diemdanh(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        now = int(datetime.utcnow().timestamp())

        # Đọc dữ liệu cũ, xử lý nếu file không tồn tại hoặc trống
        async with self.lock:
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    diemdanh_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                diemdanh_data = {}
            
            last_time = diemdanh_data.get(user_id, 0)
            # Kiểm tra đã 24h chưa
            if now - last_time >= 86400:
                # Cập nhật thời gian điểm danh mới
                diemdanh_data[user_id] = now
                with open(self.data_file, "w", encoding="utf-8") as f:
                    json.dump(diemdanh_data, f, indent=4)
                
                # Cập nhật tiền (money.json)
                try:
                    with open(self.money_file, "r", encoding="utf-8") as f:
                        money_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    money_data = {}

                current_money = money_data.get(user_id, 0)
                money_data[user_id] = current_money + 1000
                with open(self.money_file, "w", encoding="utf-8") as f:
                    json.dump(money_data, f, indent=4)

                # Gửi phản hồi thành công
                embed = discord.Embed(
                    description="Bạn đã điểm danh thành công! +1000 gold",
                    color=discord.Color.green()
                )
            else:
                # Tính thời gian còn lại
                remaining = 86400 - (now - last_time)
                hours = remaining // 3600
                minutes = (remaining % 3600) // 60
                embed = discord.Embed(
                    description=f"Bạn đã điểm danh rồi. Hãy quay lại sau {hours} giờ {minutes} phút",
                    color=discord.Color.red()
                )

        # Gửi thông báo embed (một lần duy nhất cho interaction)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(DiemDanh(bot))