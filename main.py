import random

import discord
import asyncio
from discord import FFmpegPCMAudio, app_commands
from discord.ext import commands
from discord.ui import View

import yt_dlp
import youtubesearchpython
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import json

from os import path, listdir
from mutagen.mp3 import MP3
import sys
from typing import Literal
import traceback
import datetime

from api_keys import api_key_testing as api_key

import functools



# ---------------- Bot class ------------


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=prefix, intents=intents)
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            print_message('no guild', "Trying to sync commands")
            await self.tree.sync()
            print_message('no guild', f"Synced slash commands for {self.user}")
        await bot.change_presence(activity=discord.Game(name=f"/help"))
        print_message('no guild', 'Logged in as:\n{0.user.name}\n{0.user.id}'.format(bot))

    async def on_guild_join(self, guild_object):
        guild[guild_object.id] = Guild(guild_object.id)
        print_message(guild_object.id, f"Joined guild {guild_object.name} with {guild_object.member_count} members and {len(guild_object.voice_channels)} voice channels")
        save_json()
        text_channels = guild_object.text_channels
        sys_channel = guild_object.system_channel
        if sys_channel is not None:
            if sys_channel.permissions_for(guild_object.me).send_messages:
                await sys_channel.send(f"Hello **`{guild_object.name}`**! I am `{self.user.display_name}`. Thank you for inviting me.\n\nTo see what commands I have available type `/help`.", delete_after=60)
                return
        else:
            await text_channels[0].send(f"Hello **`{guild_object.name}`**! I am `{self.user.display_name}`. Thank you for inviting me.\n\nTo see what commands I have available type `/help`.", delete_after=60)


    async def on_voice_state_update(self, member, before, after):
        voice_state = member.guild.voice_client
        if voice_state is not None and len(voice_state.channel.members) == 1:
            after.channel.guild.voice_client.stop()
            await voice_state.disconnect()
            print_message(member.guild.id, "Disconnecting when last person left")
        if not member.id == self.user.id:
            return
        elif before.channel is None:
            voice = after.channel.guild.voice_client
            time = 0
            while True:
                await asyncio.sleep(1)
                time +=  1
                if voice.is_playing() and not voice.is_paused():
                    time = 0
                if time >= guild[member.guild.id].options.buffer:  # how many seconds of inactivity to disconnect | 300 = 5min | 600 = 10min
                    guild[member.guild.id].options.stopped = True
                    voice.stop()
                    await voice.disconnect()
                    print_message(member.guild.id, f"Disconnecting after {guild[member.guild.id].options.buffer} seconds of nothing playing")
                if not voice.is_connected():
                    break

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            print_command(ctx, 'Permission Fail', ctx.command)
            await ctx.reply("（ ͡° ͜ʖ ͡°)つ━☆・。\n"
                            "⊂　　 ノ 　　　・゜+.\n"
                            "　しーＪ　　　°。+ ´¨)\n"
                            "　　　　　　　　　.· ´¸.·´¨) ¸.·*¨)\n"
                            "　　　　　　　　　　(¸.·´ (¸.·' ☆ **Fuck off**\n"
                            "*You don't have permission to use this command*")
        else:
            print_message(ctx.guild.id, f"{error}")
            await ctx.reply(f"{error}   {bot.get_user(my_id).mention}", ephemeral=True)


# ---------------- Data Classes ------------

class ContextImitation:
    def __init__(self, guild_object, guild_id, author, interaction):
        self.guild = guild_object
        self.guild.id = guild_id
        self.author = author
        self.message = MessageImitation(author, interaction)
        self.interaction = interaction

    def defer(self):
        self.interaction.response.defer()
        return asyncio.sleep(0)

    def send(self, *args, **kwargs):
        return self.interaction.response.send_message(*args, **kwargs)

    def reply(self, *args, **kwargs):
        return self.interaction.response.send_message(*args, **kwargs)


class MessageImitation:
    def __init__(self, author, interaction):
        self.author = author
        self.channel = ChannelImitation(interaction)

class ChannelImitation:
    def __init__(self, interaction):
        self.id = interaction.channel_id
        self.interaction = interaction

    def send(self, *args, **kwargs):
        return self.interaction.response.send_message(*args, **kwargs)


class Options:
    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.stopped = False
        self.loop = False
        self.is_radio = False
        self.language = 'cs'
        self.response_type = 'short'  # long or short
        self.search_query = 'Never gonna give you up'
        self.buttons = False
        self.volume = 1.0
        self.buffer = 600 # how many seconds of nothing before it disconnects | 600 = 10min


class Video:
    def __init__(self, url, author, title=None, picture=None, duration=None, channel_name=None, channel_link=None):
        self.url = url
        self.author = author

        video = None

        if title is None and picture is None and duration is None and channel_name is None and channel_link is None:
            try:
                video = youtubesearchpython.Video.getInfo(url)  # mode=ResultMode.json
            except Exception as e:
                raise ValueError(f"Not a youtube link: {e}")


        self.title = title
        self.picture = picture
        self.duration = duration
        self.channel_name = channel_name
        self.channel_link = channel_link


        if video:
            self.title = video['title']
            self.picture = 'https://img.youtube.com/vi/' + video['id'] + '/default.jpg'
            self.duration = video['duration']['secondsText']
            self.channel_name = video['channel']['name']
            self.channel_link = video['channel']['link']

    def renew(self):
        pass


class Radio:
    def __init__(self, name, author):
        self.author = author
        self.url = radio_dict[name]['url']

        self.picture = radio_dict[name]['thumbnail']
        self.channel_name = radio_dict[name]['type']
        self.channel_link = self.url
        self.title = name
        self.duration = 'Stream'
        self.radio_website = radio_dict[name]['type']

    def renew(self):
        if self.radio_website == 'radia_cz':
            html = urlopen(self.url).read()
            soup = BeautifulSoup(html, features="lxml")
            data1 = soup.find('div', attrs={'class': 'interpret-image'})
            data2 = soup.find('div', attrs={'class': 'interpret-info'})

            self.picture = data1.find('img')['src']
            self.channel_name = data2.find('div', attrs={'class': 'nazev'}).text.lstrip().rstrip()
            self.title = data2.find('div', attrs={'class': 'song'}).text.lstrip().rstrip()
            self.duration = 'Stream'
        if self.radio_website == 'actve':
            r = requests.get(self.url).json()
            self.picture = r['coverBase']
            self.channel_name = r['artist']
            self.title = r['title']
            self.duration = 'Stream'


class LocalFile:
    def __init__(self, title, duration, author):
        self.url = None
        self.author = author
        self.title = title
        self.picture = vlc_logo
        self.duration = duration
        self.channel_name = 'Local file'
        self.channel_link = 'Local file'

    def renew(self):
        pass


class FromProbe:
    def __init__(self, url, title, duration, author, channel_name, channel_link):
        self.url = url
        self.author = author
        self.title = title
        self.picture = vlc_logo
        self.duration = duration
        self.channel_name = channel_name
        self.channel_link = channel_link

    def renew(self):
        pass


class Guild:
    def __init__(self, guild_id):
        self.options = Options(guild_id)
        self.queue = []
        self.search_list = []
        self.now_playing = Video(url='https://www.youtube.com/watch?v=dQw4w9WgXcQ', author=bot.get_user(my_id))


# ------------ PRINT --------------------

def print_command(ctx, text_data, opt, text_only=False):
    now_time = datetime.datetime.now()
    message = f"{now_time.strftime('%d/%m/%y %X')} -{ctx.guild.id}- {text_data}: {opt}"

    if not text_only:
        message = f"{now_time.strftime('%d/%m/%y %X')} -{ctx.guild.id}- Command ({text_data}) was requested by" \
                  f" ({ctx.message.author}) -- (options: {opt})"
        if text_data == 'queue_add':
            if opt[3]:
                message = f"{now_time.strftime('%d/%m/%y %X')} -{ctx.guild.id}- Muted ({text_data}) was requested by" \
                          f" ({ctx.message.author}) -- (options: {opt})"

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

# ---------------------------------------------- GUILD TO JSON ---------------------------------------------------------

def video_to_json(video):
    try:
        author = video.author.id
    except AttributeError:
        author = my_id

    video_dict = {'url': video.url,
                  'author': author,
                  'title': video.title,
                  'picture': video.picture,
                  'duration': video.duration,
                  'channel_name': video.channel_name,
                  'channel_link': video.channel_link}
    return video_dict


def guild_to_json(guild_object):
    guild_dict = {}
    search_dict = {}
    queue_dict = {}
    if guild_object.search_list:
        for index, video in enumerate(guild_object.search_list):
            search_dict[index] = video_to_json(video)

    if guild_object.queue:
        for index, video in enumerate(guild_object.queue):
            queue_dict[index] = video_to_json(video)

    guild_dict['options'] = guild_object.options.__dict__
    guild_dict['queue'] = queue_dict
    guild_dict['search_list'] = search_dict
    guild_dict['now_playing'] = video_to_json(guild_object.now_playing)

    return guild_dict


