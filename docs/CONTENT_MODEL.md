# 建築データモデル

## 目的

「記事」と「地図データ」を別々に管理すると、情報が重複し、更新漏れが起きやすくなります。本プロジェクトでは、1つの構造化データを基礎に、地図・一覧・詳細・ルート・建築家ページなどを生成できる形を目指します。

## 基本単位

1レコード = 原則として1つの「訪問対象となる建築／建築群」。

建物そのものと施設運営情報は更新頻度が違うため、論理的に分離します。

---

## 推奨フィールド

### 識別

| Field | 型 | 内容 |
|---|---|---|
| `id` | string | 永続ID。URLスラッグ変更の影響を受けない |
| `slug` | string | URL用 |
| `nameJa` | string | 日本語正式名称 |
| `nameEn` | string/null | 英語正式名称 |
| `aliases` | string[] | 旧称・通称 |

### 地理

| Field | 型 | 内容 |
|---|---|---|
| `prefecture` | string | 都道府県 |
| `municipality` | string | 市区町村 |
| `area` | string | 丸の内、上野など回遊用エリア |
| `address` | string | 住所 |
| `lat` / `lng` | number | 地図座標 |
| `nearestStations` | object[] | 駅名、徒歩目安 |

### 建築基本情報

| Field | 型 | 内容 |
|---|---|---|
| `completionYear` | number/null | 主たる竣工年 |
| `completionDateText` | string/null | より詳細な年代表現 |
| `era` | enum | traditional / early-modern / modern / postwar / contemporary |
| `architects` | object[] | 建築家・設計組織・役割 |
| `buildingTypes` | string[] | 美術館、駅、住宅等 |
| `styles` | string[] | アール・デコ、モダニズム等 |
| `structures` | string[] | 木造、RC、S等 |
| `materials` | string[] | 煉瓦、打放しコンクリート等 |
| `renovations` | object[] | 改修・復原履歴 |

### ユーザー向け評価

| Field | 型 | 内容 |
|---|---|---|
| `importance` | 1-5 | 建築史・知名度・作品性など総合 |
| `visitPriority` | 1-5 | 建築観光としての推奨度 |
| `beginnerFriendly` | 1-5 | 初心者でも面白さが伝わりやすいか |
| `photoAppeal` | 1-5 | 視覚的な魅力 |
| `historicalValue` | 1-5 | 歴史的価値 |
| `designValue` | 1-5 | デザイン上の価値 |

評価値は断定的な「客観点数」ではなく、並び替え・推薦のための編集スコアとして扱います。

### 解説

| Field | 型 | 内容 |
|---|---|---|
| `oneLiner` | string | 一言で魅力 |
| `summary` | string | 100〜200字程度の一般向け説明 |
| `whyVisit` | string | 行く理由 |
| `highlights` | string[] | 現地で見るポイント3〜5件 |
| `history` | string/null | 歴史 |
| `designExplanation` | string/null | 設計解説 |
| `structureExplanation` | string/null | 構造解説 |
| `contextExplanation` | string/null | 都市・地域との関係 |
| `expertNotes` | string/null | 専門向け補足 |

### 見学情報

`visit` オブジェクトにまとめます。

```json
{
  "status": "public",
  "interiorAccess": "ticketed",
  "exteriorAccess": "public",
  "openingHoursText": "公式サイトを確認",
  "feeText": "展示により異なる",
  "reservationRequired": false,
  "photographyPolicy": "varies",
  "barrierFree": "partial",
  "estimatedVisitMinutes": 60,
  "officialUrl": "https://...",
  "lastChecked": "2026-09-11"
}
```

### 写真

写真は必ずライセンス／許諾情報とセットで管理します。

```json
{
  "src": "...",
  "alt": "...",
  "caption": "...",
  "creator": "...",
  "sourceUrl": "...",
  "license": "CC BY 4.0",
  "licenseUrl": "...",
  "commercialUse": true,
  "modificationAllowed": true
}
```

### 出典・検証

```json
{
  "sources": [
    {
      "url": "https://...",
      "title": "公式ページ",
      "publisher": "...",
      "sourceType": "official",
      "supports": ["completionYear", "architects", "visit"]
    }
  ],
  "verification": {
    "status": "reviewed",
    "lastVerified": "2026-09-11",
    "verifiedFields": ["completionYear", "architects"],
    "needsReview": ["openingHoursText"]
  }
}
```

---

## 検証ステータス

- `seed` — 候補として登録しただけ
- `researched` — 複数資料を確認したが編集監査前
- `reviewed` — 一次情報を中心に主要項目を確認済み
- `needs-update` — 公開情報などが古い可能性あり
- `disputed` — 資料間で情報が一致していない
- `archived` — 消失・閉鎖等。資料価値のため保持

---

## 見学ステータス

- `public` — 通常見学可能
- `limited` — 曜日・期間・イベント等に制限あり
- `exterior-only` — 外観のみを安全・合法に見られる
- `reservation` — 予約が必要
- `private` — 私有・非公開。訪問誘導しない
- `closed` — 閉館・閉鎖
- `demolished` — 現存しない
- `unknown` — 未確認

住宅作品などを無理に観光スポット化しないことが重要です。

---

## 年代区分（初期案）

ユーザー表示用は細かくしすぎず、内部では年を保持します。

- 伝統・近世: 〜1867
- 近代前期: 1868〜1911
- 近代: 1912〜1945
- 戦後: 1946〜1989
- 現代: 1990〜

検索画面では「江戸以前」「明治・大正・昭和前期」「戦後モダニズム」「現代」など、一般に理解しやすい表現へ変換できます。

---

## 建築家データ

将来、建築家ページを作るため、単なる文字列ではなくID参照へ移行します。

```json
{
  "id": "kenzo-tange",
  "nameJa": "丹下健三",
  "nameEn": "Kenzo Tange",
  "birthYear": 1913,
  "deathYear": 2005,
  "officialUrl": null
}
```

建物側:

```json
{
  "architectId": "kenzo-tange",
  "role": "architect"
}
```

---

## 将来のルートモデル

```json
{
  "id": "marunouchi-modern-2h",
  "title": "丸の内・有楽町 建築2時間コース",
  "durationMinutes": 120,
  "buildingIds": ["...", "...", "..."],
  "themeTags": ["近代建築", "現代建築"],
  "transport": "walk",
  "description": "..."
}
```

これにより記事を別管理せず、建築DBを組み合わせて周遊コンテンツを作れます。
