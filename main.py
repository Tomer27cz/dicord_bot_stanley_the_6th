import discord
import asyncio
from discord import FFmpegPCMAudio, app_commands, Forbidden
from discord.ext import commands
from discord.ui import View


import yt_dlp
from youtubesearchpython import *
from urllib.request import urlopen
from bs4 import BeautifulSoup

from os import path, listdir
from math import ceil
from mutagen.mp3 import MP3
import sys
from typing import Literal
import traceback
import datetime
import pickle

from database import radia_stream, radia_url, radia_literal1, radia_literal2, radia_literal3, radia_literal4,\
    favourite_radia_literal, radia_name, radia_thumbnail,  react_dict, guild_ids, language_list_literal, language_list
from database import text
from database import text_cs, text_de, text_eo, text_es, text_fr, text_it, text_ja, text_ko, text_la, text_zh_cn
from api_keys import api_key, api_key_testing

import functools


PREFIX = '$'
BOT_ID = 1007004463933952120
MY_ID = 349164237605568513

api_key_testing = api_key_testing
api_key = api_key

guild_id_objects = []

# get same amount of list, string and booleans
dict_list_list = []
dict_boolean_true_list = []
dict_boolean_false_list = []
dict_string_list = []
for guild_index, guild_val in enumerate(guild_ids):
    guild_id_objects.append(discord.Object(id=guild_val))
for index_i in range(20):
    globals()[f'dict_list_list_{index_i}'] = []
    globals()[f'dict_boolean_true_list_{index_i}'] = []
    globals()[f'dict_boolean_false_list_{index_i}'] = []
    globals()[f'dict_string_list_{index_i}'] = []
    for guild_index, guild_val in enumerate(guild_ids):
        globals()[f'dict_list_list_{index_i}'].append([])
        globals()[f'dict_boolean_true_list_{index_i}'].append('True')
        globals()[f'dict_boolean_false_list_{index_i}'].append('False')
        globals()[f'dict_string_list_{index_i}'].append("")


# ---------------- Bot class ------------


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=PREFIX, intents=intents)
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        print_message('no guild',
                      "--------------------------------------- NEW / REBOOTED ----------------------------------------")
        if not self.synced:
            print_message('no guild', "Trying to sync commands")
            await self.tree.sync()
            print_message('no guild', f"Synced slash commands for {self.user}")
        await bot.change_presence(activity=discord.Game(name=f"{PREFIX}help"))
        print_message('no guild', 'Logged in as:\n{0.user.name}\n{0.user.id}'.format(bot))

    async def on_voice_state_update(self, member, before, after):
        if not member.id == self.user.id:
            return
        elif before.channel is None:
            voice = after.channel.guild.voice_client
            time = 0
            while True:
                await asyncio.sleep(1)
                time = time + 1
                if voice.is_playing() and not voice.is_paused():
                    time = 0
                if time == 300:  # how many seconds of inactivity to disconnect | 300 = 5min
                    stopped[member.guild.id] = 'True'
                    voice.stop()
                    await voice.disconnect()
                    print_message(member.guild.id, "Disconnecting after 180 second of nothing playing")
                if not voice.is_connected():
                    break

    async def on_command_error(self, ctx, error):
        print_message(ctx.guild.id, f"{error}")
        await ctx.reply(f"{error}   {bot.get_user(MY_ID).mention}", ephemeral=True)


bot = Bot()

# noinspection PyUnresolvedReferences
queue = dict(zip(guild_ids, dict_list_list_1))
# noinspection PyUnresolvedReferences
qt = dict(zip(guild_ids, dict_list_list_2))
# noinspection PyUnresolvedReferences
qi = dict(zip(guild_ids, dict_list_list_3))
# noinspection PyUnresolvedReferences
qd = dict(zip(guild_ids, dict_list_list_4))
# noinspection PyUnresolvedReferences
qu = dict(zip(guild_ids, dict_list_list_5))
# noinspection PyUnresolvedReferences
qa = dict(zip(guild_ids, dict_list_list_6))
# noinspection PyUnresolvedReferences
qal = dict(zip(guild_ids, dict_list_list_7))
# noinspection PyUnresolvedReferences
sl_link = dict(zip(guild_ids, dict_list_list_8))
# noinspection PyUnresolvedReferences
sl_title = dict(zip(guild_ids, dict_list_list_9))
# noinspection PyUnresolvedReferences
sl_picture = dict(zip(guild_ids, dict_list_list_10))
# noinspection PyUnresolvedReferences
sl_duration = dict(zip(guild_ids, dict_list_list_11))
# noinspection PyUnresolvedReferences
sl_username = dict(zip(guild_ids, dict_list_list_12))
# noinspection PyUnresolvedReferences
sl_author = dict(zip(guild_ids, dict_list_list_13))
# noinspection PyUnresolvedReferences
sl_author_link = dict(zip(guild_ids, dict_list_list_14))
# noinspection PyUnresolvedReferences
now_link = dict(zip(guild_ids, dict_string_list_1))
# noinspection PyUnresolvedReferences
now_title = dict(zip(guild_ids, dict_string_list_2))
# noinspection PyUnresolvedReferences
now_picture = dict(zip(guild_ids, dict_string_list_3))
# noinspection PyUnresolvedReferences
now_duration = dict(zip(guild_ids, dict_string_list_4))
# noinspection PyUnresolvedReferences
now_username = dict(zip(guild_ids, dict_string_list_5))
# noinspection PyUnresolvedReferences
now_author = dict(zip(guild_ids, dict_string_list_6))
# noinspection PyUnresolvedReferences
now_author_link = dict(zip(guild_ids, dict_string_list_7))
# noinspection PyUnresolvedReferences
removed_embed = dict(zip(guild_ids, dict_boolean_true_list_2))
# noinspection PyUnresolvedReferences
loop_mode = dict(zip(guild_ids, dict_boolean_false_list_1))
# noinspection PyUnresolvedReferences
stopped = dict(zip(guild_ids, dict_boolean_false_list_2))
# noinspection PyUnresolvedReferences
org_search = dict(zip(guild_ids, dict_string_list_8))
# noinspection PyUnresolvedReferences
custom_search = dict(zip(guild_ids, dict_string_list_9))
# noinspection PyUnresolvedReferences
is_radio = dict(zip(guild_ids, dict_boolean_false_list_5))
# noinspection PyUnresolvedReferences
radio_type_global = dict(zip(guild_ids, dict_string_list_10))
# noinspection PyUnresolvedReferences
# game_board = dict(zip(guild_ids, dict_string_list_10))
# noinspection PyUnresolvedReferences
response_type = dict(zip(guild_ids, dict_string_list_11))
# noinspection PyUnresolvedReferences
player_control_buttons = dict(zip(guild_ids, dict_boolean_false_list_6))
# noinspection PyUnresolvedReferences
guild_lang = dict(zip(guild_ids, dict_string_list_12))


vlc_logo_link = 'https://cdn.discordapp.com/attachments/892403162315644931/1008054767379030096/vlc.png'


# Sound effects listing
all_sound_effects = listdir('sound_effects')  # getting file names
for file_index, file_val in enumerate(all_sound_effects):
    all_sound_effects[file_index] = all_sound_effects[file_index][:len(file_val) - 4]  # getting rid of extension


# ------------------------------------------------ Config ------------------------------------------------------

for index_g, val_g in enumerate(guild_ids):
    response_type[val_g] = 'short'
    guild_lang[val_g] = 'en'

guild_lang[1008145667622969397] = 'cs'

# -------------------------------------------- Load Config -----------------------------------------------------
# removed_embed, response_type, player_control_buttons, guild_lang


def load_config():
    global removed_embed, response_type, player_control_buttons, guild_lang
    filename = 'config.pk'

    with open(filename, 'rb') as fi:
        config_list = pickle.load(fi)

    print(config_list)

    removed_embed = config_list[0]
    response_type = config_list[1]
    player_control_buttons = config_list[2]
    guild_lang = config_list[3]


def save_config():
    global removed_embed, response_type, player_control_buttons, guild_lang
    filename = 'config.pk'

    config_list = [removed_embed, response_type, player_control_buttons, guild_lang]

    print(config_list)

    with open(filename, 'wb') as fi:
        # dump your data into the file
        pickle.dump(config_list, fi)


# load_config()  # ----------------------- load config on startup --------------------


def reset_config():
    global removed_embed, response_type, player_control_buttons, guild_lang

    original_config = [removed_embed, response_type, player_control_buttons, guild_lang]

    for guild_id in guild_ids:
        removed_embed[guild_id] = 'True'
        player_control_buttons[guild_id] = 'False'
        response_type[guild_id] = 'short'
        guild_lang[guild_id] = 'en'

    now_config = [removed_embed, response_type, player_control_buttons, guild_lang]
    return [original_config, now_config]