def guilds_to_json(guild_dict):
    guilds_dict = {}
    for guild_id, guilds_object in guild_dict.items():
        guilds_dict[int(guild_id)] = guild_to_json(guilds_object)
    return guilds_dict

# ---------------------------------------------- JSON TO GUILD ---------------------------------------------------------

def json_to_video(video_dict):
    try:
        author = bot.get_user(video_dict['author'])
    except AttributeError:
        author = bot.get_user(bot_id)

    video = Video(url=video_dict['url'],
                  author=author,
                  title=video_dict['title'],
                  picture=video_dict['picture'],
                  duration=video_dict['duration'],
                  channel_name=video_dict['channel_name'],
                  channel_link=video_dict['channel_link'])
    return video


def json_to_guild(guild_dict):
    guild_object = Guild(guild_dict['options']['guild_id'])
    guild_object.options = Options(guild_dict['options']['guild_id'])
    guild_object.options.__dict__ = guild_dict['options']
    guild_object.queue = [json_to_video(video_dict) for video_dict in guild_dict['queue'].values()]
    guild_object.search_list = [json_to_video(video_dict) for video_dict in guild_dict['search_list'].values()]
    guild_object.now_playing = json_to_video(guild_dict['now_playing'])

    return guild_object


def json_to_guilds(guilds_dict):
    guilds_object = {}
    for guild_id, guild_dict in guilds_dict.items():
        guilds_object[int(guild_id)] = json_to_guild(guild_dict)

    return guilds_object

# ---------------------------------------------- LOAD -------------------------------------------------------------

print_message('no guild', "--------------------------------------- NEW / REBOOTED ----------------------------------------")

print_message('no guild', 'Loading radio.json ...')
with open('src/radio.json', 'r') as file:
    radio_dict = json.load(file)

print_message('no guild', 'Loading languages.json ...')
with open('src/languages.json', 'r') as file:
    languages_dict = json.load(file)
    text = languages_dict['en']

print_message('no guild', 'Loading other.json ...')
with open('src/other.json', 'r') as file:
    other = json.load(file)
    react_dict = other['reactions']
    prefix = other['prefix']
    my_id = other['my_id']
    bot_id = other['bot_id']
    vlc_logo = other['logo']
    authorized_users = other['authorized']


# ---------------------------------------------- BOT --------------------------------------------------------

bot = Bot()

# -----------------------------------------------------------------------------------------------------------


print_message('no guild', 'Loading guilds.json ...')
with open('src/guilds.json', 'r') as file:
    guild = json_to_guilds(json.load(file))

# print_message('no guild', 'Building new guilds.json ...')
#
# with open('src/guilds.json', 'r') as file:
#     jf = json.load(file)
#
# guild = dict(zip(jf.keys(), [Guild(int(guild)) for guild in jf.keys()]))
# with open('src/guilds.json', 'w') as f:
#     f.write(json.dumps(guilds_to_json(guild), indent=4))
#
# exit(1)

print_message('no guild', 'Loading sound_effects folder ...')
try:
    all_sound_effects = listdir('sound_effects')
    for file_index, file_val in enumerate(all_sound_effects):
        all_sound_effects[file_index] = all_sound_effects[file_index][:len(file_val) - 4]
except FileNotFoundError:
    all_sound_effects = ["No sound effects found"]


# ---------------------------------------------- SAVE JSON -------------------------------------------------------------

def save_json():
    with open('src/guilds.json', 'w') as f:
        json.dump(guilds_to_json(guild), f, indent=4)
    print_message(guild_id='all', content='Updated guilds.json')

# ---------------------------------------------- TEXT ----------------------------------------------------------

def tg(guild_id, content):
    lang = guild[guild_id].options.language
    return languages_dict[lang][content]

# --------- video_info / url --------

def get_pure_url(url):
    url = url[:url.index('&list=')]
    return url


def get_playlist_from_url(url):
    try:
        code = url[url.index('&list=')+1:url.index('&index=')]
    except ValueError:
        code = url[url.index('&list=')+1:]
    playlist_url = 'https://www.youtube.com/playlist?' + code
    return playlist_url

# -------------- convert / get -----------

def mp3_length(path_of_mp3):
    audio = MP3(path_of_mp3)
    length = audio.info.length
    return length


def convert_duration(duration):
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

# ---------------EMBED--------------

def create_embed(video, name, guild_id):
    #  (link, title, picture, duration, user, author, author_link)
    #  (  0    1       2         3        4    5          6      )
    embed = (discord.Embed(title=name,
                           description=f'```\n{video.title}\n```',
                           color=discord.Color.blurple()))
    if name == tg(guild_id, "Now playing"):
        guild[guild_id].now_playing = video
    embed.add_field(name=tg(guild_id, 'Duration'), value=convert_duration(video.duration))
    try:
        embed.add_field(name=tg(guild_id, 'Requested by'), value=video.author.mention)
    except AttributeError:
        embed.add_field(name=tg(guild_id, 'Requested by'), value=video.author)
    embed.add_field(name=tg(guild_id, 'Author'), value=f'[{video.channel_name}]({video.channel_link})')
    embed.add_field(name=tg(guild_id, 'URL'), value=f'[{video.url}]({video.url})')
    embed.set_thumbnail(url=video.picture)

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

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict):
        super().__init__(source, guild[ctx.guild.id].options.volume)

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
                await interaction.response.send_message(tg(self.guild_id, "Player **already resumed!**"),
                                                        ephemeral=True)
            else:
                await interaction.response.send_message(tg(self.guild_id, "No audio playing"), ephemeral=True)
        else:
            await interaction.response.send_message(tg(self.guild_id, "No audio"), ephemeral=True)

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
                await interaction.response.send_message(tg(self.guild_id, "Player **already paused!**"),
                                                        ephemeral=True)
            else:
                await interaction.response.send_message(tg(self.guild_id, "No audio playing"), ephemeral=True)
        else:
            await interaction.response.send_message(tg(self.guild_id, "No audio"), ephemeral=True)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['stop'], style=discord.ButtonStyle.red, custom_id='stop')
    async def stop_callback(self, interaction, button):
        voice = discord.utils.get(bot.voice_clients, guild=self.guild)
        if voice:
            if voice.is_playing() or voice.is_paused():
                voice.stop()
                guild[interaction.guild_id].options.stopped = True
                await interaction.response.edit_message(view=None)
            else:
                await interaction.response.send_message(tg(self.guild_id, "No audio playing"), ephemeral=True)
        else:
            await interaction.response.send_message(tg(self.guild_id, "No audio"), ephemeral=True)


class SearchOptionView(View):

    def __init__(self, ctx, force=False):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.guild = ctx.guild
        self.guild_id = ctx.guild.id
        self.force = force

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['1'], style=discord.ButtonStyle.blurple, custom_id='1')
    async def callback_1(self, interaction, button):
        video = guild[self.guild_id].search_list[0]
        if self.force:
            guild[self.guild_id].queue.insert(0, video)
        else:
            guild[self.guild_id].queue.append(video)
        await interaction.response.edit_message(content=f'[`{video.title}`](<{video.url}>) '
                                                        f'{tg(self.guild_id, "added to queue!")}', view=None)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['2'], style=discord.ButtonStyle.blurple, custom_id='2')
    async def callback_2(self, interaction, button):
        video = guild[self.guild_id].search_list[1]
        if self.force:
            guild[self.guild_id].queue.insert(0, video)
        else:
            guild[self.guild_id].queue.append(video)
        await interaction.response.edit_message(content=f'[`{video.title}`](<{video.url}>) '
                                                        f'{tg(self.guild_id, "added to queue!")}', view=None)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['3'], style=discord.ButtonStyle.blurple, custom_id='3')
    async def callback_3(self, interaction, button):
        video = guild[self.guild_id].search_list[2]
        if self.force:
            guild[self.guild_id].queue.insert(0, video)
        else:
            guild[self.guild_id].queue.append(video)
        await interaction.response.edit_message(content=f'[`{video.title}`](<{video.url}>) '
                                                        f'{tg(self.guild_id, "added to queue!")}', view=None)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['4'], style=discord.ButtonStyle.blurple, custom_id='4')
    async def callback_4(self, interaction, button):
        video = guild[self.guild_id].search_list[3]
        if self.force:
            guild[self.guild_id].queue.insert(0, video)
        else:
            guild[self.guild_id].queue.append(video)
        await interaction.response.edit_message(content=f'[`{video.title}`](<{video.url}>) '
                                                        f'{tg(self.guild_id, "added to queue!")}', view=None)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['5'], style=discord.ButtonStyle.blurple, custom_id='5')
    async def callback_5(self, interaction, button):
        video = guild[self.guild_id].search_list[4]
        if self.force:
            guild[self.guild_id].queue.insert(0, video)
        else:
            guild[self.guild_id].queue.append(video)
        await interaction.response.edit_message(content=f'[`{video.title}`](<{video.url}>) '
                                                        f'{tg(self.guild_id, "added to queue!")}', view=None)

    # # noinspection PyUnusedLocal
    # @discord.ui.button(emoji=react_dict['false'], style=discord.ButtonStyle.red, custom_id='6')
    # async def callback_6(self, interaction, button):
    #     await interaction.response.edit_message(content=f'{tg(self.guild_id, "Nothing selected")}', view=None)


