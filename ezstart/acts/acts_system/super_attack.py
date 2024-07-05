import discord
from ezstart.database import alldata
from ezstart.database import maindb
from ezstart.acts import act_base

class SuperAttack(act_base.Act):
    def __init__(self, user_id, channel_id, bot, act_id, attack, crit_msg, enemy_id=-1, enemy=False):
        super().__init__(user_id, channel_id, bot, act_id, attack, crit_msg, enemy_id, enemy)

    async def act(self):
        level = await self.get_act_level()-1
        dmg = int(self.attack * 2 * (1 + level * 0.1))
        await self.db.change_hp(self.target_id, dmg, not self.enemy)
        msg = f"{self.merit} {self.my_name}は{alldata.acts_data[self.act_id]['name']}を使った！{self.crit_msg}{dmg:,}のダメージを与えた！"
        msg += await self.consume_tp()
        return msg
