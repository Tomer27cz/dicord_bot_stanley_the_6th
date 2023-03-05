import discord
import asyncio
from discord import FFmpegPCMAudio, app_commands, Forbidden
from discord.ext import commands
from discord.ui import View


import yt_dlp
import youtubesearchpython
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests

from os import path, listdir
from math import ceil
from mutagen.mp3 import MP3
import sys
from typing import Literal
import traceback
import datetime

from database import radia_stream, radia_url, radia_cz_literal1, radia_cz_literal2, radia_cz_literal3, radia_cz_literal4, \
    favourite_radia_literal, radia_name, radia_thumbnail, radio_website, guild_ids, react_dict, language_list_literal
from database import text
# noinspection PyUnresolvedReferences
from database import text_cs, text_de, text_eo, text_es, text_fr, text_it, text_ja, text_ko, text_la, text_zh_cn
# noinspection PyUnresolvedReferences
from api_keys import api_key, api_key_testing

import functools


PREFIX = '$'
BOT_ID = 1007004463933952120
MY_ID = 349164237605568513

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
        voice_state = member.guild.voice_client
        if voice_state is not None and len(voice_state.channel.members) == 1:
            after.channel.guild.voice_client.stop()
            await voice_state.disconnect()
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
                    options[member.guild.id].stopped = True
                    voice.stop()
                    await voice.disconnect()
                    print_message(member.guild.id, "Disconnecting after 180 second of nothing playing")
                if not voice.is_connected():
                    break

    async def on_command_error(self, ctx, error):
        print_message(ctx.guild.id, f"{error}")
        await ctx.reply(f"{error}   {bot.get_user(MY_ID).mention}", ephemeral=True)


# ---------------- Data Classes ------------

class ContextImitation:
    def __init__(self, guild, guild_id, author, message):
        self.guild = guild
        self.guild.id = guild_id
        self.author = author
        self.message = message
        self.message.author = author


class Guild:
    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.stopped = False
        self.loop = False
        self.is_radio = False
        self.language = 'cs'
        self.response_type = 'short'  # long or short
        self.search_query = 'Never gonna give you up'
        self.buttons = False


class Video:
    def __init__(self, url, author):
        self.url = url
        self.author = author

        try:
            video = youtubesearchpython.Video.getInfo(url)  # mode=ResultMode.json
        except Exception as e:
            raise ValueError(f"Not a youtube link: {e}")

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
        self.url = radia_url[radia_name.index(name)]

        self.picture = radia_thumbnail[radia_name.index(name)]
        self.channel_name = radio_website[radia_name.index(name)]
        self.channel_link = self.url
        self.title = name
        self.duration = 'Stream'
        self.radio_website = radio_website[radia_name.index(name)]

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
        self.picture = vlc_logo_link
        self.duration = duration
        self.channel_name = 'Local file'
        self.channel_link = 'Local file'


bot = Bot()

queue = dict(zip(guild_ids, [[] for _ in range(len(guild_ids))]))
search_list = dict(zip(guild_ids, [[] for _ in range(len(guild_ids))]))
now_playing = dict(zip(guild_ids, [Video(url='dQw4w9WgXcQ', author='Tomer27cz#4272') for _ in range(len(guild_ids))]))
options = dict(zip(guild_ids, [Guild(guild_ids[_]) for _ in range(len(guild_ids))]))


# Sound effects listing
all_sound_effects = listdir('sound_effects')  # getting file names
for file_index, file_val in enumerate(all_sound_effects):
    all_sound_effects[file_index] = all_sound_effects[file_index][:len(file_val) - 4]  # getting rid of extension

vlc_logo_link = 'https://cdn.discordapp.com/attachments/892403162315644931/1008054767379030096/vlc.png'

# ---------------------------------------------- TEXT ----------------------------------------------------------


def text_guild(guild_id, content):
    lang = options[guild_id].language
    if lang == 'en':
        return content
    return globals()[f'text_{lang}'][content]


# ---------video_info / url --------


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

# -------------- convert -----------


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


# ------------ other get/set info --------------------


def mp3_length(path_of_mp3):
    audio = MP3(path_of_mp3)
    length = audio.info.length
    return length


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


# ---------------EMBED--------------


