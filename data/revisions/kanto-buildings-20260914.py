import json,copy
from pathlib import Path
R=Path(__file__).resolve().parents[2];DATE='2026-09-14'
geo=json.loads((R/'data/additions/kanto-geography-review.json').read_text())
def source(id,title,url,publisher,scope):return dict(id=id,title=title,url=url,publisher=publisher,scope=scope,sourceType='official',checkedAt=DATE)
def comp(part,material,text,refs,origin=None):
 d=dict(part=part,material=material,description=text,sourceIds=refs)
 if origin:d['origin']=origin
 return d
items=[]
def add(id,name,municipality,area,address,year,architects,types,deck,summary,highlights,components,sources,fields,visit,**extra):
 g=geo[id]
 b=dict(id=id,slug=id,nameJa=name,nameEn='',prefecture='神奈川県' if address.startswith('神奈川') else '東京都',municipality=municipality,area=area,address=address,lat=g['lat'],lng=g['lng'],completionYear=year,era='early-modern' if year<=1911 else 'modern' if year<=1945 else 'postwar' if year<=1988 else 'contemporary',architects=architects,buildingTypes=types,styles=[],materials=[],oneLiner=deck,summary=summary,highlights=highlights,components=components,articleSourceIds=fields['article'],visit=dict(lastChecked=DATE,**visit),sources=sources,**extra)
 for c in components:
  for m in c['material'].split('・'):
   if m not in b['materials']:b['materials'].append(m)
 if 'osmId' in g:
  u=f'https://www.openstreetmap.org/{g["osmType"]}/{g["osmId"]}'
  b['sources'].append(dict(id='location',title='施設位置（OpenStreetMap）',url=u,publisher='OpenStreetMap contributors',scope=f'{g["osmType"]} {g["osmId"]}。データ時点 {g["sourceTimestamp"]}。建築史・見学条件の根拠には使用しない。',sourceType='open-map',checkedAt=DATE))
  evidence=dict(kind='facility-point',lat=g['lat'],lng=g['lng'],osmType=g['osmType'],osmId=g['osmId'],sourceTimestamp=g['sourceTimestamp'],sourceIds=['location'],license='ODbL 1.0',licenseUrl='https://opendatacommons.org/licenses/odbl/1-0/',attribution='OpenStreetMap contributors')
  method='名称を持つ公開施設点を、公式の名称・所在地と照合。' if g['osmType']=='node' else '名称を持つ公開地図の対象形状を公式名称・所在地と照合し、形状内の代表点を採用。境界枠の中心・駅の乗降地点を代用しない。'
 else:
  b['sources'].append(dict(id='location',title='施設位置（Wikidata）',url=g['sourceUrl'],publisher='Wikidata contributors',scope='Q4346431の施設座標のみ。名称と所在地は図書館の公式案内と照合。レンガ棟の輪郭・入口は未照合。',sourceType='reference',checkedAt=DATE))
  evidence=None;method=g['method']
 b['location']=dict(status='address-matched',precision='facility',sourceIds=['location',*fields['address']],checkedAt=DATE,method=method,note='施設位置を示します。対象棟単独の輪郭と公開入口の詳細照合は未完了です。')
 if evidence:b['location']['evidence']=evidence
 b['verification']=dict(status='basic-checked',lastVerified=DATE,fields={k:dict(status='source-checked',sourceIds=refs,checkedAt=DATE) for k,refs in fields.items() if k!='article'},pending=['対象棟の輪郭と公開入口の詳細照合','見学条件の訪問直前の再確認','写真の利用許諾と掲載素材の確認','未記載の材料の樹種・石種・産地と改修後の仕様'])
 items.append(b);return b
