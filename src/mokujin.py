#!/usr/bin/env python3
import datetime
import logging
import os
import sys
import configurator
import random

import discord

sys.path.insert(1, (os.path.dirname(os.path.dirname(__file__))))
from functools import reduce
from discord.ext import commands
from src import tkfinder, util
from src.resources import embed, const
from github import Github

base_path = os.path.dirname(__file__)
config = configurator.Configurator(os.path.abspath(os.path.join(base_path, "resources", "config.json")))
prefix = '§'
description = 'The premier Tekken 7 Frame bot, made by Baikonur#4927, continued by Tib#1303'
bot = commands.Bot(command_prefix=prefix, description=description)

# Set logger to log errors
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

logfile_directory = os.path.abspath(os.path.join(base_path, "..", "log"))
logfile_path = logfile_directory + "\\logfile.log"

# Create logfile if not exists
if not os.path.exists(logfile_directory):
    os.makedirs(logfile_directory)

if not os.path.isfile(logfile_path):
    open(logfile_path, "w")

file_handler = logging.FileHandler(logfile_path)
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

discord_token = config.read_config()['DISCORD_TOKEN']
feedback_channel_id = config.read_config()['FEEDBACK_CHANNEL_ID']
github_token = config.read_config()['GITHUB_TOKEN']
gh = Github(login_or_token=github_token)


@bot.event
async def on_ready():
    print(datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="hyld3 whining :3"))

@bot.event
async def on_reaction_add(reaction, user):
    if reaction.message.author.id == bot.user.id and user.id != bot.user.id and reaction.count < 3:
        item_index = const.EMOJI_LIST.index(reaction.emoji) if reaction.emoji in const.EMOJI_LIST else -1

        if item_index > -1:
            delete_after = config.get_auto_delete_duration(reaction.message.channel.id)
            content = reaction.message.embeds[0].description.replace('\n', '\\n').split("\\n")
            character_name = util.get_character_name_from_content(content)
            character = tkfinder.get_character_detail(character_name)
            move_list = util.get_moves_from_content(content)
            move = move_list[item_index]

            result = util.display_moves_by_input(character, move)
            gif_val = None
            for f in result.fields:
                if 'Gif' in f.name:
                    gif_val = f.value
            await reaction.message.channel.send(embed=result, delete_after=delete_after)
            if gif_val is not None:
                await reaction.message.channel.send(gif_val)
            await reaction.remove(bot.user)

            
@bot.event
async def on_message(message):
    """This has the main functionality of the bot. It has a lot of
    things that would be better suited elsewhere but I don't know
    if I'm going to change it."""
    try:
        channel = message.channel
        if str(message.author) in const.BLACKLIST:
            return

        if message.content.startswith('!clear-messages'):
            # delete x of the bot last messages
            number = int(message.content.split(' ', 1)[1])
            messages = []
            async for m in channel.history(limit=100):
                if m.author == bot.user:
                    messages.append(m)

            to_delete = [message]
            for i in range(number):
                to_delete.append(messages[i])

            await channel.delete_messages(to_delete)

        elif message.content == '!help':
            await channel.send(embed=embed.help_embed())

        elif message.content.startswith('!roll'):
            params = message.content.split(' ')
            print(params)
            n = random.randint(int(params[1]), int(params[2]))
            await channel.send("> Kinjin says: %s" % (str(n)))

        
        elif message.content.startswith('!random'):
            all_chars = tkfinder.get_character_list()

            if len(message.content[1:].split(' ', 1)) > 1:
                banned_chars = [s.replace(' ', '') for s in message.content[1:].split(' ', 1)[1:]][0].split(',')

                del all_chars["generic"]
                
                for i in banned_chars:
                    if i in all_chars:
                        del all_chars[i]
                    else:
                        for k, v in all_chars.items():
                            if i in v:
                                del all_chars[k]
                                continue

                print(all_chars)
            all_char_names = list(all_chars.keys())
            await channel.send("> Your random character is: **" + random.choice(all_char_names) + "**")
            
        # Find a move
        elif message.content.startswith('!') and len(message.content[1:].split(' ', 1)) > 1:

            delete_after = config.get_auto_delete_duration(channel.id)
            user_message_list = message.content[1:].split(' ', 1)

            original_name = user_message_list[0].lower()
            original_move = user_message_list[1]

            character_name = tkfinder.correct_character_name(original_name)

            if character_name is not None:
                character = tkfinder.get_character_detail(character_name)
                move_type = util.get_move_type(original_move.lower())

                if move_type:
                    result = util.display_moves_by_type(character, move_type)
                else:
                    result = util.display_moves_by_input(character, original_move)
            else:
                result = embed.error_embed(f'Character {original_name} does not exist.')
                delete_after = 5

            gif_val = None
            for f in result.fields:
                if 'Gif' in f.name:
                    gif_val = f.value
            bot_message = await channel.send(embed=result, delete_after=delete_after)
            if gif_val is not None:
                await channel.send(gif_val)
            if embed.MOVE_NOT_FOUND_TITLE == bot_message.embeds[0].title:
                content = bot_message.embeds[0].description.replace('\n', '\\n').split("\\n")
                movelist = util.get_moves_from_content(content)
                for i in range(len(movelist)):
                    await bot_message.add_reaction(const.EMOJI_LIST[i])

        await bot.process_commands(message)
    except Exception as e:
        time_now = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        error_msg = f'{time_now} | Message: {message.content} from {message.author.name} in {message.channel.guild.name}.' \
                    f'\n Error: {e}'
        print(error_msg)
        logger.error(error_msg)


bot.run(discord_token)
