import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import yt_dlp as youtube_dl
import asyncio

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
    "options": "-vn -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "executable": r"C:\ffmpeg\bin\ffmpeg.exe",
}

queues = {}


async def play_next(ctx, guild_id):
    if guild_id in queues and queues[guild_id]:
        url, title = queues[guild_id].pop(0)
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        ctx.voice_client.play(
            source,
            after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next(ctx, guild_id), bot.loop
            ),
        )
        asyncio.run_coroutine_threadsafe(ctx.send(f"Tocando: **{title}**"), bot.loop)
    else:
        await ctx.voice_client.disconnect()
        await ctx.send("Fila finalizada, desconectando do canal de voz.")


@bot.command()
async def play(ctx, *, query=None):
    if query is None:
        await ctx.send(
            "Você precisa fornecer o nome ou link da música. Exemplo: `!play <música>`"
        )
        return

    if ctx.author.voice is None:
        await ctx.send("Você precisa estar em um canal de voz para tocar música!")
        return

    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await channel.connect()

    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if "entries" in info:
                info = info["entries"][0]
            url2 = info["url"]
            title = info.get("title", "Música desconhecida")

            guild_id = ctx.guild.id
            if guild_id not in queues:
                queues[guild_id] = []

            queues[guild_id].append((url2, title))

            if not ctx.voice_client.is_playing():
                await play_next(ctx, guild_id)
            else:
                await ctx.send(f"Adicionado à fila: **{title}**")
        except Exception as e:
            await ctx.send(f"Erro ao tocar música: {e}")


@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Música pulada!")
    else:
        await ctx.send("Não há música tocando para pular.")


@bot.command()
async def stop(ctx):
    guild_id = ctx.guild.id
    if ctx.voice_client:
        ctx.voice_client.stop()
        queues[guild_id] = []
        await ctx.voice_client.disconnect()
        await ctx.send("Desconectado e fila limpa!")
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
async def queue(ctx):
    guild_id = ctx.guild.id
    if guild_id in queues and queues[guild_id]:
        msg = "Fila atual:\n"
        for i, (_, title) in enumerate(queues[guild_id], start=1):
            msg += f"{i}. {title}\n"
        await ctx.send(msg)
    else:
        await ctx.send("A fila está vazia.")


bot.run(DISCORD_TOKEN)