add('tokyo-station-marunouchi','東京駅 丸の内駅舎','千代田区','丸の内','東京都千代田区丸の内1-9-1',1914,['辰野金吾','葛西萬司'],['駅舎','歴史建築'],'南北のドームと、復原された赤煉瓦の駅舎。','1914年に完成した、辰野金吾・葛西萬司設計の駅舎です。戦後に2階建てとなった部分は2007〜2012年の保存・復原工事で3階建てに戻されました。長い外壁と南北のドームに加え、東京ステーションギャラリーでは建物を支える煉瓦を見ることができます。',['南北に並ぶドーム','構造用と化粧用の煉瓦の違い','創建部分と保存・復原部分'],[
 comp('骨組み・壁','鉄骨・煉瓦','創建時の建物は鉄骨煉瓦造です。ギャラリーの内部では、柱や梁の鉄骨と構造用の煉瓦を確認できます。外壁の化粧用の煉瓦とは役割が異なります。',['building']),
 comp('外壁・復原','化粧煉瓦','外観の赤い煉瓦と、室内で見える構造用の煉瓦は同じものではありません。保存・復原工事で戻された上部もあるため、現在の壁面すべてを1914年のままとは扱いません。',['building'])],
 [source('building','東京駅の建物と煉瓦','https://www.ejrcf.or.jp/gallery/institution.html','東京ステーションギャラリー','1914年の構造、構造煉瓦と化粧煉瓦、2007〜2012年の保存・復原。'),source('history','東京駅開業','https://jpsearch.go.jp/gallery/ndl-q0ME7pww8Ok','国立国会図書館／ジャパンサーチ','1914年の落成・開業と辰野金吾・葛西萬司の設計のみを参照。復原工事の終了年は施設運営者の資料を優先。'),source('access','アクセス','https://www.ejrcf.or.jp/gallery/access.html','東京ステーションギャラリー','丸の内駅舎内の所在地と丸の内北口の関係。'),source('visit','利用案内','https://www.ejrcf.or.jp/gallery/','東京ステーションギャラリー','ギャラリーの利用は駅の通行と別。展覧会・休館日の確認先。')],
 dict(nameJa=['building'],completionYear=['building','history'],openingYear=['history'],architects=['history'],address=['access'],buildingTypes=['building'],article=['building','history']),
 dict(status='limited',officialUrl='https://www.ejrcf.or.jp/gallery/',note='駅舎内には交通施設・美術館など異なる用途があります。ギャラリーの入館条件は駅の通行とは別に確認してください。ピンは丸の内駅舎の位置で、北口・南口や改札を指定するものではありません。',sourceIds=['access','visit']),openingYear=1914,openingLabel='開業',aliases=['東京駅','丸の内駅舎'])
add('tokyo-st-marys-cathedral','東京カテドラル聖マリア大聖堂','文京区','関口','東京都文京区関口3-16-15',1964,['丹下健三'],['教会','宗教建築'],'曲面の屋根と、十字架形の光。','丹下健三が設計し、1964年に完成したカトリックの大聖堂です。8面の曲面が組み合わさって屋根と壁を形づくり、中央の開口部から光を取り入れます。ステンレスの外装と、内部のコンクリートの表情を見比べられます。',['十字架形の開口部','屋根と壁をつなぐ曲面','外装と内部で異なる素材の表情'],[
 comp('屋根・壁','コンクリート','8面のHPシェルを組み合わせた構成です。HPシェルは反り方の異なる曲面を用いた構造で、別々の屋根と壁を載せる形とは異なります。',['construction']),
 comp('外装','ステンレス','外側はステンレスで覆われています。2000年代の改修では外装やトップライトなども対象となりました。金属の外装を建物の骨組みそのものとは区別します。',['construction'])],
 [source('cathedral','東京カテドラル聖マリア大聖堂','https://tokyo.catholic.jp/archdiocese/cathedral/','カトリック東京大司教区','設計者、1964年の落成献堂、所在地。'),source('construction','東京カテドラル聖マリア大聖堂 改修工事竣工','https://www.taisei-design.jp/de/news/2008/01_01.html','大成建設','自社施工による1964年完成、HPシェル、ステンレス外装と2000年代の改修。'),source('interior','関口教会の記録','https://catholic-sekiguchi.jp/info/sekiguchi/5024/4/','カトリック関口教会','1964年の完成と内部コンクリート、中央からの採光。'),source('visit','カトリック関口教会','https://catholic-sekiguchi.jp/','カトリック関口教会','大聖堂の見学はカテドラル事務所への問合せと案内。')],
 dict(nameJa=['cathedral'],completionYear=['cathedral','construction'],architects=['cathedral'],address=['cathedral'],buildingTypes=['cathedral'],article=['cathedral','construction','interior']),
 dict(status='limited',officialUrl='https://catholic-sekiguchi.jp/',notice='見学は大聖堂の案内を確認',note='現在も礼拝を行う教会です。大聖堂の見学については、公式サイトが案内するカテドラル事務所へご確認ください。礼拝や行事の利用を優先し、見学可能な範囲に従ってください。',sourceIds=['visit']),aliases=['聖マリア大聖堂','関口教会'])