def config_set(guild_id, variable, value):
    global removed_embed, response_type, player_control_buttons, guild_lang

    if variable == 'removed_embed':
        if value == 'True' or value == 'False':
            removed_embed[guild_id] = value
        else:
            return [False, '`bool_value` required']

    if variable == 'player_control_buttons':
        if value == 'True' or value == 'False':
            player_control_buttons[guild_id] = value
        else:
            return [False, '`bool_value` required']

    if variable == 'response_type':
        if value == 'short' or value == 'long':
            response_type[guild_id] = value
        else:
            return [False, '`response_type_value` required']

    if variable == 'language':
        if value in language_list:
            guild_lang[guild_id] = value
        else:
            return [False, '`language_code` required']

# ---------------------------------------------- TEXT ----------------------------------------------------------


def text_guild(guild_id, content):
    lang = guild_lang[guild_id]
    if lang == 'en':
        return content
    return globals()[f'text_{lang}'][content]


# -----search_list----


def sl_add(va_list_local, guild_id):
    global sl_link, sl_title, sl_picture, sl_duration, sl_username, sl_author, sl_author_link
    sl_link[guild_id].append(va_list_local[0])
    sl_title[guild_id].append(va_list_local[1])
    sl_picture[guild_id].append(va_list_local[2])
    sl_duration[guild_id].append(va_list_local[3])
    sl_username[guild_id].append(va_list_local[4])
    sl_author[guild_id].append(va_list_local[5])
    sl_author_link[guild_id].append(va_list_local[6])


def sl_clear(guild_id):
    global sl_link, sl_title, sl_picture, sl_duration, sl_username, \
        sl_author, sl_author_link
    sl_link[guild_id].clear()
    sl_title[guild_id].clear()
    sl_picture[guild_id].clear()
    sl_duration[guild_id].clear()
    sl_username[guild_id].clear()
    sl_author[guild_id].clear()
    sl_author_link[guild_id].clear()


def sl_get_va(number, guild_id):
    global sl_link, sl_title, sl_picture, sl_duration, sl_username, \
        sl_author, sl_author_link
    va_list = [sl_link[guild_id][number], sl_title[guild_id][number], sl_picture[guild_id][number],
               sl_duration[guild_id][number], sl_username[guild_id][number], sl_author[guild_id][number],
               sl_author_link[guild_id][number]]
    return va_list


# ----------queue list-------


def queue_add(va_list, guild_id, n=None):
    print(f"queue_add: {va_list}\n{guild_id}\n{n}")
    global queue, qt, qi, qd, qu, qa, qal
    if not n and n != 0:
        queue[guild_id].append(va_list[0])
        qt[guild_id].append(va_list[1])
        qi[guild_id].append(va_list[2])
        qd[guild_id].append(va_list[3])
        qu[guild_id].append(va_list[4])
        qa[guild_id].append(va_list[5])
        qal[guild_id].append(va_list[6])
        return
    if n > len(queue):
        n = len(queue)
    queue[guild_id].insert(n, va_list[0])
    qt[guild_id].insert(n, va_list[1])
    qi[guild_id].insert(n, va_list[2])
    qd[guild_id].insert(n, va_list[3])
    qu[guild_id].insert(n, va_list[4])
    qa[guild_id].insert(n, va_list[5])
    qal[guild_id].insert(n, va_list[6])


def queue_clear(guild_id):
    global queue, qt, qi, qd, qu, qa, qal
    queue[guild_id].clear()
    qt[guild_id].clear()
    qi[guild_id].clear()
    qd[guild_id].clear()
    qu[guild_id].clear()
    qa[guild_id].clear()
    qal[guild_id].clear()


def queue_export(guild_id):
    global queue
    export_message = ''
    queue_length = len(queue[guild_id])-1
    for index, val in enumerate(queue[guild_id]):
        url_code = val[32:]
        export_message += url_code
        if index < queue_length:
            export_message += ','
    return export_message


def queue_import(message, user, guild_id):
    global queue, qt, qi, qd, qu, qa, qal
    list_of_codes = message.split(",")
    for index, val in enumerate(list_of_codes):
        url = 'https://www.youtube.com/watch?v=' + val
        va_list = get_video_info(url, user)
        queue_add(va_list, guild_id)
    return len(list_of_codes)


def queue_remove(n, guild_id):
    global queue, qt, qi, qd, qu, qa, qal
    va_list = [queue[guild_id][n], qt[guild_id][n], qi[guild_id][n], qd[guild_id][n], qu[guild_id][n], qa[guild_id][n],
               qal[guild_id][n]]
    del (queue[guild_id][n])
    del (qt[guild_id][n])
    del (qi[guild_id][n])
    del (qd[guild_id][n])
    del (qu[guild_id][n])
    del (qa[guild_id][n])
    del (qal[guild_id][n])
    return va_list


def queue_get_va(n, guild_id):
    global queue, qt, qi, qd, qu, qa, qal
    va_list = [queue[guild_id][n], qt[guild_id][n], qi[guild_id][n], qd[guild_id][n], qu[guild_id][n], qa[guild_id][n],
               qal[guild_id][n]]
    return va_list


# ---------video_info / url --------


def get_video_info(url, user):
    if url[0:30] == "https://www.youtube.com/watch?":
        video = Video.getInfo(url)  # mode=ResultMode.json
        title = video['title']
        picture = 'https://img.youtube.com/vi/' + video['id'] + '/default.jpg'
        # noinspection PyTypeChecker
        duration = video['duration']['secondsText']
        # noinspection PyTypeChecker
        channel_name = video['channel']['name']
        # noinspection PyTypeChecker
        channel_link = video['channel']['link']
        return [url, title, picture, duration, user, channel_name, channel_link]
    else:
        raise ValueError


def get_pure_url(url):
    url = url[:url.index('&list=')]
    return url


def get_playlist_from_url(url):
    print(f"get playlist : {url}")
    code = url[url.index('&list=')+1:url.index('&index=')]
    playlist_url = 'https://www.youtube.com/playlist?' + code
    print(f"get playlist finished: {playlist_url}")
    return playlist_url


def get_info_radio(url, radio_type, author):
    html = urlopen(url).read()
    soup = BeautifulSoup(html, features="lxml")
    data1 = soup.find('div', attrs={'class': 'interpret-image'})
    data2 = soup.find('div', attrs={'class': 'interpret-info'})

    thumbnail = data1.find('img')['src']
    author_name = data2.find('div', attrs={'class': 'nazev'})
    song_name = data2.find('div', attrs={'class': 'song'})
    author_name_final = author_name.text.lstrip().rstrip()
    song_name_final = song_name.text.lstrip().rstrip()

    va_list = [radia_url[radia_name.index(radio_type)], song_name_final, thumbnail, 'Stream', author, author_name_final,
               radia_url[radia_name.index(radio_type)]]
    return va_list


# -------------- convert -----------


def convert_tuple(tup):
    str_out = ''
    for item in tup:
        str_out = str_out + item
    return str_out


