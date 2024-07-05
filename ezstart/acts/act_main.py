from ezstart.acts.acts_system import *

class ActSystem:
    def __init__(self, bot):
        self.bot = bot


    async def act_message(self, ctx, user_id, channel_id, attack, enemy_id, enemy, crit_msg, act_id):
        acts = {
            1: super_attack.SuperAttack(user_id, channel_id, self.bot, act_id, attack, crit_msg, enemy_id, enemy)
        }
        if act_id not in acts:
            return "- 指定された行動はありませんでした。"
        msg = await acts[act_id].act()
        return msg
