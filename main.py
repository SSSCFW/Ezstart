from ezstart.database import alldata
from ezstart.database import maindb

import discord
import json
import traceback
from discord.ext import tasks
from discord.ext import commands
info = json.load(open("json/info.json", "r", encoding="utf-8_sig"))


class Main(commands.Bot):
    def __init__(self):
        Intents = discord.Intents.default()
        Intents.members = True
        Intents.message_content = True
        super().__init__(command_prefix=info["prefix"], intents=Intents, application_id=info["client_id"])
        self.bot = self
        self.db = None
        self.remove_command("help")  # helpコマンドを削除

    async def setup_hook(self):
        self.bot.connect_db = await maindb.connect_db()
        self.db = maindb.Database(self.bot)
        load_command = ["debug", "game", "item", "channel", "other"]
        for cmd in load_command:
            await self.load_extension(f"ezstart.command.{cmd}")

    @commands.Cog.listener()
    async def on_ready(self):
        print("Login!")
        print(self.user.id)
        print('------')
        await self.db.create_table()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        try:
            if isinstance(error, commands.CommandInvokeError):
                try:
                    msg = discord.Embed(title=f"エラー", description=f"{error}", color=0xC41415)
                    await ctx.reply(embed=msg)
                    print(f"error[{ctx.author.guild.name}: {ctx.author.name}: {ctx.message.content}]\n{error}\n----------")
                except RuntimeError:
                    print(traceback.format_exc())
            elif isinstance(error, commands.CommandError):
                return
            elif isinstance(error, commands.CommandOnCooldown):
                msg = discord.Embed(
                    description=f"{ctx.author.mention}:{error.retry_after:.2f}秒後にそのコマンドを使用できます！",
                    color=0xC41415)
                return await ctx.send(embed=msg)
            elif isinstance(error, commands.MissingPermissions):
                print(f"permission[{ctx.author.guild.name}: {ctx.author.name}: {ctx.message.content}]")
                msg = discord.Embed(title=f"エラー", description=f"必要な権限がないためエラーが発生しました。", color=0xC41415)
                msg.add_field(name="サーバー情報",
                              value=f"サーバーの名前:  {ctx.message.guild.name}\nサーバーのID:  {ctx.message.guild.id}",
                              inline=False)
                return await ctx.author.send(embed=msg)
            elif isinstance(error, commands.BotMissingPermissions):
                try:
                    return await ctx.send(embed=discord.Embed(description="権限が不足"))
                except:
                    return await ctx.author.send(embed=discord.Embed(description="権限が不足"))
        except discord.Forbidden:
            print(f"permission[{ctx.message.author.guild.name}: {ctx.message.author.name}: {ctx.message.content}]")
            msg = discord.Embed(title=f"エラー", description=f"必要な権限がないためエラーが発生しました。", color=0xC41415)
            msg.add_field(name="サーバー情報", value=f"サーバーの名前:  {ctx.message.guild.name}\nサーバーのID:  {ctx.message.guild.id}",
                          inline=False)
            return await ctx.author.send(embed=msg)


bot = Main()
bot.run(info["token"])
