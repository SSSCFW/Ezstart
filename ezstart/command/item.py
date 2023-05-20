from ezstart.database import alldata
from ezstart.database import maindb
from ezstart.function import item_system

import discord
from discord.ext import commands
import traceback
import asyncio

batu = "🚫"


class ItemCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = maindb.Database(self.bot)
        self.item = item_system.System(bot)

    async def cog_before_invoke(self, ctx):
        ban = await self.db.ban_check(ctx)
        if not ban:
            raise commands.CommandError("条件が満たされていないためコマンドを実行できません。")

    @commands.command(aliases=["p"])
    @commands.bot_has_permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True,
                                  manage_messages=True, read_message_history=True)
    async def pocket(self, ctx, user: discord.User = None):
        try:
            user_name = ctx.author.name
            user_id = ctx.author.id
            if user_id in alldata.stop_command:
                return
            if user:
                if ctx.author.id in alldata.admin:
                    user_id = user.id
                    user_name = user.name
                else:
                    return await ctx.reply(alldata.cmd_error_msg)

            max_page = 6
            main_embed = discord.Embed(title=f"{user_name}",
                                       description=f"`0/{max_page}`\n```css\n"
                                                   f"[0] 目次\n[1] アイテム|特殊\n[2] アイテム|道具\n[3] アイテム|武器\n[4] アイテム|薬物\n"
                                                   f"[5] 素材\n[6] スキル```")
            main_embed.set_footer(text="ページ数を送信してください。(x で処理を止めます。)", )
            msg = await ctx.reply(embed=main_embed)

            def check(c):
                return c.author.id == ctx.author.id

            while True:
                try:
                    guess = await self.bot.wait_for("message", timeout=60, check=check)
                except asyncio.TimeoutError:
                    return await msg.add_reaction(batu)
                if guess.content == "x":
                    return await msg.add_reaction(batu)
                if guess.content == "0":
                    await msg.edit(embed=main_embed)
                    await alldata.delete(ctx)
                if guess.content in list("1234"):
                    embed = await self.item.get_item_list(ctx, user_id, guess.content, max_page)
                    embed.set_footer(text="ページ数を送信してください。(x で処理を止めます。)", )
                    await msg.edit(embed=embed)
                    await alldata.delete(ctx)
                if guess.content == "5":
                    embed = await self.item.get_material_list(ctx, user_id, guess.content, max_page)
                    embed.set_footer(text="ページ数を送信してください。(x で処理を止めます。)", )
                    await msg.edit(embed=embed)
                    await alldata.delete(ctx)
                if guess.content == "6":
                    embed = await self.item.get_skill_list(ctx, user_id, guess.content, max_page)
                    embed.set_footer(text="ページ数を送信してください。(x で処理を止めます。)", )
                    await msg.edit(embed=embed)
                    await alldata.delete(ctx)
        except:
            return await alldata.error_send(ctx)

    @commands.command()
    @commands.bot_has_permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True,
                                  manage_messages=True, read_message_history=True)
    async def use(self, ctx, item_name, user: discord.User = None):
        try:
            user_id = ctx.author.id
            if item_name in ["魚", "f"]:
                if not user:
                    user = ctx.author
                user_id2 = user.id
                text = await self.item.fish(ctx, user_id, user_id2)
                embed = discord.Embed(description=text)
                return await ctx.reply(embed=embed)
            if item_name in ["力のポーション", "p"]:
                text = await self.item.potion_effect(ctx, user_id, 1002, 2, 7, 8, "\n(短縮形: p)")
                embed = discord.Embed(description=text)
                return await ctx.reply(embed=embed)
            if item_name in ["俊敏のポーション", "s"]:
                text = await self.item.potion_effect(ctx, user_id, 1001, 1, 3, 15, "\n(短縮形: s)")
                embed = discord.Embed(description=text)
                return await ctx.reply(embed=embed)
        except:
            return await alldata.error_send(ctx)

    @commands.command(aliases=["we"])
    @commands.bot_has_permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True,
                                  manage_messages=True, read_message_history=True)
    async def weapon(self, ctx, number=None):
        try:
            user_id = ctx.author.id
            if user_id in alldata.stop_command:
                return
            alldata.stop_command.append(user_id)
            we_id = await self.db.get_equip(user_id, "weapon")
            we_list = "・0|なし\n"

            alldata.we_desc.setdefault(we_id, "--------------------------")
            we_description = f"{alldata.we_desc[we_id]}"

            alldata.items.setdefault(we_id, f"存在しないアイテム: {we_id}")
            equip_name = alldata.items[we_id]

            select = {"0": 0}
            for i, name in enumerate(alldata.weapons.keys()):
                if await self.db.get_item_count(user_id, name):
                    we_list += f"[{i + 1}:{alldata.items[name]}] | 熟練度-{await self.db.get_we_point(user_id, name)}\n"
                    select[str(i + 1)] = name

            async def equip(equip_id, said_msg=None):
                if user_id in alldata.stop_command:
                    alldata.stop_command.remove(user_id)
                if await self.db.get_item_count(user_id, equip_id) or equip_id == 0:
                    alldata.we_desc.setdefault(equip_id, "--------------------------")
                    await self.db.set_equip(user_id, equip_id, "weapon")
                    equip_embed = discord.Embed(
                        description=f"```diff\n+ 武器を「{alldata.items[equip_id]}」に変更しました。``````js\n{alldata.we_desc[equip_id]}```")
                    if said_msg:
                        return await said_msg.edit(embed=equip_embed)
                    return await ctx.reply(embed=equip_embed)

            if number:
                select.setdefault(str(number), 0)
                weapon = select[str(number)]
                return await equip(weapon)

            embed = discord.Embed(title=f"現在は「{equip_name}」", description=f"<@{user_id}>```css\n{we_list}``````js\n{we_description}```")
            embed.set_footer(text="数字を送信してください。(xで処理を終了)", )
            msg = await ctx.reply(embed=embed)

            while True:
                def c(b):
                    return b.author.id == ctx.author.id

                try:
                    guess = await self.bot.wait_for("message", timeout=60, check=c)
                except asyncio.TimeoutError:
                    alldata.stop_command.remove(user_id)
                    await msg.add_reaction(batu)
                    return
                ct = guess.content
                if ct == "x":
                    alldata.stop_command.remove(user_id)
                    return await msg.add_reaction(batu)
                if ct in select.keys():
                    alldata.stop_command.remove(ctx.author.id)

                    select.setdefault(ct, 0)
                    select_id = select[ct]
                    return await equip(select_id, msg)
        except:
            if ctx.author.id in alldata.stop_command:
                alldata.stop_command.remove(ctx.author.id)
            return await alldata.error_send(ctx)

    @commands.command()
    @commands.bot_has_permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True,
                                  manage_messages=True, read_message_history=True)
    async def skill(self, ctx, number=None):
        try:
            user_id = ctx.author.id
            if user_id in alldata.stop_command:
                return
            alldata.stop_command.append(user_id)
            skill_id = await self.db.get_equip(user_id, "skill")
            skill_list = "・0|なし\n"

            alldata.skills.setdefault(skill_id, f"存在しないスキル: {skill_id}")
            equip_name = alldata.skills[skill_id]

            select = {"0": 0}
            for i, name in enumerate(alldata.skills.keys()):
                if level := await self.db.get_skill_count(user_id, name):
                    skill_list += f"[{i}:{alldata.skills[name]}] | Lv.{level}\n"
                    select[str(i)] = name

            async def equip(equip_id, said_msg=None):
                if user_id in alldata.stop_command:
                    alldata.stop_command.remove(user_id)
                if await self.db.get_skill_count(user_id, equip_id) or equip_id == 0:
                    alldata.we_desc.setdefault(equip_id, "--------------------------")
                    await self.db.set_equip(user_id, equip_id, "skill")
                    equip_embed = discord.Embed(
                        description=f"```diff\n+ スキルを「{alldata.skills[equip_id]}」に変更しました。```")
                    if said_msg:
                        return await said_msg.edit(embed=equip_embed)
                    return await ctx.reply(embed=equip_embed)

            if number:
                alldata.stop_command.remove(user_id)
                select.setdefault(str(number), 0)
                skill = select[str(number)]
                return await equip(skill)

            embed = discord.Embed(title=f"現在は「{equip_name}」", description=f"<@{user_id}>```css\n{skill_list}```")
            embed.set_footer(text="数字を送信してください。(xで処理を終了)", )
            msg = await ctx.reply(embed=embed)

            while True:
                def c(b):
                    return b.author.id == ctx.author.id

                try:
                    guess = await self.bot.wait_for("message", timeout=60, check=c)
                except asyncio.TimeoutError:
                    alldata.stop_command.remove(user_id)
                    await msg.add_reaction(batu)
                    return
                ct = guess.content
                if ct == "x":
                    alldata.stop_command.remove(user_id)
                    return await msg.add_reaction(batu)
                if ct in select.keys():
                    alldata.stop_command.remove(ctx.author.id)

                    select.setdefault(ct, 0)
                    select_id = select[ct]
                    return await equip(select_id, msg)
        except:
            if ctx.author.id in alldata.stop_command:
                alldata.stop_command.remove(ctx.author.id)
            return await alldata.error_send(ctx)

    @commands.command()
    @commands.bot_has_permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True,
                                  manage_messages=True, read_message_history=True)
    async def tool(self, ctx, number=None):
        try:
            user_id = ctx.author.id
            if user_id in alldata.stop_command:
                return
            alldata.stop_command.append(user_id)
            tool_id = await self.db.get_equip(user_id, "tool")
            tool_list = "・0|なし\n"

            alldata.items.setdefault(tool_id, f"存在しないアイテム: {tool_id}")
            equip_name = alldata.items[tool_id]

            select = {"0": 0}
            for i, name in enumerate(alldata.tools.keys()):
                if await self.db.get_item_count(user_id, name):
                    tool_list += f"[{i + 1}:{alldata.items[name]}]\n"
                    select[str(i + 1)] = name

            async def equip(equip_id, said_msg=None):
                if user_id in alldata.stop_command:
                    alldata.stop_command.remove(user_id)
                if await self.db.get_item_count(user_id, equip_id) or equip_id == 0:
                    alldata.we_desc.setdefault(equip_id, "--------------------------")
                    await self.db.set_equip(user_id, equip_id, "tool")
                    equip_embed = discord.Embed(
                        description=f"```diff\n+ 道具を「{alldata.items[equip_id]}」に変更しました。```")
                    if said_msg:
                        return await said_msg.edit(embed=equip_embed)
                    return await ctx.reply(embed=equip_embed)

            if number:
                select.setdefault(str(number), 0)
                weapon = select[str(number)]
                return await equip(weapon)

            embed = discord.Embed(title=f"現在は「{equip_name}」", description=f"<@{user_id}>```css\n{tool_list}```")
            embed.set_footer(text="数字を送信してください。(xで処理を終了)", )
            msg = await ctx.reply(embed=embed)

            while True:
                def c(b):
                    return b.author.id == ctx.author.id

                try:
                    guess = await self.bot.wait_for("message", timeout=60, check=c)
                except asyncio.TimeoutError:
                    alldata.stop_command.remove(user_id)
                    await msg.add_reaction(batu)
                    return
                ct = guess.content
                if ct == "x":
                    alldata.stop_command.remove(user_id)
                    return await msg.add_reaction(batu)
                if ct in select.keys():
                    alldata.stop_command.remove(ctx.author.id)

                    select.setdefault(ct, 0)
                    select_id = select[ct]
                    return await equip(select_id, msg)
        except:
            if ctx.author.id in alldata.stop_command:
                alldata.stop_command.remove(ctx.author.id)
            return await alldata.error_send(ctx)

    @commands.command(aliases=["c"])
    @commands.bot_has_permissions(read_messages=True, send_messages=True, embed_links=True, add_reactions=True,
                                  manage_messages=True, read_message_history=True)
    async def craft(self, ctx):
        try:
            user_id = ctx.author.id
            alldata.stop_command.append(user_id)
            all_recipe = [
                ["最初から作れるアイテム", [
                    [1, "item", {  # 作成するアイテムid, 作成する種類(item, skill, material)
                        "item": {0: 0},  # 必要なアイテムid: 必要個数
                        "material": {1: 5},  # 必要素材
                        "skill": {0: 0}  # 必要スキル
                    },
                     "基本的なツルハシ。採掘で使用する。(toolで装備)"],  # アイテム説明
                    [2, "item", {
                        "item": {0: 0},
                        "material": {2: 5}
                    },
                     "石でできたツルハシ。さらに固いものを採掘できる。"],
                    [3, "item", {
                        "item": {0: 0},
                        "material": {3: 5}
                    },
                     "鉄でできたツルハシ。さらに固いものを採掘できる。"],
                    [10, "item", {
                        "item": {0: 0},
                        "material": {1: 50, 2: 30}
                    },
                     "森林で釣りができる。"],
                    [-1, "item", {
                        "item": {0: 0},
                        "material": {4: 64}
                    },
                     "武器がクラフトできるようになる。"],
                    [-2, "item", {
                        "item": {0: 0},
                        "material": {6: 16, 7: 16}
                    },
                     "ポーションがクラフトできるようになる。"],
                    ], True],  # このページを開ける条件
                ["武器(金床)", [
                    [101, "item", {  # 作成するアイテムid, 作成する種類(item, skill, material)
                        "item": {0: 0},  # 必要なアイテムid: 必要個数
                        "material": {1: 30}  # 必要素材
                    },
                     "木でできた剣。攻撃力が上昇する。weaponで装備。"],  # アイテム説明
                    [102, "item", {
                        "item": {0: 0},
                        "material": {2: 30}
                    },
                     "石でできた剣。攻撃力が上昇する。"],
                    [103, "item", {
                        "item": {101: 5},
                        "material": {4: 50, 8: 2}
                    },
                     "木でできた剣。攻撃力が上昇する。"],
                    [1, "skill", {
                        "item": {0: 0},
                        "material": {6: 50, 7: 50, 8: 1}
                    },
                     "相手に毒を付与するスキル。skillで装着。"]
                ], await self.db.get_item_count(user_id, -1)],  # このページを開ける条件(金床を所持していること)
                ["ポーション(醸造台)", [
                    [1001, "item", {  # 作成するアイテムid, 作成する種類(item, skill, material)
                        "item": {0: 0},  # 必要なアイテムid: 必要個数
                        "material": {6: 5}  # 必要素材
                    },
                     "移動速度が上昇する。(15ターン Lv.3)"],  # アイテム説明
                    [1002, "item", {
                        "item": {0: 0},
                        "material": {7: 5}
                    },
                     "攻撃力が上昇する。(8ターン Lv.7)"]
                ], await self.db.get_item_count(user_id, -2)],  # このページを開ける条件(醸造台を所持していること)
            ]
            max_page = len(all_recipe)
            all_page_msg = "\n".join("+ {}\n{}".format(i + 1, msg[0]) for i, msg in enumerate(all_recipe))
            main_embed = discord.Embed(title="レシピの目次",
                                       description=f"```diff\n{all_page_msg}\n\nx:処理停止```")
            main_embed.set_thumbnail(url=self.bot.user.display_avatar)
            main_embed.set_footer(text="ページ数を送信してください。(x で処理を止めます。)", )
            msg = await ctx.reply(embed=main_embed)

            def c(b):
                return b.author.id == ctx.author.id

            while True:
                try:
                    guess = await self.bot.wait_for("message", timeout=60, check=c)
                except asyncio.TimeoutError:
                    alldata.stop_command.remove(ctx.author.id)
                    return await msg.add_reaction(alldata.batu)
                if guess.content == "x":
                    alldata.stop_command.remove(ctx.author.id)
                    return await msg.add_reaction(alldata.batu)
                if guess.content == "r":
                    await alldata.delete(ctx)
                    await msg.edit(embed=main_embed)
                    continue
                ct = guess.content
                if ct.isdigit() and int(ct) in (range(1, len(all_recipe) + 1)):
                    page = int(ct)
                    recipe = all_recipe[page - 1][1]
                    title = all_recipe[page - 1][0]
                    await alldata.delete(ctx)
                    if not all_recipe[page - 1][2]:
                        embed = discord.Embed(title=f"{ct}/{max_page}",
                                              description=f"```diff\n- 必要なものが揃ってないためまだこのページは開けません！```")
                        embed.set_footer(text="ページ数を送信してください。(x:処理停止 r:目次に戻る)", )
                        await msg.edit(embed=embed)
                        continue

                    res = ""
                    for i, content in enumerate(recipe):  # レシピのアイテム一覧
                        material_list_msg = ""
                        for item_type, info in content[2].items():  # アイテムの種類とレシピの情報
                            for item_id, count in info.items():  # アイテムidとアイテムの情報
                                if item_id != 0:
                                    if item_type == "item":
                                        material_list_msg += f"・{alldata.items[item_id]} {count}個\n"
                                    if item_type == "material":
                                        material_list_msg += f"・{alldata.materials[item_id]} {count}個\n"
                                    if item_type == "skill":
                                        material_list_msg += f"・{alldata.skills[item_id]} Lv.{count}\n"
                        complete_item_type = alldata.items
                        if content[1] == "material":
                            complete_item_type = alldata.materials
                        if content[1] == "skill":
                            complete_item_type = alldata.skills
                        res += f"[{i + 1}:{complete_item_type[content[0]]}]\n{material_list_msg}\n{content[3]}\n"
                    embed = discord.Embed(title=title, description=f"```css\n{res}```")
                    embed.set_footer(text="作りたいアイテムの数値を送信してください。(x:処理停止 r:目次に戻る)", )
                    await msg.edit(embed=embed)
                    while True:
                        try:
                            guess2 = await self.bot.wait_for("message", timeout=60, check=c)
                        except asyncio.TimeoutError:
                            alldata.stop_command.remove(ctx.author.id)
                            return await msg.add_reaction(alldata.batu)
                        if guess2.content == "x":
                            alldata.stop_command.remove(ctx.author.id)
                            return await msg.add_reaction(alldata.batu)
                        if guess2.content == "r":
                            await alldata.delete(ctx)
                            await msg.edit(embed=main_embed)
                            break
                        if guess2.content.isdigit() and 0 < int(guess2.content) <= len(recipe):
                            await alldata.delete(ctx)
                            number = int(guess2.content)-1
                            create_msg = ""
                            need_item = []
                            for item_type, info in recipe[number][2].items():
                                for item_id, count in info.items():
                                    if item_id != 0:
                                        have_item, temp_msg = 0, ""
                                        if item_type == "item":
                                            select = alldata.items
                                            have_item = await self.db.get_item_count(user_id, item_id)
                                            temp_msg = f"+ {select[item_id]}: {count}個 | 所有:{have_item} 必要:{count}個\n"
                                        if item_type == "material":
                                            select = alldata.materials
                                            have_item = await self.db.get_material_count(user_id, item_id)
                                            temp_msg = f"+ {select[item_id]}: {count}個 | 所有:{have_item} 必要:{count}個\n"
                                        if item_type == "skill":
                                            select = alldata.skills
                                            have_item = await self.db.get_skill_count(user_id, item_id)
                                            temp_msg = f"+ {select[item_id]}: {count}個 | 所有:{have_item} 必要: Lv.{count}\n"
                                        if count > have_item:
                                            temp_msg = temp_msg.replace("+", "-")
                                        create_msg += temp_msg
                                        need_item.append(have_item // count)
                            max_count = min(need_item)
                            create_msg += f"\n\n最大{max_count}個作成可能。(all で全て作成)"
                            create_type = "item"
                            create_item = alldata.items
                            if recipe[number][1] == "material":
                                create_type = "material"
                                create_item = alldata.materials
                            if recipe[number][1] == "skill":
                                create_type = "skill"
                                create_item = alldata.skills
                            create_item_id = recipe[number][0]
                            await msg.edit(embed=alldata.em(f"```fix\n{create_item[create_item_id]}``````diff\n{create_msg}```"
                                                            f"```diff\n+ 作りたい個数を数字で送信してください。(1以上)```"))
                            while True:
                                try:
                                    craft_count = await self.bot.wait_for("message", timeout=60, check=c)
                                except asyncio.TimeoutError:
                                    alldata.stop_command.remove(ctx.author.id)
                                    return await msg.add_reaction(alldata.batu)
                                if craft_count.content == "x":
                                    alldata.stop_command.remove(ctx.author.id)
                                    return await msg.add_reaction(alldata.batu)
                                counts = max_count
                                if craft_count.content != "all":
                                    if not craft_count.content.isdigit():
                                        continue
                                    counts = int(craft_count.content)
                                await alldata.delete(ctx)
                                if counts < 1:
                                    continue
                                select_recipe = recipe[number]
                                material_msg = ""
                                ok_flag = True
                                for item_type, info in select_recipe[2].items():
                                    for item_id, count in info.items():
                                        if item_id != 0:
                                            select = alldata.items
                                            have_item, temp_msg, unit, unit2 = 0, "", "個", ""
                                            if item_type == "item":
                                                count = count * counts
                                                have_item = await self.db.get_item_count(user_id, item_id)
                                            if item_type == "material":
                                                count = count * counts
                                                select = alldata.materials
                                                have_item = await self.db.get_material_count(user_id, item_id)
                                            if item_type == "skill":
                                                count = count * counts
                                                select = alldata.skills
                                                have_item = await self.db.get_skill_count(user_id, item_id)
                                                unit = ""
                                                unit2 = "Lv."
                                            if have_item >= count:
                                                material_msg += f"+ {select[item_id]}: {unit2}{count}{unit} | " \
                                                                f"所有:{have_item} -> {unit2}{have_item - count}{unit}\n"
                                            else:
                                                material_msg += f"- {select[item_id]}: {unit2}{count}{unit} | " \
                                                                f"所有:{have_item} -> {unit2}{count - have_item}{unit}不足\n"
                                                ok_flag = False
                                material_msg += f"\n\n{counts}個作成"
                                if not ok_flag:
                                    alldata.stop_command.remove(ctx.author.id)
                                    embed = discord.Embed(
                                        description=f"```fix\n{create_item[create_item_id]}``````diff\n{material_msg}\n- 素材が不足しています。```")
                                    await msg.edit(embed=embed)
                                    return await msg.add_reaction(alldata.batu)
                                if ok_flag:
                                    embed = discord.Embed(
                                        description=f"```fix\n{create_item[create_item_id]}``````diff\n{material_msg}\n+ OK?```")
                                    embed.set_footer(text="ok: 確定 x:処理停止", )
                                    await msg.edit(embed=embed)
                                    while True:
                                        try:
                                            last_ok = await self.bot.wait_for("message", timeout=60, check=c)
                                        except asyncio.TimeoutError:
                                            alldata.stop_command.remove(ctx.author.id)
                                            return await msg.add_reaction(alldata.batu)
                                        if last_ok.content == "x":
                                            alldata.stop_command.remove(ctx.author.id)
                                            return await msg.add_reaction(alldata.batu)
                                        if last_ok.content == "ok":
                                            for item_type, info in select_recipe[2].items():
                                                if item_type == "item":
                                                    await self.db.consume_craft_item(user_id, info, counts)
                                                if item_type == "material":
                                                    await self.db.consume_craft_material(user_id, info, counts)
                                                if item_type == "skill":
                                                    await self.db.consume_craft_skill(user_id, info, counts)
                                            success = discord.Embed(
                                                description=f"```fix\n「{create_item[create_item_id]}」を{counts}個作りました。```")
                                            await msg.edit(embed=success)
                                            if create_type == "item":
                                                await self.db.give_item(user_id, create_item_id, counts)
                                            if create_type == "material":
                                                await self.db.give_material(user_id, create_item_id, counts)
                                            if create_type == "skill":
                                                await self.db.give_skill(user_id, create_item_id, counts)
                                            alldata.stop_command.remove(ctx.author.id)
                                            return await msg.add_reaction(alldata.batu)
        except:
            if ctx.author.id in alldata.stop_command:
                alldata.stop_command.remove(ctx.author.id)
            return await alldata.error_send(ctx)


async def setup(bot: commands.Bot):
    await bot.add_cog(ItemCommand(bot))
