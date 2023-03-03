import discord
from discord.ext import commands
from discord.ui import Button, View
from discord import app_commands

from random import randint
import pygame

from database import res_x, res_y, text_color_dict, rim_color, color_dict, font_size_dict, background_color, react_dict, games
from database import text as text


def print_screen(b, guild_id):
    global res_x, res_y, text_color_dict, rim_color, color_dict, font_size_dict, background_color

    game_size = b.size
    s1 = s2 = (res_x/50)
    cell_length = 175
    space_between = 33
    res = (res_x-(2*s1))
    for z in range(game_size):
        cell_length = round((res - (res / 10)) / game_size)
        space_between = round((res/10) / (game_size - 1))
    curve = 8

    pygame.init()
    screen = pygame.display.set_mode((res_x, res_y), pygame.RESIZABLE)

    # pygame text
    font1 = pygame.font.Font("cogs/clear-sans.regular.ttf", round((512/4)/game_size))
    font2 = pygame.font.Font("cogs/clear-sans.regular.ttf", round((352/4)/game_size))
    font3 = pygame.font.Font("cogs/clear-sans.regular.ttf", round((272/4)/game_size))
    font4 = pygame.font.Font("cogs/clear-sans.regular.ttf", round((192/4)/game_size))

    screen.fill(rim_color)

    # rim = pygame.draw.rect(screen, rim_color, (border, border, 1000 + border * 2, 1000 + border * 2), 0, curve)

    for p in range(game_size):
        for g in range(game_size):
            exec(f"cell_{g * p} = pygame.draw.rect(screen, {color_dict[b.data[p][g]]},"
                 f" (s1+(({cell_length + space_between})*{g}), s2+(({cell_length + space_between})*{p}),"
                 f" cell_length, cell_length), 0, {curve})")
            if b.data[p][g] != 0:
                exec(f"text_{g * p} = {font_size_dict[b.data[p][g]]}.render('{b.data[p][g]}', True,"
                     f" {text_color_dict[b.data[p][g]]})")
                exec(f"text_rect_{g * p} = text_{g * p}.get_rect()")
                exec(f"text_rect_{g * p}.center = (s1+((({cell_length + space_between})*{g})+round({cell_length}/2)), s2+((({cell_length + space_between})*{p})+round({cell_length}/2)))")
                exec(f"screen.blit(text_{g * p}, text_rect_{g * p})")

    pygame.image.save(screen, f'cogs/images/Game2048_frame_{guild_id}.png')
    pygame.quit()


class Board:
    def __init__(self, board_size):
        self.game_running = True
        self.size = board_size
        self.score = 0
        self.tile = 2
        data = []
        for i in range(self.size):
            data.append([0] * self.size)
        self.data = data

    def gen_random(self):
        empty = []
        for num_y, val_y in enumerate(self.data):
            for num_x, val_x in enumerate(val_y):
                if val_x == 0:
                    empty.append([num_y, num_x])
        if not empty:
            self.game_over()
            return
        r = randint(0, len(empty) - 1)
        self.data[empty[r][0]][empty[r][1]] = 2

    def compress(self):
        for i in range(self.size):
            self.data[i] = list(filter((0).__ne__, self.data[i]))
            for x in range(self.size - len(self.data[i])):
                self.data[i].append(0)

    def merge(self):
        for i in range(self.size):
            for index, value in enumerate(self.data[i]):
                if index + 1 < self.size:
                    if self.data[i][index + 1] == value:
                        merged = value * 2
                        if merged > self.tile:
                            self.tile = merged
                        self.data[i][index] = merged
                        self.score = self.score + merged
                        self.data[i][index + 1] = 0

    def rotate_old(self):
        for x in range(0, int(self.size / 2)):
            for y in range(x, self.size - x - 1):
                temp = self.data[x][y]
                self.data[x][y] = self.data[y][self.size - 1 - x]
                self.data[y][self.size - 1 - x] = self.data[self.size - 1 - x][self.size - 1 - y]
                self.data[self.size - 1 - x][self.size - 1 - y] = self.data[self.size - 1 - y][x]
                self.data[self.size - 1 - y][x] = temp

    def rotate(self):
        size = self.size - 1
        rotated_data = [[] for _ in range(self.size)]
        for i, v in enumerate(self.data):
            for index, val in enumerate(self.data[i]):
                rotated_data[size - index].append(val)
        self.data = rotated_data

    def move_up(self):
        self.rotate()
        self.compress()
        self.merge()
        self.compress()
        for i in range(3):
            self.rotate()

    def move_down(self):
        for i in range(3):
            self.rotate()
        self.compress()
        self.merge()
        self.compress()
        self.rotate()

    def move_left(self):
        self.compress()
        self.merge()
        self.compress()

    def move_right(self):
        for i in range(2):
            self.rotate()
        self.compress()
        self.merge()
        self.compress()
        for i in range(2):
            self.rotate()

    def move_input(self, key):
        starting_data = []
        for i in range(self.size):
            starting_data.append(self.data[i])
        if key == "up":
            self.move_up()
        elif key == "down":
            self.move_down()
        elif key == "left":
            self.move_left()
        elif key == "right":
            self.move_right()
        if starting_data != self.data:
            self.gen_random()

    def run(self):
        self.gen_random()

    def game_over(self):
        self.game_running = False
        print("game over")


