# Ez'start (Eazy start)
discordのゲームBOTであるRe'startの簡易版です。
ご自由にお使いください。
## 動作環境
* Python-3.11.0
* discord.py-2.2.2
* numpy-1.24.3
* aiosqlite-0.19.0
## 初期設定
info.jsonにtokenとclient_id(BOTのユーザーID)を入力。
alldataにあるadminに自分のIDを追加(管理者)
## 実装コマンド
### game
* attack - 攻撃する。
* reset - 戦闘をリセットする。
* mine - 採掘して素材を集める。
### item
* pocket - 持ち物を開く。
* use - アイテムを使用する。
* weapon - 武器を装備
* skill - スキルを装備
* tool - 道具を装備
* craft - 素材を使用して物を作る。
### channel
* change - 場所を変更。
### other
* status - ステータスを確認。
* effectstatus - 現在のプレイヤーの戦闘状態を確認
* prank - プレイヤーレベルランキングを表示
### debug
* exp - 経験値を付与(管理者のみ)
* itemid - アイテムを付与(管理者のみ)
* skillid - スキルを付与(管理者のみ)
* sozaiid - 素材を付与(管理者のみ)
* effect - エフェクトを付与(管理者のみ)
* meffect - 敵にエフェクトを付与(管理者のみ)
* cban - ユーザーのBAN値を変更(管理者のみ)
* mycoin - ユーザーのBAN値を確認する。
