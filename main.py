#!/bin/python

import discord
from discord.ext import commands

import logging
import uuid
import json
from datetime import datetime
from time import sleep
import os

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

if os.path.isfile("data.json"):
    data: dict = json.loads(open("data.json").read())
else:
    data = {}

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(intents=intents, command_prefix="rob!")

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(f"`{bot.command_prefix}help`"))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_pings, trigger=CronTrigger(second=0))
    scheduler.start()

    asyncio.get_event_loop().run_forever()

@bot.event
async def on_command_error(context, error):
	await context.reply(f"`error <:[\n\n{error}`")

@bot.before_invoke
async def log_command(context):
	print(f"\033[0;44m@{context.author}\033[0m ran \033[0;91m{context.prefix}{context.command}\033[0m in \033[0;44m#{context.channel.name}\033[0m on \033[1m{context.guild.name}\033[0m")

def save_json():
    data_file = open("data.json", "w")
    data_file.write(json.dumps(data))
    data_file.close()

@bot.command(name="start", brief="start a new thread")
async def start_thread(context, *, users=commands.parameter(description="the members of the thread (can be ping or ID)", displayed_name="thread_members")):
    message: discord.Message = context.message
    if type(message.channel) != discord.TextChannel:
        await message.channel.send("`cannot start thread here :[`")
        return

    args = users.replace("<@", "").replace(">", "").split(" ")

    for arg in args:
        user = message.guild.get_member(int(arg))
        if user == None:
            args.remove(arg)
            continue
        if user.bot:
            args.remove(arg)
            continue

    thread_channel = await message.channel.create_thread(name=f"R.O.B. thread", type=discord.ChannelType.public_thread)
    thread_id = thread_channel.id

    data[str(thread_id)] = {}
    data[str(thread_id)]["members"] = args
    data[str(thread_id)]["current"] = 0
    data[str(thread_id)]["last_ping"] = int(datetime.now().timestamp())
    data[str(thread_id)]["reblog_url"] = ""

    msg = f"`order:`"
    for arg in args:
        msg += f"\n<@{arg}>"
    
    await thread_channel.send(msg)

@bot.command(name="next", brief="pass on the turn")
async def next_turn(context, *, reblog_url=commands.parameter(default="", displayed_default="None", description="the url to display with the ping")):
    message: discord.Message = context.message
    thread_id = str(message.channel.id)
    if not thread_id in data.keys():
        await message.channel.send("`no thread here`")
        return

    if message.author.id != int(data[str(thread_id)]["members"][data[str(thread_id)]["current"]]):
        if "force" in message.content.split(' ')[1:]:
            await message.channel.send(f"`force passing {message.guild.get_member(int(data[str(thread_id)]['members'][data[str(thread_id)]['current']])).display_name}'s turn...`")
        else:
            await message.channel.send(f"`it's not your turn! >:[\n it's currently {message.guild.get_member(int(data[str(thread_id)]['members'][data[str(thread_id)]['current']])).display_name}'s turn`")
            return

    data[str(thread_id)]["current"] = (data[str(thread_id)]["current"] + 1) % len(data[str(thread_id)]["members"])
    data[str(thread_id)]["reblog_url"] = reblog_url

    await message.channel.send(f"`your turn `<@{data[str(thread_id)]['members'][data[str(thread_id)]['current']]}>`!\n`\n{data[str(thread_id)]['reblog_url']}")
    
    data[str(thread_id)]["last_ping"] = int(datetime.now().timestamp())

@bot.command(name="end", brief="end the thread")
async def end_thread(context):
    message: discord.Message = context.message
    thread_id = str(message.channel.id)
    if not thread_id in data.keys():
        await message.channel.send("`no thread here`")
        return

    data.pop(thread_id)

    await message.channel.send("```interaction ended!```")

@bot.command(name="join", brief="join the thread")
async def join_thread(context, index:int=commands.parameter(default=-1, description="the index to join the reblog order at")):
    message: discord.Message = context.message
    thread_id = str(message.channel.id)
    if not thread_id in data.keys():
        await message.channel.send("`no thread here`")
        return
    
    if index < 0:
        index = len(data[str(thread_id)]["members"]) + index + 1

    data[str(thread_id)]["members"].insert(index, str(message.author.id))
    if data[str(thread_id)]["current"] >= index:
            data[str(thread_id)]["current"] = data[str(thread_id)]["current"] + 1

    msg = f"joined thread!\n\nnew order:"
    for i in range(len(data[str(thread_id)]["members"])):
        msg += f"\n{str(i).zfill(int(len(data[str(thread_id)]['members'])/10))}. {message.guild.get_member(int(data[str(thread_id)]['members'][i])).display_name}"
        if i == data[str(thread_id)]["current"]:
            msg += " <=="
    
    await message.channel.send('`'+msg+'`')