b=add('myonichikan-central','自由学園明日館 中央棟','豊島区','西池袋','東京都豊島区西池袋2-31-3',1922,['フランク・ロイド・ライト','遠藤新'],['学校','歴史建築'],'大きな幾何学模様の窓と、低く広がる旧校舎。','フランク・ロイド・ライトと遠藤新が設計した自由学園の旧校舎です。中央棟のホールでは、幾何学模様の窓と、その上に設けられた食堂とのつながりが見どころです。開校・各棟の完成は同じ年ではなく、中央棟の年表と文化財の年代表示にも違いがあります。',['ホールの幾何学模様の窓','中央棟のホールと食堂','低い屋根と庭との関係'],[
 comp('骨組み・屋根','木材・鉄板','文化庁は中央棟を木造、一部2階、切妻造の鉄板葺として記載しています。外観の印象だけで石造の建物と判断せず、骨組みと仕上げを分けて見ます。',['heritage']),
 comp('ホールの窓','木材・ガラス','幾何学模様をつくる窓の枠は木製です。施設の解説では、ステンドグラスではなく木の枠で構成したことを説明しています。線の組合せが大きな窓の表情をつくります。',['building'])],
 [source('building','明日館の建築・年表','https://jiyu.jp/architecture/','自由学園明日館','開校1921年、中央棟全体の完成と年表1922年、設計者、ホールの窓。'),source('heritage','自由学園明日館 中央棟','https://kunishitei.bunka.go.jp/heritage/detail/102/561','文化庁','文化財の年代は大正10年（1921年）。木造、鉄板葺、所在地。施設竣工年表と併記する。'),source('access','交通案内','https://jiyu.jp/access/','自由学園明日館','所在地と施設の案内。'),source('visit','建物見学','https://jiyu.jp/tour/','自由学園明日館','見学カレンダー、貸館との併用、撮影条件と公開範囲。')],
 dict(nameJa=['heritage'],completionYear=['building','heritage'],openingYear=['building'],architects=['building'],address=['access'],buildingTypes=['heritage','building'],article=['building','heritage']),
 dict(status='limited',officialUrl='https://jiyu.jp/tour/',note='貸館と見学を並行して行う施設です。見学できる日と部屋は公式カレンダーで確認してください。中央棟・東西教室棟と、道路を挟んだ講堂は別の建物です。撮影や庭への立入りは施設の条件に従ってください。',sourceIds=['visit']),openingYear=1921,openingLabel='開校',aliases=['自由学園明日館','明日館','ライト'],factNotes=[dict(text='竣工欄は施設の年表にある中央棟全体の完成年（1922年）です。文化庁の年代欄は1921年と記載されており、両方の表記を残しています。',sourceIds=['building','heritage'])])