def convert(duration):
    try:
        if duration is None or duration == 0 or duration == '0':
            return 'Stream'
        seconds = int(duration) % (24 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        if hour:
            if not minutes:
                minutes = 00
            if not seconds:
                seconds = 00
            return "%d:%02d:%02d" % (hour, minutes, seconds)
        if not hour:
            if not minutes:
                minutes = 00
            if not seconds:
                seconds = 00
            return "%02d:%02d" % (minutes, seconds)
    except (ValueError, TypeError):
        return duration


# ------------ other get/set info --------------------

def now_playing(va_list, guild_id):
    global now_link, now_title, now_picture, now_duration, now_username, now_author, now_author_link
    now_link[guild_id] = va_list[0]
    now_title[guild_id] = va_list[1]
    now_picture[guild_id] = va_list[2]
    now_duration[guild_id] = va_list[3]
    now_username[guild_id] = va_list[4]
    now_author[guild_id] = va_list[5]
    now_author_link[guild_id] = va_list[6]


def mp3_length(path_of_mp3):
    audio = MP3(path_of_mp3)
    length = audio.info.length
    return length


def set_response_type(response_type_now, guild_id):
    response_type[guild_id] = response_type_now


def print_command(ctx, text_data, options, text_only=False):
    now_time = datetime.datetime.now()
    message = f"{now_time.strftime('%d/%m/%y %X')} -{ctx.guild.id}- {text_data}: {options}"

    if not text_only:
        message = f"{now_time.strftime('%d/%m/%y %X')} -{ctx.guild.id}- Command ({text_data}) was requested by" \
                  f" ({ctx.message.author}) -- (options: {options})"
        if text_data == 'queue_add':
            if options[3]:
                message = f"{now_time.strftime('%d/%m/%y %X')} -{ctx.guild.id}- Muted ({text_data}) was requested by" \
                          f" ({ctx.message.author}) -- (options: {options})"

    print(message)
    message += "\n"

    f = open("log.txt", "a", encoding="utf-8")
    f.write(message)
    f.close()


def print_message(guild_id, content):
    now_time = datetime.datetime.now()
    f = open("log.txt", "a")
    messages = content.split('\n')
    for index, val in enumerate(messages):
        message = f"{now_time.strftime('%d/%m/%y %X')} -{guild_id}- {val}"
        print(message)
        f.write(message + '\n')
    f.close()


# ---------------EMBED--------------


def create_embed(va_list, name, guild_id):
    #  (link, title, picture, duration, user, author, author_link)
    #  (  0    1       2         3        4    5          6      )
    embed = (discord.Embed(title=name,
                           description=f'```css\n{va_list[1]}\n```',
                           color=discord.Color.blurple()))
    if name == text_guild(guild_id, "Now playing"):
        now_playing(va_list, guild_id)
    if va_list[3]:
        embed.add_field(name=text_guild(guild_id, 'Duration'), value=convert(va_list[3]))
    if va_list[4]:
        try:
            embed.add_field(name=text_guild(guild_id, 'Requested by'), value=va_list[4].mention)
        except AttributeError:
            embed.add_field(name=text_guild(guild_id, 'Requested by'), value=va_list[4])
    if va_list[5] and va_list[6]:
        embed.add_field(name=text_guild(guild_id, 'Author'), value=f'[{va_list[5]}]({va_list[6]})')
    if va_list[0]:
        embed.add_field(name=text_guild(guild_id, 'URL'), value=f'[{va_list[0]}]({va_list[0]})')
    if va_list[2]:
        embed.set_thumbnail(url=va_list[2])

    return embed


# ------------- Youtube DL classes -----------


YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, cr_search: str, *, cr_loop: asyncio.BaseEventLoop = None):
        cr_loop = cr_loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, cr_search, download=False, process=False)
        data = await cr_loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Couldn\'t find anything that matches `{}`'.format(cr_search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('Couldn\'t find anything that matches `{}`'.format(cr_search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await cr_loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hours'.format(hours))
        if minutes > 0:
            duration.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration.append('{} seconds'.format(seconds))

        return ', '.join(duration)

# ----------------------------------------------------------------------------------------------------------------------


# ------------------------------------ View Classes --------------------------------------------------------------------


class PlayerControlView(View):

    def __init__(self, ctx):
        super().__init__(timeout=7200)
        self.guild = ctx.guild
        self.guild_id = ctx.guild.id

    @discord.ui.button(emoji=react_dict['play'], style=discord.ButtonStyle.blurple, custom_id='play')
    async def callback(self, interaction, button):
        voice = discord.utils.get(bot.voice_clients, guild=self.guild)
        if voice:
            if voice.is_paused():
                voice.resume()
                # noinspection PyUnresolvedReferences
                pause_button = [x for x in self.children if x.custom_id == 'pause'][0]
                pause_button.style = discord.ButtonStyle.blurple
                button.style = discord.ButtonStyle.grey
                await interaction.response.edit_message(view=self)
            elif voice.is_playing():
                await interaction.response.send_message(text_guild(self.guild_id, "Player **already resumed!**"),
                                                        ephemeral=True)
            else:
                await interaction.response.send_message(text_guild(self.guild_id, "No audio playing"), ephemeral=True)
        else:
            await interaction.response.send_message(text_guild(self.guild_id, "No audio"), ephemeral=True)

    @discord.ui.button(emoji=react_dict['pause'], style=discord.ButtonStyle.blurple, custom_id='pause')
    async def pause_callback(self, interaction, button):
        voice = discord.utils.get(bot.voice_clients, guild=self.guild)
        if voice:
            if voice.is_playing():
                voice.pause()
                # noinspection PyUnresolvedReferences
                play_button = [x for x in self.children if x.custom_id == 'play'][0]
                play_button.style = discord.ButtonStyle.blurple
                button.style = discord.ButtonStyle.grey
                await interaction.response.edit_message(view=self)
            elif voice.is_paused():
                await interaction.response.send_message(text_guild(self.guild_id, "Player **already paused!**"),
                                                        ephemeral=True)
            else:
                await interaction.response.send_message(text_guild(self.guild_id, "No audio playing"), ephemeral=True)
        else:
            await interaction.response.send_message(text_guild(self.guild_id, "No audio"), ephemeral=True)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['stop'], style=discord.ButtonStyle.red, custom_id='stop')
    async def stop_callback(self, interaction, button):
        voice = discord.utils.get(bot.voice_clients, guild=self.guild)
        if voice:
            if voice.is_playing() or voice.is_paused():
                voice.stop()
                stopped[interaction.guild_id] = 'True'
                await interaction.response.edit_message(view=None)
            else:
                await interaction.response.send_message(text_guild(self.guild_id, "No audio playing"), ephemeral=True)
        else:
            await interaction.response.send_message(text_guild(self.guild_id, "No audio"), ephemeral=True)


class SearchOptionView(View):

    def __init__(self, ctx, is_play=False):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.guild = ctx.guild
        self.guild_id = ctx.guild.id
        self.is_play = is_play

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['1'], style=discord.ButtonStyle.blurple, custom_id='1')
    async def callback_1(self, interaction, button):
        va_list = sl_get_va(0, self.guild.id)
        queue_add(va_list, self.guild.id)
        await interaction.response.edit_message(content=f'`{va_list[1]}` '
                                                        f'{text_guild(self.guild_id, "added to queue!")}', view=None)
        if self.is_play:
            await play(self.ctx)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['2'], style=discord.ButtonStyle.blurple, custom_id='2')
    async def callback_2(self, interaction, button):
        va_list = sl_get_va(1, self.guild.id)
        queue_add(va_list, self.guild.id)
        await interaction.response.edit_message(content=f'`{va_list[1]}` '
                                                        f'{text_guild(self.guild_id, "added to queue!")}', view=None)
        if self.is_play:
            await play(self.ctx)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['3'], style=discord.ButtonStyle.blurple, custom_id='3')
    async def callback_3(self, interaction, button):
        va_list = sl_get_va(2, self.guild.id)
        queue_add(va_list, self.guild.id)
        await interaction.response.edit_message(content=f'`{va_list[1]}` '
                                                        f'{text_guild(self.guild_id, "added to queue!")}', view=None)
        if self.is_play:
            await play(self.ctx)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['4'], style=discord.ButtonStyle.blurple, custom_id='4')
    async def callback_4(self, interaction, button):
        va_list = sl_get_va(3, self.guild.id)
        queue_add(va_list, self.guild.id)
        await interaction.response.edit_message(content=f'`{va_list[1]}` '
                                                        f'{text_guild(self.guild_id, "added to queue!")}', view=None)
        if self.is_play:
            await play(self.ctx)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['5'], style=discord.ButtonStyle.blurple, custom_id='5')
    async def callback_5(self, interaction, button):
        va_list = sl_get_va(4, self.guild.id)
        queue_add(va_list, self.guild.id)
        await interaction.response.edit_message(content=f'`{va_list[1]}` '
                                                        f'{text_guild(self.guild_id, "added to queue!")}', view=None)
        if self.is_play:
            await play(self.ctx)


class PlaylistOptionView(View):

    def __init__(self, ctx, url):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.url = url
        self.guild = ctx.guild
        self.guild_id = ctx.guild.id

    # noinspection PyUnusedLocal
    @discord.ui.button(label='Yes', style=discord.ButtonStyle.blurple)
    async def callback_1(self, interaction, button):
        playlist_url = get_playlist_from_url(self.url)
        response = await queue_command(self.ctx, playlist_url, None, None, True)
        await interaction.response.edit_message(content=response[1], view=None)

    # noinspection PyUnusedLocal
    @discord.ui.button(label='No, just add this', style=discord.ButtonStyle.blurple)
    async def callback_2(self, interaction, button):
        pure_url = get_pure_url(self.url)
        response = await queue_command(self.ctx, pure_url, None, None, True)
        await interaction.response.edit_message(content=response[1], view=None)
        await play(self.ctx)


# ---------------------------------------Youtube Search--------------------------------------------------


