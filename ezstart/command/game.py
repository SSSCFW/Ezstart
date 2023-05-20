from ezstart.database import alldata
from ezstart.database import maindb
from ezstart.function import attack
from ezstart.function import mine_system

import discord
from discord.ext import commands
import traceback
from datetime import datetime, timedelta, timezone


class GameCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = maindb.Database(self.bot)
        self.attack = attack.System(self.bot)
        self.mine_system = mine_system.System(self.bot)

    async def cog_before_invoke(self, ctx):
        ban = await self.db.ban_check(ctx)
        if not ban:
            raise commands.CommandError("条件が満たされていないためコマンドを実行できません。")

    @commands.command(aliases=["atk"])
    @commands.bot_has_permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True,
                                  manage_messages=True, read_message_history=True)
    async def attack(self, ctx):
        try:
            channel_id = ctx.channel.id
            user_id = ctx.author.id
            if user_id in alldata.stop_command or channel_id in alldata.channel_stop:
                return

            try:
                alldata.channel_stop.append(channel_id)
                await self.attack.attack_system(ctx, user_id, channel_id)
            finally:
                if channel_id in alldata.channel_stop:
                    alldata.channel_stop.remove(channel_id)
        except:
            return await alldata.error_send(ctx)

    @commands.command(aliases=["re", "rs"])
    @commands.bot_has_permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True,
                                  manage_messages=True, read_message_history=True)
    async def reset(self, ctx):
        try:
            channel_id = ctx.channel.id
            get_battle = await self.db.fetchrow("SELECT 0 FROM channel_join WHERE channel_id=?", (channel_id,))
            if get_battle:
                await self.attack.next_battle(ctx, channel_id, False, 0, False)
            else:
                await ctx.reply(embed=discord.Embed(description="```diff\n+ このチャンネルで戦闘はしていません。```"))
        except:
            return await alldata.error_send(ctx)

    @commands.command()
    @commands.bot_has_permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True,
                                  manage_messages=True, read_message_history=True)
    async def mine(self, ctx):
        try:
            cool_time = 3
            if ctx.author.id in alldata.mine_cool_time:
                difference = (datetime.now() - alldata.mine_cool_time[ctx.author.id]).total_seconds()
                if difference < cool_time:
                    msg = discord.Embed(
                        description=f"{ctx.author.mention}:{cool_time - difference:.3f}秒後にそのコマンドを使用できます！",
                        color=0xC41415)
                    return await ctx.send(embed=msg)
            alldata.mine_cool_time[ctx.author.id] = datetime.now()
            await self.mine_system.mine(ctx, cool_time)
        except:
            return await alldata.error_send(ctx)


async def setup(bot: commands.Bot):
    await bot.add_cog(GameCommand(bot))