b['verification']['fields']['completionYear']['status']='qualified'
b['verification']['pending'].append('中央棟の完成年と文化財年代の定義差を原資料で追加確認')
add('kanagawa-music-hall','神奈川県立音楽堂','横浜市西区','紅葉ケ丘','神奈川県横浜市西区紅葉ケ丘9-2',1954,['前川國男'],['ホール','文化施設'],'木の内装で音を響かせる音楽ホール。','前川國男が設計し、1954年に開館した音楽ホールです。客席の壁と天井に木を使い、音の響きと空間のまとまりを生み出しています。「木のホール」という呼び名は内装の特徴で、建物全体が木造という意味ではありません。',['木で仕上げた客席空間','ホールを包む壁と天井','鉄筋コンクリートの骨組みとの違い'],[
 comp('骨組み','鉄筋コンクリート','施設概要では鉄筋コンクリート造とされています。木の内装と、それを支える建物の骨組みは別の材料です。',['building']),
 comp('客席の壁・天井','木材','客席の壁と天井に木材を使用しています。形や素材と響きの関係が見どころですが、樹種や産地は今回確認した公式案内では確定していません。',['building','official'])],
 [source('building','音楽堂について','https://www.kanagawa-ongakudo.com/about','神奈川県立音楽堂','前川國男建築設計事務所の設計、1954年開館、構造、所在地、木の壁。'),source('official','神奈川県立音楽堂','https://www.kanagawa-ongakudo.com/','神奈川県立音楽堂','壁・天井の木材と音楽ホールの紹介。'),source('tour','前川建築見学ツアー','https://www.kanagawa-ongakudo.com/tour','神奈川県立音楽堂','1954年11月竣工の説明と見学プログラム。'),source('visit','見学について（2026年9月1日）','https://www.kanagawa-ongakudo.com/news_detail/2241','神奈川県立音楽堂','ツアー以外の見学は原則不可という最新案内。')],
 dict(nameJa=['building'],completionYear=['tour'],openingYear=['building'],architects=['building'],address=['building'],buildingTypes=['building'],article=['building','official']),
 dict(status='limited',officialUrl='https://www.kanagawa-ongakudo.com/news_detail/2241',notice='見学は原則ツアーのみ',note='2026年9月1日の公式案内では、見学は「前川建築見学ツアーin音楽堂」で実施し、ツアー以外は原則受け付けないとしています。公演の入場とは別に、ツアーの日程・申込条件をご確認ください。',sourceIds=['visit','tour']),openingYear=1954,aliases=['木のホール','県立音楽堂'])
add('osanbashi-terminal','横浜港大さん橋国際客船ターミナル','横浜市中区','海岸通','神奈川県横浜市中区海岸通1-1-4',2002,['アレハンドロ・ザエラ・ポロ','ファッシド・ムサヴィ'],['客船ターミナル','交通施設'],'スロープと木のデッキが連続する客船ターミナル。','2002年に完成した現在のターミナルです。アレハンドロ・ザエラ・ポロとファッシド・ムサヴィが設計し、スロープを通じて屋内と屋上をつなぎました。大さん橋そのものの歴史と、現在の建物の完成年は分けて記録しています。',['屋上へ続くスロープ','起伏のある木のデッキ','港の眺めと建物の断面'],[
 comp('骨組み','鉄骨・鉄筋コンクリート','公式の建築概要では鉄骨造、一部鉄筋コンクリート造としています。木のデッキが見える部分と、その下で建物を支える構造を区別できます。',['building']),
 comp('屋上デッキ','イペ材','屋上広場の床にはイペ材が使われています。運営者は、耐久性などに優れた重い木材と説明しています。床の板の連続と、屋上の起伏を合わせて見る部分です。',['roof'],'公式の屋上広場案内にブラジル産と記載。個別交換材の履歴は未確認。')],
 [source('building','大さん橋の建築','https://osanbashi.jp/about/architecture','横浜港大さん橋国際客船ターミナル','2002年の現在の建物、設計者、構造、スロープ。'),source('roof','屋上広場','https://osanbashi.jp/floorguide/rooftop','横浜港大さん橋国際客船ターミナル','屋上の公開とブラジル産イペ材のデッキ。'),source('access','大さん橋国際客船ターミナルの施設概要','https://www.city.yokohama.lg.jp/business/kyoso/public-facility/kaku-katsuyou/kowan/5kikoubo.html','横浜市','対象施設名と海岸通1丁目1番4号の所在地。'),source('visit','大さん橋国際客船ターミナル','https://www.city.yokohama.lg.jp/kanko-bunka/minato/yokohamako/gaiyo/osanbasi.html','横浜市','屋上とCIQ等の立入可能範囲の違い。')],
 dict(nameJa=['access'],completionYear=['building'],architects=['building'],address=['access'],buildingTypes=['building'],article=['building']),
 dict(status='limited',officialUrl='https://osanbashi.jp/floorguide/rooftop',note='屋上広場と、出入国の手続き区域や事務所では公開条件が異なります。催事や客船利用による立入制限を確認してください。ピンはターミナルの施設位置で、乗船口や駐車場入口ではありません。',sourceIds=['roof','visit']),aliases=['大さん橋','横浜大さん橋','くじらのせなか'])