def create_embed(video, name, guild_id):
    #  (link, title, picture, duration, user, author, author_link)
    #  (  0    1       2         3        4    5          6      )
    embed = (discord.Embed(title=name,
                           description=f'```\n{video.title}\n```',
                           color=discord.Color.blurple()))
    if name == text_guild(guild_id, "Now playing"):
        now_playing[guild_id] = video
    embed.add_field(name=text_guild(guild_id, 'Duration'), value=convert_duration(video.duration))
    try:
        embed.add_field(name=text_guild(guild_id, 'Requested by'), value=video.author.mention)
    except AttributeError:
        embed.add_field(name=text_guild(guild_id, 'Requested by'), value=video.author)
    embed.add_field(name=text_guild(guild_id, 'Author'), value=f'[{video.channel_name}]({video.channel_link})')
    embed.add_field(name=text_guild(guild_id, 'URL'), value=f'[{video.url}]({video.url})')
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
                options[interaction.guild_id].stopped = True
                await interaction.response.edit_message(view=None)
            else:
                await interaction.response.send_message(text_guild(self.guild_id, "No audio playing"), ephemeral=True)
        else:
            await interaction.response.send_message(text_guild(self.guild_id, "No audio"), ephemeral=True)


class SearchOptionView(View):

    def __init__(self, ctx):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.guild = ctx.guild
        self.guild_id = ctx.guild.id

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['1'], style=discord.ButtonStyle.blurple, custom_id='1')
    async def callback_1(self, interaction, button):
        video = search_list[self.guild.id][0]
        queue[self.guild.id].append(video)
        await interaction.response.edit_message(content=f'`{video.title}` '
                                                        f'{text_guild(self.guild_id, "added to queue!")}', view=None)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['2'], style=discord.ButtonStyle.blurple, custom_id='2')
    async def callback_2(self, interaction, button):
        video = search_list[self.guild.id][1]
        queue[self.guild.id].append(video)
        await interaction.response.edit_message(content=f'`{video.title}` '
                                                        f'{text_guild(self.guild_id, "added to queue!")}', view=None)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['3'], style=discord.ButtonStyle.blurple, custom_id='3')
    async def callback_3(self, interaction, button):
        video = search_list[self.guild.id][2]
        queue[self.guild.id].append(video)
        await interaction.response.edit_message(content=f'`{video.title}` '
                                                        f'{text_guild(self.guild_id, "added to queue!")}', view=None)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['4'], style=discord.ButtonStyle.blurple, custom_id='4')
    async def callback_4(self, interaction, button):
        video = search_list[self.guild.id][3]
        queue[self.guild.id].append(video)
        await interaction.response.edit_message(content=f'`{video.title}` '
                                                        f'{text_guild(self.guild_id, "added to queue!")}', view=None)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['5'], style=discord.ButtonStyle.blurple, custom_id='5')
    async def callback_5(self, interaction, button):
        video = search_list[self.guild.id][4]
        queue[self.guild.id].append(video)
        await interaction.response.edit_message(content=f'`{video.title}` '
                                                        f'{text_guild(self.guild_id, "added to queue!")}', view=None)


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
        await interaction.response.edit_message(content=text_guild(self.guild_id, "Adding playlist to queue..."), view=None)
        if self.force:
            response = await queue_command(self.ctx, playlist_url, 0, None, True)
        else:
            response = await queue_command(self.ctx, playlist_url, None, None, True)
        # await interaction.followup.send(content=response[1]) ---- works without (if it doesn't work, uncomment this)

    # noinspection PyUnusedLocal
    @discord.ui.button(label='No, just this', style=discord.ButtonStyle.blurple)
    async def callback_2(self, interaction, button):
        pure_url = get_pure_url(self.url)
        if self.force:
            response = await queue_command(self.ctx, pure_url, 0, True)
        else:
            response = await queue_command(self.ctx, pure_url, None, True)
        await interaction.response.edit_message(content=response[1], view=None)
        await play(self.ctx)


# ---------------------------------------Youtube Search--------------------------------------------------