@bot.hybrid_command(name='search', with_app_command=True, description=text['search'],  help=text['search'])
@app_commands.describe(search_query=text['search_query'])
async def search_command(ctx: commands.Context,
                         search_query,
                         display_type: Literal['text', 'embed'] = 'text',
                         is_internal=False):
    print_command(ctx, 'search', [search_query, display_type])
    global org_search, custom_search
    await ctx.defer()
    guild_id = ctx.guild.id
    message = ''
    org_search[guild_id] = search_query
    response = response_type[guild_id]
    if display_type == 'text':
        response = 'short'
    if display_type == 'embed':
        response = 'long'
        await ctx.reply(text_guild(guild_id, 'Searching...'), ephemeral=True)

    custom_search[guild_id] = VideosSearch(search_query, limit=5)
    sl_clear(guild_id)

    view = SearchOptionView(ctx, is_internal)

    for i in range(5):
        url = custom_search[ctx.guild.id].result()['result'][i]['link']
        va_list = get_video_info(url, ctx.author)
        sl_add(va_list, guild_id)

        if response == 'long':
            embed = create_embed(va_list, f'{text_guild(guild_id, "Result #")}{i + 1}', guild_id)
            await ctx.message.channel.send(embed=embed)
        if response == 'short':
            message += f'{text_guild(guild_id, "Result #")}{i+1} : `{va_list[1]}`\n'
    if response == 'short':
        await ctx.reply(message, view=view)


# -------------------------------------Queue---------------------------------------------------------


@bot.hybrid_command(name='queue', with_app_command=True, description=text['queue_add'], help=text['queue_add'])
@app_commands.describe(url=text['url'], position=text['pos'], mute_response=text['mute_response'],
                       search_number=text['search_number'])
async def queue_command(ctx: commands.Context,
                        url=None,
                        search_number: app_commands.Range[int, 1, 20] = None,
                        position: int = None,
                        mute_response: bool = None,
                        is_internal: bool = False
                        ):
    print_command(ctx, 'queue', [url, search_number, position, mute_response])

    guild_id = ctx.guild.id

    if position:
        position -= 1

    if not url and not search_number and not position and not mute_response:
        message = text_guild(guild_id, "`url` or `search results` are **required**")

        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return [False, message]

    if (position and not url and not search_number) or (mute_response and not search_number and not url):
        message = text_guild(guild_id, "`url` or `search results` are **required**")

        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return [False, message]

    if url and search_number:
        message = text_guild(guild_id, "Chose only one  `url`  or  `search results`")

        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return [False, message]

    if search_number:
        n = search_number - 1
        va_list = [sl_link[guild_id][n], sl_title[guild_id][n], sl_picture[guild_id][n], sl_duration[guild_id][n],
                   sl_username[guild_id][n], sl_author[guild_id][n], sl_author_link[guild_id][n]]
        queue_add(va_list, guild_id, position)

        message = f'`{va_list[1]}` {text_guild(guild_id, "added to queue!")}'

        if not mute_response:
            await ctx.reply(message)
        return [True, message]

    elif url[0:33] == "https://www.youtube.com/playlist?":
        try:
            playlist_videos = Playlist.getVideos(url)
        except KeyError:
            print_message(guild_id, "------------------------------- playlist -------------------------")
            tb = traceback.format_exc()
            print_message(guild_id, tb)
            print_message(guild_id, "--------------------------------------------------------------")

            message = f'This playlist is unviewable: `{url}`'

            await ctx.reply(message)

            return [False, message]
        playlist_songs = 0

        playlist_videos = playlist_videos['videos']
        if position or position == 0:
            playlist_videos = list(reversed(playlist_videos))

        for index, val in enumerate(playlist_videos):

            playlist_songs += 1

            # noinspection PyTypeChecker
            va_list = [
                f"https://www.youtube.com/watch?v={playlist_videos[index]['id']}",
                playlist_videos[index]['title'],
                f"https://img.youtube.com/vi/{playlist_videos[index]['id']}/default.jpg",
                playlist_videos[index]['duration'],
                ctx.author,
                playlist_videos[index]['channel']['name'],
                f"https://www.youtube.com{playlist_videos[index]['channel']['link']}",
            ]

            queue_add(va_list, guild_id, position)

        message = f"`{playlist_songs}` {text_guild(guild_id, 'songs from playlist added to queue!')}"

        if not mute_response:
            await ctx.reply(message)

        return [True, message]

    elif url:
        if url[len(url) - 7:len(url) - 1] == 'index=':
            view = PlaylistOptionView(ctx, url)

            message = text_guild(guild_id,
                                 'This video is from a **playlist**, do you want to add the playlist to **queue?**')
            await ctx.reply(message, view=view)
            return [False]
        try:
            va_list = get_video_info(url, ctx.author)
            queue_add(va_list, guild_id, position)

            message = f'`{va_list[1]}` {text_guild(guild_id, "added to queue!")}'

            if not mute_response:
                await ctx.reply(message)

            return [True, message]

        except (ValueError, IndexError, TypeError):
            try:
                url_only_id = 'https://www.youtube.com/watch?' + url
                va_list = get_video_info(url_only_id, ctx.author)
                queue_add(va_list, guild_id, position)

                message = f'`{va_list[1]}` {text_guild(guild_id, "added to queue!")}'

                if not mute_response:
                    await ctx.reply(message)

                return [True, message]

            except (ValueError, IndexError, TypeError):

                await search_command(ctx, url, 'text', is_internal)

                message = f'`{url}` {text_guild(guild_id, "is not supported!")}'

                # await ctx.reply(message, ephemeral=True)

                return [False, message]


@bot.hybrid_command(name='remove', with_app_command=True, description=text['queue_remove'],
                    help=text['queue_remove'])
@app_commands.describe(number=text['number'], all_songs=text['all_songs'])
async def remove(ctx: commands.Context, number: int = None, all_songs: Literal['True'] = None,
                 ephemeral: Literal['True', 'False'] = 'False'):
    print_command(ctx, 'remove', [number, all_songs, ephemeral])
    guild_id = ctx.guild.id

    if not number and not all_songs:
        await show(ctx)
    if number and all_songs:
        await ctx.reply(text_guild(guild_id, "Chose only one!"), ephemeral=True)
        return
    if all_songs == 'True':
        queue_clear(guild_id)
        if ephemeral == 'True':
            await ctx.reply(text_guild(guild_id, 'Removed **all** songs from queue'), ephemeral=True)
        else:
            await ctx.reply(text_guild(guild_id, 'Removed **all** songs from queue'))
        return
    elif number:
        if number > len(queue[guild_id]):
            if not queue[guild_id]:
                await ctx.reply(text_guild(guild_id, "Nothing to **remove**, queue is **empty!**"), ephemeral=True)
                return
            await ctx.reply(text_guild(guild_id, "Index out of range!"), ephemeral=True)
            return
        n = number - 1
        if removed_embed[guild_id]:
            va_list = [queue[guild_id][n], qt[guild_id][n], qi[guild_id][n], qd[guild_id][n], qu[guild_id][n],
                       qa[guild_id][n], qal[guild_id][n]]
            if response_type[guild_id] == 'long':
                embed = create_embed(va_list, f'{text_guild(guild_id, "REMOVED #")}{n+1}', guild_id)
                if ephemeral == 'True':
                    await ctx.reply(embed=embed, ephemeral=True)
                else:
                    await ctx.reply(embed=embed)
            if response_type[guild_id] == 'short':
                if ephemeral == 'True':
                    await ctx.reply(f'REMOVED #{n+1} : `{va_list[1]}`', ephemeral=True)
                else:
                    await ctx.reply(f'REMOVED #{n + 1} : `{va_list[1]}`')
        queue_remove(n, guild_id)