add('asakusa-culture-center','浅草文化観光センター','台東区','雷門','東京都台東区雷門2-18-9',2012,['隈研吾'],['観光案内所','公共施設'],'木のルーバーと、重なる勾配屋根。','隈研吾が設計した雷門前の観光案内施設です。8階建ての建物を、勾配屋根のある小さな建物が重なったように構成しています。木のルーバーやガラスが見える外装と、鉄骨を主体とする構造は区別して見ることができます。',['重なって見える勾配屋根','外壁の木のルーバー','上階の展望スペース'],[
 comp('骨組みと外装','鉄骨・木材','木造の家を重ねたように見えますが、メーカーの施工事例は鉄骨造と記載しています。外壁の木のルーバーは、光を調整する部材です。',['glass','design']),
 comp('窓','Low-E複層ガラス','メーカーの施工事例ではLow-E複層ガラス「ペアマルチEA」を採用しています。これはガラス製品の種類であり、建物の構造形式とは別の情報です。',['glass'])],
 [source('design','浅草文化観光センター','https://kkaa.co.jp/project/asakusa-culture-tourist-information-center/','隈研吾建築都市設計事務所','設計、勾配屋根と木のルーバー、空間構成。'),source('glass','浅草文化観光センター 施工事例','https://glass-wonderland.jp/case/7393/','日本板硝子','2012年4月竣工、設計者、鉄骨造と採用ガラス。'),source('access','浅草文化観光センター','https://t-navi.city.taito.lg.jp/spot/1007','台東区公式観光情報サイト','所在地、観光案内と展望スペースの用途。'),source('visit','浅草文化観光センターの案内','https://www.city.taito.lg.jp/bunka_kanko/kankoinfo/info/oyakudachi/kankocenter/index.html','台東区','最新の施設利用・開館案内の確認先。')],
 dict(nameJa=['access'],completionYear=['glass'],architects=['design','glass'],address=['access'],buildingTypes=['access'],article=['design','glass','access']),
 dict(status='public',officialUrl='https://www.city.taito.lg.jp/bunka_kanko/kankoinfo/info/oyakudachi/kankocenter/index.html',note='観光案内窓口と展望スペースなど、階ごとの利用案内をご確認ください。建物の見学だけでも、休館や利用できない区域の案内を優先してください。',sourceIds=['access','visit']),aliases=['浅草観光センター','雷門観光案内所'])