@bot.hybrid_command(name='search', with_app_command=True, description=text['search'],  help=text['search'])
@app_commands.describe(search_query=text['search_query'])
async def search_command(ctx: commands.Context,
                         search_query,
                         display_type: Literal['text', 'embed'] = 'text'
                         ):
    print_command(ctx, 'search', [search_query, display_type])
    await ctx.defer()
    guild_id = ctx.guild.id

    message = ''

    response = options[guild_id].response_type
    if display_type == 'text':
        response = 'short'
    if display_type == 'embed':
        response = 'long'

    if response == 'long':
        await ctx.reply(text_guild(guild_id, 'Searching...'), ephemeral=True)

    custom_search = youtubesearchpython.VideosSearch(search_query, limit=5)
    search_list[guild_id].clear()

    view = SearchOptionView(ctx)

    for i in range(5):
        # noinspection PyTypeChecker
        url = custom_search.result()['result'][i]['link']
        video = Video(url, ctx.author)
        search_list[guild_id].append(video)

        if response == 'long':
            embed = create_embed(video, f'{text_guild(guild_id, "Result #")}{i + 1}', guild_id)
            await ctx.message.channel.send(embed=embed)
        if response == 'short':
            message += f'{text_guild(guild_id, "Result #")}{i+1} : `{video.title}`\n'
    if response == 'short':
        await ctx.reply(message, view=view)


# -------------------------------------Queue---------------------------------------------------------


@bot.hybrid_command(name='queue', with_app_command=True, description=text['queue_add'], help=text['queue_add'])
@app_commands.describe(url=text['url'], position=text['pos'], mute_response=text['mute_response'])
async def queue_command(ctx: commands.Context,
                        url=None,
                        position: int = None,
                        mute_response: bool = None,
                        is_internal: bool = False,
                        force: bool = False
                        ):
    print_command(ctx, 'queue', [url, position, mute_response])
    guild_id = ctx.guild.id
    author = ctx.author

    if not url:
        message = text_guild(guild_id, "`url` is **required**")
        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return [False, message]

    elif url[0:33] == "https://www.youtube.com/playlist?":
        try:
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

            if position or position == 0: queue[guild_id].insert(position, video)
            else: queue[guild_id].append(video)

        message = f"`{playlist_songs}` {text_guild(guild_id, 'songs from playlist added to queue!')}"
        if not mute_response:
            await ctx.reply(message)

        return [True, message]

    elif url:
        if 'index=' in url or 'list=' in url:
            print(f"{url} is playlist")
            view = PlaylistOptionView(ctx, url, force)

            message = text_guild(guild_id,
                                 'This video is from a **playlist**, do you want to add the playlist to **queue?**')
            await ctx.reply(message, view=view)
            return [False, message]
        try:
            video = Video(url, author)

            if position or position == 0: queue[guild_id].insert(position, video)
            else: queue[guild_id].append(video)

            message = f'`{video.title}` {text_guild(guild_id, "added to queue!")}'

            if not mute_response:
                await ctx.reply(message)

            return [True, message]

        except (ValueError, IndexError, TypeError):
            try:
                url_only_id = 'https://www.youtube.com/watch?v=' + url.split('watch?v=')[1]
                video = Video(url_only_id, author)

                if position or position == 0: queue[guild_id].insert(position, video)
                else: queue[guild_id].append(video)

                message = f'`{video.title}` {text_guild(guild_id, "added to queue!")}'

                if not mute_response:
                    await ctx.reply(message)

                return [True, message]

            except (ValueError, IndexError, TypeError):

                if not is_internal:
                    await search_command(ctx, url, 'text')

                message = f'`{url}` {text_guild(guild_id, "is not supported!")}'

                # await ctx.reply(message, ephemeral=True)

                return [False, message]


@bot.hybrid_command(name='next_up', with_app_command=True, description=text['next_up'], help=text['next_up'])
@app_commands.describe(url=text['url'])
async def next_up(ctx: commands.Context,
                 url=None,
                 ephemeral: Literal['True', 'False'] = 'False'
                 ):
    print_command(ctx, 'next', [ephemeral])
    response = await queue_command(ctx, url, 0, True, True)
    if ephemeral:
        await ctx.reply(response[1], ephemeral=True)
    else:
        await ctx.reply(response[1])