@bot.hybrid_command(name='show', with_app_command=True, description=text['queue_show'], help=text['queue_show'])
@app_commands.describe(display_type=text['display_type'])
async def show(ctx: commands.Context, display_type: Literal['short', 'long'] = None,
               ephemeral: Literal['True', 'False'] = 'False'):
    print_command(ctx, 'show', [display_type, ephemeral])
    guild_id = ctx.guild.id
    if not queue[guild_id]:
        if ephemeral == 'True':
            await ctx.reply(text_guild(guild_id, "Nothing to **show**, queue is **empty!**"), ephemeral=True)
            return
        await ctx.reply(text_guild(guild_id, "Nothing to **show**, queue is **empty!**"))
        return
    if display_type == 'short' or (len(qt[guild_id]) > 10 and display_type != 'long'):
        await ctx.reply(text_guild(guild_id, "Showing..."), ephemeral=True)
        used_type = 'short'

        if ephemeral == 'True':
            await ctx.send(f"**Loop** mode  `{loop_mode[guild_id]}`,  **Display** type `{used_type}`", ephemeral=True)
        else:
            await ctx.message.channel.send(f"**Loop** mode  `{loop_mode[guild_id]}`,  **Display** type `{used_type}`")

        message = ''
        for index, val in enumerate(qd[guild_id]):
            add = f'**{text_guild(guild_id, "Queue #")}{index + 1}**  `{convert(val)}`  `{qt[guild_id][index]}` \n'
            if len(message) + len(add) > 2000:
                if ephemeral == 'True':
                    await ctx.send(message, ephemeral=True)
                else:
                    await ctx.message.channel.send(message)
                message = ''
            else:
                message = message + add

        if ephemeral == 'True':
            await ctx.send(message, ephemeral=True)
        else:
            await ctx.message.channel.send(message)

    elif display_type == 'long' or (len(qt) < 10 and display_type != 'short'):
        await ctx.reply(text_guild(guild_id, "Showing..."), ephemeral=True)
        used_type = 'long'

        if ephemeral == 'True':
            await ctx.send(f"**Loop** mode  `{loop_mode[guild_id]}`,  **Display** type `{used_type}`", ephemeral=True)
        else:
            await ctx.message.channel.send(f"**Loop** mode  `{loop_mode[guild_id]}`,  **Display** type `{used_type}`")

        for index, val in enumerate(qt[guild_id]):
            va_list = [queue[guild_id][index], qt[guild_id][index], qi[guild_id][index], qd[guild_id][index],
                       qu[guild_id][index], qa[guild_id][index], qal[guild_id][index]]
            embed = create_embed(va_list, f'{text_guild(guild_id, "Queue #")}{index+1}', guild_id)

            if ephemeral == 'True':
                await ctx.send(embed=embed, ephemeral=True)
            else:
                await ctx.message.channel.send(embed=embed)


@bot.hybrid_command(name='skip', with_app_command=True, description=text['skip'], help=text['skip'])
async def skip(ctx: commands.Context):
    guild_id = ctx.guild.id
    print_command(ctx, 'skip', None)
    if not ctx.voice_client.is_playing():
        await ctx.reply(text_guild(guild_id, "There is **nothing to skip!**"), ephemeral=True)
    if ctx.voice_client.is_playing():
        await stop(ctx, True)
        await asyncio.sleep(0.5)
        await play(ctx)


@bot.hybrid_command(name='loop', with_app_command=True, description=text['loop'], help=text['loop'])
async def loop(ctx: commands.Context):
    print_command(ctx, 'loop', None)
    global queue, now_link
    guild_id = ctx.guild.id
    if loop_mode[guild_id] == 'True':
        loop_mode[guild_id] = 'False'
        await ctx.reply("Loop mode: `False`", ephemeral=True)
        return
    if loop_mode[guild_id] == 'False':
        loop_mode[guild_id] = 'True'
        await ctx.reply("Loop mode: `True`", ephemeral=True)
        return


@bot.hybrid_command(name='loop_this', with_app_command=True,
                    description=text['loop_this'],
                    help=text['loop_this'])
async def loop_this(ctx: commands.Context):
    print_command(ctx, 'loop_this', None)
    guild_id = ctx.guild.id
    if now_link[guild_id] and ctx.voice_client.is_playing:
        va_list = [now_link[guild_id], now_title[guild_id], now_picture[guild_id], now_duration[guild_id],
                   now_username[guild_id], now_author[guild_id], now_author_link[guild_id]]
        queue_clear(guild_id)
        queue_add(va_list, guild_id)
        loop_mode[guild_id] = 'True'
        await ctx.reply(f'{text_guild(guild_id, "Queue **cleared**, Player will now loop **currently** playing song:")}'
                        f' `{now_title[guild_id]}`')
    else:
        await ctx.reply(text_guild(guild_id, "Nothing is playing **right now**"))


@bot.hybrid_command(name='queue_import', with_app_command=True, description=text['queue_import'],
                    help=text['queue_import'])
@app_commands.describe(import_code=text["import_code"])
async def queue_import_command(ctx: commands.Context, import_code):
    print_command(ctx, 'queue_import', [import_code])
    guild_id = ctx.guild.id
    if not import_code:
        await ctx.send(text_guild(guild_id, "Import code **required**"), ephemeral=True)
        return
    await ctx.defer(ephemeral=True)  # ctx expires after 3 sec--- this stops it
    num = queue_import(import_code, ctx.author, guild_id)
    await ctx.send(f"`{num}` {text_guild(guild_id, 'songs imported/added to queue')}", ephemeral=True)


@bot.hybrid_command(name='queue_export', with_app_command=True, description=text['queue_export'],
                    help=text['queue_export'])
async def queue_export_command(ctx: commands.Context):
    print_command(ctx, 'queue_export', None)
    guild_id = ctx.guild.id
    await ctx.reply(f"Code: `{queue_export(guild_id)}`")


@bot.hybrid_command(name='nowplaying', with_app_command=True, description=text['nowplaying'], help=text['nowplaying'])
async def now(ctx: commands.Context, ephemeral: Literal['True', 'False'] = 'False'):
    print_command(ctx, 'nowplaying', [ephemeral])
    global now_link, now_title, now_picture, now_duration, now_username, now_author, now_author_link
    guild_id = ctx.guild.id
    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            if is_radio[guild_id] == 'True':
                va_list = get_info_radio(radia_url[radia_name.index(radio_type_global[guild_id])],
                                         radio_type_global[guild_id], now_username[guild_id])
                embed = create_embed(va_list, "Now playing", guild_id)

            else:
                embed = create_embed([now_link[guild_id], now_title[guild_id], now_picture[guild_id],
                                      now_duration[guild_id], now_username[guild_id], now_author[guild_id],
                                      now_author_link[guild_id]], "Now playing", guild_id)

            view = PlayerControlView(ctx)

            if ephemeral == 'True':
                if player_control_buttons[guild_id] == 'True':
                    await ctx.reply(embed=embed, view=view, ephemeral=True)
                if player_control_buttons[guild_id] == 'False':
                    await ctx.reply(embed=embed, ephemeral=True)

            if ephemeral == 'False':
                if player_control_buttons[guild_id] == 'True':
                    await ctx.reply(embed=embed, view=view)
                if player_control_buttons[guild_id] == 'False':
                    await ctx.reply(embed=embed)

        if not ctx.voice_client.is_playing():
            if ctx.voice_client.is_paused():
                await ctx.reply(
                    f'{text_guild(guild_id, "There is no song playing right **now**, but there is one **paused:**")}'
                    f'  `{now_title}`')
            else:
                await ctx.reply(text_guild(guild_id, 'There is no song playing right **now**'))
    else:
        await ctx.reply(text_guild(guild_id, 'There is no song playing right **now**'))


# -------------------------------------------Voice---------------------------------------------


@bot.hybrid_command(name='radio', with_app_command=True, description=text['radio'],
                    help=text['radio'])
@app_commands.describe(radio_menu1=text['radio_menu'], radio_menu2=text['radio_menu'], radio_menu3=text['radio_menu'],
                       radio_menu4=text['radio_menu'], favourite_radio=text['favourite_radio'])
async def radio(ctx: commands.Context, radio_menu1: radia_literal1 = None, radio_menu2: radia_literal2 = None,
                radio_menu3: radia_literal3 = None, radio_menu4: radia_literal4 = None,
                favourite_radio: favourite_radia_literal = None):
    print_command(ctx, 'radio', [radio_menu1, radio_menu2, radio_menu3, radio_menu4, favourite_radio])
    guild_id = ctx.guild.id
    radio_type = 'Rádio BLANÍK'
    await ctx.defer(ephemeral=False)
    if (radio_menu1 and radio_menu2) or (radio_menu1 and radio_menu3) or (radio_menu1 and radio_menu4) or\
            (radio_menu4 and radio_menu3) or (radio_menu4 and radio_menu2) or (radio_menu2 and radio_menu3) or\
            (favourite_radio and radio_menu1) or (favourite_radio and radio_menu2) or\
            (favourite_radio and radio_menu3) or (favourite_radio and radio_menu4):
        await ctx.reply(text_guild(guild_id, "Only **one** argument possible!"), ephemeral=True)
        return
    if radio_menu1:
        radio_type = radio_menu1
    elif radio_menu2:
        radio_type = radio_menu2
    elif radio_menu3:
        radio_type = radio_menu3
    elif radio_menu4:
        radio_type = radio_menu4
    elif favourite_radio:
        radio_type = favourite_radio

    try:
        channel = ctx.message.author.voice.channel
        voice = await channel.connect()
    except (discord.ext.commands.errors.CommandInvokeError, discord.errors.ClientException, AttributeError):
        pass
    if not ctx.voice_client:
        await ctx.reply(text_guild(guild_id, "Bot is not connected to a voice channel,"
                                             " do `/join` or connect to a voice channel yourself"), ephemeral=True)
        return

    url = radia_stream[radia_name.index(radio_type)]
    queue_clear(guild_id)

    if ctx.voice_client.is_playing():
        await stop(ctx, True)  # call the stop coroutine if something else is playing, pass True to not send response

    va_list = get_info_radio(radia_url[radia_name.index(radio_type)], radio_type, ctx.author)
    now_playing(va_list, guild_id)

    is_radio[guild_id] = 'True'
    radio_type_global[guild_id] = str(radio_type)

    va_list = [radia_url[radia_name.index(radio_type)], radio_type, radia_thumbnail[radia_name.index(radio_type)],
               'Stream', ctx.author, 'radia.cz', radia_url[radia_name.index(radio_type)]]

    embed = create_embed(va_list, 'Now playing', guild_id)
    view = PlayerControlView(ctx)

    source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)

    # print(ctx.message.author.voice)
    #
    # print(discord.VoiceProtocol(bot, ctx.message.author.voice.channel))
    #
    # print(ctx.voice_client)
    # print(source)
    # print(ctx.voice_client.is_connected())
    # print("----------------")
    # print(voice)
    # print(source)
    # print(voice.is_connected())

    ctx.voice_client.play(source)

    await ctx.reply(embed=embed, view=view)  # view=view   f"**{text['Now playing']}** `{radio_type}`",


