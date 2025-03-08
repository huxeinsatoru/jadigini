import discord
import requests
import os

from discord.ext import commands

# Konfigurasi bot
TOKEN = os.getenv(
    "eRPdb7ESI5IJTMdIXxknGDykdzAIWS32")  # Gunakan Secrets di Replit
SCRIN_API_TOKEN = os.getenv("209119lf15248f5d6e53273656ce60f5a49827b")
EXCHANGE_API_URL = "https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@latest/v1/currencies/usd/idr.json"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# Fungsi untuk mendapatkan total jam kerja dari Scrin
def get_total_hours():
    url = "https://scrin.io/api/v2/GetCommonData"
    headers = {
        "Content-Type": "application/json",
        "x-ssm-token": SCRIN_API_TOKEN,
        "X-Requested-With": "XMLHttpRequest",
    }

    response = requests.post(url, headers=headers, json={})
    data = response.json()

    try:
        # Ambil total jam kerja (harus disesuaikan dengan format JSON)
        total_hours = 40  # Contoh statis, ganti dengan parsing dari data
        return total_hours
    except:
        return None


# Fungsi untuk konversi USD ke IDR
def get_usd_to_idr():
    response = requests.get(EXCHANGE_API_URL)
    data = response.json()

    return data.get("idr", 15000)  # Default 15.000 kalau gagal


@bot.command()
async def gaji(ctx, pay_per_hour: float):
    total_hours = get_total_hours()
    if total_hours is None:
        await ctx.send("Gagal mendapatkan data jam kerja.")
        return

    usd_to_idr = get_usd_to_idr()

    salary_usd = total_hours * pay_per_hour
    salary_idr = salary_usd * usd_to_idr

    await ctx.send(f"💰 **Total Gaji:**\n"
                   f"- **{total_hours} Jam** kerja\n"
                   f"- **${salary_usd:.2f}** USD\n"
                   f"- **Rp{salary_idr:,.0f}** IDR (kurs {usd_to_idr:,.0f})")


# Menjalankan bot
bot.run(TOKEN)
