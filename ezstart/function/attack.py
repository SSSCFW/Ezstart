from ezstart.database import alldata
from ezstart.database import maindb
from ezstart.acts import act_main

import discord
from discord.ext import commands
import random
import jmespath
import numpy as np

enemies = alldata.enemies


class System:
    def __init__(self, bot):
        self.bot = bot
        self.db = maindb.Database(self.bot)
        self.act_main = act_main.ActSystem(self.bot)

    async def attack_system(self, ctx, user_id, channel_id, act=None):
        try:
            player_hp, error_message = await self.db.join_battle(user_id, channel_id)
            if error_message:
                error_embed = discord.Embed(description=error_message, color=0xC41415)
                return await ctx.send(embed=error_embed)
            player_level = await self.db.get_player_level(user_id)
            enemy_level = await self.db.get_enemy_level(channel_id)
            enemy_id = await self.db.get_enemy_id(channel_id)
            enemy_img = enemies[enemy_id]["img"]
            user_name = self.bot.get_user(user_id).display_name
            enemy_name = enemies[enemy_id]["name"]
            process_message = []

            weapon = await self.db.get_equip(user_id, "weapon")
            skill = await self.db.get_equip(user_id, "skill")
            await self.weapon_effect(user_id, channel_id, weapon, skill)

            player_speed = await self.db.get_effect_level(user_id, 1)
            enemy_speed = await self.db.get_effect_level(channel_id, 1)

            enemy_speed_status = jmespath.search("status.base.speed", alldata.enemies[enemy_id])
            if not enemy_speed_status:
                enemy_speed_status = 1

            first_atk = False
            if player_level >= enemy_level*enemy_speed_status:
                first_atk = True
            if player_speed >= enemy_speed:
                first_atk = True

            total_loop = 0
            player_death = False
            player_win = False
            while total_loop < 2:
                if first_atk and not player_death:  # プレイヤーの攻撃
                    got_message, enemy_hp = await self.player_attack(ctx, user_id, user_name, channel_id, enemy_name, enemy_id, player_level, act)
                    process_message += got_message
                    if enemy_hp <= 0:
                        player_win = True
                        process_message.append(f"+ {enemy_name}を倒した！")
                        break
                    first_atk = False
                    total_loop += 1
                    continue
                if not first_atk:  # 敵の攻撃
                    got_message, player_hp = await self.enemy_attack(ctx, user_id, user_name, channel_id, enemy_name, enemy_id, enemy_level)
                    process_message += got_message
                    if player_hp <= 0:
                        player_death = True
                        process_message.append(f"- {user_name}は倒れてしまった。。。")
                    first_atk = True
                    total_loop += 1
                    continue
                break  # 無限ループ対策
            if player_win:
                win_msg = await self.win_message(ctx, user_id, channel_id, enemy_name, enemy_id, enemy_level)
                total_msg = f"```diff\n{'\n'.join(process_message)}```{win_msg}"
                if len(total_msg) >= 1850:
                    print(f"勝利メッセージ上限: {total_msg}文字\n{total_msg}\n----------")
                    total_msg = "```diff\n文字数が上限を超えました。```"
                embed_process = discord.Embed(description=total_msg)
                next_msg = await self.next_battle(ctx, channel_id, True, 1)
                win_embeds = [embed_process, next_msg]
                return await ctx.reply(embeds=win_embeds)
            player_hp = await self.db.get_player_hp(user_id)
            player_max_hp = await self.db.player_max_hp(user_id)
            player_tp = await self.db.get_player_tp(user_id)
            player_max_tp = await self.db.get_player_max_tp(user_id)
            enemy_hp = await self.db.get_enemy_hp(channel_id)
            enemy_max_hp = await self.db.enemy_max_hp(channel_id)
            enemy_tp = await self.db.get_enemy_tp(channel_id)
            enemy_max_tp = await self.db.get_enemy_max_tp(channel_id)
            player_effect_msg = await self.get_effect_msg(user_id)
            enemy_effect_msg = await self.get_effect_msg(channel_id)
            await self.db.remove_effect(user_id)
            await self.db.remove_effect(channel_id)
            enemy_des = f"```css\n[HP] {enemy_hp:,}/{enemy_max_hp:,}\n[TP] {enemy_tp:,}/{enemy_max_tp}``````js\n{enemy_effect_msg}```"
            player_des = f"```css\n[HP] {player_hp:,}/{player_max_hp:,}\n[TP] {player_tp:,}/{player_max_tp}``````js\n{player_effect_msg}```"
            embed_status = discord.Embed()
            embed_status.add_field(name=f"{user_name}: Lv.{player_level:,}", value=player_des)
            embed_status.add_field(name=f"{enemy_name}: Lv.{enemy_level:,}", value=enemy_des)
            embed_status.set_thumbnail(url=enemy_img)
            embed_process = discord.Embed(description=f"```diff\n{'\n'.join(process_message)}```")
            embeds = [embed_status, embed_process]
            return await ctx.reply(embeds=embeds)
        except:
            return await alldata.error_send(ctx)

    async def get_effect_msg(self, target_id):
        effect_list = await self.db.fetch(
            "SELECT effect_id, level, count FROM effect WHERE target_id=$1 ORDER BY effect_id", (target_id,))
        special_count = {-2: "∞", -3: "∞終"}
        effect_msg = "{}".format(
            "\n".join("['{}'][Lv{}:#{}ターン]".format(alldata.effects[x[0]], x[1], special_count.setdefault(x[2], x[2] - 1)) for x in effect_list))
        if not effect_msg:
            effect_msg = " "
        return effect_msg

    async def player_attack(self, ctx, user_id, user_name, channel_id, enemy_name, enemy_id, player_level, act=None):
        try:
            rand = random.random()
            enemy_max_hp = await self.db.enemy_max_hp(channel_id)
            atk = await self.get_player_attack_power(user_id, player_level, rand, enemy_id)
            attack_msg = []
            crit_msg = ""

            if act is None:
                attack_msg.append(await self.get_attack_message(user_id, user_name, enemy_name, atk, rand, False))
            else:
                attack_msg.append(await self.act_main.act_message(ctx, user_id, channel_id, atk, enemy_id, False, crit_msg, act))
                atk = 0 # act内で敵の体力を減らすため、減らした後の攻撃力を0にする
            # エフェクトメッセージ
            effect_msg = await self.get_effect_message(user_id, user_name, enemy_name, channel_id, True, enemy_max_hp)
            if effect_msg:
                attack_msg.append(effect_msg)
            enemy_hp = await self.db.change_enemy_hp(channel_id, atk)
            await self.db.add_player_tp(user_id, 1)
            return attack_msg, enemy_hp
        except:
            return await alldata.error_send(ctx)

    async def get_player_attack_power(self, user_id, player_level, rand, enemy_id):
        dmg = 1
        weapon = await self.db.get_equip(user_id, "weapon")
        # := はセイウチ演算子 変数の代入と使用を同時に行える。
        if atk_level := await self.db.get_effect_level(user_id, 2):  # 攻撃力増加のエフェクトによる攻撃力増加
            level = atk_level
            dmg += 0.25 * level
        weapon_bonus = await alldata.we_atk(self.bot, user_id, weapon)
        plus = rand / 5 + 1
        atk = (player_level * plus + 35) * weapon_bonus * dmg
        return int(atk)

    async def enemy_attack(self, ctx, user_id, user_name, channel_id, enemy_name, enemy_id, enemy_level):
        try:
            rand = random.random()
            player_max_hp = await self.db.player_max_hp(user_id)
            atk = await self.get_enemy_attack_power(channel_id, enemy_level, rand, enemy_id)
            attack_msg = []
            acts = jmespath.search("status.acts", alldata.enemies[enemy_id])
            act_id = None
            if acts:
                tp = await self.db.get_enemy_tp(channel_id)
                act_list = [int(k) for k, v in acts.items() if random.random() < v["percent"] and tp >= alldata.acts_data[int(k)]["tp"]]
                if act_list:
                    act_id = random.choice(act_list)
            if act_id is None:
                attack_msg.append(await self.get_attack_message(channel_id, enemy_name, user_name, atk, rand, True))
            if act_id:
                attack_msg.append(await self.act_main.act_message(ctx, user_id, channel_id, atk, enemy_id, True, "", act_id))
                atk = 0  # act内で敵の体力を減らすため、減らした後の攻撃力を0にする
            await self.enemy_attack_effect(enemy_id, channel_id, user_id)
            # エフェクトメッセージ
            effect_msg = await self.get_effect_message(channel_id, enemy_name, user_name, user_id, False, player_max_hp)
            if effect_msg:
                attack_msg.append(effect_msg)
            player_hp = await self.db.change_player_hp(user_id, atk)
            await self.db.add_enemy_tp(channel_id, 1)
            return attack_msg, player_hp
        except:
            return await alldata.error_send(ctx)

    async def get_enemy_attack_power(self, channel_id, enemy_level, rand, enemy_id):
        dmg = 1
        if atk_level := await self.db.get_effect_level(channel_id, 2):
            level = atk_level
            dmg += 0.25 * level
        status = jmespath.search("status.base.atk", alldata.enemies[enemy_id])
        if not status:
            status = 1
        plus = 2 + rand
        atk = (enemy_level * plus + 5.3) * dmg * status
        return int(atk)

    async def get_attack_message(self, my_id, my_name, target_name, atk, rand, enemy):
        msg = ""
        pos = "+"
        neg = "-"
        atk_msg = "与えた！"
        if enemy:
            pos = "-"
            neg = "+"
            atk_msg = "受けた。"
        if atk == 0:
            msg += f"{neg} {my_name}の攻撃は当たらなかった。。。"
        else:
            msg += f"{pos} {my_name}の攻撃！{atk:,}のダメージを{atk_msg}"
        return msg

    async def get_effect_message(self, my_id, my_name, target_name, target_id, enemy, enemy_max_hp):
        msg = ""
        pos = "-"
        neg = "+"
        if enemy:  # enemyがTrue = プレイヤーの攻撃で与えるエフェクトダメージ
            pos = "+"
            neg = "-"
        if level := await self.db.get_effect_level(target_id, 3):  # 毒によるダメージ
            dmg = int((enemy_max_hp / 95) * level)
            await self.db.change_hp(target_id, dmg, enemy)
            msg += f"{pos} {target_name}は毒で{dmg:,}ダメージを受けた。"
        return msg

    async def weapon_effect(self, user_id, channel_id, weapon, skill):
        if weapon in alldata.weapons_data:
            status = alldata.weapons_data[weapon]["status"]
            target_effects = [
                ("atk_enemy_effect", channel_id),
                ("atk_me_effect", user_id)
            ]
            for target in target_effects:
                if target[0] in status:
                    target_id = target[1]
                    data = status[target[0]]
                    for effect, value in data.items():
                        if random.random() >= value["percent"]:
                            continue
                        if value["check"] and await self.db.get_effect_count(target_id, effect):
                            continue
                        await self.db.give_effect(target_id, effect, value["level"], value["count"], value["add_level"], value["add_count"])

        if skill == 1:
            if not await self.db.get_effect_count(user_id, 3):
                level = await self.db.get_skill_count(user_id, 1)
                await self.db.give_effect(channel_id, 3, level, 1)

    async def enemy_effect(self, enemy_id, channel_id):  # 敵が出現したときに付与されるエフェクト
        effects = jmespath.search("status.first_effect", alldata.enemies[enemy_id])
        if effects:
            effects_list = []
            for effect, value in effects.items():
                effects_list.append((channel_id, int(effect), value["level"], value["count"]))
            if effects_list:
                await self.db.give_effect_many(effects_list)

    async def enemy_attack_effect(self, enemy_id, channel_id, user_id):  # 敵が攻撃したときに付与されるエフェクト
        effects = jmespath.search("status.atk_effect", alldata.enemies[enemy_id])
        if effects:
            effects_list = []
            for effect, value in effects.items():
                if random.random() < value["percent"]:
                    target_id = user_id
                    if value["target"] == "me":
                        target_id = channel_id
                    if value["check"] and await self.db.get_effect_count(target_id, int(effect)):
                        continue
                    effects_list.append((target_id, int(effect), value["level"], value["count"]))
            if effects_list:
                await self.db.give_effect_many(effects_list)

    async def win_message(self, ctx, user_id, channel_id, enemy_name, enemy_id, enemy_level):
        members = await self.db.fetch("SELECT * FROM channel_join WHERE channel_id=$1", (channel_id,))
        exp_msg = lv_up_msg = get_item_msg = ""
        enemy_rank = enemies[enemy_id]["rank"]
        rank_exp = {
            "★★☆☆☆☆☆": 1.5,
            "★★★☆☆☆☆": 5,
            "★★★★☆☆☆": 10,
            "★★★★★☆☆": 50,
            "★★★★★★☆": 100,
            "★★★★★★★": 500,
        }
        rank_exp.setdefault(enemy_rank, 1)  # 存在しないランクは1倍
        status = jmespath.search("status", alldata.enemies[enemy_id])
        exp_mpl = rank_exp[enemy_rank]
        if "exp" in status:
            exp_mpl = status["exp"]
        place = await self.db.get_place(channel_id)
        for member in members:
            member_id = member[1]
            member_name = self.bot.get_user(member_id).name

            exp = int(enemy_level * exp_mpl)
            exp_msg += f"' {member_name}は{exp:,}expを獲得した。'\n"
            lv_up_msg += await self.db.add_exp(member_id, exp)  # 経験値をプレイヤーに付与してレベルアップのメッセージを取得

            #   素材獲得の処理
            # [素材id, 個数, 条件]
            get_material_list = [
                [1, 1, random.random() < 0.03 and place == 1],  # 森林で3%の確率で木材が落ちる
                [6, 1, random.random() < 0.03],  # どこでも3%
                [7, 1, random.random() < 0.03],
                [8, 1, enemy_id == 13],  # EzStartから確定で落ちる。
            ]
            material_np = np.array(get_material_list)  # numpyの配列に変換
            for i in material_np[material_np[:, 2] == 1]:  # 条件を満たすリストだけ抽出
                await self.db.give_material(member_id, i[0], i[1])
                if not get_item_msg:
                    get_item_msg = "\n"
                get_item_msg += f"'{member_name}は素材: {alldata.materials[i[0]]}を{i[1]}個手に入れた！'\n"
        process_msg = f"```js\n{exp_msg}\n{lv_up_msg}{get_item_msg}```"
        if len(process_msg) >= 1850:
            print(f"報酬メッセージ上限: {process_msg}文字\n{process_msg}\n----------")
            process_msg = "```diff\n+ 文字数が上限を超えました。```"
        await self.db.add_monster_count(user_id, 1)  # 倒した数
        return process_msg

    async def delete_effect_3(self, channel_id):
        channels = await self.db.fetch("SELECT user_id FROM channel_join WHERE channel_id=$1 ORDER BY user_id DESC",
                                       (channel_id,))
        if not channels:
            return
        for user in channels:
            await self.db.execute("DELETE FROM effect WHERE target_id=$1 and count=-3", (user[0],))

    def get_next_enemy(self, place):
        # 通常の敵のリスト
        # 場所id: [敵リスト]
        table = {
            1: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            2: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            3: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        }
        table.setdefault(place, [1])  # 存在しない場所だったときのデフォルト値
        enemy_id = random.choice(table[place])  # リストからランダムで1つ取得

        # 特殊な敵
        if random.random() < 0.0005:  # 星7
            enemy_id = 13
        elif random.random() < 0.001:  # 星6
            enemy_id = 12
        elif random.random() < 0.005:  # 星5
            enemy_list = [14]
            if place in [2, 3]:  # 浅い洞窟と深い洞窟限定
                enemy_list.append(15)  # リストに値を追加
            enemy_id = random.choice(enemy_list)
        elif random.random() < 0.01:  # 星4
            enemy_id = 11
        elif random.random() < 0.05:  # 星3
            enemy_id = 0
        return enemy_id

    async def next_battle(self, ctx, channel_id, level_up=True, level=0, only_embed=True, enemy_id=-1):
        await self.delete_effect_3(channel_id)  # プレイヤーの∞終エフェクトを削除
        await self.db.execute("DELETE FROM channel_join WHERE channel_id=$1", (channel_id,))
        await self.db.set_enemy_tp(channel_id, 0, False)
        if level_up and enemy_id == -1:
            place = await self.db.get_place(channel_id)
            enemy_id = self.get_next_enemy(place)
            await self.db.execute("DELETE FROM effect WHERE target_id=$1", (channel_id,))  # 敵のエフェクトを削除
            await self.db.add_enemy_level(channel_id, level)
            await self.db.set_enemy_id(channel_id, enemy_id)
        else:
            await self.db.execute("DELETE FROM effect WHERE target_id=$1 and count=-3", (channel_id,))  # 敵の∞終エフェクトを削除
        if enemy_id != -1:
            await self.db.execute("DELETE FROM effect WHERE target_id=$1", (channel_id,))  # 敵のエフェクトを削除
            await self.db.set_enemy_id(channel_id, enemy_id)
        enemy_id = await self.db.get_enemy_id(channel_id)
        enemy_level = await self.db.get_enemy_level(channel_id)
        enemy_max_hp = await self.db.enemy_max_hp(channel_id)
        await self.enemy_effect(enemy_id, channel_id)
        await self.db.set_enemy_hp(channel_id, enemy_max_hp)
        enemy_name = enemies[enemy_id]["name"]
        enemy_rank = enemies[enemy_id]["rank"]
        enemy_img = enemies[enemy_id]["img"]
        embed = discord.Embed(
            description=f'```css\n[{enemy_name}]```\n```py\n"Level": "{enemy_level:,}"\n"HP": "{enemy_max_hp:,}"\n"{enemy_rank}"```')
        embed.set_image(url=enemy_img)
        if only_embed:
            return embed
        return await ctx.reply(embed=embed)