class PlaylistOptionView(View):

    def __init__(self, ctx, url, force=False):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.url = url
        self.guild = ctx.guild
        self.guild_id = ctx.guild.id
        self.force = force

    # noinspection PyUnusedLocal
    @discord.ui.button(label='Yes', style=discord.ButtonStyle.blurple)
    async def callback_1(self, interaction, button):
        playlist_url = get_playlist_from_url(self.url)
        await interaction.response.edit_message(content=tg(self.guild_id, "Adding playlist to queue..."), view=None)
        if self.force:
            response = await queue_command(self.ctx, playlist_url, 0, True, self.force)
        else:
            response = await queue_command(self.ctx, playlist_url, None, True, self.force)

        msg = await interaction.original_response()
        await msg.edit(content=response[1])

    # noinspection PyUnusedLocal
    @discord.ui.button(label='No, just this', style=discord.ButtonStyle.blurple)
    async def callback_2(self, interaction, button):
        pure_url = get_pure_url(self.url)
        if self.force:
            response = await queue_command(self.ctx, pure_url, 0, True, self.force)
        else:
            response = await queue_command(self.ctx, pure_url, None, True, self.force)
        await interaction.response.edit_message(content=response[1], view=None)
        await play(self.ctx)


# --------------------------------------- QUEUE --------------------------------------------------


@bot.hybrid_command(name='queue', with_app_command=True, description=text['queue_add'], help=text['queue_add'])
@app_commands.describe(url=text['url'], position=text['pos'], mute_response=text['mute_response'], force=text['force'])
async def queue_command(ctx: commands.Context,
                        url=None,
                        position: int = None,
                        mute_response: bool = None,
                        force: bool = False
                        ):
    print_command(ctx, 'queue', [url, position, mute_response])
    guild_id = ctx.guild.id
    author = ctx.author

    if not url:
        message = tg(guild_id, "`url` is **required**")
        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return [False, message]


    elif url[0:33] == "https://www.youtube.com/playlist?":
        try:
            # noinspection PyUnresolvedReferences
            if not ctx.interaction.response.is_done():
                await ctx.defer()

            playlist_videos = youtubesearchpython.Playlist.getVideos(url)
        except KeyError:
            print_message(guild_id, "------------------------------- playlist -------------------------")
            tb = traceback.format_exc()
            print_message(guild_id, tb)
            print_message(guild_id, "--------------------------------------------------------------")

            message = f'This playlist is unviewable: `{url}`'

            if not mute_response:
                await ctx.reply(message)

            return [False, message]
        playlist_songs = 0

        playlist_videos = playlist_videos['videos']
        if position or position == 0:
            playlist_videos = list(reversed(playlist_videos))

        for index, val in enumerate(playlist_videos):
            playlist_songs += 1

            # noinspection PyTypeChecker
            url = f"https://www.youtube.com/watch?v={playlist_videos[index]['id']}"
            video = Video(url, author)

            if position or position == 0: guild[guild_id].queue.insert(position, video)
            else: guild[guild_id].queue.append(video)

        message = f"`{playlist_songs}` {tg(guild_id, 'songs from playlist added to queue!')}"
        if not mute_response:
            await ctx.reply(message)

        save_json()

        return [True, message, None]

    elif url:
        if 'index=' in url or 'list=' in url:
            view = PlaylistOptionView(ctx, url, force)

            message = tg(guild_id,
                                 'This video is from a **playlist**, do you want to add the playlist to **queue?**')
            await ctx.reply(message, view=view)
            return [False, message]
        try:

            video = Video(url, author)

            if position or position == 0: guild[guild_id].queue.insert(position, video)
            else: guild[guild_id].queue.append(video)

            message = f'[`{video.title}`](<{video.url}>) {tg(guild_id, "added to queue!")}'

            if not mute_response:
                await ctx.reply(message)

            save_json()

            return [True, message, video]

        except (ValueError, IndexError, TypeError):
            try:
                url_only_id = 'https://www.youtube.com/watch?v=' + url.split('watch?v=')[1]
                video = Video(url_only_id, author)

                if position or position == 0: guild[guild_id].queue.insert(position, video)
                else: guild[guild_id].queue.append(video)

                message = f'[`{video.title}`](<{video.url}>) {tg(guild_id, "added to queue!")}'

                if not mute_response:
                    await ctx.reply(message)

                save_json()

                return [True, message, video]

            except (ValueError, IndexError, TypeError):
                try:
                    # https://www.youtube.com/shorts/JRPKE_A9yjw
                    url_shorts = url.replace('shorts/', 'watch?v=')
                    video = Video(url_shorts, author)

                    if position or position == 0: guild[guild_id].queue.insert(position, video)
                    else: guild[guild_id].queue.append(video)

                    message = f'[`{video.title}`](<{video.url}>) {tg(guild_id, "added to queue!")}'

                    if not mute_response:
                        await ctx.reply(message)

                    save_json()

                    return [True, message, video]

                except (ValueError, IndexError, TypeError):

                    await search_command(ctx, url, 'short', force)

                    message = f'[`{url}`](<{url}>) {tg(guild_id, "is not supported!")}'

                    # await ctx.reply(message, ephemeral=True)

                    save_json()

                    return [False, message]


@bot.hybrid_command(name='next_up', with_app_command=True, description=text['next_up'], help=text['next_up'])
@app_commands.describe(url=text['url'], ephemeral=text['ephemeral'])
async def next_up(ctx: commands.Context,
                 url=None,
                 ephemeral: bool = False
                 ):
    print_command(ctx, 'next', [ephemeral])
    response = await queue_command(ctx, url, 0, True, True)

    if response[0]:

        if ctx.voice_client:
            if not ctx.voice_client.is_playing():
                await play(ctx)
                return
        else:
            await play(ctx)
            return

        await ctx.reply(response[1], ephemeral=ephemeral)

    else:
        return

    save_json()


@bot.hybrid_command(name='skip', with_app_command=True, description=text['skip'], help=text['skip'])
async def skip(ctx: commands.Context):
    guild_id = ctx.guild.id
    print_command(ctx, 'skip', None)
    if not ctx.voice_client.is_playing():
        await ctx.reply(tg(guild_id, "There is **nothing to skip!**"), ephemeral=True)
    if ctx.voice_client.is_playing():
        await stop(ctx, True)
        await asyncio.sleep(0.5)
        await play(ctx)


@bot.hybrid_command(name='remove', with_app_command=True, description=text['queue_remove'], help=text['queue_remove'])
@app_commands.describe(number=text['number'], display_type=text['display_type'], ephemeral=text['ephemeral'])
async def remove(ctx: commands.Context,
                 number: int,
                 display_type: Literal['short', 'long'] = None,
                 ephemeral: bool = False
                 ):
    print_command(ctx, 'remove', [number, display_type, ephemeral])
    guild_id = ctx.guild.id

    if not display_type:
        display_type = guild[guild_id].options.response_type

    if number:
        if number > len(guild[guild_id].queue):
            if not guild[guild_id].queue:
                await ctx.reply(tg(guild_id, "Nothing to **remove**, queue is **empty!**"), ephemeral=True)
                return
            await ctx.reply(tg(guild_id, "Index out of range!"), ephemeral=True)
            return

        video = guild[guild_id].queue[number]

        if display_type == 'long':
            embed = create_embed(video, f'{tg(guild_id, "REMOVED #")}{number}', guild_id)
            await ctx.reply(embed=embed, ephemeral=ephemeral)
        if display_type == 'short':
            await ctx.reply(f'REMOVED #{number} : [`{video.title}`](<{video.url}>)', ephemeral=ephemeral)

        guild[guild_id].queue.pop(number)

    save_json()


@bot.hybrid_command(name='clear', with_app_command=True, description=text['clear'], help=text['clear'])
@app_commands.describe(ephemeral=text['ephemeral'])
async def clear(ctx: commands.Context,
                 ephemeral: bool = False
                 ):
    print_command(ctx, 'clear', [ephemeral])
    guild_id = ctx.guild.id
    guild[guild_id].queue.clear()
    await ctx.reply(tg(guild_id, 'Removed **all** songs from queue'), ephemeral=ephemeral)
    return


@bot.hybrid_command(name='shuffle', with_app_command=True, description=text['shuffle'], help=text['shuffle'])
@app_commands.describe(ephemeral=text['ephemeral'])
async def shuffle(ctx: commands.Context,
                 ephemeral: bool = False
                 ):
    print_command(ctx, 'shuffle', [ephemeral])
    guild_id = ctx.guild.id
    random.shuffle(guild[guild_id].queue)
    await ctx.reply(tg(guild_id, 'Songs in queue shuffled'), ephemeral=ephemeral)
    return