@bot.hybrid_command(name='remove', with_app_command=True, description=text['queue_remove'], help=text['queue_remove'])
@app_commands.describe(number=text['number'])
async def remove(ctx: commands.Context,
                 number: int,
                 ephemeral: Literal['True', 'False'] = 'False'
                 ):
    print_command(ctx, 'remove', [number, ephemeral])
    guild_id = ctx.guild.id

    if number:
        if number > len(queue[guild_id]):
            if not queue[guild_id]:
                await ctx.reply(text_guild(guild_id, "Nothing to **remove**, queue is **empty!**"), ephemeral=True)
                return
            await ctx.reply(text_guild(guild_id, "Index out of range!"), ephemeral=True)
            return

        video = queue[guild_id][number]

        if options[guild_id].response_type == 'long':
            embed = create_embed(video, f'{text_guild(guild_id, "REMOVED #")}{number}', guild_id)
            if ephemeral == 'True':
                await ctx.reply(embed=embed, ephemeral=True)
            else:
                await ctx.reply(embed=embed)
        if options[guild_id].response_type == 'short':
            if ephemeral == 'True':
                await ctx.reply(f'REMOVED #{number} : `{video.title}`', ephemeral=True)
            else:
                await ctx.reply(f'REMOVED #{number} : `{video.title}`')

        queue[guild_id].pop(number)

@bot.hybrid_command(name='clear', with_app_command=True, description=text['clear'], help=text['clear'])
async def clear(ctx: commands.Context,
                 ephemeral: Literal['True', 'False'] = 'False'
                 ):
    print_command(ctx, 'clear', [ephemeral])
    guild_id = ctx.guild.id
    queue[guild_id].clear()
    if ephemeral == 'True':
        await ctx.reply(text_guild(guild_id, 'Removed **all** songs from queue'), ephemeral=True)
    else:
        await ctx.reply(text_guild(guild_id, 'Removed **all** songs from queue'))
    return


@bot.hybrid_command(name='show', with_app_command=True, description=text['queue_show'], help=text['queue_show'])
@app_commands.describe(display_type=text['display_type'])
async def show(ctx: commands.Context,
               display_type: Literal['short', 'long'] = None,
               ephemeral: Literal['True', 'False'] = 'False'
               ):
    print_command(ctx, 'show', [display_type, ephemeral])
    guild_id = ctx.guild.id
    max_embed = 5
    if not queue[guild_id]:
        if ephemeral == 'True':
            await ctx.reply(text_guild(guild_id, "Nothing to **show**, queue is **empty!**"), ephemeral=True)
            return
        await ctx.reply(text_guild(guild_id, "Nothing to **show**, queue is **empty!**"))
        return
    if display_type == 'short' or (len(queue[guild_id]) > max_embed and display_type != 'long'):
        await ctx.reply(text_guild(guild_id, "Showing..."), ephemeral=True)
        used_type = 'short'

        if ephemeral == 'True':
            await ctx.send(f"**Loop** mode  `{options[guild_id].loop}`,  **Display** type `{used_type}`", ephemeral=True)
        else:
            await ctx.message.channel.send(f"**Loop** mode  `{options[guild_id].loop}`,  **Display** type `{used_type}`")

        message = ''
        for index, val in enumerate(queue[guild_id]):
            add = f'**{text_guild(guild_id, "Queue #")}{index}**  `{convert_duration(val.duration)}`  `{val.title}` \n'
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

    elif display_type == 'long' or (len(queue[guild_id]) < max_embed and display_type != 'short'):
        await ctx.reply(text_guild(guild_id, "Showing..."), ephemeral=True)
        used_type = 'long'

        if ephemeral == 'True':
            await ctx.send(f"**Loop** mode  `{options[guild_id].loop}`,  **Display** type `{used_type}`", ephemeral=True)
        else:
            await ctx.message.channel.send(f"**Loop** mode  `{options[guild_id].loop}`,  **Display** type `{used_type}`")

        for index, val in enumerate(queue[guild_id]):
            embed = create_embed(val, f'{text_guild(guild_id, "Queue #")}{index}', guild_id)

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
async def loop_command(ctx: commands.Context):
    print_command(ctx, 'loop', None)
    guild_id = ctx.guild.id
    if options[guild_id].loop:
        options[guild_id].loop = False
        await ctx.reply("Loop mode: `False`", ephemeral=True)
        return
    if not options[guild_id].loop:
        options[guild_id].loop = True
        await ctx.reply("Loop mode: `True`", ephemeral=True)
        return


