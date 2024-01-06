from ezstart.database import alldata
from ezstart.database import maindb
from ezstart.function import attack

import discord
from discord.ext import commands
import traceback
import asyncio
import math

batu = "🚫"


class OtherCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = maindb.Database(self.bot)
        self.attack = attack.System(bot)

    async def cog_before_invoke(self, ctx):
        ban = await self.db.ban_check(ctx)
        if not ban:
            raise commands.CommandError("条件が満たされていないためコマンドを実行できません。")

    @commands.command(aliases=["st"])
    @commands.bot_has_permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True,
                                  manage_messages=True, read_message_history=True)
    async def status(self, ctx, user: discord.User = None):
        try:
            if user and ctx.author.id not in alldata.admin:
                return await ctx.send(alldata.cmd_error_msg)
            if not user:
                user = ctx.author
            user_id = user.id
            player_exp = await self.db.get_exp(user_id)
            player_level = await self.db.get_player_level(user_id)
            player_hp = await self.db.player_max_hp(user_id)
            atk = await self.attack.get_player_attack_power(user_id, player_level, 0, 1)
            enemy_count = await self.db.get_monster_count(user_id)
            next_level = (player_level + 1) ** 2 - player_exp
            rank = list(await self.db.fetchrow(
                """SELECT 
                    (SELECT Count(0) FROM player WHERE player.exp > player1.exp) + 1 AS rank 
                    FROM player AS player1 WHERE user_id=?""", (user_id,)))[0]
            st_msg = f"```css\n[レベル] {player_level:,}\n[体力] {player_hp:,}\n[攻撃力] {atk:,}\n[経験値] {player_exp:,}\n" \
                     f"[次のレベルまで] {next_level:,}\n[倒した数] {enemy_count:,}体\n[ランク] {rank:,}位```"
            embed = discord.Embed(title=f"{user.name}", description=f"{st_msg}")
            embed.set_thumbnail(url=user.display_avatar)
            await ctx.send(embed=embed)
        except:
            return await alldata.error_send(ctx)

    @commands.command(aliases=["es", "effectstatus"])
    @commands.bot_has_permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True,
                                  manage_messages=True, read_message_history=True)
    async def effect_status(self, ctx, user: discord.User = None):
        try:
            des = ""
            user_id = ctx.author.id
            channel_id = ctx.channel.id
            if user:
                if ctx.author.id in alldata.admin:
                    user_id = user.id
                else:
                    return await ctx.send(alldata.cmd_error_msg)
            user_name = self.bot.get_user(user_id)
            player_level = await self.db.get_player_level(user_id)
            battle = await self.db.fetchrow("SELECT channel_id FROM channel_join WHERE user_id=?", (user_id,))
            if not battle:
                des = "※このプレイヤーが戦闘に参加していなかったためモンスターはコマンドを打ったチャンネルの敵です。"
            if battle:
                channel_id = battle[0]

            player_max_hp = await self.db.player_max_hp(user_id)
            player_hp = await self.db.get_player_hp(user_id)
            if not player_hp and player_hp != 0:
                player_hp = player_max_hp

            enemy_id = await self.db.get_enemy_id(channel_id)
            enemy_level = await self.db.get_enemy_level(channel_id)
            enemy_hp = await self.db.get_enemy_hp(channel_id)
            enemy_max_hp = await self.db.enemy_max_hp(channel_id)

            enemy_img = alldata.enemies[enemy_id]["img"]
            enemy_name = alldata.enemies[enemy_id]["name"]

            player_effect_msg = await self.attack.get_effect_msg(user_id)
            enemy_effect_msg = await self.attack.get_effect_msg(channel_id)

            embed_enemy = discord.Embed(description=f"**{enemy_name}:  Lv.{enemy_level:,}**```css\n[HP] {enemy_hp:,}/{enemy_max_hp:,}```"
                                                    f"```js\n{enemy_effect_msg}```")
            embed_enemy.set_thumbnail(url=enemy_img)

            embed_player = discord.Embed(description=f"**{user_name}:  Lv.{player_level:,}**```css\n[HP] {player_hp:,}/{player_max_hp:,}```"
                                                     f"```js\n{player_effect_msg}```")
            embed_player.set_thumbnail(url=ctx.author.display_avatar)

            embed = discord.Embed(description=f"```fix\n戦闘状況```\n{des}")

            embeds = [embed, embed_enemy, embed_player]
            return await ctx.reply(embeds=embeds)
        except:
            return await alldata.error_send(ctx)

    @commands.command()
    @commands.bot_has_permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True,
                                  manage_messages=True, read_message_history=True)
    async def prank(self, ctx):
        try:
            if ctx.author.id in alldata.stop_command: return
            alldata.stop_command.append(ctx.author.id)
            # DESC: 降順(値の大きい順)で取得
            players = await self.db.fetch("SELECT user_id, exp FROM player ORDER BY exp DESC")
            max_page = len(players) // 10 + 1

            async def rank(page):
                users = {}
                for player in players[(page * 10) - 10:]:
                    user = self.bot.get_user(player[0])
                    player_exp = player[1]
                    if not user:
                        continue
                    player_level = int(math.sqrt(player_exp))
                    if user.id not in users:
                        users[user.id] = [user.name, player_level]
                    if len(users) >= 10: break
                rank_msg = "\n".join("{:,}位：{} (Lv{:,})".format(i + 1 + ((page * 10) - 10), a[0], a[1]) for i, a in enumerate(users.values()))
                if len(rank_msg) >= 1850:
                    rank_msg = "文字数制限を超えたため表示できません。"
                return rank_msg

            get_rank_msg = await rank(1)
            embed = discord.Embed(title=f"**プレイヤーレベルのランキング**", description=f"```{get_rank_msg}```")
            embed.set_footer(text=f"1/{max_page} ページ数を送信してください。(x:処理停止)", )
            msg = await ctx.send(embed=embed)
            while True:
                def c(b):
                    return b.author.id == ctx.author.id

                try:
                    guess = await self.bot.wait_for("message", timeout=120, check=c)
                except asyncio.TimeoutError:
                    alldata.stop_command.remove(ctx.author.id)
                    return await msg.add_reaction(batu)
                if guess.content == "x":
                    alldata.stop_command.remove(ctx.author.id)
                    return await msg.add_reaction(batu)
                if guess.content.isdigit():
                    count = int(guess.content)
                    if 0 < count <= max_page:
                        await alldata.delete(ctx)
                        get_rank_msg = await rank(count)
                        embed = discord.Embed(title=f"**プレイヤーレベルのランキング**", description=f"```{get_rank_msg}```")
                        embed.set_footer(text=f"{count}/{max_page} ページ数を送信してください。(x:処理停止)", )
                        await msg.edit(embed=embed)
                    else:
                        continue
        except:
            if ctx.author.id in alldata.stop_command:
                alldata.stop_command.remove(ctx.author.id)
            return await alldata.error_send(ctx)

    @commands.command()
    @commands.bot_has_permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True,
                                  manage_messages=True, read_message_history=True)
    async def srank(self, ctx):
        try:
            if ctx.author.id in alldata.stop_command: return
            alldata.stop_command.append(ctx.author.id)
            # ASC: 昇順(値の小さい順)で取得 | 敢えて降順ではなく昇順で取得している。
            channels = await self.db.fetch("SELECT channel_id, enemy_level FROM channel_enemy ORDER BY enemy_level ASC")
            max_page = len(channels) // 10 + 1

            # map関数でチャンネルIDをguildに変換。存在しないチャンネルIDはNoneにする。
            channel_to_guild = tuple(map(lambda x: (self.bot.get_channel(x[0]).guild if self.bot.get_channel(x[0]) else None, x[1]), channels))
            # 辞書にして重複を削除してタプルに変換(二次元配列の最初のインデックス0がキー、1が値になる。辞書のキーは重複できない性質を利用。最初に昇順で取得したのは最後に見つかった重複キーの値を使用するから。)
            channels = tuple(dict(channel_to_guild).items())
            # Noneを削除
            channels = list(filter(lambda x: x[0], channels))
            # レベルの降順に整理
            channels.sort(reverse=True, key=lambda x: x[1])

            async def rank(page):
                guilds = {}
                for channel in channels[(page * 10) - 10:]:
                    guild = channel[0]
                    enemy_level = channel[1]
                    if guild.id not in guilds:
                        guilds[guild.id] = [guild.name, enemy_level]
                    if len(guilds) >= 10:
                        break
                rank_msg = "\n".join("{:,}位：{} (Lv{:,})".format(i + 1 + ((page * 10) - 10), a[0], a[1]) for i, a in enumerate(guilds.values()))
                if len(rank_msg) >= 1850:
                    rank_msg = "文字数制限を超えたため表示できません。"
                return rank_msg

            get_rank_msg = await rank(1)
            embed = discord.Embed(title=f"**サーバーランキング**", description=f"```{get_rank_msg}```")
            embed.set_footer(text=f"1/{max_page} ページ数を送信してください。(x:処理停止)", )
            msg = await ctx.send(embed=embed)
            while True:
                def c(b):
                    return b.author.id == ctx.author.id

                try:
                    guess = await self.bot.wait_for("message", timeout=120, check=c)
                except asyncio.TimeoutError:
                    alldata.stop_command.remove(ctx.author.id)
                    return await msg.add_reaction(batu)
                if guess.content == "x":
                    alldata.stop_command.remove(ctx.author.id)
                    return await msg.add_reaction(batu)
                if guess.content.isdigit():
                    count = int(guess.content)
                    if 0 < count <= max_page:
                        await alldata.delete(ctx)
                        get_rank_msg = await rank(count)
                        embed = discord.Embed(title=f"**サーバーランキング**", description=f"```{get_rank_msg}```")
                        embed.set_footer(text=f"{count}/{max_page} ページ数を送信してください。(x:処理停止)", )
                        await msg.edit(embed=embed)
                    else:
                        continue
        except:
            if ctx.author.id in alldata.stop_command:
                alldata.stop_command.remove(ctx.author.id)
            return await alldata.error_send(ctx)


async def setup(bot: commands.Bot):
    await bot.add_cog(OtherCommand(bot))