add('ilcl-brick-building','国際子ども図書館 レンガ棟','台東区','上野','東京都台東区上野公園12-49',1906,['久留正道','真水英夫','関東地方建設局営繕部','安藤忠雄','日建設計'],['図書館','歴史建築'],'旧帝国図書館を、ガラスの増築で使い継ぐ建物。','1906年に帝国図書館として完成し、1929年の増築を経た建物です。国際子ども図書館への改修では、既存の外壁や内装を生かしながらガラスの空間などを加えました。安藤忠雄らが担当したのは改修で、1906年の原設計とは異なります。',['保存された大階段','室内から見える旧外壁','旧館とガラス部分のつながり'],[
 comp('既存部分','煉瓦・鉄骨','図書館の解説はレンガ棟を鉄骨で補強した煉瓦造としています。改修の際には免震工法を用いて既存建物を保存しました。創建部分と増築部分の構造を一律には扱いません。',['building','renewal']),
 comp('改修で加えた空間','ガラス','改修ではガラスの空間を加え、以前は外に面していた壁を室内側から見られるようにしています。歴史的な壁面と新しい透明な外皮を見比べられます。',['building','renewal'])],
 [source('history','建物の歴史','https://www.kodomo.go.jp/about/building/history','国立国会図書館 国際子ども図書館','1906年の帝国図書館落成と後年の沿革。'),source('building','施設の紹介','https://www.kodomo.go.jp/about/building/institution','国立国会図書館 国際子ども図書館','レンガ棟と2015年のアーチ棟の区別、構造、保存・増築、2002年全面開館。'),source('renewal','国際子ども図書館 レンガ棟','https://www.ktr.mlit.go.jp/eizen/shihon/eizen_shihon00000083.html','国土交通省 関東地方整備局','創建時の設計担当、改修設計の担当と2002年3月の改修竣工、保存と免震。'),source('access','交通手段・アクセス','https://www.kodomo.go.jp/use/access/access','国立国会図書館 国際子ども図書館','施設名と所在地。'),source('visit','見学（一般向け）','https://www.kodomo.go.jp/use/tour/public','国立国会図書館 国際子ども図書館','自由見学は予約不要。ガイドツアー・団体見学は事前申込み。')],
 dict(nameJa=['building'],completionYear=['history'],architects=['renewal'],address=['access'],buildingTypes=['history','building'],article=['history','building','renewal']),
 dict(status='public',officialUrl='https://www.kodomo.go.jp/use/tour/public',note='館内の自由見学は予約不要と案内されています。ガイドツアーや団体見学は事前申込みが必要です。資料を利用する人の妨げにならないよう、各室の撮影・利用条件に従ってください。',sourceIds=['visit','building']),aliases=['旧帝国図書館','帝国図書館','国際子ども図書館'],designers=[dict(name=n,role=r,sourceIds=['renewal']) for n,r in [('久留正道','創建'),('真水英夫','創建'),('関東地方建設局営繕部','改修'),('安藤忠雄','改修'),('日建設計','改修')]],factNotes=[dict(text='1906年は創建時の完成年です。2002年の改修、2015年に完成した別棟のアーチ棟とは分けています。',sourceIds=['history','building','renewal'])])
items[1]['components'][0]['sourceIds']=['construction','interior']
R.joinpath('data/additions').mkdir(exist_ok=True)
R.joinpath('data/additions/kanto-20260914.json').write_text(json.dumps(items,ensure_ascii=False,separators=(',',':'))+'\n')
# Explicit geometric evidence for the six OSM-derived points; no government diagrams are reproduced.
features=[]
for b in items:
 g=geo[b['id']]
 if 'osmId' not in g:continue
 props={k:g[k] for k in ['osmType','osmId','sourceTimestamp']};props['point']=[b['lng'],b['lat']];props['precision']='facility';props['sourceUrl']=b['sources'][-1]['url']
 features.append(dict(type='Feature',id=b['id'],properties=props,geometry=dict(type='Polygon',coordinates=[g['ring']]) if 'ring' in g else dict(type='Point',coordinates=[b['lng'],b['lat']])))
R.joinpath('data/additions/kanto-osm-evidence.geojson').write_text(json.dumps(dict(type='FeatureCollection',license='ODbL 1.0',licenseUrl='https://opendatacommons.org/licenses/odbl/1-0/',attribution='OpenStreetMap contributors',features=features),ensure_ascii=False,separators=(',',':'))+'\n')
print(len(items),len(R.joinpath('data/additions/kanto-20260914.json').read_bytes()),len(features))