@bot.hybrid_command(name='loop_this', with_app_command=True, description=text['loop_this'], help=text['loop_this'])
async def loop_this(ctx: commands.Context):
    print_command(ctx, 'loop_this', None)
    guild_id = ctx.guild.id
    if now_playing[guild_id] and ctx.voice_client.is_playing:
        queue[guild_id].clear()
        queue[guild_id].append(now_playing[guild_id])
        options[guild_id].loop = True
        await ctx.reply(f'{text_guild(guild_id, "Queue **cleared**, Player will now loop **currently** playing song:")}'
                        f' `{now_playing[guild_id].title}`')
    else:
        await ctx.reply(text_guild(guild_id, "Nothing is playing **right now**"))


@bot.hybrid_command(name='nowplaying', with_app_command=True, description=text['nowplaying'], help=text['nowplaying'])
async def now(ctx: commands.Context,
              ephemeral: Literal['True', 'False'] = 'False'
              ):
    print_command(ctx, 'nowplaying', [ephemeral])
    guild_id = ctx.guild.id
    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            now_playing[guild_id].renew()
            embed = create_embed(now_playing[guild_id], "Now playing", guild_id)

            view = PlayerControlView(ctx)

            if ephemeral == 'True':
                if options[guild_id].buttons:
                    await ctx.reply(embed=embed, view=view, ephemeral=True)
                else:
                    await ctx.reply(embed=embed, ephemeral=True)

            if ephemeral == 'False':
                if options[guild_id].buttons:
                    await ctx.reply(embed=embed, view=view)
                else:
                    await ctx.reply(embed=embed)

        if not ctx.voice_client.is_playing():
            if ctx.voice_client.is_paused():
                await ctx.reply(
                    f'{text_guild(guild_id, "There is no song playing right **now**, but there is one **paused:**")}'
                    f'  `{now_playing[guild_id].title}`')
            else:
                await ctx.reply(text_guild(guild_id, 'There is no song playing right **now**'))
    else:
        await ctx.reply(text_guild(guild_id, 'There is no song playing right **now**'))


# -------------------------------------------Voice---------------------------------------------


@bot.hybrid_command(name='radio', with_app_command=True, description=text['radio'], help=text['radio'])
@app_commands.describe(radia_cz_1=text['radio_menu'], radia_cz_2=text['radio_menu'], radia_cz_3=text['radio_menu'],
                       radia_cz_4=text['radio_menu'], favourite_radio=text['favourite_radio'])
async def radio(ctx: commands.Context,
                radia_cz_1: radia_cz_literal1 = None,
                radia_cz_2: radia_cz_literal2 = None,
                radia_cz_3: radia_cz_literal3 = None,
                radia_cz_4: radia_cz_literal4 = None,
                favourite_radio: favourite_radia_literal = None
                ):
    print_command(ctx, 'radio', [radia_cz_1, radia_cz_2, radia_cz_3, radia_cz_4, favourite_radio])
    guild_id = ctx.guild.id
    radio_type = 'Rádio BLANÍK'
    await ctx.defer(ephemeral=False)
    if (radia_cz_1 and radia_cz_2) or (radia_cz_1 and radia_cz_3) or (radia_cz_1 and radia_cz_4) or\
            (radia_cz_4 and radia_cz_3) or (radia_cz_4 and radia_cz_2) or (radia_cz_2 and radia_cz_3) or\
            (favourite_radio and radia_cz_1) or (favourite_radio and radia_cz_2) or\
            (favourite_radio and radia_cz_3) or (favourite_radio and radia_cz_4):
        await ctx.reply(text_guild(guild_id, "Only **one** argument possible!"), ephemeral=True)
        return
    if radia_cz_1:
        radio_type = radia_cz_1
    elif radia_cz_2:
        radio_type = radia_cz_2
    elif radia_cz_3:
        radio_type = radia_cz_3
    elif radia_cz_4:
        radio_type = radia_cz_4
    elif favourite_radio:
        radio_type = favourite_radio


    if not ctx.voice_client:
        response = await join(ctx, None, True)
        if not response:
            return

    url = radia_stream[radia_name.index(radio_type)]
    queue[guild_id].clear()

    if ctx.voice_client.is_playing():
        await stop(ctx, True)  # call the stop coroutine if something else is playing, pass True to not send response

    radio_class = Radio(radio_type, ctx.author)
    now_playing[guild_id] = radio_class

    options[guild_id].is_radio = True

    embed = create_embed(radio_class, 'Now playing', guild_id)

    source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)

    ctx.voice_client.play(source)

    if options[guild_id].buttons:
        view = PlayerControlView(ctx)
        await ctx.reply(embed=embed, view=view)
    else:
        await ctx.reply(embed=embed)  # view=view   f"**{text['Now playing']}** `{radio_type}`",


