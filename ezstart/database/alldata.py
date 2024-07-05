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

admin = (345342072045174795,)  # 管理者コマンドを使える人のid
cmd_error_msg = "```diff\n- お前は誰だ?```"  # 特定の人しか使えないコマンド

batu = "🚫"

# equipで使えるテキスト ここに追加しないと新しい装備を追加することはできない。(無駄な種類を増やさないため)
equips = ("weapon", "skill", "tool")

# エフェクト一覧
effects_json = open("json/other/effects.json", "r", encoding="utf-8_sig")
effects_data = {int(k): v for (k, v) in json.load(effects_json).items()}

effects = {k: v["name"] for (k, v) in effects_data.items()}

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

weapons_json = open("json/item/weapons.json", "r", encoding="utf-8_sig")
weapons_data = {int(k): v for (k, v) in json.load(weapons_json).items()}

potions_json = open("json/item/potions.json", "r", encoding="utf-8_sig")
potions_data = {int(k): v for (k, v) in json.load(potions_json).items()}

tools_json = open("json/item/tools.json", "r", encoding="utf-8_sig")
tools_data = {int(k): v for (k, v) in json.load(tools_json).items()}

specials_json = open("json/item/specials.json", "r", encoding="utf-8_sig")
specials_data = {int(k): v for (k, v) in json.load(specials_json).items()}

materials_json = open("json/item/materials.json", "r", encoding="utf-8_sig")
materials_data = {int(k): v for (k, v) in json.load(materials_json).items()}

skills_json = open("json/item/skills.json", "r", encoding="utf-8_sig")
skills_data = {int(k): v for (k, v) in json.load(skills_json).items()}

places_json = open("json/other/places.json", "r", encoding="utf-8_sig")
places_data = {int(k): v for (k, v) in json.load(places_json).items()}

acts_json = open("json/other/acts.json", "r", encoding="utf-8_sig")
acts_data = {int(k): v for (k, v) in json.load(acts_json).items()}

items_data = tools_data | weapons_data | potions_data | specials_data
# ツールの機能
# ツールid: {"場所": [採掘可能場所], "採掘ランク": 数値が高いほど取れる種類が増える, "出現幸運": 数値が高いほど取れやすくなる, "獲得幸運": 数値が高いほど多く取れる}
# tools.jsonからstatusの部分だけ抜き出す
can_mining = {k: v["status"] for (k, v) in tools_data.items()}

# アイテム一覧
tools = {k: v["name"] for (k, v) in tools_data.items()}

weapons = {k: v["name"] for (k, v) in weapons_data.items()}

potions = {k: v["name"] for (k, v) in potions_data.items()}

specials = {k: v["name"] for (k, v) in specials_data.items()}

# それぞれのアイテムの辞書を結合
items = specials | tools | weapons | potions
# useで使用できるアイテム (useというキーにある各要素をキーにしてそのアイテムのidを値にする。)
use_items = {i: k for (k, v) in items_data.items() for i in ([] if "use" not in v else v["use"])}

# 素材一覧
materials = {k: v["name"] for (k, v) in materials_data.items()}

# スキル一覧
skills = {k: v["name"] for (k, v) in skills_data.items()}

# 場所一覧 ["名前", 解放レベル]
places = places_data

# 武器の攻撃力補正
async def we_atk(bot, user_id, weapon):
    db = maindb.Database(bot)
    juk = 0.0000056 * await db.get_we_point(user_id, weapon)  # 熟練度による攻撃力ボーナス

    if not weapon in weapons_data: # 設定してない武器の場合
        return 1
    atk = weapons_data[weapon]["status"]["atk"]+juk*weapons_data[weapon]["status"]["bonus"]
    return atk

# banのメッセージ
ban_message = {0: "+ OK", 1: "- BAN", 2: "生命体の真実を隠す者"}