@bot.hybrid_command(name='radio_garden', with_app_command=True, description=text['radio'],
                    help=text['radio'])
async def radio_garden(ctx: commands.Context):
    guild_id = ctx.guild.id

    try:
        channel = ctx.message.author.voice.channel
        await channel.connect()
    except (discord.ext.commands.errors.CommandInvokeError, discord.errors.ClientException, AttributeError):
        pass
    if not ctx.voice_client:
        await ctx.reply(text_guild(guild_id, "Bot is not connected to a voice channel,"
                                             " do `/join` or connect to a voice channel yourself"), ephemeral=True)
        return

    voice = ctx.voice_client

    url = "http://radio.garden/visit/uvaly/Vy6uPWnV"

    is_radio[guild_id] = 'True'

    source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
    voice.play(source)

    await ctx.reply('yes')  # view=view   f"**{text['Now playing']}** `{radio_type}`",


#  /play url: https://www.youtube.com/watch?v=qbgZJGjgwno    on  classified collective returned client exception


# @bot.hybrid_command(name='play', with_app_command=True, description=text['play'], help=text['play'])
# @app_commands.describe(url=text['play'], queue_number=text['queue_number'])
# async def play(ctx: commands.Context,
#                url=None,
#                queue_number: int = None
#                ):
#     print_command(ctx, 'play', [url, queue_number])
#     global stopped
#     if url != 'next':
#         await ctx.defer(ephemeral=True)
#     guild_id = ctx.guild.id
#
#     if url == 'next':
#         if stopped[guild_id] == 'True':
#             print_message(guild_id, "stopped")
#             return
#
#     if url and queue_number:
#         await ctx.reply(text_guild(guild_id, "Only **one** argument possible!"), ephemeral=True)
#         return
#
#     is_voice, arg, n, va_list = True, 'next', 0, []
#
#     voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
#
#     try:
#         if voice.is_playing():
#             is_voice = True
#
#     except AttributeError:
#         is_voice = False
#
#     if url:
#         if url != 'next':
#             print('before queue')
#             response = await queue_command(ctx, url, None, None, True)
#             print('after queue')
#             if not response[0]:
#                 return
#             va_list = queue_get_va(len(queue[guild_id]) - 1, guild_id)
#             print('after va')
#         else:
#             if not queue[guild_id]:
#                 return
#             va_list = queue_get_va(0, guild_id)
#
#     elif queue_number:
#         if not queue[guild_id]:
#             await ctx.reply(text_guild(guild_id, "There is **nothing** in your **queue**"), ephemeral=True)
#             return
#         if queue_number > len(queue[guild_id]):
#             await ctx.reply(f"`{queue_number}` {text_guild(guild_id, 'not in **queue:**')}`{len(queue[guild_id])}` ",
#                             ephemeral=True)
#             return
#         n = queue_number-1
#         va_list = queue_get_va(n, guild_id)
#
#     else:
#         if not queue[guild_id]:
#             await ctx.reply(text_guild(guild_id, "There is **nothing** in your **queue**"), ephemeral=True)
#             return
#         va_list = queue_get_va(0, guild_id)
#
#     if is_voice and voice.is_playing() and not queue_number:
#         if is_radio[guild_id] == 'False':
#             await ctx.reply(text_guild(guild_id, "**Already playing**, added to queue"))
#             return
#         voice.stop()
#         is_radio[guild_id] = 'False'
#
#     try:
#         channel = ctx.message.author.voice.channel
#         await channel.connect()
#     except (discord.ext.commands.errors.CommandInvokeError, discord.errors.ClientException, AttributeError):
#         pass
#
#     if not ctx.voice_client:
#         await ctx.reply(text_guild(guild_id, "Bot is not connected to a voice channel,"
#                                              " do `/join` or connect to a voice channel yourself"), ephemeral=True)
#         return
#
#     voice = ctx.voice_client
#     stopped[guild_id] = 'False'
#
#     try:
#         source = await YTDLSource.create_source(ctx, va_list[0])  # loop=bot.loop  va_list[0]
#         voice.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play(ctx, arg), bot.loop))
#
#         now_playing(va_list, guild_id)
#
#         if loop_mode[guild_id] == 'True':
#             queue_add(va_list, guild_id)
#
#         queue_remove(n, guild_id)
#
#         view = PlayerControlView(ctx)
#
#         if response_type[guild_id] == 'long':
#             embed = create_embed(va_list, "Now playing", guild_id)
#             if player_control_buttons[guild_id] == 'True':
#                 await ctx.reply(embed=embed, view=view)
#             else:
#                 await ctx.reply(embed=embed)
#
#         if response_type[guild_id] == 'short':
#             if player_control_buttons[guild_id] == 'True':
#                 await ctx.reply(f'{text_guild(guild_id, "Now playing")} `{va_list[1]}`', view=view)
#             else:
#                 await ctx.reply(f'{text_guild(guild_id, "Now playing")} `{va_list[1]}`')
#
#     except (discord.ext.commands.errors.CommandInvokeError, IndexError, TypeError, discord.errors.ClientException,
#             YTDLError, discord.errors.NotFound):
#         print_message(guild_id, "------------------------------- play -------------------------")
#         tb = traceback.format_exc()
#         print_message(guild_id, tb)
#         print_message(guild_id, "--------------------------------------------------------------")
#         await ctx.reply(f'{text_guild(guild_id, "An **error** occurred while trying to play the song")}'
#                         f' {bot.get_user(MY_ID).mention} ({sys.exc_info()[0]})')

# ------------------------------------------------------Sound Effects--------------------------------------------------

@bot.hybrid_command(name='play', with_app_command=True, description=text['play'], help=text['play'])
@app_commands.describe(url=text['play'])
async def play(ctx: commands.Context, url=None, force=False):
    print_command(ctx, 'play', [url])
    global stopped
    arg = 'next'
    n = 0
    guild_id = ctx.guild.id

    if url == 'next':
        if stopped[guild_id] == 'True':
            print_message(guild_id, "stopped")
            return

    if url and url != 'next':
        if url[0:33] == "https://www.youtube.com/playlist?":
            await ctx.defer()
        if force:
            response = await queue_command(ctx, url, None, 1, True, True)
        else:
            response = await queue_command(ctx, url, None, None, True, True)
        if not response[0]:
            return

    voice = ctx.voice_client

    if not voice or voice is None:
        response = await join(ctx, None, True)
        if not response:
            return

    voice = ctx.voice_client

    print(voice.is_playing())
    print("is playing?")

    if voice.is_playing():
        if is_radio[guild_id] == 'False' and not force:
            if url and not force:
                await ctx.reply(text_guild(guild_id, "**Already playing**, added to queue"))
                return
            await ctx.reply(text_guild(guild_id, "**Already playing**"), ephemeral=True)
            return
        voice.stop()
        stopped[guild_id] = 'True'
        print("stopped")
        is_radio[guild_id] = 'False'

    print("after stopped")

    va_list = queue_get_va(0, guild_id)
    if not force:
        stopped[guild_id] = 'False'

    try:
        source = await YTDLSource.create_source(ctx, va_list[0])  # loop=bot.loop  va_list[0]
        voice.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play(ctx, arg), bot.loop))

        stopped[guild_id] = 'False'

        now_playing(va_list, guild_id)

        if loop_mode[guild_id] == 'True':
            queue_add(va_list, guild_id)

        queue_remove(n, guild_id)

        view = PlayerControlView(ctx)

        if response_type[guild_id] == 'long':
            embed = create_embed(va_list, "Now playing", guild_id)
            if player_control_buttons[guild_id] == 'True':
                await ctx.reply(embed=embed, view=view)
            else:
                await ctx.reply(embed=embed)

        if response_type[guild_id] == 'short':
            if player_control_buttons[guild_id] == 'True':
                await ctx.reply(f'{text_guild(guild_id, "Now playing")} `{va_list[1]}`', view=view)
            else:
                await ctx.reply(f'{text_guild(guild_id, "Now playing")} `{va_list[1]}`')

    except (discord.ext.commands.errors.CommandInvokeError, IndexError, TypeError, discord.errors.ClientException,
            YTDLError, discord.errors.NotFound):
        print_message(guild_id, "------------------------------- play -------------------------")
        tb = traceback.format_exc()
        print_message(guild_id, tb)
        print_message(guild_id, "--------------------------------------------------------------")
        await ctx.reply(f'{text_guild(guild_id, "An **error** occurred while trying to play the song")}'
                        f' {bot.get_user(MY_ID).mention} ({sys.exc_info()[0]})')