@bot.hybrid_command(name='show', with_app_command=True, description=text['queue_show'], help=text['queue_show'])
@app_commands.describe(display_type=text['display_type'], ephemeral=text['ephemeral'])
async def show(ctx: commands.Context,
               display_type: Literal['short', 'medium', 'long'] = None,
               ephemeral: bool = False
               ):
    print_command(ctx, 'show', [display_type, ephemeral])
    guild_id = ctx.guild.id
    max_embed = 5
    if not guild[guild_id].queue:
        await ctx.reply(tg(guild_id, "Nothing to **show**, queue is **empty!**"), ephemeral=ephemeral)
        return

    if not display_type:
        if len(guild[guild_id].queue) <= max_embed:
            display_type = 'long'
        else:
            display_type = 'medium'

    if display_type == 'long':
        await ctx.send(f"**THE QUEUE**\n **Loop** mode  `{guild[guild_id].options.loop}`,  **Display** type `{display_type}`", ephemeral=ephemeral, mention_author=False)

        for index, val in enumerate(guild[guild_id].queue):
            embed = create_embed(val, f'{tg(guild_id, "Queue #")}{index}', guild_id)

            await ctx.send(embed=embed, ephemeral=ephemeral, mention_author=False)


    if display_type == 'medium':
        embed = discord.Embed(title="Song Queue", description=f'Loop: {guild[guild_id].options.loop} | Display type: {display_type}', color=0x00ff00)

        message = ''
        for index, val in enumerate(guild[guild_id].queue):
            add = f'**{index}** --> `{convert_duration(val.duration)}`  [{val.title}](<{val.url}>) \n'

            if len(message) + len(add) > 1023:
                embed.add_field(name="", value=message, inline=False)
                message = ''
            else:
                message = message + add

        embed.add_field(name="", value=message, inline=False)

        if len(embed) < 6000:
            await ctx.reply(embed=embed, ephemeral=ephemeral, mention_author=False)
        else:
            await ctx.reply("HTTPException(discord 6000 character limit) >> using display type `short`", ephemeral=ephemeral, mention_author=False)
            display_type = 'short'


    if display_type == 'short':
        send = f"**THE QUEUE**\n **Loop** mode  `{guild[guild_id].options.loop}`,  **Display** type `{display_type}`"
        # noinspection PyUnresolvedReferences
        if ctx.interaction.response.is_done(): await ctx.send(send, ephemeral=ephemeral, mention_author=False)
        else: await ctx.reply(send, ephemeral=ephemeral, mention_author=False)

        message = ''
        for index, val in enumerate(guild[guild_id].queue):
            add = f'**{tg(guild_id, "Queue #")}{index}**  `{convert_duration(val.duration)}`  [`{val.title}`](<{val.url}>) \n'
            if len(message) + len(add) > 2000:
                if ephemeral:
                    await ctx.send(message, ephemeral=ephemeral, mention_author=False)
                else:
                    await ctx.message.channel.send(content=message, mention_author=False)
                message = ''
            else:
                message = message + add

        if ephemeral:
            await ctx.send(message, ephemeral=ephemeral, mention_author=False)
        else:
            await ctx.message.channel.send(content=message, mention_author=False)

    save_json()


@bot.hybrid_command(name='search', with_app_command=True, description=text['search'],  help=text['search'])
@app_commands.describe(search_query=text['search_query'], display_type=text['display_type'], force=text['force'])
async def search_command(ctx: commands.Context,
                         search_query,
                         display_type: Literal['short', 'long'] = None,
                         force: bool = False,
                         ):
    print_command(ctx, 'search', [search_query, display_type, force])
    # noinspection PyUnresolvedReferences
    if not ctx.interaction.response.is_done():
        await ctx.defer()
    guild_id = ctx.guild.id

    guild[guild_id].options.search_query = search_query

    if display_type is None:
        display_type = guild[guild_id].options.response_type

    message = ''

    if display_type == 'long':
        await ctx.reply(tg(guild_id, 'Searching...'), ephemeral=True)

    custom_search = youtubesearchpython.VideosSearch(search_query, limit=5)
    guild[guild_id].search_list.clear()

    view = SearchOptionView(ctx, force)

    if not custom_search.result()['result']:
        await ctx.reply(tg(guild_id, 'No results found!'))
        return

    for i in range(5):
        # noinspection PyTypeChecker
        url = custom_search.result()['result'][i]['link']
        video = Video(url, ctx.author)
        guild[guild_id].search_list.append(video)

        if display_type == 'long':
            embed = create_embed(video, f'{tg(guild_id, "Result #")}{i + 1}', guild_id)
            await ctx.message.channel.send(embed=embed)
        if display_type == 'short':
            message += f'{tg(guild_id, "Result #")}{i+1} : [`{video.title}`](<{video.url}>)\n'
    if display_type == 'short':
        await ctx.reply(message, view=view)

    save_json()


# --------------------------------------- PLAYER --------------------------------------------------


@bot.hybrid_command(name='play', with_app_command=True, description=text['play'], help=text['play'])
@app_commands.describe(url=text['play'], force=text['force'])
async def play(ctx: commands.Context,
               url=None,
               force=False
               ):
    print_command(ctx, 'play', [url])
    arg = 'next'
    response = []
    guild_id = ctx.guild.id

    if url == 'next':
        if guild[guild_id].options.stopped:
            print_message(guild_id, "stopped")
            return

    voice = ctx.voice_client

    if not voice or voice is None:
        # noinspection PyUnresolvedReferences
        if not ctx.interaction.response.is_done():
            await ctx.defer()
        response = await join(ctx, None, True)
        if not response:
            return


    if url and url != 'next':
        if force:
            response = await queue_command(ctx, url=url, position=0, mute_response=True, force=force)
        else:
            response = await queue_command(ctx, url=url, position=None, mute_response=True, force=force)
        if not response[0]:
            return

    voice = ctx.voice_client

    if voice.is_playing():
        if not guild[guild_id].options.is_radio and not force:
            if url and not force:
                if response:
                    await ctx.reply(f'{tg(guild_id, "**Already playing**, added to queue")}: [`{response[2].title}`](<{response[2].url}>)')
                    return
                else:
                    await ctx.reply(f'{tg(guild_id, "**Already playing**, added to queue")}')
                    return
            await ctx.reply(tg(guild_id, "**Already playing**"), ephemeral=True)
            return
        voice.stop()
        guild[guild_id].options.stopped = True
        guild[guild_id].options.is_radio = False

    if not guild[guild_id].queue:
        if url != 'next':
            await ctx.reply(tg(guild_id, "There is **nothing** in your **queue**"))
        return

    video = guild[guild_id].queue[0]
    if not force:
        guild[guild_id].options.stopped = False

    try:
        source = await YTDLSource.create_source(ctx, video.url)  # loop=bot.loop  va_list[0]
        voice.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play(ctx, arg), bot.loop))

        guild[guild_id].options.stopped = False

        guild[guild_id].now_playing = video

        if guild[guild_id].options.loop:
            guild[guild_id].queue.append(video)

        guild[guild_id].queue.pop(0)

        view = PlayerControlView(ctx)

        if guild[guild_id].options.response_type == 'long':
            embed = create_embed(video, "Now playing", guild_id)
            if guild[guild_id].options.buttons:
                await ctx.reply(embed=embed, view=view)
            else:
                await ctx.reply(embed=embed)

        if guild[guild_id].options.response_type == 'short':
            if guild[guild_id].options.buttons:
                await ctx.reply(f'{tg(guild_id, "Now playing")} [`{video.title}`](<{video.url}>)', view=view)
            else:
                await ctx.reply(f'{tg(guild_id, "Now playing")} [`{video.title}`](<{video.url}>)')

        await volume_command(ctx, guild[guild_id].options.volume*100, False, True)

        save_json()

    except (discord.ext.commands.errors.CommandInvokeError, IndexError, TypeError, discord.errors.ClientException,
            YTDLError, discord.errors.NotFound):
        print_message(guild_id, "------------------------------- play -------------------------")
        tb = traceback.format_exc()
        print_message(guild_id, tb)
        print_message(guild_id, "--------------------------------------------------------------")
        await ctx.reply(f'{tg(guild_id, "An **error** occurred while trying to play the song")}'
                        f' {bot.get_user(my_id).mention} ({sys.exc_info()[0]})')


@bot.hybrid_command(name='radio', with_app_command=True, description=text['radio'], help=text['radio'])
@app_commands.describe(favourite_radio=text['favourite_radio'], radio_code=text['radio_code'])
async def radio(ctx: commands.Context,
                favourite_radio: Literal['Rádio BLANÍK','Rádio BLANÍK CZ','Evropa 2','Fajn Radio','Hitrádio PopRock','Český rozhlas Pardubice','Radio Beat','Country Radio','Radio Kiss','Český rozhlas Vltava','Hitrádio Černá Hora'] = None,
                radio_code: int = None,
                ):
    print_command(ctx, 'radio', [favourite_radio, radio_code])
    guild_id = ctx.guild.id
    radio_type = 'Rádio BLANÍK'
    await ctx.defer(ephemeral=False)
    if favourite_radio and radio_code:
        await ctx.reply(tg(guild_id, "Only **one** argument possible!"), ephemeral=True)
        return

    if favourite_radio:
        radio_type = favourite_radio
    elif radio_code:
        radio_type = list(radio_dict.keys())[radio_code]

    if not ctx.voice_client:
        response = await join(ctx, None, True)
        if not response:
            return

    url = radio_dict[radio_type]['stream']
    guild[guild_id].queue.clear()

    if ctx.voice_client.is_playing():
        await stop(ctx, True)  # call the stop coroutine if something else is playing, pass True to not send response

    radio_class = Radio(radio_type, ctx.author)
    guild[guild_id].now_playing = radio_class

    guild[guild_id].options.is_radio = True

    embed = create_embed(radio_class, 'Now playing', guild_id)

    source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)

    ctx.voice_client.play(source)

    await volume_command(ctx, guild[guild_id].options.volume*100, False, True)

    if guild[guild_id].options.buttons:
        view = PlayerControlView(ctx)
        await ctx.reply(embed=embed, view=view)
    else:
        await ctx.reply(embed=embed)  # view=view   f"**{text['Now playing']}** `{radio_type}`",

    save_json()


