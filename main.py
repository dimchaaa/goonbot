from flask import Flask
from threading import Thread
import discord
from discord.ext import commands, tasks
import asyncio
import time
from replit import db
import os

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!", 200

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

GUILD_ID = 1197119892806176838
ROLE_ID = 1387769609188540537

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    check_expired_roles.start()

@tasks.loop(minutes=1)
async def check_expired_roles():
    current_time = time.time()
    expired_users = []
    for key in db.keys():
        if key.startswith("role_expiry_"):
            user_id = int(key.replace("role_expiry_", ""))
            expiry_time = db[key]
            if current_time >= expiry_time:
                expired_users.append(user_id)
    for user_id in expired_users:
        guild = bot.get_guild(GUILD_ID)
        member = guild.get_member(user_id)
        role = guild.get_role(ROLE_ID)
        if member and role and role in member.roles:
            try:
                await member.remove_roles(role)
                print(f"Removed expired role from {member.name}")
                try:
                    channel = member.dm_channel
                    if channel is None:
                        channel = await member.create_dm()
                    await channel.send("Your goonkey access has expired.")
                except:
                    pass
            except Exception as e:
                print(f"Error removing role from {member.name}: {str(e)}")
        del db[f"role_expiry_{user_id}"]

async def delete_after_delay(ctx, reply):
    await asyncio.sleep(5)
    try:
        await ctx.message.delete()
    except:
        pass
    try:
        await reply.delete()
    except:
        pass

@bot.command()
async def lockg00nchannel(ctx):
    guild = bot.get_guild(GUILD_ID)
    member = guild.get_member(ctx.author.id)
    role = guild.get_role(ROLE_ID)
    if not member or not role:
        reply = await ctx.send("Could not find member or role.")
    elif role not in member.roles:
        reply = await ctx.send(f"{ctx.author.mention}, you don't have the goonkey role.")
    else:
        await member.remove_roles(role)
        if f"role_expiry_{ctx.author.id}" in db:
            del db[f"role_expiry_{ctx.author.id}"]
        reply = await ctx.send(f"{ctx.author.mention}, your goonkey role has been removed.")
    await delete_after_delay(ctx, reply)

@bot.command()
async def unlockg00nchannel(ctx):
    guild = bot.get_guild(GUILD_ID)
    member = guild.get_member(ctx.author.id)
    role = guild.get_role(ROLE_ID)
    if not member or not role:
        reply = await ctx.send("Could not find member or role.")
    else:
        await member.add_roles(role)
        db[f"role_expiry_{ctx.author.id}"] = time.time() + (15 * 60)
        reply = await ctx.send(f"{ctx.author.mention}, you now have the goonkey role for 15 minutes!")
    await delete_after_delay(ctx, reply)

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    print("Error: DISCORD_BOT_TOKEN not found in secrets!")
    exit(1)

keep_alive()
bot.run(TOKEN)
