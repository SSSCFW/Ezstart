from ezstart.database import alldata
from ezstart.database.alldata import *
from ezstart.database import maindb
from ezstart.function import attack

import discord
from discord.ext import commands
import traceback
import math
import io
import textwrap
import contextlib
import asyncio


class DebugCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = maindb.Database(self.bot)
        self.attack = attack.System(bot)

    @commands.command()
    async def exp(self, ctx, exp: int, user: discord.User = None):
        try:
            if ctx.author.id not in admin:
                return await ctx.send(cmd_error_msg)
            if not user:
                user = ctx.author
            user_id = user.id
            msg = await self.db.add_exp(user_id, int(exp))
            await ctx.send(f"<@{user_id}>は{exp}EXPを獲得した。\n{msg}")
        except:
            return await alldata.error_send(ctx)

    @commands.command(aliases=["effect"])
    async def effectid(self, ctx, effect_id: int, level: int = 1, count: int = 1, user: discord.User = None, msg=None):
        try:
            if ctx.author.id not in admin:
                return await ctx.send(cmd_error_msg)
            if not user:
                user = ctx.author
            effect_id = int(effect_id)
            level = int(level)
            count = int(count)
            lists = alldata.effects
            lists.setdefault(effect_id, "[None]")
            if msg == "delete":
                await self.db.delete_effect(user.id, effect_id)
                await ctx.send(f"`ID:{effect_id}`:`{lists[effect_id]}`を削除しました。")
            if not msg:
                await ctx.send(f"{user.name}は`ID:{effect_id} Level:{level} Turn:{count}`:`{lists[effect_id]}`を付与した！")
                await self.db.give_effect(user.id, effect_id, level, count)
        except:
            return await alldata.error_send(ctx)

    @commands.command(aliases=["meffect"])
    async def meffectid(self, ctx, effect_id: int, level: int = 1, count: int = 1, channel: discord.TextChannel = None, msg=None):
        try:
            if ctx.author.id not in admin:
                return await ctx.send(cmd_error_msg)
            if not channel:
                channel = ctx.channel
            effect_id = int(effect_id)
            level = int(level)
            count = int(count)
            lists = alldata.effects
            lists.setdefault(effect_id, "[None]")
            if msg == "delete":
                await self.db.delete_effect(channel.id, effect_id)
                await ctx.send(f"`ID:{effect_id}`:`{lists[effect_id]}`を削除しました。")
            if not msg:
                await ctx.send(f"{channel.name}は`ID:{effect_id} Level:{level} Turn:{count}`:`{lists[effect_id]}`を付与した！")
                await self.db.give_effect(channel.id, effect_id, level, count)
        except:
            return await alldata.error_send(ctx)

    @commands.command(name="itemid")
    async def item_id(self, ctx, item_id: int, co: int = 1, user: discord.User = None, msg=None):
        try:
            if ctx.author.id not in admin:
                return await ctx.send(cmd_error_msg)
            if not user:
                user = ctx.author
            lists = alldata.items
            lists.setdefault(item_id, "[None]")
            if msg == "delete":
                await self.db.delete_item(user.id, item_id)
                await ctx.send(f"`ID:{item_id}`:`{lists[item_id]}`を削除しました。")
            if not msg:
                await ctx.send(f"{user.name}は`ID:{item_id}`:`{lists[item_id]}`を`{co}`個手に入れた！")
                await self.db.give_item(user.id, item_id, co)
        except:
            return await alldata.error_send(ctx)

    @commands.command(name="sozaiid")
    async def sozai_id(self, ctx, material_id: int, co: int = 1, user: discord.User = None, msg=None):
        try:
            if ctx.author.id not in admin:
                return await ctx.send(cmd_error_msg)
            if not user:
                user = ctx.author
            lists = alldata.materials
            lists.setdefault(material_id, "[None]")
            if msg == "delete":
                await self.db.delete_material(user.id, material_id)
                await ctx.send(f"`ID:{material_id}`:`{lists[material_id]}`を削除しました。")
            if not msg:
                await ctx.send(f"{user.name}は`ID:{material_id}`:`{lists[material_id]}`を`{co}`個手に入れた！")
                await self.db.give_material(user.id, material_id, co)
        except:
            return await alldata.error_send(ctx)

    @commands.command(name="skillid")
    async def skill_id(self, ctx, skill_id: int, co: int = 1, user: discord.User = None, msg=None):
        try:
            if ctx.author.id not in admin:
                return await ctx.send(cmd_error_msg)
            if not user:
                user = ctx.author
            lists = alldata.skills
            lists.setdefault(skill_id, "[None]")
            if msg == "delete":
                await self.db.delete_skill(user.id, skill_id)
                await ctx.send(f"`ID:{skill_id}`:`{lists[skill_id]}`を削除しました。")
            if not msg:
                await ctx.send(f"{user.name}は`ID:{skill_id}`:`{lists[skill_id]}`を`{co}`個手に入れた！")
                await self.db.give_skill(user.id, skill_id, co)
        except:
            return await alldata.error_send(ctx)

    @commands.command()
    async def cban(self, ctx, count, user: discord.User = None):
        try:
            if ctx.author.id not in admin:
                return await ctx.send(cmd_error_msg)
            if not user:
                user = ctx.author
            user_id = user.id
            await self.db.set_ban(user_id, count)
            await ctx.send(f"<@{user_id}>はBanを{count}に変更しました。")
        except:
            return await alldata.error_send(ctx)

    @commands.command()
    async def rea(self, ctx, enemy_id):
        try:
            if ctx.author.id not in admin:
                return await ctx.send(cmd_error_msg)
            channel_id = ctx.channel.id
            await self.attack.next_battle(ctx, channel_id, enemy_id=enemy_id, level_up=False, only_embed=False)
        except:
            return await alldata.error_send(ctx)

    @commands.command()
    async def bosslv(self, ctx, level, channel=None):
        try:
            if ctx.author.id not in admin:
                return await ctx.send(cmd_error_msg)
            if channel is None: channel = ctx.channel.id
            await self.db.set_enemy_level(channel, level)
            embed2 = discord.Embed(
                description=f"<#{channel}>```fix\n{channel}``````diff\n+ 完了\n+ 敵のレベルを{level}に変更しました。```")
            await ctx.reply(embed=embed2)
        except:
            print(f"エラー[{ctx.message.author.guild.name}: {ctx.message.author.name}: {ctx.message.content}]")
            msg = discord.Embed(title=f"！！ＥＲＲＯＲ！！",
                                description=f"M:{ctx.message.content}\nG:{ctx.guild.name}/{ctx.guild.id}\nC:{ctx.channel.name}/{ctx.channel.id}/<#{ctx.channel.id}>\nU:{ctx.author.name}/{ctx.author.id}/<@{ctx.author.id}>```py\n{traceback.format_exc()}```",
                                color=0xC41415)
            await self.bot.get_channel(error_log_ch).send(embed=msg)
            return await ctx.send(embed=msg)

    @commands.command()
    @commands.bot_has_permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True,
                                  manage_messages=True, read_message_history=True)
    async def mycoin(self, ctx, user2: discord.User = None):
        try:
            user = ctx.author
            if user2:
                if ctx.author.id in alldata.admin:
                    user = user2
                else:
                    return await ctx.send(alldata.cmd_error_msg)
            ban = await self.db.get_ban(user.id)
            ban_text = f"{ban}"

            if ban in alldata.ban_message:
                ban_text = f"{alldata.ban_message[ban]}"

            embed = discord.Embed(title=f"{user.name}の財布だったもの",
                                  description=f"BAN:\n```diff\n{ban_text}```")

            await ctx.reply(embed=embed)
        except:
            return await alldata.error_send(ctx)


async def setup(bot: commands.Bot):
    await bot.add_cog(DebugCommand(bot))