@bot.hybrid_command(name='ps', with_app_command=True, description=text['ps'], help=text['ps'])
@app_commands.describe(effect_number=text['effects_number'], mute_response=text['mute_response'])
async def ps(ctx: commands.Context,
             effect_number: app_commands.Range[int, 1, len(all_sound_effects)],
             mute_response: bool = False
             ):
    print_command(ctx, 'ps', [effect_number])
    guild_id = ctx.guild.id
    guild[guild_id].options.is_radio = False
    try:
        name = all_sound_effects[effect_number]
    except IndexError:
        if not mute_response:
            await ctx.reply(tg(guild_id, "Number **not in list** (use `/sound` to get all sound effects)"), ephemeral=True)
        return False

    filename = "sound_effects/" + name + ".mp3"
    if path.exists(filename):
        source = FFmpegPCMAudio(filename)
        video = LocalFile(name, convert_duration(mp3_length(filename)), ctx.author)
        guild[guild_id].now_playing = video
    else:
        filename = "sound_effects/" + name + ".wav"
        if path.exists(filename):
            source = FFmpegPCMAudio(filename)

        else:
            if not mute_response:
                await ctx.reply(tg(guild_id, "No such file/website supported"), ephemeral=True)
            return False

    if not ctx.voice_client:
        await join(ctx, None, True)

    voice = ctx.voice_client

    await stop(ctx, True)
    voice.play(source)
    await volume_command(ctx, guild[guild_id].options.volume*100, False, True)
    if not mute_response:
        await ctx.reply(f"{tg(guild_id, 'Playing sound effect number')} `{effect_number}`", ephemeral=True)

    save_json()

    return True


@bot.hybrid_command(name='nowplaying', with_app_command=True, description=text['nowplaying'], help=text['nowplaying'])
@app_commands.describe(ephemeral=text['ephemeral'])
async def now(ctx: commands.Context,
              ephemeral: bool = False
              ):
    print_command(ctx, 'nowplaying', [ephemeral])
    guild_id = ctx.guild.id
    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            guild[guild_id].now_playing.renew()
            embed = create_embed(guild[guild_id].now_playing, "Now playing", guild_id)

            view = PlayerControlView(ctx)

            if guild[guild_id].options.buttons:
                await ctx.reply(embed=embed, view=view, ephemeral=ephemeral)
            else:
                await ctx.reply(embed=embed, ephemeral=ephemeral)

        if not ctx.voice_client.is_playing():
            if ctx.voice_client.is_paused():
                await ctx.reply(
                    f'{tg(guild_id, "There is no song playing right **now**, but there is one **paused:**")}'
                    f'  [`{guild[guild_id].now_playing.title}`](<{guild[guild_id].now_playing.url}>)', ephemeral=ephemeral)
            else:
                await ctx.reply(tg(guild_id, 'There is no song playing right **now**'), ephemeral=ephemeral)
    else:
        await ctx.reply(tg(guild_id, 'There is no song playing right **now**'), ephemeral=ephemeral)

    save_json()


@bot.hybrid_command(name='last', with_app_command=True, description=text['last'], help=text['last'])
@app_commands.describe(ephemeral=text['ephemeral'])
async def last(ctx: commands.Context,
              ephemeral: bool = False
              ):
    print_command(ctx, 'last', [ephemeral])
    guild_id = ctx.guild.id
    guild[guild_id].now_playing.renew()
    embed = create_embed(guild[guild_id].now_playing, "Last played", guild_id)

    view = PlayerControlView(ctx)

    if guild[guild_id].options.buttons:
        await ctx.reply(embed=embed, view=view, ephemeral=ephemeral)
    else:
        await ctx.reply(embed=embed, ephemeral=ephemeral)

    save_json()

@bot.hybrid_command(name='loop', with_app_command=True, description=text['loop'], help=text['loop'])
async def loop_command(ctx: commands.Context):
    print_command(ctx, 'loop', None)
    guild_id = ctx.guild.id
    if guild[guild_id].options.loop:
        guild[guild_id].options.loop = False
        await ctx.reply("Loop mode: `False`", ephemeral=True)
        return
    if not guild[guild_id].options.loop:
        guild[guild_id].options.loop = True
        await ctx.reply("Loop mode: `True`", ephemeral=True)
        return


@bot.hybrid_command(name='loop_this', with_app_command=True, description=text['loop_this'], help=text['loop_this'])
async def loop_this(ctx: commands.Context):
    print_command(ctx, 'loop_this', None)
    guild_id = ctx.guild.id
    if guild[guild_id].now_playing and ctx.voice_client.is_playing:
        guild[guild_id].queue.clear()
        guild[guild_id].queue.append(guild[guild_id].now_playing)
        guild[guild_id].options.loop = True
        await ctx.reply(f'{tg(guild_id, "Queue **cleared**, Player will now loop **currently** playing song:")}'
                        f' [`{guild[guild_id].now_playing.title}`](<{guild[guild_id].now_playing.url}>)')
    else:
        await ctx.reply(tg(guild_id, "Nothing is playing **right now**"))


# --------------------------------------- VOICE --------------------------------------------------


@bot.hybrid_command(name='stop', with_app_command=True, description=f'Stop the player')
@app_commands.describe(mute_response=text['mute_response'])
async def stop(ctx: commands.Context,
               mute_response: bool = False
               ):
    print_command(ctx, 'stop', [mute_response])
    guild_id = ctx.guild.id

    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        voice.stop()
    else:
        if not mute_response:
            await ctx.reply(tg(guild_id, "Bot is not connected to a voice channel"), ephemeral=True)
            return
    guild[guild_id].options.stopped = True
    guild[guild_id].options.loop = False

    if not mute_response:
        await ctx.reply("Player **stopped!**", ephemeral=True)

    save_json()


@bot.hybrid_command(name='pause', with_app_command=True, description=f'Pause the player')
@app_commands.describe(mute_response=text['mute_response'])
async def pause(ctx: commands.Context,
                mute_response: bool = False
                ):
    print_command(ctx, 'pause', [mute_response])
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice:
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
    else:
        if not mute_response:
            await ctx.reply(tg(ctx.guild.id, "Bot is not connected to a voice channel"), ephemeral=True)

    save_json()


@bot.hybrid_command(name='resume', with_app_command=True, description=f'Resume the player')
@app_commands.describe(mute_response=text['mute_response'])
async def resume(ctx: commands.Context,
                 mute_response: bool = False
                 ):
    print_command(ctx, 'resume', [mute_response])
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
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
    else:
        if not mute_response:
            await ctx.reply(tg(ctx.guild.id, "Bot is not connected to a voice channel"), ephemeral=True)

    save_json()


@bot.hybrid_command(name='join', with_app_command=True, description=text['join'], help=text['join'])
@app_commands.describe(channel_id=text['channel_id'], mute_response=text['mute_response'])
async def join(ctx: commands.Context,
               channel_id=None,
               mute_response: bool = False
               ):
    guild_id = ctx.guild.id
    print_command(ctx, 'join', [channel_id])

    if not channel_id:
        if ctx.author.voice:
            channel = ctx.message.author.voice.channel
            if ctx.voice_client:
                if ctx.voice_client.channel != channel:
                    await ctx.voice_client.disconnect(force=True)

                else:
                    if not mute_response:
                        await ctx.reply(tg(guild_id, "I'm already in this channel"), ephemeral=True)
                    return True
            await channel.connect()
            await ctx.guild.change_voice_state(channel=channel, self_deaf=True)
            if not mute_response:
                await ctx.reply(f"{tg(guild_id, 'Joined voice channel:')}  `{channel.name}`", ephemeral=True)
            return True

        await ctx.reply(tg(guild_id, "You are **not connected** to a voice channel"), ephemeral=True)
        return False

    try:
        voice_channel = bot.get_channel(int(channel_id))
        if ctx.voice_client:
            await ctx.voice_client.disconnect(force=True)
        await voice_channel.connect()
        await ctx.guild.change_voice_state(channel=voice_channel, self_deaf=True)
        if not mute_response:
            await ctx.reply(f"{tg(guild_id, 'Joined voice channel:')}  `{voice_channel.name}`", ephemeral=True)
        return True
    except (discord.ext.commands.errors.CommandInvokeError, discord.errors.ClientException, AttributeError):

        print_message(guild_id, "------------------------------- join -------------------------")
        tb = traceback.format_exc()
        print_message(guild_id, tb)
        print_message(guild_id, "--------------------------------------------------------------")
        await ctx.reply(tg(guild_id, "Channel **doesn't exist** or bot doesn't have"
                                             " **sufficient permission** to join"), ephemeral=True)
        return False