# @bot.hybrid_command(name='radio_garden', with_app_command=True, description=text['radio'],
#                     help=text['radio'])
# async def radio_garden(ctx: commands.Context):
#     guild_id = ctx.guild.id
# 
#     try:
#         channel = ctx.message.author.voice.channel
#         await channel.connect()
#     except (discord.ext.commands.errors.CommandInvokeError, discord.errors.ClientException, AttributeError):
#         pass
#     if not ctx.voice_client:
#         await ctx.reply(text_guild(guild_id, "Bot is not connected to a voice channel,"
#                                              " do `/join` or connect to a voice channel yourself"), ephemeral=True)
#         return
# 
#     voice = ctx.voice_client
# 
#     url = "http://radio.garden/visit/uvaly/Vy6uPWnV"
# 
#     is_radio[guild_id] = 'True'
# 
#     source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
#     voice.play(source)
# 
#     await ctx.reply('yes')  # view=view   f"**{text['Now playing']}** `{radio_type}`",
# 




@bot.hybrid_command(name='play', with_app_command=True, description=text['play'], help=text['play'])
@app_commands.describe(url=text['play'], force=text['force'])
async def play(ctx: commands.Context,
               url=None,
               force=False
               ):
    print_command(ctx, 'play', [url])
    arg = 'next'
    guild_id = ctx.guild.id

    if url == 'next':
        if options[guild_id].stopped:
            print_message(guild_id, "stopped")
            return

    if url and url != 'next':
        if url[0:33] == "https://www.youtube.com/playlist?":
            await ctx.defer()
        if force:
            response = await queue_command(ctx, url=url, position=0, mute_response=True, is_internal=False, force=force)
        else:
            response = await queue_command(ctx, url=url, position=None, mute_response=True, is_internal=False, force=force)
        if not response[0]:
            return

    voice = ctx.voice_client

    if not voice or voice is None:
        # noinspection PyUnresolvedReferences
        if not ctx.interaction.response.is_done():
            await ctx.defer()
        response = await join(ctx, None, True)
        if not response:
            return

    voice = ctx.voice_client

    if voice.is_playing():
        if not options[guild_id].is_radio and not force:
            if url and not force:
                await ctx.reply(text_guild(guild_id, "**Already playing**, added to queue"))
                return
            await ctx.reply(text_guild(guild_id, "**Already playing**"), ephemeral=True)
            return
        voice.stop()
        options[guild_id].stopped = True
        options[guild_id].is_radio = False

    if not queue[guild_id]:
        await ctx.reply(text_guild(guild_id, "There is **nothing** in your **queue**"), ephemeral=True)
        return

    video = queue[guild_id][0]
    if not force:
        options[guild_id].stopped = False

    try:
        source = await YTDLSource.create_source(ctx, video.url)  # loop=bot.loop  va_list[0]
        voice.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play(ctx, arg), bot.loop))

        options[guild_id].stopped = False

        now_playing[guild_id] = video

        if options[guild_id].loop:
            queue[guild_id].append(video)

        queue[guild_id].pop(0)

        view = PlayerControlView(ctx)

        if options[guild_id].response_type == 'long':
            embed = create_embed(video, "Now playing", guild_id)
            if options[guild_id].buttons:
                await ctx.reply(embed=embed, view=view)
            else:
                await ctx.reply(embed=embed)

        if options[guild_id].response_type == 'short':
            if options[guild_id].buttons:
                await ctx.reply(f'{text_guild(guild_id, "Now playing")} `{video.title}`', view=view)
            else:
                await ctx.reply(f'{text_guild(guild_id, "Now playing")} `{video.title}`')

    except (discord.ext.commands.errors.CommandInvokeError, IndexError, TypeError, discord.errors.ClientException,
            YTDLError, discord.errors.NotFound):
        print_message(guild_id, "------------------------------- play -------------------------")
        tb = traceback.format_exc()
        print_message(guild_id, tb)
        print_message(guild_id, "--------------------------------------------------------------")
        await ctx.reply(f'{text_guild(guild_id, "An **error** occurred while trying to play the song")}'
                        f' {bot.get_user(MY_ID).mention} ({sys.exc_info()[0]})')


