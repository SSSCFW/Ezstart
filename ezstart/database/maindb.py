from ezstart.database import alldata

import math
import aiosqlite
import traceback
import os


async def connect_db():
    db_path = "../ezstart/ezstart.db"
    if not os.path.exists(db_path):
        open(db_path, mode="w")
    conn = await aiosqlite.connect(db_path)
    return conn


class Database:
    def __init__(self, bot):
        self.bot = bot
        self.main = self.bot.connect_db

    def call_db(self):
        return self.main

    async def fetchrow(self, sql, *place):
        main = self.main
        cur = await main.execute(sql, *place)
        row = await cur.fetchone()
        await cur.close()
        return row
    
    async def fetch(self, sql, *place):
        main = self.main
        cur = await main.execute(sql, *place)
        rows = await cur.fetchall()
        await cur.close()
        return rows

    async def create_table(self):
        cur = await self.main.cursor()
        # 敵(チャンネル)の基本状態
        await cur.execute("CREATE TABLE IF NOT EXISTS channel_enemy"
                          "(channel_id bigint, enemy_hp bigint, enemy_level bigint, enemy_id bigint, place bigint)")
        # プレイヤーの基本情報
        await cur.execute("CREATE TABLE IF NOT EXISTS player(user_id bigint, exp bigint, monster bigint, ban bigint)")
        # アイテム
        await cur.execute("CREATE TABLE IF NOT EXISTS item(user_id bigint, item_id bigint, count bigint, UNIQUE(user_id, item_id))")
        # 素材
        await cur.execute("CREATE TABLE IF NOT EXISTS material(user_id bigint, material_id bigint, count bigint, UNIQUE(user_id, material_id))")
        # スキル
        await cur.execute("CREATE TABLE IF NOT EXISTS skill(user_id bigint, skill_id bigint, count bigint, UNIQUE(user_id, skill_id))")
        # エフェクト プレイヤー(user)と敵(channel)の2つが使用する。
        # UNIQUE制約 同じ値が重複しないようにするため
        await cur.execute("CREATE TABLE IF NOT EXISTS effect(target_id bigint, effect_id bigint, level bigint, count bigint, "
                          "UNIQUE(target_id, effect_id))")
        # プレイヤーがチャンネルの戦闘に参加している時に使う
        await cur.execute("CREATE TABLE IF NOT EXISTS channel_join(channel_id bigint, user_id bigint, hp bigint)")
        # 装備品
        await cur.execute("CREATE TABLE IF NOT EXISTS equipment(user_id bigint, equip_id bigint, equip text)")
        # 武器の熟練度
        await cur.execute("CREATE TABLE IF NOT EXISTS weapon_point(user_id bigint, weapon_id bigint, point bigint)")
        await self.main.commit()
        await cur.close()

    async def get_effect_count(self, target_id, effect_id):  # エフェクトのターン数を取得
        current_count = await self.fetchrow("SELECT count FROM effect WHERE target_id=? and effect_id=?",
                                            (target_id, effect_id))
        if not current_count:
            return 0
        return current_count[0]

    async def get_effect_level(self, target_id, effect_id):  # エフェクトのレベルを取得
        current_count = await self.fetchrow("SELECT level FROM effect WHERE target_id=? and effect_id=?",
                                            (target_id, effect_id))
        if not current_count:
            return 0
        return current_count[0]

    async def give_effect(self, target_id, effect_id, level, count):
        main = self.main
        await main.execute("INSERT INTO effect VALUES(?,?,?,?)"
                           "ON CONFLICT(target_id, effect_id) DO "
                           "UPDATE SET level=excluded.level, count=excluded.count", (target_id, int(effect_id), int(level), int(count)))
        await main.commit()

    async def remove_effect(self, target_id, loop=1):
        main = self.main
        except_count = (-2, -3)
        await main.execute(f"UPDATE effect set count="
                           f"(CASE WHEN count-$1<0 THEN 0 ELSE count-$1 END) "
                           f"WHERE target_id=$2 and count not in {except_count}", (loop, target_id))
        await main.execute("DELETE FROM effect WHERE count=0 and target_id=?", (target_id, ))
        await main.commit()

    async def delete_effect(self, target_id, effect_id):
        main = self.main
        await main.execute("DELETE FROM effect WHERE target_id=? and effect_id=?", (target_id, effect_id))
        await main.commit()

    async def get_we_point(self, user_id, weapon_id):  # 武器の熟練度を取得
        current_count = await self.fetchrow("SELECT point FROM weapon_point WHERE user_id=? and weapon_id=?",
                                            (user_id, weapon_id))
        if not current_count:
            return 0
        return current_count[0]

    async def give_we_point(self, user_id, weapon_id, count):
        main = self.main
        await main.execute("INSERT INTO weapon_point VALUES($1,$2,$3)"
                           "ON CONFLICT(user_id, weapon_id) DO "
                           "UPDATE SET point=weapon_point.point+$3", (user_id, int(weapon_id), int(count)))
        await main.commit()

    async def get_item_count(self, user_id, item_id):  # アイテムのカウントを取得
        current_count = await self.fetchrow("SELECT count FROM item WHERE user_id=? and item_id=?",
                                            (user_id, item_id))
        if not current_count:
            return 0
        return current_count[0]

    async def give_item(self, user_id, item_id, count):
        main = self.main
        await main.execute("INSERT INTO item VALUES($1,$2,$3)"
                           "ON CONFLICT(user_id, item_id) DO "
                           "UPDATE SET count=item.count+$3", (user_id, int(item_id), int(count)))
        await main.commit()

    async def consume_item(self, user_id, item_id, count, get=True):
        main = self.main
        current_count = [0]
        if get:
            current_count = await self.fetchrow("SELECT count FROM item WHERE user_id=? and item_id=?",
                                                (user_id, item_id))
            if not current_count:
                return 0
        await main.execute("UPDATE item set count="
                           "(CASE WHEN count-$1<0 THEN 0 ELSE count-$1 END) "
                           "WHERE user_id=$2 and item_id=$3", (count, user_id, item_id))
        await main.execute("DELETE FROM item WHERE count=0 and user_id=? and item_id=?", (user_id, item_id))
        await main.commit()
        return current_count[0]

    async def consume_craft_item(self, user_id, dicts, counts=1):
        main = self.main
        for item_id, count in dicts.items():
            count *= counts
            await main.execute("UPDATE item set count="
                               "(CASE WHEN count-$1<0 THEN 0 ELSE count-$1 END) "
                               "WHERE user_id=$2 and item_id=$3", (count, user_id, item_id))
            await main.execute("DELETE FROM item WHERE count=0 and user_id=? and item_id=?", (user_id, item_id))
            await main.commit()
        return True

    async def delete_item(self, user_id, item_id):
        main = self.main
        await main.execute("DELETE FROM item WHERE user_id=? and item_id=?", (user_id, item_id))
        await main.commit()

    async def get_material_count(self, user_id, material_id):  # 素材のカウントを取得
        current_count = await self.fetchrow("SELECT count FROM material WHERE user_id=? and material_id=?",
                                            (user_id, material_id))
        if not current_count:
            return 0
        return current_count[0]

    async def give_material(self, user_id, material_id, count):
        main = self.main
        await main.execute("INSERT INTO material VALUES($1,$2,$3)"
                           "ON CONFLICT(user_id, material_id) DO "
                           "UPDATE SET count=material.count+$3", (user_id, int(material_id), int(count)))
        await main.commit()

    async def consume_material(self, user_id, material_id, count, get=False):
        main = self.main
        current_count = [0]
        if get:
            current_count = await self.fetchrow("SELECT count FROM material WHERE user_id=? and item_id=?",
                                        (user_id, material_id))
            if not current_count:
                return 0
        await main.execute("UPDATE material set count="
                           "(CASE WHEN count-$1<0 THEN 0 ELSE count-$1 END) "
                           "WHERE user_id=$2 and material_id=$3", (count, user_id, material_id))
        await main.execute("DELETE FROM material WHERE count=0 and user_id=? and material_id=?", (user_id, material_id))
        await main.commit()
        return current_count[0]

    async def consume_craft_material(self, user_id, dicts, counts=1):
        main = self.main
        for material_id, count in dicts.items():
            count *= counts
            await main.execute("UPDATE material set count="
                               "(CASE WHEN count-$1<0 THEN 0 ELSE count-$1 END) "
                               "WHERE user_id=$2 and material_id=$3", (count, user_id, material_id))
            await main.execute("DELETE FROM material WHERE count=0 and user_id=? and material_id=?", (user_id, material_id))
            await main.commit()
        return True

    async def delete_material(self, user_id, item_id):
        main = self.main
        await main.execute("DELETE FROM material WHERE user_id=? and material_id=?", (user_id, item_id))
        await main.commit()

    async def get_skill_count(self, user_id, skill_id):  # スキルのカウントを取得
        current_count = await self.fetchrow("SELECT count FROM skill WHERE user_id=? and skill_id=?",
                                            (user_id, skill_id))
        if not current_count:
            return 0
        return current_count[0]

    async def give_skill(self, user_id, skill_id, count):
        main = self.main
        await main.execute("INSERT INTO skill VALUES($1,$2,$3)"
                           "ON CONFLICT(user_id, skill_id) DO "
                           "UPDATE SET count=skill.count+$3", (user_id, int(skill_id), int(count)))
        await main.commit()

    async def consume_skill(self, user_id, skill_id, count, get=True):
        main = self.main
        current_count = [0]
        if get:
            current_count = await self.fetchrow("SELECT count FROM skill WHERE user_id=? and skill_id=?",
                                                (user_id, skill_id))
            if not current_count:
                return 0
        await main.execute("UPDATE skill set count="
                           "(CASE WHEN count-$1<0 THEN 0 ELSE count-$1 END) "
                           "WHERE user_id=$2 and skill_id=$3", (count, user_id, skill_id))
        await main.execute("DELETE FROM skill WHERE count=0 and user_id=? and skill_id=?", (user_id, skill_id))
        await main.commit()
        return current_count[0]

    async def consume_craft_skill(self, user_id, dicts, counts=1):
        main = self.main
        for skill_id, count in dicts.items():
            count *= counts
            await main.execute("UPDATE skill set count="
                               "(CASE WHEN count-$1<0 THEN 0 ELSE count-$1 END) "
                               "WHERE user_id=$2 and skill_id=$3", (count, user_id, skill_id))
            await main.execute("DELETE FROM skill WHERE count=0 and user_id=? and skill_id=?", (user_id, skill_id))
            await main.commit()
        return True

    async def delete_skill(self, user_id, skill_id):
        main = self.main
        await main.execute("DELETE FROM skill WHERE user_id=? and skill_id=?", (user_id, skill_id))
        await main.commit()

    async def get_exp(self, user_id):
        main = self.main
        get = await self.fetchrow("SELECT exp FROM player WHERE user_id=?", (user_id,))
        if not get:
            await main.execute(
                "INSERT INTO player values( ?, ?, ?, ? )", (user_id, 1, 0, 0))
            await main.commit()
            get = [1]
        return get[0]

    async def get_player_level(self, user_id, exp=None):
        if exp or exp == 0:
            return int(math.sqrt(exp))
        exp = await self.get_exp(user_id)
        return int(math.sqrt(exp))

    async def get_monster_count(self, user_id):
        main = self.main
        get = await self.fetchrow("SELECT monster FROM player WHERE user_id=?", (user_id,))
        if not get:
            await main.execute(
                "INSERT INTO player values( ?, ?, ?, ? )", (user_id, 1, 0, 0))
            await main.commit()
            get = [0]
        return get[0]

    async def get_equip(self, user_id, text):
        get = await self.fetchrow("SELECT equip_id FROM equipment WHERE user_id=? and equip=?", (user_id, text))
        if not get:
            return 0
        return get[0]

    async def set_equip(self, user_id, equip_id, text):
        main = self.main
        get = await self.fetchrow("SELECT equip_id FROM equipment WHERE user_id=? and equip=?", (user_id, text))
        if not get:
            if text not in alldata.equips:
                return
            await main.execute(
                "INSERT INTO equipment values( ?, ?, ? )", (user_id, equip_id, text))
        else:
            await main.execute("UPDATE equipment SET equip_id=? WHERE user_id=? and equip=?", (equip_id, user_id, text))
        await main.commit()

    async def get_ban(self, user_id):
        main = self.main
        get = await self.fetchrow("SELECT ban FROM player WHERE user_id=?", (user_id,))
        if not get:
            await main.execute(
                "INSERT INTO player values( ?, ?, ?, ? )", (user_id, 1, 0, 0))
            await main.commit()
            get = [0]
        return get[0]

    async def add_exp(self, user_id, exp, message=True):
        main = self.main
        current_exp = await self.get_exp(user_id)
        result_exp = current_exp + exp
        await main.execute("UPDATE player SET exp=? WHERE user_id=?", (result_exp, user_id))
        await main.commit()
        if message and result_exp > (int(math.sqrt(current_exp)) + 1) ** 2:
            level = int(math.sqrt(result_exp))
            get_name = self.bot.get_user(user_id).name
            return f"! {get_name}のレベルが{level:,}になった！\n"
        return ""

    async def add_monster_count(self, user_id, count):
        main = self.main
        current_value = await self.get_monster_count(user_id)
        result_value = current_value + count
        await main.execute("UPDATE player SET monster=? WHERE user_id=?", (result_value, user_id))
        await main.commit()

    async def set_ban(self, user_id, count):
        main = self.main
        await self.get_ban(user_id)
        await main.execute("UPDATE player SET ban=? WHERE user_id=?", (count, user_id))
        await main.commit()

    async def get_enemy_id(self, channel_id):
        main = self.main
        get = await self.fetchrow("SELECT enemy_id FROM channel_enemy WHERE channel_id=?", (channel_id, ))
        if not get:
            await main.execute("INSERT INTO channel_enemy values( ?, ?, ?, ?, ? )",
                               (channel_id, 70, 1, 1, 1))
            await main.commit()
            get = [1]
        return get[0]

    async def set_enemy_id(self, channel_id, enemy_id):
        main = self.main
        await self.get_enemy_id(channel_id)
        await main.execute("UPDATE channel_enemy SET enemy_id=? WHERE channel_id=?", (int(enemy_id), channel_id))
        await main.commit()

    async def get_enemy_hp(self, channel_id):
        try:
            main = self.main
            channel = await self.fetchrow("SELECT enemy_hp FROM channel_enemy WHERE channel_id=?", (channel_id, ))
            if not channel:
                await main.execute("INSERT INTO channel_enemy values( ?, ?, ?, ?, ? )",
                                   (channel_id, 70, 1, 1, 1))
                await main.commit()
                channel = [70]
            return channel[0]
        except:
            print(
                f"エラー\n----------------------------------------------------\n{traceback.format_exc()}\n----------------------------------------------------")
            return

    async def change_enemy_hp(self, channel_id, hp, min_zero=True):
        main = self.main
        current = await self.get_enemy_hp(channel_id)
        total = current-int(hp)
        if min_zero and total < 0:
            total = 0
        await main.execute("UPDATE channel_enemy SET enemy_hp=? WHERE channel_id=?", (total, channel_id))
        await main.commit()
        return total

    async def set_enemy_hp(self, channel_id, hp):
        main = self.main
        await main.execute("UPDATE channel_enemy SET enemy_hp=? WHERE channel_id=?", (hp, channel_id))
        await main.commit()
        return

    async def get_enemy_level(self, channel_id):
        try:
            main = self.main
            channel = await self.fetchrow("SELECT enemy_level FROM channel_enemy WHERE channel_id=?", (channel_id, ))
            if not channel:
                await main.execute("INSERT INTO channel_enemy values( ?, ?, ?, ?, ? )",
                                   (channel_id, 70, 1, 1, 1))
                await main.commit()
                channel = [1]
            return channel[0]
        except:
            print(
                f"エラー\n----------------------------------------------------\n{traceback.format_exc()}\n----------------------------------------------------")
            return

    async def add_enemy_level(self, channel_id, level):
        main = self.main
        current = await self.get_enemy_level(channel_id)
        total = current+int(level)
        await main.execute("UPDATE channel_enemy SET enemy_level=? WHERE channel_id=?", (total, channel_id))
        await main.commit()
        return total

    async def get_place(self, channel_id):
        try:
            main = self.main
            channel = await self.fetchrow("SELECT place FROM channel_enemy WHERE channel_id=?", (channel_id, ))
            if not channel:
                await main.execute("INSERT INTO channel_enemy values( ?, ?, ?, ?, ? )",
                                   (channel_id, 70, 1, 1, 1))
                await main.commit()
                channel = [1]
            return channel[0]
        except:
            print(
                f"エラー\n----------------------------------------------------\n{traceback.format_exc()}\n----------------------------------------------------")
            return

    async def set_place(self, channel_id, place):
        main = self.main
        await self.get_place(channel_id)
        await main.execute("UPDATE channel_enemy SET place=? WHERE channel_id=?", (place, channel_id))
        await main.commit()

    async def get_player_hp(self, user_id):
        hp = await self.fetchrow("SELECT hp FROM channel_join WHERE user_id=?", (user_id, ))
        if not hp:
            return None
        return hp[0]

    async def change_player_hp(self, user_id, hp, min_zero=True):
        main = self.main
        current = await self.get_player_hp(user_id)
        total = current-int(hp)
        if min_zero and total < 0:
            total = 0
        await main.execute("UPDATE channel_join SET hp=? WHERE user_id=?", (total, user_id))
        await main.commit()
        return total

    async def player_max_hp(self, user_id):
        level = await self.get_player_level(user_id)
        hp = int(level * 6 + 40)
        return hp

    async def enemy_max_hp(self, channel_id):
        level = await self.get_enemy_level(channel_id)
        hp = level * 10 + 70
        return hp

    async def join_battle(self, user_id, channel_id):
        try:
            error_message = ""
            main = self.main
            battle = await self.fetchrow("SELECT channel_id FROM channel_join WHERE user_id=?", (user_id,))
            hp = await self.fetchrow("SELECT hp FROM channel_join WHERE user_id=?", (user_id,))
            player_hp = await self.player_max_hp(user_id)
            if not battle:  # チャンネルの戦闘が開始されてないとき
                await main.execute("INSERT INTO channel_join values( ?, ?, ? )", (channel_id, user_id, player_hp))
                await main.commit()
                return player_hp, error_message
            if not hp:  # プレイヤーがチャンネルに参加していないとき
                await main.execute("INSERT INTO channel_join values( ?, ?, ? )", (channel_id, user_id, player_hp))
                await main.commit()
                return player_hp, error_message
            battle_channel_id = battle[0]  # 戦闘中のチャンネル
            battle_channel = self.bot.get_channel(battle_channel_id)
            if not battle_channel:  # discordに存在しないチャンネルの場合
                await main.execute("DELETE FROM channel_join WHERE channel_id=?", (battle_channel_id,))
                await main.execute("INSERT INTO channel_join values( ?, ?, ? )", (channel_id, user_id, player_hp))
                await main.commit()
                return player_hp, error_message
            player_hp = hp[0]
            if battle[0] != channel_id:
                error_message = f"<@{user_id}>さんはすでに<#{battle_channel.id}>に参加していますよ？"
            elif player_hp == 0:
                error_message = f"<@{user_id}>さんは倒れています。"
            return player_hp, error_message
        except:
            print(f"{traceback.format_exc()}\n--------")
            return 0, traceback.format_exc()

    async def change_hp(self, target_id, hp, enemy=False, min_zero=True):
        if enemy:
            await self.change_enemy_hp(target_id, hp, min_zero)
        else:
            await self.change_player_hp(target_id, hp, min_zero)

    async def ban_check(self, ctx):
        get_ban = await self.get_ban(ctx.author.id)
        if get_ban == 1:
            return False
        return True