@bot.hybrid_command(name='disconnect', with_app_command=True, description=text['die'], help=text['die'])
async def disconnect(ctx: commands.Context):
    guild_id = ctx.guild.id
    print_command(ctx, 'disconnect', None)
    if ctx.voice_client:
        await stop(ctx, True)
        await ctx.reply(f"{tg(guild_id, 'Left voice channel:')} `{ctx.guild.voice_client.channel}`",
                        ephemeral=True, mention_author=False)
        await ctx.guild.voice_client.disconnect(force=True)
    else:
        await ctx.reply(tg(guild_id, "Bot is **not** in a voice channel"), ephemeral=True, mention_author=False)

    save_json()


@bot.hybrid_command(name='volume', with_app_command=True, description=text['volume'], help=text['volume'])
@app_commands.describe(volume=text['volume'], ephemeral=text['ephemeral'], mute_response=text['mute_response'])
async def volume_command(ctx: commands.Context,
                         volume = None,
                         ephemeral: bool = False,
                         mute_response: bool = False
                         ):
    print_command(ctx, 'volume', [volume, ephemeral, mute_response])
    guild_id = ctx.guild.id

    if volume:
        new_volume = int(volume) / 100

        guild[guild_id].options.volume = new_volume
        voice = ctx.voice_client
        if voice:
            try:
                if voice.source:
                    voice.source.volume = new_volume
                    voice.source = discord.PCMVolumeTransformer(voice.source, volume=new_volume)
            except AttributeError:
                pass

        if not mute_response:
            await ctx.reply(f'{tg(guild_id, "Changed the volume for this server to:")} `{guild[guild_id].options.volume*100}%`', ephemeral=ephemeral)
    else:
        if not mute_response:
            await ctx.reply(f'{tg(guild_id, "The volume for this server is:")} `{guild[guild_id].options.volume*100}%`', ephemeral=ephemeral)

    save_json()


# --------------------------------------- MENU --------------------------------------------------


@bot.tree.context_menu(name='Add to queue')
async def add_to_queue(inter, message: discord.Message):
    ctx = ContextImitation(inter.guild, inter.guild_id, inter.user, inter)
    print_command(ctx, 'add_to_queue', [message.content])
    response = await queue_command(ctx, message.content, None, True)
    if not inter.response.is_done():
        await inter.response.send_message(content=response[1], ephemeral=True)