# @bot.hybrid_command(name='stream', with_app_command=True, description=text['stream'], help=text['stream'])
# @app_commands.describe(url=text['play'], force=text['force'])
# async def play(ctx: commands.Context,
#                url=None,
#                force=False
#                ):
#     print_command(ctx, 'play', [url])
#     arg = 'next'
#     guild_id = ctx.guild.id


# ------------------------------------------------------Sound Effects--------------------------------------------------

@bot.hybrid_command(name='sound', with_app_command=True, description=text['sound'], help=text['sound'])
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
async def ps(ctx: commands.Context,
             effect_number: app_commands.Range[int, 1, len(all_sound_effects)]
             ):
    print_command(ctx, 'ps', [effect_number])
    guild_id = ctx.guild.id
    options[guild_id].is_radio = False
    try:
        name = all_sound_effects[effect_number-1]
    except IndexError:
        await ctx.reply(text_guild(guild_id, "Number **not in list** (use `/sound` to get all sound effects)"),
                        ephemeral=True)
        return

    filename = "sound_effects/" + name + ".mp3"
    if path.exists(filename):
        source = FFmpegPCMAudio(filename)
        video = LocalFile(name, convert_duration(mp3_length(filename)), ctx.author)
        now_playing[guild_id] = video
    else:
        filename = "sound_effects/" + name + ".wav"
        if path.exists(filename):
            source = FFmpegPCMAudio(filename)
        else:
            await ctx.reply(text_guild(guild_id, "No such file/website supported"), ephemeral=True)
            return

    try:
        await join(ctx, None, True)
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
async def player_control(ctx: commands.Context,
                         action_type: Literal['stop', 'pause', 'resume'] = None,
                         mute_response: bool = False
                         ):
    print_command(ctx, 'player', [action_type, mute_response])
    guild_id = ctx.guild.id

    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if not action_type or not action_type and mute_response:
        view = PlayerControlView(ctx)
        await ctx.reply("Player control", view=view)

    if action_type == "stop":
        voice.stop()
        options[guild_id].stopped = True

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
#

@bot.hybrid_command(name='stop', with_app_command=True, description=f'Stop the player')
@app_commands.describe(mute_response=text['mute_response'])
async def stop(ctx: commands.Context,
               mute_response: bool = False
               ):
    print_command(ctx, 'stop', [mute_response])
    guild_id = ctx.guild.id

    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    voice.stop()
    options[guild_id].stopped = True

    if not mute_response:
        await ctx.reply("Player **stopped!**", ephemeral=True)


@bot.hybrid_command(name='pause', with_app_command=True, description=f'Pause the player')
@app_commands.describe(mute_response=text['mute_response'])
async def pause(ctx: commands.Context,
                mute_response: bool = False
                ):
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
async def resume(ctx: commands.Context,
                 mute_response: bool = False
                 ):
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


@bot.hybrid_command(name='zz_nuke', with_app_command=True)
@commands.check(is_authorised)
async def nuke(ctx: commands.Context,
               message,
               guild=None,
               delete: bool = True
               ):
    # guild_id = ctx.guild.id
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


@bot.hybrid_command(name='zz_log', with_app_command=True)
@commands.is_owner()
async def log_command(ctx: commands.Context):
    print_command(ctx, 'log', None)
    log = discord.File('log.txt')
    await ctx.reply(file=log, ephemeral=True)


