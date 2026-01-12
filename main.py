import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import yt_dlp as youtube_dl

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN not found. Check your .env file.")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

YDL_OPTIONS = {
    "format": "bestaudio",
    "noplaylist": True,
    "default_search": "ytsearch",
}

FFMPEG_OPTIONS = {
    "options": "-vn",
    "executable": r"C:\ffmpeg\bin\ffmpeg.exe",  # altere para o seu caminho
}


@bot.command()
async def play(ctx, *, query):
    if ctx.author.voice is None:
        await ctx.send("Você precisa estar em um canal de voz para tocar música!")
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        voice = await channel.connect()
    else:
        voice = ctx.voice_client
        await voice.move_to(channel)

    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if "entries" in info:
                info = info["entries"][0]
            url2 = info["url"]
            title = info.get("title", "Música desconhecida")
            voice.play(discord.FFmpegPCMAudio(url2, **FFMPEG_OPTIONS))
            await ctx.send(f"Tocando: **{title}**")
        except Exception as e:
            await ctx.send(f"Erro ao tocar música: {e}")


@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Desconectado do canal de voz!")
    else:
        await ctx.send("O bot não está em nenhum canal de voz.")


@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Música pausada!")
    else:
        await ctx.send("Não há música tocando.")


@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Música resumida!")
    else:
        await ctx.send("Não há música pausada.")


@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Música pulada!")
    else:
        await ctx.send("Não há música tocando para pular.")


bot.run(DISCORD_TOKEN)
