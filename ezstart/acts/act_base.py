import discord
import jmespath
from ezstart.database import alldata
from ezstart.database import maindb

class Act:
    def __init__(self, user_id, channel_id, bot, act_id, attack, crit_msg, enemy_id, enemy=False):
        self.bot = bot
        self.user_id = user_id
        self.channel_id = channel_id
        self.act_id = act_id
        self.enemy = enemy
        self.enemy_id = enemy_id
        self.attack = attack
        self.crit_msg = crit_msg

        self.merit = "+"
        self.demerit = "-"

        self.target_id = self.channel_id
        self.my_id = self.user_id

        self.target_name = alldata.enemies[enemy]["name"]
        self.my_name = bot.get_user(user_id).display_name
        if enemy:
            self.merit, self.demerit = self.demerit, self.merit
            self.target_id, self.my_id = self.my_id, self.target_id
            self.target_name, self.my_name = self.my_name, self.target_name

        self.db = maindb.Database(self.bot)

    async def get_user_tp(self):
        if not self.enemy:
            return await self.db.get_enemy_tp(self.channel_id)
        return await self.db.get_player_tp(self.user_id)

    async def get_act_level(self):
        if not self.enemy:
            weapon = await self.db.get_equip(self.user_id, "weapon")
            return await self.db.get_act_level(self.user_id, weapon, self.act_id, True)
        acts = jmespath.search("status.acts", alldata.enemies[self.enemy_id])
        if acts:
            if str(self.act_id) in acts:
                return acts[str(self.act_id)]["level"]
        return 1

    async def consume_tp(self):
        tp = alldata.acts_data[self.act_id]['tp']
        if not self.enemy:
            await self.db.add_player_tp(self.user_id, -tp)
        else:
            await self.db.add_enemy_tp(self.channel_id, -tp)
        return f"\n{self.demerit*3} {self.target_name}はTPを{tp}消費した。 {self.demerit*3}"
    async def act(self):
        pass