def create_embed_2048(b, guild_id):
    embed = (discord.Embed(title="2048 Game", color=discord.Color.from_rgb(250, 248, 239)))
    file = discord.File(f'cogs/images/Game2048_frame_{guild_id}.png', filename="image.png")
    embed.add_field(name="Score", value=b.score)
    embed.add_field(name="Highest tile", value=b.tile)
    embed.set_image(url="attachment://image.png")

    return [[file], embed]


class Game2048ControlView(View):

    def __init__(self, ctx, b):
        super().__init__(timeout=180)
        self.guild = ctx.guild
        self.guild_id = ctx.guild.id
        self.b = b

    @discord.ui.button(emoji=react_dict['left'], style=discord.ButtonStyle.blurple, custom_id='left')
    async def callback_left(self, interaction, button):
        self.b.move_input('left')
        print_screen(self.b, self.guild_id)
        data = create_embed_2048(self.b, self.guild_id)
        await interaction.response.edit_message(embed=data[1], attachments=data[0], view=self)

    @discord.ui.button(emoji=react_dict['down'], style=discord.ButtonStyle.blurple, custom_id='down')
    async def callback_down(self, interaction, button):
        self.b.move_input('down')
        print_screen(self.b, self.guild_id)
        data = create_embed_2048(self.b, self.guild_id)
        await interaction.response.edit_message(embed=data[1], attachments=data[0], view=self)

    @discord.ui.button(emoji=react_dict['up'], style=discord.ButtonStyle.blurple, custom_id='up')
    async def callback_up(self, interaction, button):
        self.b.move_input('up')
        print_screen(self.b, self.guild_id)
        data = create_embed_2048(self.b, self.guild_id)
        await interaction.response.edit_message(embed=data[1], attachments=data[0], view=self)

    @discord.ui.button(emoji=react_dict['right'], style=discord.ButtonStyle.blurple, custom_id='right')
    async def callback_right(self, interaction, button):
        self.b.move_input('right')
        print_screen(self.b, self.guild_id)
        data = create_embed_2048(self.b, self.guild_id)
        await interaction.response.edit_message(embed=data[1], attachments=data[0], view=self)


class Game2048(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded Game2048 cog.")

    @commands.hybrid_command(name='game', with_app_command=True)
    # @app_commands.describe(game_size=text['game_size'])    add later
    async def game_selector(self, ctx: commands.Context, game_type: games):
        if game_type == '2048':
            await self.game2048(ctx)

    @commands.hybrid_command(name='game2048', with_app_command=True, description=text['game2048'], help=text['game2048'])
    @app_commands.describe(game_size=text['game_size'])
    async def game2048(self, ctx: commands.Context, game_size: int = None):
        guild_id = ctx.guild.id
        await ctx.defer(ephemeral=False)
        if not game_size:
            game_size = 4
        b = Board(game_size)
        b.run()

        print_screen(b, guild_id)
        data = create_embed_2048(b, guild_id)

        view = Game2048ControlView(ctx, b)

        await ctx.reply(file=data[0][0], embed=data[1], view=view)


async def setup(bot):
    await bot.add_cog(Game2048(bot))
