from ezstart.database import alldata
from ezstart.database import maindb

import discord
from discord.ext import commands
import random
import asyncio

enemies = alldata.enemies


def influence_value(original, tool_influence, place_influence):
    return original * (1+tool_influence*place_influence)


class System:
    def __init__(self, bot):
        self.bot = bot
        self.db = maindb.Database(self.bot)

    async def mine(self, ctx, cool_time):
        try:
            user_id = ctx.author.id
            user_name = ctx.author.name
            channel_id = ctx.channel.id
            mine_msg = ""
            tool_id = await self.db.get_equip(user_id, "tool")
            place = await self.db.get_place(channel_id)
            if tool_id not in alldata.can_mining.keys():
                return await ctx.reply("```diff\n- 無効なツールです！```")
            tool_info = alldata.can_mining[tool_id]
            if place not in tool_info["place"]:
                return await ctx.reply(embed=alldata.em("```diff\n- このツールでここは採掘できません！！```"))
            for item_type, item in alldata.place_mining[place].items():
                if not item:  # アイテムの設定がされてなかったら
                    continue  # 次のループへ
                for item_id, info in item.items():  # アイテムidとアイテムの獲得情報
                    min_count, max_count, probability, rank, get_fortune, count_fortune = info[0], info[1], info[2], info[3], info[4], info[5]
                    if tool_info["rank"] >= rank and random.random() < influence_value(probability, tool_info["get_luck"], get_fortune):
                        # 獲得する量
                        count = random.randint(int(influence_value(min_count, tool_info["count_luck"], count_fortune)),
                                               int(influence_value(max_count, tool_info["count_luck"], count_fortune)))
                        if item_type == "item":
                            await self.db.give_item(user_id, item_id, count)
                            mine_msg += f"+ {alldata.items[item_id]}: {count}個\n"
                        if item_type == "material":
                            await self.db.give_material(user_id, item_id, count)
                            mine_msg += f"+ {alldata.materials[item_id]}: {count}個\n"
            embed = discord.Embed(
                description=f"```css\n[{alldata.items[tool_id]}] {alldata.places[place][0]}\n[採掘者:{user_name}]``````diff\n{mine_msg}```")
            result = await ctx.reply(embed=embed)
            if cool_time <= 0:
                return
            await asyncio.sleep(cool_time)
            return await result.add_reaction("👌")
        except:
            return await alldata.error_send(ctx)