@bot.hybrid_command(name='zz_change_config', with_app_command=True)
@app_commands.describe(guild='all, this, {guild_id}')
@commands.is_owner()
async def change_config(ctx: commands.Context,
                        stopped: Literal['True', 'False'] = None,
                        loop: Literal['True', 'False'] = None,
                        is_radio: Literal['True', 'False'] = None,
                        buttons: Literal['True', 'False'] = None,
                        language: language_list_literal = None,
                        response_type: Literal['short', 'long'] = None,
                        guild = None,
                        ):
    print_command(ctx, 'owner_commands', [stopped, loop, is_radio, buttons, language, response_type, guild])
    guild_id = ctx.guild.id

    guilds = []
    if guild == 'all':
        for guild in bot.guilds:
            guilds.append(guild.id)
    elif guild == 'this':
        guilds.append(ctx.guild.id)
    else:
        try:
            if int(guild) in bot.guilds:
                guilds.append(guild)
            else:
                await ctx.reply(text_guild(guild_id, "That guild doesn't exist or the bot is no"), ephemeral=True)
                return
        except (ValueError, TypeError):
            await ctx.reply(text_guild(guild_id, "That is not a **guild id!**"), ephemeral=True)
            return

    for guild_id in guilds:
        if stopped:
            options[guild_id].stopped = bool(stopped)
        if loop:
            options[guild_id].loop = bool(loop)
        if is_radio:
            options[guild_id].is_radio = bool(is_radio)
        if buttons:
            options[guild_id].buttons = bool(buttons)
        if language:
            options[guild_id].language = language
        if response_type:
            options[guild_id].response_type = response_type

        config = f'`stopped={options[guild_id].stopped}`, `loop={options[guild_id].loop}`,' \
                 f' `is_radio={options[guild_id].is_radio}`, `buttons={options[guild_id].buttons}`,' \
                 f' `language={options[guild_id].language}`, `response_type={options[guild_id].response_type}`'

        await ctx.reply(f'**Config for guild `{guild_id}`**\n {config}', ephemeral=True)


# @owner_commands.error
@change_config.error
@nuke.error
@log_command.error
async def owner_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        print_command(ctx, 'owner_commands', 'Failed')
        await ctx.reply("（ ͡° ͜ʖ ͡°)つ━☆・。\n"
                        "⊂　　 ノ 　　　・゜+.\n"
                        "　しーＪ　　　°。+ ´¨)\n"
                        "　　　　　　　　　.· ´¸.·´¨) ¸.·*¨)\n"
                        "　　　　　　　　　　(¸.·´ (¸.·' ☆ **Fuck off**\n")

@bot.hybrid_command(name='ping', with_app_command=True, description=text['ping'], help=text['ping'])
async def ping(ctx: commands.Context):
    print_command(ctx, 'ping', None)
    await ctx.reply(f'**Pong!** Latency: {round(bot.latency * 1000)}ms')


@bot.hybrid_command(name='language', with_app_command=True, description=text['language'], help=text['language'])
async def language_command(ctx: commands.Context,
                   country_code: language_list_literal
                   ):
    guild_id = ctx.guild.id
    print_command(ctx, 'language', [country_code])
    options[guild_id].language = country_code
    await ctx.reply(f'{text_guild(guild_id, "Changed the language for this server to: ")} `{options[guild_id].language}`')


@bot.hybrid_command(name='join', with_app_command=True, description=text['join'], help=text['join'])
@app_commands.describe(channel_id=text['channel_id'])
async def join(ctx: commands.Context,
               channel_id=None,
               mute_response: bool = False
               ):
    guild_id = ctx.guild.id
    print_command(ctx, 'join', [channel_id])

    if not channel_id:
        if ctx.author.voice:
            if ctx.voice_client:
                await ctx.voice_client.disconnect(force=True)
            channel = ctx.message.author.voice.channel
            await channel.connect()
            await ctx.guild.change_voice_state(channel=channel, self_deaf=True)
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
        await ctx.guild.change_voice_state(channel=voice_channel, self_deaf=True)
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


# Context menu commands
@bot.tree.context_menu(name='Add to queue')
async def add_to_queue(inter, message: discord.Message):
    ctx = ContextImitation(inter.guild, inter.guild_id, inter.user, message)
    print(ctx.author)
    response = await queue_command(ctx, message.content, None, True, True)
    await inter.response.send_message(content=response[1], ephemeral=True)


@bot.tree.context_menu(name='Show Profile')
async def show_profile(inter, member: discord.Member):
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




bot.run(api_key)
