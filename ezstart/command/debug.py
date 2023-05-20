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

    @commands.command(aliases=["effect"])
    async def effectid(self, ctx, effect_id: int, co: int = 1, co2: int = 1, user: discord.User = None, msg=None):
        try:
            if ctx.author.id not in admin:
                return await ctx.send(cmd_error_msg)
            if not user:
                user = ctx.author
            lists = alldata.effects
            lists.setdefault(effect_id, "[None]")
            if msg == "delete":
                await self.db.delete_effect(user.id, effect_id)
                await ctx.send(f"`ID:{effect_id}`:`{lists[effect_id]}`を削除しました。")
            if not msg:
                await ctx.send(f"{user.name}は`ID:{effect_id} Level:{co} Turn:{co2}`:`{lists[effect_id]}`を付与した！")
                await self.db.give_effect(user.id, effect_id, co, co2)
        except:
            return await alldata.error_send(ctx)

    @commands.command(aliases=["meffect"])
    async def meffectid(self, ctx, effect_id: int, co: int = 1, co2: int = 1, channel: discord.TextChannel = None, msg=None):
        try:
            if ctx.author.id not in admin:
                return await ctx.send(cmd_error_msg)
            if not channel:
                channel = ctx.channel
            lists = alldata.effects
            lists.setdefault(effect_id, "[None]")
            if msg == "delete":
                await self.db.delete_effect(channel.id, effect_id)
                await ctx.send(f"`ID:{effect_id}`:`{lists[effect_id]}`を削除しました。")
            if not msg:
                await ctx.send(f"{channel.name}は`ID:{effect_id} Level:{co} Turn:{co2}`:`{lists[effect_id]}`を付与した！")
                await self.db.give_effect(channel.id, effect_id, co, co2)
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
