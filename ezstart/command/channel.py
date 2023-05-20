from ezstart.database import alldata
from ezstart.database import maindb
from ezstart.function import attack

import discord
from discord.ext import commands
import traceback
import asyncio

batu = "🚫"


class ChannelCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = maindb.Database(self.bot)
        self.attack = attack.System(bot)

    async def cog_before_invoke(self, ctx):
        ban = await self.db.ban_check(ctx)
        if not ban:
            raise commands.CommandError("条件が満たされていないためコマンドを実行できません。")

    @commands.command()
    @commands.bot_has_permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True,
                                  manage_messages=True, read_message_history=True)
    async def change(self, ctx):
        try:
            channel_id = ctx.channel.id
            if ctx.author.id in alldata.stop_command: return
            if ctx.channel.id in alldata.channel_stop: return
            get_enemy = await self.db.get_enemy_id(channel_id)

            monster = alldata.enemies[get_enemy]
            read = monster["rank"]
            place = await self.db.get_place(channel_id)
            alldata.places.setdefault(place, ["存在しない場所", 9**15])
            place_name = alldata.places[place][0]
            if read not in ["★☆☆☆☆☆☆", "★★☆☆☆☆☆", "★★★☆☆☆☆", "★★★★☆☆☆"]:
                return await ctx.send(f"```diff\n+ 現在は「{place_name}」\n- ★5以上の敵がいる場合移動はできません！```")

            alldata.stop_command.append(ctx.author.id)
            alldata.channel_stop.append(channel_id)
            enemy_level = await self.db.get_enemy_level(channel_id)

            ch = ""
            showed_next = False
            select = {}
            for i, (place_id, info) in enumerate(alldata.places.items()):
                if info[1] == -2:
                    continue
                elif enemy_level >= info[1]:
                    select[str(i + 1)] = place_id
                    text = f"敵Lv {info[1]}"
                    if info[1] == 1:
                        text = "なし"
                    ch += f"[{i + 1}:{info[0]}] 条件| {text}\n"
                else:
                    if not showed_next:
                        showed_next = True
                        text = f"敵Lv {info[1]}"
                        ch += f"[？？？] 条件| {text}"
            embed = discord.Embed(title=f"現在は「{place_name}」", description=f"```css\n{ch}```")
            embed.set_footer(text="行きたい場所の数値を送信してください。", )
            msg = await ctx.reply(embed=embed)

            def c(b):
                return b.author.id == ctx.author.id
            while True:
                try:
                    guess = await self.bot.wait_for("message", timeout=60, check=c)
                except asyncio.TimeoutError:
                    alldata.stop_command.remove(ctx.author.id)
                    alldata.channel_stop.remove(channel_id)
                    return await msg.add_reaction(batu)
                ct = guess.content
                if ct == "x":
                    alldata.stop_command.remove(ctx.author.id)
                    alldata.channel_stop.remove(channel_id)
                    return await msg.add_reaction(batu)
                if ct in select.keys():
                    select_id = select[ct]
                    embed = discord.Embed(description=f"```diff\n+ {alldata.places[select_id][0]}に移動しました。```")
                    await msg.edit(embed=embed)
                    await self.db.set_place(channel_id, select_id)
                    alldata.stop_command.remove(ctx.author.id)
                    alldata.channel_stop.remove(channel_id)
                    return await self.attack.next_battle(ctx, channel_id, level_up=True, level=0, only_embed=False)
        except:
            if ctx.author.id in alldata.stop_command:
                alldata.stop_command.remove(ctx.author.id)
            if ctx.channel.id in alldata.channel_stop:
                alldata.channel_stop.remove(ctx.channel.id)
            return await alldata.error_send(ctx)


async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelCommand(bot))