@bot.tree.context_menu(name='Show Profile')
async def show_profile(inter, member: discord.Member):
    ctx = ContextImitation(inter.guild, inter.guild_id, inter.user, inter)
    print_command(ctx, 'show_profile', [member])
    embed = discord.Embed(title=f"{member.name}#{member.discriminator}", description=f"ID: `{member.id}` | Name: `{member.display_name}` | Nickname: `{member.nick}`")
    embed.add_field(name="Created at", value=member.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
    embed.add_field(name="Joined at", value=member.joined_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)

    embed.add_field(name="Roles", value=", ".join([role.mention for role in member.roles[1:]]), inline=False)

    embed.add_field(name='Top Role', value=f'{member.top_role.mention}', inline=True)

    # noinspection PyUnresolvedReferences
    embed.add_field(name='Badges', value=', '.join([badge.name for badge in member.public_flags.all()]), inline=False)

    embed.add_field(name='Avatar', value=f'[Default Avatar]({member.avatar}) | [Display Avatar]({member.display_avatar})', inline=False)

    embed.add_field(name='Activity', value=f'`{member.activity}`', inline=False)

    embed.add_field(name='Activities', value=f'`{member.activities}`', inline=True)
    embed.add_field(name='Status', value=f'`{member.status}`', inline=True)
    embed.add_field(name='Web Status', value=f'`{member.web_status}`', inline=True)

    embed.add_field(name='Raw Status', value=f'`{member.raw_status}`', inline=True)
    embed.add_field(name='Desktop Status', value=f'`{member.desktop_status}`', inline=True)
    embed.add_field(name='Mobile Status', value=f'`{member.mobile_status}`', inline=True)

    embed.add_field(name='Voice', value=f'`{member.voice}`', inline=False)

    embed.add_field(name='Premium Since', value=f'`{member.premium_since}`', inline=False)

    embed.add_field(name='Accent Color', value=f'`{member.accent_color}`', inline=True)
    embed.add_field(name='Color', value=f'`{member.color}`', inline=True)
    embed.add_field(name='Banner', value=f'`{member.banner}`', inline=True)

    embed.add_field(name='System', value=f'`{member.system}`', inline=True)
    embed.add_field(name='Pending', value=f'`{member.pending}`', inline=True)
    embed.add_field(name='Bot', value=f'`{member.bot}`', inline=True)


    embed.set_thumbnail(url=member.avatar)
    await inter.response.send_message(embed=embed, ephemeral=True)


# --------------------------------------- GENERAL --------------------------------------------------


@bot.hybrid_command(name='ping', with_app_command=True, description=text['ping'], help=text['ping'])
async def ping(ctx: commands.Context):
    print_command(ctx, 'ping', None)
    await ctx.reply(f'**Pong!** Latency: {round(bot.latency * 1000)}ms')
    save_json()


# noinspection PyTypeHints
@bot.hybrid_command(name='language', with_app_command=True, description=text['language'], help=text['language'])
@app_commands.describe(country_code=text['country_code'])
async def language_command(ctx: commands.Context,
                   country_code: Literal[tuple(languages_dict.keys())]
                   ):
    guild_id = ctx.guild.id
    print_command(ctx, 'language', [country_code])
    guild[guild_id].options.language = country_code
    await ctx.reply(f'{tg(guild_id, "Changed the language for this server to: ")} `{guild[guild_id].options.language}`')
    save_json()


@bot.hybrid_command(name='sound_effects', with_app_command=True, description=text['sound'], help=text['sound'])
@app_commands.describe(ephemeral=text['ephemeral'])
async def sound_effects(ctx: commands.Context,
                ephemeral: bool = True
                ):
    print_command(ctx, 'sound', [ephemeral])
    embed = discord.Embed(title="Sound Effects", colour=discord.Colour.from_rgb(241, 196, 15))
    message = ''
    for index, val in enumerate(all_sound_effects):
        add = f'**{index}** --> {val}\n'

        if len(message) + len(add) > 1023:
            embed.add_field(name="", value=message, inline=False)
            message = ''
        else:
            message = message + add

    embed.add_field(name="", value=message, inline=False)

    await ctx.send(embed=embed, ephemeral=ephemeral)


@bot.hybrid_command(name='list_radios', with_app_command=True, description=text['list_radios'], help=text['list_radios'])
@app_commands.describe(ephemeral=text['ephemeral'])
async def list_radios(ctx: commands.Context,
                      ephemeral: bool = True
                      ):
    print_command(ctx, 'list_radios', [ephemeral])
    embed = discord.Embed(title="Radio List")
    message = ''
    for index, (name, val) in enumerate(radio_dict.items()):
        add = f'**{index}** --> {name}\n'

        if len(message) + len(add) > 1023:
            embed.add_field(name="", value=message, inline=False)
            message = ''
        else:
            message = message + add

    embed.add_field(name="", value=message, inline=False)

    await ctx.send(embed=embed, ephemeral=ephemeral)


# ---------------------------------------- ADMIN --------------------------------------------------


async def is_authorised(ctx):
    if ctx.author.id in authorized_users or ctx.author.id == 349164237605568513:
        return True


@bot.hybrid_command(name='admin_announce', with_app_command=True)
@commands.check(is_authorised)
async def announce_command(ctx: commands.Context,
                      message
                      ):
    print_command(ctx, 'announce', [message])
    for guild_object in bot.guilds:
        await guild_object.system_channel.send(message)

    await ctx.reply(f'Announced message to all servers: `{message}`')


@bot.hybrid_command(name='admin_rape_play', with_app_command=True)
@commands.check(is_authorised)
async def rape_play_command(ctx: commands.Context,
                      effect_number: int = None,
                      channel_id = None,
                      ):
    print_command(ctx, 'rape_play', [effect_number, channel_id])

    if not effect_number and effect_number != 0:
        effect_number = 1

    if not channel_id:
        response = await join(ctx, None, True)
        if response:
            pass
        else:
            await ctx.reply(f'You need to be in a voice channel to use this command', ephemeral=True)
            return
    else:
        response = await join(ctx, channel_id, True)
        if response:
            pass
        else:
            await ctx.reply(f'An error occurred when connecting to the voice channel', ephemeral=True)
            return

    await ps(ctx, effect_number, True)
    await ear_rape_command(ctx)

    await ctx.reply(f'Playing effect `{effect_number}` with ear rape in `{channel_id if channel_id else "user channel"}` >>> effect can only be turned off by `/disconnect`', ephemeral=True)


@bot.hybrid_command(name='admin_rape', with_app_command=True)
@commands.check(is_authorised)
async def ear_rape_command(ctx: commands.Context):
    print_command(ctx, 'rape', None)
    guild_id = ctx.guild.id
    times = 10
    new_volume = 10000000000000

    guild[guild_id].options.volume = 1.0

    voice = ctx.voice_client
    if voice:
        try:
            if voice.source:
                for i in range(times):
                    voice.source.volume = new_volume
                    voice.source = discord.PCMVolumeTransformer(voice.source, volume=new_volume)
        except AttributeError:
            pass

        await ctx.reply(f'Haha get ear raped >>> effect can only be turned off by `/disconnect`', ephemeral=True)
    else:
        await ctx.reply(f'Ear Rape can only be activated if the bot is in a voice channel', ephemeral=True)

    save_json()


@bot.hybrid_command(name='admin_kys', with_app_command=True)
@commands.check(is_authorised)
async def kys(ctx: commands.Context):
    guild_id = ctx.guild.id
    print_command(ctx, 'kys', None)
    await ctx.reply(tg(guild_id, "Committing seppuku..."))
    exit(3)


# @bot.hybrid_command(name='zz_nuke', with_app_command=True)
# @commands.check(is_authorised)
# async def nuke(ctx: commands.Context,
#                message,
#                guild=None,
#                delete: bool = True
#                ):
#     # guild_id = ctx.guild.id
#     print_command(ctx, 'nuke', [guild, message, delete])
#
#     await ctx.defer()
#     all_guild = False
#     guilds = []
#     text_channel_list = []
#     nuked = []
#     not_nuked = []
#
#     if guild:
#         try:
#             guild = int(guild)
#         except (TypeError, ValueError):
#             if guild != 'all':
#                 await ctx.reply("That is not a guild id", ephemeral=True)
#                 return
#             all_guild = True
#
#         if not all_guild:
#             guild_object = bot.get_guild(guild)
#             if guild_object is None:
#                 await ctx.reply("That guild doesn't exist", ephemeral=True)
#                 return
#             guilds = [guild_object]
#
#         if all_guild:
#             guilds = []
#             for guild in bot.guilds:
#                 guilds.append(guild)
#
#     if not guild:
#         guild_object = ctx.guild
#         guilds = [guild_object]
#
#     for guild_object in guilds:
#         for channel in guild_object.text_channels:
#             try:
#                 msg = await channel.send(message)
#                 if delete:
#                     await msg.delete()
#                 nuked.append(channel.name)
#             except Forbidden:
#                 not_nuked.append(channel.name)
#                 print(channel.name)
#             text_channel_list.append(channel)
#     await ctx.reply(f"Nuke complete with `{len(nuked)}` channels", ephemeral=True)
#     print_command(ctx, 'Nuked channels', nuked, True)
#     print_command(ctx, 'Not accessible channels', not_nuked, True)

@bot.hybrid_command(name='admin_config', with_app_command=True)
@commands.check(is_authorised)
async def config_command(ctx: commands.Context,
                         config_file: discord.Attachment,
                         config_type:  Literal['guilds', 'other', 'radio', 'languages'] = 'guilds',
                         ):
    print_command(ctx, 'config', [config_file, config_type])

    if config_file.filename != f'{config_type}.json':
        await ctx.reply(f'You need to upload a `{config_type}.json` file', ephemeral=True)
        return

    content = config_file.read()

    with open(f'src/{config_type}.json', 'wb') as f:
        f.write(content)

    if config_type == 'guilds':
        print_message('no guild', 'Loading guilds.json ...')
        with open('src/guilds.json', 'r') as f:
            globals()['guild'] = json_to_guilds(json.load(f))

        await ctx.reply("Loaded new `guilds.json`", ephemeral=True)
    else:
        await ctx.reply(f"Saved new `{config_type}.json`", ephemeral=True)


@bot.hybrid_command(name='admin_log', with_app_command=True)
@commands.check(is_authorised)
async def log_command(ctx: commands.Context,
                      log_type: Literal['log.txt', 'guilds.json', 'other.json', 'radio.json', 'languages.json'] = 'log.txt'
                      ):
    print_command(ctx, 'log', [log_type])
    save_json()
    if log_type == 'other.json':
        file_to_send = discord.File('src/other.json')
    elif log_type == 'radio.json':
        file_to_send = discord.File('src/radio.json')
    elif log_type == 'languages.json':
        file_to_send = discord.File('src/languages.json')
    elif log_type == 'guilds.json':
        file_to_send = discord.File('src/guilds.json')
    else:
        file_to_send = discord.File('log.txt')
    await ctx.reply(file=file_to_send, ephemeral=True)


# noinspection PyTypeHints
@bot.hybrid_command(name='admin_change_config', with_app_command=True)
@app_commands.describe(server='all, this, {guild_id}', volume='No division', buffer='In seconds', language='Language code', response_type='short, long', buttons='True, False', is_radio='True, False', loop='True, False', stopped='True, False')
@commands.check(is_authorised)
async def change_config(ctx: commands.Context,
                        stopped: bool = None,
                        loop: bool = None,
                        is_radio: bool = None,
                        buttons: bool = None,
                        language: Literal[tuple(languages_dict.keys())] = None,
                        response_type: Literal['short', 'long'] = None,
                        buffer: int = None,
                        volume = None,
                        server = None,
                        ):
    print_command(ctx, 'owner_commands', [stopped, loop, is_radio, buttons, language, response_type, volume, server])
    guild_id = ctx.guild.id

    save_json()

    guilds = []

    if not server:
        server = 'this'

    if server == 'all':
        for guild_id, guild_class in guild:
            guilds.append(guild_id)
    elif server == 'this':
        guilds.append(ctx.guild.id)
    else:
        try:
            if int(server) in bot.guilds:
                guilds.append(int(server))
            else:
                await ctx.reply(tg(guild_id, "That guild doesn't exist or the bot is not in it"), ephemeral=True)
                return
        except (ValueError, TypeError):
            await ctx.reply(tg(guild_id, "That is not a **guild id!**"), ephemeral=True)
            return

    for guild_id in guilds:
        if stopped:
            guild[guild_id].options.stopped = stopped
        if loop:
            guild[guild_id].options.loop = loop
        if is_radio:
            guild[guild_id].options.is_radio = is_radio
        if buttons:
            guild[guild_id].options.buttons = buttons
        if language:
            guild[guild_id].options.language = language
        if response_type:
            guild[guild_id].options.response_type = response_type
        if volume:
            guild[guild_id].options.volume = volume
        if buffer:
            guild[guild_id].options.buffer = buffer

        config = f'`stopped={guild[guild_id].options.stopped}`, `loop={guild[guild_id].options.loop}`,' \
                 f' `is_radio={guild[guild_id].options.is_radio}`, `buttons={guild[guild_id].options.buttons}`,' \
                 f' `language={guild[guild_id].options.language}`, `response_type={guild[guild_id].options.response_type}`,' \
                 f' `volume={guild[guild_id].options.volume}`, `buffer={guild[guild_id].options.buffer}`'

        save_json()

        await ctx.reply(f'**Config for guild `{guild_id}`**\n {config}', ephemeral=True)


@bot.hybrid_command(name='admin_probe', with_app_command=True)
@commands.check(is_authorised)
async def probe_command(ctx: commands.Context,
                        url = None,
                        ephemeral: bool = False
                        ):
    print_command(ctx, 'probe', [url])
    guild_id = ctx.guild.id
    if url is None:
        await ctx.reply("Please provide a url", ephemeral=ephemeral)
        return

    codec, bitrate = await discord.FFmpegOpusAudio.probe(url)
    if codec is None and bitrate is None:
        await ctx.reply(f"`{url}` does not have `bitrate` and `codec` properties", ephemeral=ephemeral)
        return

    try:
        if not ctx.voice_client:
            response = await join(ctx, None, True)
            if not response:
                return

        if ctx.voice_client.is_playing():
            await stop(ctx, True)

        guild[guild_id].now_playing = FromProbe(url=url, author=ctx.author, title='URL Probe', duration=0, channel_link=url, channel_name='URL Probe')

        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)

        ctx.voice_client.play(source)

        await volume_command(ctx, guild[guild_id].options.volume * 100, False, True)

        await ctx.reply(f'{tg(guild_id, "Now playing")}: [`{url}`](<{url}>)', ephemeral=ephemeral)
    except Exception as e:
        await ctx.reply(f'Error: {e}', ephemeral=ephemeral)

    save_json()