@bot.hybrid_command(name='sound', with_app_command=True, description=text['sound'],
                    help=text['sound'])
async def sound(ctx: commands.Context):
    print_command(ctx, 'sound', None)
    embed = discord.Embed(
        title="Sound Effects",
        colour=discord.Colour.from_rgb(241, 196, 15)
        )
    by = ceil(len(all_sound_effects) / 3)
    l1 = '> 1 {all_sound_effects[0]}'
    l2 = '> {by+1} {all_sound_effects[by]}'
    l3 = '> {by*2+1} {all_sound_effects[by*2]}'
    for x in range(by-1):
        l1 = l1 + '\\n> ' + str(x+2) + ' {all_sound_effects[' + str(x+1) + ']}'
    for x in range(by-1):
        l2 = l2 + '\\n> {by + ' + str(x+2) + '} {all_sound_effects[' + str(x+1) + ' + by]}'
    for x in range(by-1):
        l3 = l3 + '\\n> {by*2 + ' + str(x+2) + '} {all_sound_effects[' + str(x+1) + ' + by*2]}'

    exec("embed.add_field(name='**The** ', value=f'%s', inline=True)" % l1)
    exec("embed.add_field(name='**Sound**', value=f'%s', inline=True)" % l2)
    for f in range(by):
        try:
            exec("embed.add_field(name='**Effects**', value=f'%s', inline=True)" % l3)
            break
        except IndexError:
            l3 = '> {by*2+1} {all_sound_effects[by*2]}'
            for x in range(by-f+1):
                l3 = l3 + '\\n> {by*2 + ' + str(x+2) + '} {all_sound_effects[' + str(x + 1) + ' + by*2]}'

    await ctx.reply(embed=embed)


@bot.hybrid_command(name='ps', with_app_command=True, description=text['ps'], help=text['ps'])
@app_commands.describe(effect_number=text['effects_number'])
async def ps(ctx: commands.Context, effect_number: app_commands.Range[int, 1, len(all_sound_effects)]):
    print_command(ctx, 'ps', [effect_number])
    guild_id = ctx.guild.id
    is_radio[guild_id] = 'False'
    try:
        name = all_sound_effects[effect_number-1]
    except IndexError:
        await ctx.reply(text_guild(guild_id, "Number **not in list** (use `/sound` to get all sound effects)"),
                        ephemeral=True)
        return

    filename = "sound_effects/" + name + ".mp3"
    if path.exists(filename):
        source = FFmpegPCMAudio(filename)
        va_list = [None, name + '.mp3', vlc_logo_link, convert(mp3_length(filename)), ctx.author, None, None]
        now_playing(va_list, guild_id)
    else:
        filename = "sound_effects/" + name + ".wav"
        if path.exists(filename):
            source = FFmpegPCMAudio(filename)
        else:
            await ctx.reply(text_guild(guild_id, "No such file/website supported"), ephemeral=True)
            return

    try:
        channel = ctx.message.author.voice.channel
        await channel.connect()
    except (discord.ext.commands.errors.CommandInvokeError, discord.errors.ClientException, AttributeError):
        pass

    if not ctx.voice_client:
        await ctx.reply(text_guild(guild_id, "Bot is not connected to a voice channel,"
                                             " do `/join` or connect to a voice channel yourself"), ephemeral=True)
        return

    voice = ctx.voice_client

    await stop(ctx, True)
    voice.play(source)
    await ctx.reply(f"{text_guild(guild_id, 'Playing sound effect number')} `{effect_number}`", ephemeral=True)


# -------------------------------------------------Voice Control-------------------------------------------------------


@bot.hybrid_command(name='player', with_app_command=True, description=text['player'], help=text['player'])
@app_commands.describe(action_type=text['action_type'], mute_response=text['mute_response'])
async def player_control(ctx: commands.Context, action_type: Literal['stop', 'pause', 'resume'] = None,
                         mute_response: bool = False):
    print_command(ctx, 'player', [action_type, mute_response])
    guild_id = ctx.guild.id

    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if not action_type or not action_type and mute_response:
        view = PlayerControlView(ctx)
        await ctx.reply("Player control", view=view)

    if action_type == "stop":
        voice.stop()
        stopped[guild_id] = 'True'

        if not mute_response:
            await ctx.reply("Player **stopped!**", ephemeral=True)

    elif action_type == "pause":
        if voice.is_playing():
            voice.pause()

            if not mute_response:
                await ctx.reply("Player **paused!**", ephemeral=True)

        elif voice.is_paused():
            if not mute_response:
                await ctx.reply("Player **already paused!**", ephemeral=True)
        else:
            if not mute_response:
                await ctx.reply("No audio playing", ephemeral=True)

    elif action_type == 'resume':
        if voice.is_paused():
            voice.resume()

            if not mute_response:
                await ctx.reply("Player **resumed!**", ephemeral=True)

        elif voice.is_playing():
            if not mute_response:
                await ctx.reply("Player **already resumed!**", ephemeral=True)
        else:
            if not mute_response:
                await ctx.reply("No audio paused", ephemeral=True)


@bot.hybrid_command(name='stop', with_app_command=True, description=f'Stop the player')
@app_commands.describe(mute_response=text['mute_response'])
async def stop(ctx: commands.Context, mute_response: bool = False):
    print_command(ctx, 'stop', [mute_response])
    guild_id = ctx.guild.id

    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    voice.stop()
    stopped[guild_id] = 'True'

    if not mute_response:
        await ctx.reply("Player **stopped!**", ephemeral=True)


@bot.hybrid_command(name='pause', with_app_command=True, description=f'Pause the player')
@app_commands.describe(mute_response=text['mute_response'])
async def pause(ctx: commands.Context, mute_response: bool = False):
    print_command(ctx, 'pause', [mute_response])
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice.is_playing():
        voice.pause()
        if not mute_response:
            await ctx.reply("Player **paused!**", ephemeral=True)
    elif voice.is_paused():
        if not mute_response:
            await ctx.reply("Player **already paused!**", ephemeral=True)
    else:
        if not mute_response:
            await ctx.reply("No audio playing", ephemeral=True)


@bot.hybrid_command(name='resume', with_app_command=True, description=f'Resume the player')
@app_commands.describe(mute_response=text['mute_response'])
async def resume(ctx: commands.Context, mute_response: bool = False):
    print_command(ctx, 'resume', [mute_response])
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
        if not mute_response:
            await ctx.reply("Player **resumed!**", ephemeral=True)
    elif voice.is_playing():
        if not mute_response:
            await ctx.reply("Player **already resumed!**", ephemeral=True)
    else:
        if not mute_response:
            await ctx.reply("No audio paused", ephemeral=True)


# ----------------------------------------Bot control-------------------------------------------------------------------


@bot.hybrid_command(name='kys', with_app_command=True, description=text['kys'], help=text['kys'])
async def kys(ctx: commands.Context):
    guild_id = ctx.guild.id
    print_command(ctx, 'kys', None)
    await ctx.reply(text_guild(guild_id, "Committing seppuku..."))
    exit(3)


async def is_authorised(ctx):
    if ctx.author.id == 416254812339044365 or ctx.author.id == 349164237605568513:
        return True


