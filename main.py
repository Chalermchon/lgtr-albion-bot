import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import re
import os
from dotenv import load_dotenv

load_dotenv()

# กำหนด Prefix และตั้งค่าบอท
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# ตัวแปรเก็บข้อความเดิมและข้อมูลเวลาปิด
last_message = None
closing_times = {}

# ฟังก์ชันคำนวณเวลาปิดและเวลาถอยหลัง
def calculate_closing_times(current_time, closing_times):
    description = ""
    for location, closing_time in closing_times.items():
        countdown = closing_time - current_time
        countdown_seconds = countdown.total_seconds()

        # กำหนดสีของข้อความ
        if countdown_seconds <= 0:
            countdown_color = 0x95a5a6  # สีเทา (ปิดแล้ว)
            description += f"~~**{location}** (ปิดเวลา {closing_time.strftime('%H:%M:%S')} - ปิดแล้ว)~~\n"
        else:
            countdown_color = 0x1abc9c  # สีเขียว ถ้ายังมีเวลาเหลือ
            if countdown_seconds <= 3600:  # ถ้าเหลือเวลา < 1 ชั่วโมง
                countdown_color = 0xe74c3c  # สีแดง

            # แปลงเวลาถอยหลังเป็น ชั่วโมง นาที วินาที
            countdown_hours = int(countdown_seconds // 3600)
            countdown_minutes = int((countdown_seconds % 3600) // 60)
            countdown_seconds = int(countdown_seconds % 60)

            description += (
                f">>**{location}** (ปิดเวลา {closing_time.strftime('%H:%M:%S')}, "
                f"เหลือเวลา "
                f"{countdown_hours} ชั่วโมง {countdown_minutes} นาที "
                f"{countdown_seconds} วินาที)\n"
            )

    # คืนค่า Embed พร้อมข้อความ
    embed = discord.Embed(
        title="ผลลัพธ์อัพเดต",
        description=description,
        color=countdown_color  # ใช้สีที่คำนวณไว้
    )
    return embed

# เมื่อบอทพร้อม
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")

    # เริ่มงานที่เป็น loop ทันทีหลังจากที่บอทพร้อม
    update_loop.start()

# @bot.tree.add_command(name='ping')
# async def 

# คำสั่ง !path
@bot.command()
async def path(ctx, *, args=None):
    global last_message, closing_times

    try:
        # เวลาปัจจุบัน (GMT+7)
        current_time = datetime.utcnow() + timedelta(hours=7)

        if args:
            # แปลง Input เป็น Dictionary
            input_data = {pair.split("=")[0].strip(): pair.split("=")[1].strip() for pair in args.split(",")}

            # อัปเดตเวลาปิดใน closing_times
            for location, duration in input_data.items():
                hours = 0
                mins = 0

                # ใช้ regex ดึงข้อมูลชั่วโมงและนาที
                hours_match = re.search(r'(\d+)hrs', duration)
                mins_match = re.search(r'(\d+)mins', duration)

                if hours_match:
                    hours = int(hours_match.group(1))
                if mins_match:
                    mins = int(mins_match.group(1))

                # คำนวณเวลาปิด (UTC+7)
                closing_times[location] = current_time + timedelta(hours=hours, minutes=mins)

            # ถ้ามี map ที่ปิดแล้ว ให้ปิดทั้งหมด
            if any(closing_time <= current_time for closing_time in closing_times.values()):
                for location in closing_times:
                    closing_times[location] = current_time

            # แสดงผลเริ่มต้น
            embed = calculate_closing_times(current_time, closing_times)

            # ส่งข้อความใหม่หรือแก้ไขข้อความเดิม
            if last_message:
                await last_message.edit(embed=embed)
            else:
                last_message = await ctx.send(embed=embed)

        else:
            embed = discord.Embed(
                title="ข้อมูลไม่ครบถ้วน",
                description="กรุณาระบุข้อมูล path ที่ต้องการเพิ่ม",
                color=0xe74c3c  # สีแดง
            )
            await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="เกิดข้อผิดพลาด",
            description=f"ข้อผิดพลาด: {e}",
            color=0xe74c3c  # สีแดง
        )
        await ctx.send(embed=embed)

# คำสั่ง !newpath เพื่อลบ path ล่าสุดและแสดงผลใหม่ทันที
@bot.command()
async def newpath(ctx, *, args=None):
    global last_message, closing_times

    try:
        # รีเซ็ตข้อมูล path ก่อนหน้านี้
        closing_times.clear()

        # เวลาปัจจุบัน (GMT+7)
        current_time = datetime.utcnow() + timedelta(hours=7)

        if args:
            # แปลง Input เป็น Dictionary
            input_data = {pair.split("=")[0].strip(): pair.split("=")[1].strip() for pair in args.split(",")}

            # อัปเดตเวลาปิดใน closing_times
            for location, duration in input_data.items():
                hours = 0
                mins = 0

                # ใช้ regex ดึงข้อมูลชั่วโมงและนาที
                hours_match = re.search(r'(\d+)hrs', duration)
                mins_match = re.search(r'(\d+)mins', duration)

                if hours_match:
                    hours = int(hours_match.group(1))
                if mins_match:
                    mins = int(mins_match.group(1))

                # คำนวณเวลาปิด (UTC+7)
                closing_times[location] = current_time + timedelta(hours=hours, minutes=mins)

            # ถ้ามี map ที่ปิดแล้ว ให้ปิดทั้งหมด
            if any(closing_time <= current_time for closing_time in closing_times.values()):
                for location in closing_times:
                    closing_times[location] = current_time

            # แสดงผลเริ่มต้น
            embed = calculate_closing_times(current_time, closing_times)

            # ลบข้อความเก่าก่อนแล้วส่งข้อความใหม่
            if last_message:
                await last_message.delete()

            # ส่งข้อความใหม่
            last_message = await ctx.send(embed=embed)

        else:
            embed = discord.Embed(
                title="ข้อมูลไม่ครบถ้วน",
                description="กรุณาระบุข้อมูล path ที่ต้องการเพิ่ม",
                color=0xe74c3c  # สีแดง
            )
            await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="เกิดข้อผิดพลาด",
            description=f"ข้อผิดพลาด: {e}",
            color=0xe74c3c  # สีแดง
        )
        await ctx.send(embed=embed)

# ฟังก์ชัน update ข้อมูลตามเวลาทุก 30 วินาที
@tasks.loop(seconds=1)
async def update_loop():
    if last_message:
        current_time = datetime.utcnow() + timedelta(hours=7)
        embed = calculate_closing_times(current_time, closing_times)
        await last_message.edit(embed=embed)

bot.run(os.getenv('DISCORD_BOT_TOKEN'))
