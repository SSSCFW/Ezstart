from ezstart.database import alldata
from ezstart.database import maindb

import discord
from discord.ext import commands
import random
import numpy as np

enemies = alldata.enemies


class System:
    def __init__(self, bot):
        self.bot = bot
        self.db = maindb.Database(self.bot)

    async def get_item_list(self, ctx, user_id, pg, max_pg):
        try:
            username = self.bot.get_user(user_id).name
            select = {"1": ["特殊", alldata.specials], "2": ["道具", alldata.tools], "3": ["武器", alldata.weapons], "4": ["薬物", alldata.potions]}

            # 指定したアイテムの辞書の最小idと最大idの範囲でアイテムを取得(負荷軽減のため範囲を絞る)
            my_items = await self.db.fetch("SELECT item_id, count FROM item WHERE user_id=? and "
                                           "item_id >= ? and item_id <= ? ORDER BY item_id",
                                           (user_id, min(select[pg][1]), max(select[pg][1])))
            my_items = list(map(lambda x: x if x[0] in select[pg][1].keys() else None, my_items))  # 辞書に存在しないidをNoneに置き換える
            my_items = list(filter(lambda x: x is not None, my_items))  # Noneを削除
            item_list = "\n".join("[{}] | {}個".format(select[pg][1][i[0]], i[1]) for i in my_items)
            embed = discord.Embed(title=f"{username}の持っているアイテム [{select[pg][0]}]",
                                  description=f"`{pg}/{max_pg}`\n```css\n------------------------------\n{item_list}```")
            return embed
        except:
            return await alldata.error_send(ctx)

    async def get_material_list(self, ctx, user_id, pg, max_pg):
        try:
            username = self.bot.get_user(user_id).name
            my_materials = await self.db.fetch("SELECT material_id, count FROM material WHERE user_id=? ORDER BY material_id", (user_id,))
            item_list = "\n".join("+ {} : {}個".format(alldata.materials[i[0]], i[1]) for i in my_materials)
            embed = discord.Embed(title=f"{username}の持っている素材",
                                  description=f"`{pg}/{max_pg}`\n```diff\n------------------------------\n{item_list}```")
            return embed
        except:
            return await alldata.error_send(ctx)

    async def get_skill_list(self, ctx, user_id, pg, max_pg):
        try:
            username = self.bot.get_user(user_id).name
            my_skills = await self.db.fetch("SELECT skill_id, count FROM skill WHERE user_id=? ORDER BY skill_id", (user_id,))
            item_list = "\n".join("# {} : Lv.{}".format(alldata.skills[i[0]], i[1]) for i in my_skills)
            embed = discord.Embed(title=f"{username}の持っているスキル",
                                  description=f"`{pg}/{max_pg}`\n```md\n------------------------------\n{item_list}```")
            return embed
        except:
            return await alldata.error_send(ctx)

    async def fish(self, ctx, user_id, user_id2=None):
        user_name = ctx.author.name
        if not user_id2:
            user_id2 = user_id
        battle = await self.db.fetchrow("SELECT channel_id FROM channel_join WHERE user_id=?", (user_id2,))
        if not battle:
            return f"{user_name}さん、<@{user_id2}>さんは戦闘に参加していませんよ？"
        if not await self.db.consume_item(user_id, 10000, 1):
            return f"{user_name}さんはそのアイテムを持っていません！"
        player_hp = await self.db.player_max_hp(user_id2)
        await self.db.call_db().execute("UPDATE channel_join SET hp=? WHERE user_id=?", (player_hp, user_id2))
        return f"{user_name}はお魚様の力を使い<@{user_id2}>を全回復させた！\n(短縮形: f)"

    async def potion_effect(self, ctx, user_id, item_id, effect_id, level, count, add_text=""):
        user_name = ctx.author.name
        if not await self.db.consume_item(user_id, item_id, 1):
            return f"{user_name}さんはそのアイテムを持っていません！"
        await self.db.give_effect(user_id, effect_id, level, count)
        return f"{user_name}は{alldata.effects[effect_id]}Lv.{level}({count}ターン)を付与した！{add_text}"
