import os
import json
from dotenv import load_dotenv
import discord
import requests
from discord.ext import commands
from discord import app_commands
from flask import Flask
from threading import Thread

# Load Token dari .env
load_dotenv()
TOKEN_DISCORD = os.getenv("DISCORD_BOT_TOKEN")

# Inisialisasi Flask untuk uptime
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    server = Thread(target=run)
    server.start()

# Inisialisasi bot dengan intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents)
tree = bot.tree  # Shortcut untuk slash commands

USER_DATA_FILE = "user_data.json"

# Load user data
if os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "r") as file:
        user_data = json.load(file)
else:
    user_data = {}

def save_user_data():
    with open(USER_DATA_FILE, "w") as file:
        json.dump(user_data, file, indent=4)

# Function untuk mendapatkan data kerja dari Scrin.io
def get_work_data(xssm_token, period="isMonth"):
    url = "https://scrin.io/api/v2/GetReport"
    headers = {
        "Content-Type": "application/json",
        "X-SSM-Token": xssm_token,
        "X-Requested-With": "XMLHttpRequest"
    }
    data = {
        "empl": [343684],  # Ganti dengan ID pengguna Scrin.io
        period: True,
        "group": ["employee"]
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    return None

# Function untuk mendapatkan kurs USD ke IDR
def get_exchange_rate():
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("rates", {}).get("IDR", 16000)  # Default 16,000 jika API gagal
    return 16000

# Fungsi untuk format IDR
def format_idr(amount):
    return f"{int(amount):,}".replace(",", ".")

# Fungsi untuk format USD
def format_usd(amount):
    return f"{amount:,.2f}".replace(",", ".")

# Perintah untuk menyimpan token dan rate per jam
@tree.command(name="set", description="Set up awal")
async def set_command(interaction: discord.Interaction, xssm_token: str, rate_per_hour: float):
    user_data[str(interaction.user.id)] = {
        "token": xssm_token,
        "rate": rate_per_hour,
        "discord_id": interaction.user.id
    }
    save_user_data()
    await interaction.response.send_message("✅ Berhasil Disimpan.", ephemeral=True)

# Perintah untuk reset data
@tree.command(name="reset", description="Hapus data scrin.io yang tersimpan")
async def reset_command(interaction: discord.Interaction):
    if str(interaction.user.id) in user_data:
        del user_data[str(interaction.user.id)]
        save_user_data()
        await interaction.response.send_message("✅ Berhasil Dihapus.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Kamu belum menyimpan data.", ephemeral=True)

# Fungsi untuk mengecek gaji berdasarkan periode
async def check_salary(interaction: discord.Interaction, period: str, label: str):
    user = interaction.user
    if str(user.id) not in user_data:
        await interaction.response.send_message("❌ Kamu belum memasukkan token dan rate per jam. Gunakan `/set`", ephemeral=True)
        return

    data = user_data[str(user.id)]
    work_data = get_work_data(data["token"], period)

    if not work_data or "charts" not in work_data or "timeline" not in work_data["charts"]:
        await interaction.response.send_message(f"❌ Gagal mengambil data gaji untuk {label}.", ephemeral=True)
        return

    total_minutes = sum(entry["Duration"] for entry in work_data["charts"]["timeline"])
    total_hours = total_minutes // 60
    remaining_minutes = total_minutes % 60

    usd_to_idr = get_exchange_rate()
    total_salary_idr = (total_minutes / 60) * data["rate"] * usd_to_idr
    total_salary_usd = total_salary_idr / usd_to_idr

    formatted_salary_idr = format_idr(total_salary_idr)
    formatted_salary_usd = format_usd(total_salary_usd)

    message = f"**{label}** {formatted_salary_usd} USD / {formatted_salary_idr} IDR — {total_hours} Jam {remaining_minutes} Menit"
    await interaction.response.send_message(message, ephemeral=True)

# Perintah untuk melihat gaji berdasarkan periode
@tree.command(name="hariini", description="Cek gaji hari ini")
async def hariini(interaction: discord.Interaction):
    await check_salary(interaction, "isToday", "Hari ini")

@tree.command(name="kemarin", description="Cek gaji kemarin")
async def kemarin(interaction: discord.Interaction):
    await check_salary(interaction, "isYesterday", "Kemarin")

@tree.command(name="bulanini", description="Cek gaji bulan ini")
async def bulanini(interaction: discord.Interaction):
    await check_salary(interaction, "isMonth", "Bulan ini")

@tree.command(name="tahunini", description="Cek gaji tahun ini")
async def tahunini(interaction: discord.Interaction):
    await check_salary(interaction, "isYear", "Tahun ini")

@tree.command(name="bulanlalu", description="Cek gaji bulan lalu")
async def bulanlalu(interaction: discord.Interaction):
    await check_salary(interaction, "isPrevMonth", "Bulan lalu")

@tree.command(name="minggulalu", description="Cek gaji minggu lalu")
async def minggulalu(interaction: discord.Interaction):
    await check_salary(interaction, "isPrevWeek", "Minggu lalu")

@tree.command(name="tahunlalu", description="Cek gaji tahun lalu")
async def tahunlalu(interaction: discord.Interaction):
    await check_salary(interaction, "isPrevYear", "Tahun lalu")

# Event saat bot siap
@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} siap!")
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} perintah slash berhasil disinkronkan.")
    except Exception as e:
        print(f"❌ Sync error: {e}")

keep_alive()
bot.run(TOKEN_DISCORD)