bot.remove_command('help')
@bot.hybrid_command(name='help', with_app_command=True, description='Shows all available commands', help='Shows all available commands')
async def help_command(ctx: commands.Context,
               command: Literal['language', 'sound_effects', 'list_radios', 'play', 'radio', 'ps', 'skip', 'nowplaying', 'last', 'loop', 'loop_this', 'queue', 'next_up', 'remove', 'clear', 'shuffle', 'show', 'search', 'stop', 'pause', 'resume', 'join', 'disconnect', 'volume'] = None
               ):
    print_command(ctx, 'help', [command])
    gi = ctx.guild.id

    embed = discord.Embed(title="Help", description=f"Use `/help <command>` to get help on a command | Prefix: `{prefix}`")
    embed.add_field(name="General", value=f"`/help` - {tg(gi, 'help')}\n"
                                          f"`/ping` - {tg(gi, 'ping')}\n"
                                          f"`/language` - {tg(gi, 'language')}\n"
                                          f"`/sound_ effects` - {tg(gi, 'sound')}\n"
                                          f"`/list_radios` - {tg(gi, 'list_radios')}\n"
                    , inline=False)
    embed.add_field(name="Player", value=f"`/play` - {tg(gi, 'play')}\n"
                                         f"`/radio` - {tg(gi, 'radio')}\n"
                                         f"`/ps` - {tg(gi, 'ps')}\n"
                                         f"`/player` - {tg(gi, 'player')}\n"
                                         f"`/skip` - {tg(gi, 'skip')}\n"
                                         f"`/nowplaying` - {tg(gi, 'nowplaying')}\n"
                                         f"`/last` - {tg(gi, 'last')}\n"
                                         f"`/loop` - {tg(gi, 'loop')}\n"
                                         f"`/loop_this` - {tg(gi, 'loop_this')}\n"
                    , inline=False)
    embed.add_field(name="Queue", value=f"`/queue` - {tg(gi, 'queue_add')}\n"
                                        f"`/remove` - {tg(gi, 'queue_remove')}\n"
                                        f"`/clear` - {tg(gi, 'clear')}\n"
                                        f"`/shuffle` - {tg(gi, 'shuffle')}\n"
                                        f"`/show` - {tg(gi, 'queue_show')}\n"
                                        f"`/search` - {tg(gi, 'search')}"
                    , inline=False)
    embed.add_field(name="Voice", value=f"`/stop` - {tg(gi, 'stop')}\n"
                                        f"`/pause` - {tg(gi, 'pause')}\n"
                                        f"`/resume` - {tg(gi, 'resume')}\n"
                                        f"`/join` - {tg(gi, 'join')}\n"
                                        f"`/disconnect` - {tg(gi, 'die')}\n"
                                        f"`/volume` - {tg(gi, 'volume')}"
                    , inline=False)
    embed.add_field(name="Admin Commands", value=f"`/admin_announce` - \n"
                                                 f"`/admin_rape` - \n"
                                                 f"`/admin_rape_play` - \n"
                                                 f"`/admin_kys` - \n"
                                                 f"`/admin_config` - \n"
                                                 f"`/admin_log` - \n"
                                                 f"`/admin_change_config` - \n"
                                                 f"`/admin_probe` - "
                    , inline=False)

    if command == 'ping':
        embed = discord.Embed(title="Help", description=f"`/ping` - {tg(gi, 'ping')}")

    elif command == 'language':
        embed = discord.Embed(title="Help", description=f"`/language` - {tg(gi, 'language')}")
        embed.add_field(name="Arguments", value=f"`country_code` - {tg(gi, 'country_code')}", inline=False)

    elif command == 'sound_effects':
        embed = discord.Embed(title="Help", description=f"`/sound_effects` - {tg(gi, 'sound')}")
        embed.add_field(name="Arguments", value=f"`ephemeral` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'list_radios':
        embed = discord.Embed(title="Help", description=f"`/list_radios` - {tg(gi, 'list_radios')}")
        embed.add_field(name="Arguments", value=f"`ephemeral` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'play':
        embed = discord.Embed(title="Help", description=f"`/play` - {tg(gi, 'play')}")
        embed.add_field(name="Arguments", value=f"`url` - {tg(gi, 'url')}", inline=False)
        embed.add_field(name="", value=f"`force` - {tg(gi, 'force')}", inline=False)

    elif command == 'radio':
        embed = discord.Embed(title="Help", description=f"`/radio` - {tg(gi, 'radio')}")
        embed.add_field(name="Arguments", value=f"`favourite_radio` - {tg(gi, 'favourite_radio')}", inline=False)
        embed.add_field(name="", value=f"`radio_code` - {tg(gi, 'radio_code')}", inline=False)

    elif command == 'ps':
        embed = discord.Embed(title="Help", description=f"`/ps` - {tg(gi, 'ps')}")
        embed.add_field(name="Arguments", value=f"`effect_number` - {tg(gi, 'effects_number')}", inline=False)

    elif command == 'skip':
        embed = discord.Embed(title="Help", description=f"`/skip` - {tg(gi, 'skip')}")

    elif command == 'nowplaying':
        embed = discord.Embed(title="Help", description=f"`/nowplaying` - {tg(gi, 'nowplaying')}")
        embed.add_field(name="Arguments", value=f"`ephemeral` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'last':
        embed = discord.Embed(title="Help", description=f"`/last` - {tg(gi, 'last')}")
        embed.add_field(name="Arguments", value=f"`ephemeral` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'loop':
        embed = discord.Embed(title="Help", description=f"`/loop` - {tg(gi, 'loop')}")

    elif command == 'loop_this':
        embed = discord.Embed(title="Help", description=f"`/loop_this` - {tg(gi, 'loop_this')}")

    elif command == 'queue':
        embed = discord.Embed(title="Help", description=f"`/queue` - {tg(gi, 'queue_add')}")
        embed.add_field(name="Arguments", value=f"`url` - {tg(gi, 'url')}", inline=False)
        embed.add_field(name="", value=f"`position` - {tg(gi, 'pos')}", inline=False)
        embed.add_field(name="", value=f"`mute_response` - {tg(gi, 'mute_response')}", inline=False)
        embed.add_field(name="", value=f"`force` - {tg(gi, 'force')}", inline=False)

    elif command == 'next_up':
        embed = discord.Embed(title="Help", description=f"`/next_up` - {tg(gi, 'next_up')}")
        embed.add_field(name="Arguments", value=f"`url` - {tg(gi, 'url')}", inline=False)
        embed.add_field(name="", value=f"`ephemeral` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'remove':
        embed = discord.Embed(title="Help", description=f"`/remove` - {tg(gi, 'remove')}")
        embed.add_field(name="Arguments", value=f"`number` - {tg(gi, 'number')}", inline=False)
        embed.add_field(name="", value=f"`display_type` - {tg(gi, 'display_type')}", inline=False)
        embed.add_field(name="", value=f"`ephemeral` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'clear':
        embed = discord.Embed(title="Help", description=f"`/clear` - {tg(gi, 'clear')}")
        embed.add_field(name="Arguments", value=f"`ephemeral` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'shuffle':
        embed = discord.Embed(title="Help", description=f"`/shuffle` - {tg(gi, 'shuffle')}")
        embed.add_field(name="Arguments", value=f"`ephemeral` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'show':
        embed = discord.Embed(title="Help", description=f"`/show` - {tg(gi, 'show')}")
        embed.add_field(name="Arguments", value=f"`display_type` - {tg(gi, 'display_type')}", inline=False)
        embed.add_field(name="", value=f"`ephemeral` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'search':
        embed = discord.Embed(title="Help", description=f"`/search` - {tg(gi, 'search')}")
        embed.add_field(name="Arguments", value=f"`search_query` - {tg(gi, 'search_query')}", inline=False)
        embed.add_field(name="", value=f"`display_type` - {tg(gi, 'display_type')}", inline=False)
        embed.add_field(name="", value=f"`ephemeral` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'stop':
        embed = discord.Embed(title="Help", description=f"`/stop` - {tg(gi, 'stop')}")
        embed.add_field(name="Arguments", value=f"`mute_response` - {tg(gi, 'mute_response')}", inline=False)

    elif command == 'pause':
        embed = discord.Embed(title="Help", description=f"`/pause` - {tg(gi, 'pause')}")
        embed.add_field(name="Arguments", value=f"`mute_response` - {tg(gi, 'mute_response')}", inline=False)

    elif command == 'resume':
        embed = discord.Embed(title="Help", description=f"`/resume` - {tg(gi, 'resume')}")
        embed.add_field(name="Arguments", value=f"`mute_response` - {tg(gi, 'mute_response')}", inline=False)

    elif command == 'join':
        embed = discord.Embed(title="Help", description=f"`/join` - {tg(gi, 'join')}")
        embed.add_field(name="Arguments", value=f"`channel_id` - {tg(gi, 'channel_id')}", inline=False)
        embed.add_field(name="", value=f"`mute_response` - {tg(gi, 'mute_response')}", inline=False)

    elif command == 'disconnect':
        embed = discord.Embed(title="Help", description=f"`/disconnect` - {tg(gi, 'die')}")

    elif command == 'volume':
        embed = discord.Embed(title="Help", description=f"`/volume` - {tg(gi, 'volume')}")
        embed.add_field(name="Arguments", value=f"`volume` - {tg(gi, 'volume')}", inline=False)
        embed.add_field(name="", value=f"`ephemeral` - {tg(gi, 'ephemeral')}", inline=False)
        embed.add_field(name="", value=f"`mute_response` - {tg(gi, 'mute_response')}", inline=False)

    await ctx.reply(embed=embed, ephemeral=True)

bot.run(api_key)
