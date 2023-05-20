import discord
import traceback
import json
from ezstart.database import maindb

enemy_list = open("json/enemies.json", "r", encoding="utf-8_sig")
enemies = json.load(enemy_list)


async def delete(ctx):
    async for msg in ctx.channel.history(limit=1):
        if msg.author == ctx.author:
            return await msg.delete()


async def error_send(ctx):
    print(f"エラー[{ctx.author.guild.name}: {ctx.author.name}: {ctx.message.content}]\n{traceback.format_exc()}\n-------------")
    msg = discord.Embed(title=f"！！ＥＲＲＯＲ！！",
                        description=f"M:{ctx.message.content}\nG:{ctx.guild.name}/{ctx.guild.id}\nC:{ctx.channel.name}/{ctx.channel.id}/<#{ctx.channel.id}>\nU:{ctx.author.name}/{ctx.author.id}/<@{ctx.author.id}>```py\n{traceback.format_exc()}```",
                        color=0xC41415)
    return await ctx.send(embed=msg)


def em(msg):
    try:
        embed = discord.Embed(description=msg)
        return embed
    except:
        print(f"エラー(em関数)----------\n{traceback.format_exc()}\n---------")
        return discord.Embed(description=traceback.format_exc())


stop_command = []
channel_stop = []
mine_cool_time = {}  # 採掘のクールタイム中の人

admin = [345342072045174795]  # 管理者コマンドを使える人のid
cmd_error_msg = "```diff\n- お前は誰だ?```"  # 特定の人しか使えないコマンド

batu = "🚫"

# equipで使えるテキスト ここに追加しないと新しい装備を追加することはできない。(無駄な種類を増やさないため)
equips = ["weapon", "skill", "tool"]

# エフェクト一覧
effects = {1: "素早さ上昇", 2: "攻撃力増加", 3: "毒"}

# 場所から採掘できるアイテム (アイテムと素材両方入力しないとダメ。)
# 場所id: {"種類": {id: [最小個数, 最大個数, 確率, 最低必要ランク, 出現幸運影響値※1, 獲得幸運影響値※1]}}
# ※1: 元の確率(個数) * (1 + ツールの幸運値 * 影響値) | 個数は最小最大両方掛け算される。
place_mining = {
    1: {"item":     {10000: [1, 1, 0.05, 100, 0.1, 0.1], 10001: [1, 5, 1, 100, 1, 0.3]},
        "material": {1: [1, 3, 1, 0, 1, 1]}},
    2: {"item": {},
        "material": {2: [1, 3, 1, 0, 1, 1],
                     3: [1, 3, 0.2, 0, 0.5, 0.5],
                     4: [1, 3, 0.06, 1, 0.4, 0.4]}},
    3: {"item":     {},
        "material": {2: [2, 6, 1, 0, 1, 1],
                     3: [2, 4, 0.25, 0, 0.5, 0.5],
                     4: [1, 4, 0.07, 1, 0.4, 0.4],
                     5: [1, 3, 0.03, 2, 0.2, 0.2]
                     }},
}

# ツールの機能
# ツールid: {"場所": [採掘可能場所], "採掘ランク": 数値が高いほど取れる種類が増える, "出現幸運": 数値が高いほど取れやすくなる, "獲得幸運": 数値が高いほど多く取れる・}
can_mining = {
    0: {"place": [1], "rank": 0, "get_luck": 0, "count_luck": 0},
    1: {"place": [1, 2], "rank": 0, "get_luck": 0, "count_luck": 0},
    2: {"place": [1, 2], "rank": 1, "get_luck": 0, "count_luck": 0},
    3: {"place": [1, 2, 3], "rank": 2, "get_luck": 0, "count_luck": 0},
    10: {"place": [1], "rank": 100, "get_luck": 0, "count_luck": 0}
}

# アイテム一覧
tools = {1: "木のツルハシ", 2: "石のツルハシ", 3: "鉄のツルハシ", 10: "釣り竿"}

weapons = {101: "木の剣", 102: "石の剣", 103: "EZの剣"}

potions = {1001: "俊足のポーション", 1002: "力のポーション"}

specials = {-2: "醸造台", -1: "金床", 0: "なし", 10000: "魚", 10001: "ゴミ"}

# それぞれのアイテムの辞書を結合
items = specials | tools | weapons | potions

# 素材一覧
materials = {1: "木材", 2: "丸石", 3: "石炭", 4: "鉄", 5: "ダイヤモンド", 6: "腐肉", 7: "骨", 8: "Kの手紙(破)"}

# スキル一覧
skills = {0: "なし", 1: "ポイズン"}

# 場所一覧 ["名前", 解放レベル]
places = {1: ["森林", 1], 2: ["浅い洞窟", 100], 3: ["深い洞窟", 300]}

# 武器の説明
we_desc = {
    0: "- 素手",
    101: "- 簡単に作れる剣。\n` 攻撃力が上昇する。",
    102: "- 石でできた剣。\n` 攻撃力が上昇する。",
    103: "- 簡単にできる剣。\n` 常に移動速度が上昇する。\n 相手に常に毒(Lv.1)を付与させる。"
}


# 武器の攻撃力補正
async def we_atk(bot, user_id, weapon):
    db = maindb.Database(bot)
    juk = 0.0000056 * await db.get_we_point(user_id, weapon)  # 熟練度による攻撃力ボーナス

    we_atk_dict = {
        101: 1.025+juk,
        102: 1.04+juk,
        103: 1.1+juk
    }
    we_atk_dict.setdefault(weapon, 1)  # 設定してない武器の場合
    return we_atk_dict[weapon]

# banのメッセージ
ban_message = {0: "+ OK", 1: "- BAN", 2: "生命体の真実を隠す者"}