@bot.command(name="leave", brief="leave the thread")
async def leave_thread(context, index:int|None=commands.parameter(default=None, displayed_default="all of them", description="which index to leave at")):
    message: discord.Message = context.message
    thread_id = str(message.channel.id)
    if not thread_id in data.keys():
        await message.channel.send("`no thread here`")
        return
    
    if not str(message.author.id) in data[str(thread_id)]["members"]:
        await message.channel.send("`you're not in this thread!")
    
    if index == None:
        data[str(thread_id)]["current"] = data[str(thread_id)]["current"] - data[str(thread_id)]["members"][:data[str(thread_id)]["current"]].count(str(message.author.id))
        data[str(thread_id)]["members"] = list(filter(lambda user: user != str(message.author.id), data[str(thread_id)]["members"])) # some magic from stack overflow
    else:
        if data[str(thread_id)]["members"][index] != str(message.author.id):
            await message.channel.send(f"`you're not in that index! that's `<@{data[str(thread_id)]['members'][index]}>")
            return
        data[str(thread_id)]["members"].pop(index)
        if data[str(thread_id)]["current"] > index:
            data[str(thread_id)]["current"] = data[str(thread_id)]["current"] - 1
    
    msg = f"left thread!\n\nnew order:"
    for i in range(len(data[str(thread_id)]["members"])):
        msg += f"\n{str(i).zfill(int(len(data[str(thread_id)]['members'])/10))}. {message.guild.get_member(int(data[str(thread_id)]['members'][i])).display_name}"
        if i == data[str(thread_id)]["current"]:
            msg += " <=="
    
    await message.channel.send('`'+msg+'`')

@bot.command(name="order", brief="show the reblog order")
async def show_thread_order(context):
    message: discord.Message = context.message
    thread_id = str(message.channel.id)
    if not thread_id in data.keys():
        await message.channel.send("`no thread here`")
        return
    
    msg = f"order:"
    for i in range(len(data[str(thread_id)]["members"])):
        msg += f"\n{str(i).zfill(int(len(data[str(thread_id)]['members'])/10))}. {message.guild.get_member(int(data[str(thread_id)]['members'][i])).display_name}"
        if i == data[str(thread_id)]["current"]:
            msg += " <=="
    
    await message.channel.send('`'+msg+'`')

@bot.command(name="say", brief="say something as rob (admin perm only)")
async def rob_say(context, *, text=commands.parameter(description="the text to say")):
    message: discord.Message = context.message
    if not (message.channel.permissions_for(message.author).manage_messages or message.author.id == 427151562641637376):
        await message.add_reaction('❌')
        sleep(5)
        await message.remove_reaction('❌')
        return
    await message.channel.send(text)
    await message.delete()

@bot.command(name="rename", brief="rename the current thread")
async def rename_thread(context, *, name=commands.parameter(description="new name")):
    message: discord.Message = context.message
    thread_id = str(message.channel.id)
    if not thread_id in data.keys():
        await message.channel.send("`no thread here`")
        return
    await message.channel.edit(name=name)

@bot.command(name="reping", brief="immediatelly send the reminder ping for this thread again")
async def reping(context):
    message: discord.Message = context.message
    thread_id = str(message.channel.id)
    if not thread_id in data.keys():
        await message.channel.send("`no thread here`")
        return
    await message.channel.send(f"`your turn `<@{data[thread_id]['members'][data[thread_id]['current']]}>`!\n`\n{data[thread_id]['reblog_url']}")
    data[thread_id]["last_ping"] = int(datetime.now().timestamp())

async def send_pings():
    for thread_key in list(data.keys()):
        if data[thread_key]["last_ping"] + 60*60*23 < int(datetime.now().timestamp()):
            thread_channel = bot.get_channel(int(thread_key))
            await thread_channel.send(f"`your turn `<@{data[thread_key]['members'][data[thread_key]['current']]}>`!\n`\n{data[thread_key]['reblog_url']}")
            data[thread_key]["last_ping"] = int(datetime.now().timestamp())
    save_json()


bot.run(open("TOKEN").read(), log_handler=handler)