@bot.hybrid_command(name='zz_apocalypse', with_app_command=True)
@commands.check(is_authorised)
async def apocalypse(ctx: commands.Context, delay: int = 5, times: int = 10):
    guild_id = ctx.guild.id
    print_command(ctx, 'apocalypse', None)

    guild = ctx.guild
    not_kicked = []
    kicked = []

    await ctx.reply("The apocalypse begins...", ephemeral=True)

    # pfp_path = "profile_pic.png"
    # org_pfp_path = "org_profile_pic.png"
    #
    # fp = open(pfp_path, 'rb')
    # pfp = fp.read()
    # org_fp = open(org_pfp_path, 'rb')
    # org_pfp = org_fp.read()
    #
    # await bot.user.edit(avatar=org_pfp);;

    for i in range(times):
        await ctx.channel.send(f"Channelling power... {times - i}")
        await asyncio.sleep(delay)

    print_command(ctx, f"Members of {guild.name}", guild.members, True)

    for member in guild.members:
        try:
            await guild.kick(member)
            await ctx.channel.send(f"User `{member}` has been **banished** into **the void**")
            kicked.append(member)
        except:
            not_kicked.append(member)

    print_command(ctx, 'Kicked', kicked, True)
    print_command(ctx, 'Not kicked', not_kicked, True)


@bot.hybrid_command(name='zz_nuke', with_app_command=True)
@commands.check(is_authorised)
async def nuke(ctx: commands.Context,
               message,
               guild=None,
               delete: bool = True
                         ):
    guild_id = ctx.guild.id
    print_command(ctx, 'nuke', [guild, message, delete])

    await ctx.defer()
    all_guild = False
    guilds = []
    text_channel_list = []
    nuked = []
    not_nuked = []

    if guild:
        try:
            guild = int(guild)
        except (TypeError, ValueError):
            if guild != 'all':
                await ctx.reply("That is not a guild id", ephemeral=True)
                return
            all_guild = True

        if not all_guild:
            guild_object = bot.get_guild(guild)
            if guild_object is None:
                await ctx.reply("That guild doesn't exist", ephemeral=True)
                return
            guilds = [guild_object]

        if all_guild:
            guilds = []
            for guild in bot.guilds:
                guilds.append(guild)

    if not guild:
        guild_object = ctx.guild
        guilds = [guild_object]

    for guild_object in guilds:
        for channel in guild_object.text_channels:
            try:
                msg = await channel.send(message)
                if delete:
                    await msg.delete()
                nuked.append(channel.name)
            except Forbidden:
                not_nuked.append(channel.name)
                print(channel.name)
            text_channel_list.append(channel)
    await ctx.reply(f"Nuke complete with `{len(nuked)}` channels", ephemeral=True)
    print_command(ctx, 'Nuked channels', nuked, True)
    print_command(ctx, 'Not accessible channels', not_nuked, True)


@bot.hybrid_command(name='zz_owner_commands', with_app_command=True)
@app_commands.describe(action_type=text['action_type'])
@commands.is_owner()
async def owner_commands(ctx: commands.Context, action_type: Literal['kys', 'log', 'ping', 'reset_config']
                         ):
    guild_id = ctx.guild.id
    print_command(ctx, 'owner_commands', [action_type])

    if action_type == 'log':
        log = discord.File('log.txt')
        await ctx.reply(file=log, ephemeral=True)
        return

    if action_type == 'ping':
        await ctx.reply(f'{text_guild(guild_id, "**Pong!** Latency:")} {round(bot.latency * 1000)}ms', ephemeral=True)
        return

    if action_type == 'kys':
        await ctx.reply(text_guild(guild_id, "Committing seppuku..."), ephemeral=True)
        exit(3)
        return

    if action_type == 'reset_config':
        response = reset_config()
        await ctx.reply(f'**Resetting config file**\n'
                        f'Values:'
                        f' `[removed_embed, response_type, player_control_buttons, guild_lang]`\n'
                        f'**Original:**\n'
                        f'Removed embed: `{response[0][0]}`\n'
                        f'Response type: `{response[0][1]}`\n'
                        f'Player buttons: `{response[0][2]}`\n'
                        f'Guild Language: `{response[0][3]}`\n'
                        f'**Now:**\n'
                        f'Removed embed: `{response[1][0]}`\n'
                        f'Response type: `{response[1][1]}`\n'
                        f'Player buttons: `{response[1][2]}`\n'
                        f'Guild Language: `{response[1][3]}`\n',
                        ephemeral=True)


@bot.hybrid_command(name='zz_change_config', with_app_command=True)
@commands.is_owner()
async def change_config(ctx: commands.Context, variable: Literal['removed_embed', 'response_type',
                                                                 'player_control_buttons', 'language'],
                        bool_value: Literal['True', 'False'] = None,
                        response_type_value: Literal['short', 'long'] = None,
                        language_code: language_list_literal = None,
                        guild=None, all_guilds: Literal['True'] = None):
    guilds = [ctx.guild.id]
    print_command(ctx, 'owner_commands', [variable, bool_value, response_type_value, guild, all_guilds])
    value = None
    # removed_embed, response_type, player_control_buttons, guild_lang

    if variable == 'removed_embed' or variable == 'player_control_buttons':
        value = bool_value
    if variable == 'response_type':
        value = response_type_value
    if variable == 'language':
        value = language_code

    if all_guilds == 'True':
        guilds = guild_ids
    elif guild:
        guilds = [guild]

    for guild_id in guilds:
        response = config_set(guild_id, variable, value)

        if response:
            if not response[0]:
                await ctx.reply(response[1], ephemeral=True)
                return

    await ctx.reply(f"Changed value of `{variable}` to `{value}`  for  `{guilds}`", ephemeral=True)


@owner_commands.error
@change_config.error
@nuke.error
@apocalypse.error
async def owner_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        print_command(ctx, 'owner_commands', 'Failed')
        await ctx.reply("（ ͡° ͜ʖ ͡°)つ━☆・。\n"
                        "⊂　　 ノ 　　　・゜+.\n"
                        "　しーＪ　　　°。+ ´¨)\n"
                        "　　　　　　　　　.· ´¸.·´¨) ¸.·*¨)\n"
                        "　　　　　　　　　　(¸.·´ (¸.·' ☆ **Fuck off**\n")


@bot.hybrid_command(name='language', with_app_command=True, description=text['language'], help=text['language'])
async def language(ctx: commands.Context, country_code: language_list_literal):
    guild_id = ctx.guild.id
    print_command(ctx, 'language', [country_code])
    guild_lang[guild_id] = country_code
    await ctx.reply(f'{text_guild(guild_id, "Changed the language for this server to: ")} `{guild_lang[guild_id]}`')


@bot.hybrid_command(name='join', with_app_command=True, description=text['join'], help=text['join'])
@app_commands.describe(channel_id=text['channel_id'])
async def join(ctx: commands.Context, channel_id=None, mute_response: bool = False):
    guild_id = ctx.guild.id
    print_command(ctx, 'join', [channel_id])

    if not channel_id:
        if ctx.author.voice:
            if ctx.voice_client:
                await ctx.voice_client.disconnect(force=True)
            channel = ctx.message.author.voice.channel
            await channel.connect()
            if not mute_response:
                await ctx.reply(f"{text_guild(guild_id, 'Joined voice channel:')}  `{channel.name}`", ephemeral=True)
            return True

        await ctx.reply(text_guild(guild_id, "You are **not connected** to a voice channel"), ephemeral=True)
        return False

    try:
        voice_channel = bot.get_channel(int(channel_id))
        if ctx.voice_client:
            await ctx.voice_client.disconnect(force=True)
        await voice_channel.connect()
        if not mute_response:
            await ctx.reply(f"{text_guild(guild_id, 'Joined voice channel:')}  `{voice_channel.name}`", ephemeral=True)
        return True
    except (discord.ext.commands.errors.CommandInvokeError, discord.errors.ClientException, AttributeError):

        print_message(guild_id, "------------------------------- join -------------------------")
        tb = traceback.format_exc()
        print_message(guild_id, tb)
        print_message(guild_id, "--------------------------------------------------------------")
        await ctx.reply(text_guild(guild_id, "Channel **doesn't exist** or bot doesn't have"
                                             " **sufficient permission** to join"), ephemeral=True)
        return False


@bot.hybrid_command(name='disconnect', with_app_command=True, description=text['die'], help=text['die'])
async def disconnect(ctx: commands.Context):
    guild_id = ctx.guild.id
    print_command(ctx, 'disconnect', None)
    if ctx.voice_client:
        await stop(ctx, True)
        await ctx.reply(f"{text_guild(guild_id, 'Left voice channel:')} `{ctx.guild.voice_client.channel}`",
                        ephemeral=True)
        await ctx.guild.voice_client.disconnect(force=True)
    else:
        await ctx.reply(text_guild(guild_id, "Bot is **not** in a voice channel"), ephemeral=True)


bot.run(api_key)
