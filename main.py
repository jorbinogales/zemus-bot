import base64, hashlib, hmac, io, os, random, sqlite3, time, uuid
from urllib.parse import quote

import requests
from flask import Flask, Response, request
from PIL import Image, ImageDraw, ImageFilter

app = Flask(__name__)

FIRMA_URL = os.environ.get("FIRMA_URL", "")
VK  = os.environ["VK"]
CK  = os.environ["CK"]
CS  = os.environ["CS"]
AT  = os.environ["AT"]
ATS = os.environ["ATS"]
CLAVE = os.environ.get("CLAVE", "")
DB_PATH = os.environ.get("DB_PATH", "datos.sqlite3")

MODELO = os.environ.get("MODELO", "wai-Illustrious")
ANCHO  = int(os.environ.get("ANCHO", "896"))
ALTO   = int(os.environ.get("ALTO", "1152"))
FORMATO = "png"
MODO_LOLI = True

LOLI = (
    "loli, small stature, slim childish build, narrow hips, "
    "short legs, big head, huge eyes, round cheeks"
)

PLANTILLA = (
    "1girl, petite, hetero, {acto}, from front, looking at viewer, {personaje}, "
    "nude, flat chest, arched back, blush, half-closed eyes, tongue out, "
    "glossy skin, thick outlines, cel shading, cartoon style, {fondo}, "
    "detailed pussy lips, visible clit, detailed fingers"
)

NEGATIVO = (
    "worst quality, low quality, bad anatomy, bad hands, extra fingers, "
    "missing fingers, fused fingers, deformed, mutated, extra limbs, "
    "watermark, text, lettering, poster text, signature, blurry, jpeg artifacts, "
    "cropped head, matte skin, dull skin, soft shading, airbrush, gradient, "
    "painterly, 3d render, thin uniform lineart, sketch, pastel"
)

FALLBACK_ESTILO = (
    "1girl, petite, glossy skin, thick outlines, cel shading, cartoon style, "
    "white bed"
)

CATALOGO = """
Fern|Frieren|long purple hair, purple eyes
Frieren|Frieren|long silver twintails, green eyes
Ubel|Frieren|short purple hair, purple eyes
Sense|Frieren|long purple hair, purple eyes
Edel|Frieren|long silver hair, red eyes
Aura|Frieren|long purple hair, red eyes
Tsuyu Asui|My Hero Academia|long black hair tied low, large black eyes
Ochaco Uraraka|My Hero Academia|brown bob, big brown eyes
Momo Yaoyorozu|My Hero Academia|long black ponytail
Kyoka Jiro|My Hero Academia|short dark purple hair
Mina Ashido|My Hero Academia|pink hair, black sclera
Itsuka Kendo|My Hero Academia|orange ponytail, teal eyes
Nejire Hado|My Hero Academia|long blue hair
Himiko Toga|My Hero Academia|messy blonde buns, yellow eyes
Mt. Lady|My Hero Academia|long blonde hair
Midnight|My Hero Academia|long dark blue hair
Mirko|My Hero Academia|long white hair, red eyes
Hinata Hyuga|Naruto|long dark blue hair, pale eyes
Sakura Haruno|Naruto|pink hair, green eyes
Ino Yamanaka|Naruto|blonde ponytail
Temari|Naruto|blonde ponytail, teal eyes
Tsunade|Naruto|long blonde hair
Kushina Uzumaki|Naruto|long red hair
Mei Terumi|Naruto|long red hair, green eyes
Samui|Naruto|blonde ponytail
Karin Uzumaki|Naruto|long red hair, red eyes
Konan|Naruto|blue hair, paper flower
Tenten|Naruto|dark brown buns
Kaguya Otsutsuki|Naruto|long white hair, pale eyes
Anko Mitarashi|Naruto|purple hair
Kurenai Yuhi|Naruto|long dark hair, red eyes
Orihime Inoue|Bleach|long orange hair, grey eyes
Rukia Kuchiki|Bleach|short black hair, violet eyes
Yoruichi Shihouin|Bleach|long dark purple hair
Nel Tu|Bleach|long teal hair
Rangiku Matsumoto|Bleach|long blonde hair
Soi Fon|Bleach|short black hair
Tier Harribel|Bleach|blonde hair, green eyes
Nemu Kurotsuchi|Bleach|black hair
Kukaku Shiba|Bleach|black hair
Masaki Kurosaki|Bleach|long black hair
Lisa Yadomaru|Bleach|black hair, glasses
Nami|One Piece|long orange hair
Nico Robin|One Piece|long black hair, blue eyes
Boa Hancock|One Piece|long black hair
Perona|One Piece|pink twintails, red eyes
Viola|One Piece|long black hair
Rebecca|One Piece|long blonde hair
Yamato|One Piece|long white hair, red horns
Ulti|One Piece|long teal hair, mask
Carrot|One Piece|blonde hair, bunny ears
Shirahoshi|One Piece|long pink hair
Koala|One Piece|short orange hair
Tashigi|One Piece|short black hair, glasses
Hina|One Piece|long pink hair
Uta|One Piece|red and white hair
Vivi|One Piece|blue hair
Charlotte Pudding|One Piece|pink hair, third eye
Reiju Vinsmoke|One Piece|pink hair
Nojiko|One Piece|blue hair
Kalifa|One Piece|blonde hair, glasses
Bulma|Dragon Ball|short turquoise hair
Chi-Chi|Dragon Ball|long black hair
Android 18|Dragon Ball|short blonde hair, blue eyes
Videl|Dragon Ball|short black hair
Pan|Dragon Ball|short black hair, orange bandana
Caulifla|Dragon Ball|black spiky hair
Kale|Dragon Ball|black hair
Launch|Dragon Ball|blonde hair
Marron|Dragon Ball|blonde hair
Cheelai|Dragon Ball|white hair, red eyes
Nobara Kugisaki|Jujutsu Kaisen|short brown hair
Maki Zenin|Jujutsu Kaisen|green ponytail, glasses
Mai Zenin|Jujutsu Kaisen|green ponytail
Shoko Ieiri|Jujutsu Kaisen|brown hair
Yuki Tsukumo|Jujutsu Kaisen|blonde hair
Kasumi Miwa|Jujutsu Kaisen|blue hair
Mei Mei|Jujutsu Kaisen|long black hair
Utahime Iori|Jujutsu Kaisen|long black hair
Nezuko Kamado|Demon Slayer|long black hair with orange tips, pink eyes
Shinobu Kocho|Demon Slayer|black hair with purple tips
Mitsuri Kanroji|Demon Slayer|pink and green hair
Kanao Tsuyuri|Demon Slayer|black hair, butterfly hairpin
Aoi Kanzaki|Demon Slayer|black ponytail
Daki|Demon Slayer|long black hair with green tips
Tamayo|Demon Slayer|black hair, purple eyes
Makima|Chainsaw Man|long red hair, yellow eyes
Power|Chainsaw Man|long pink hair, red horns
Himeno|Chainsaw Man|long black hair, eyepatch
Kobeni Higashiyama|Chainsaw Man|short black hair
Reze|Chainsaw Man|short black hair, green eyes
Asa Mitaka|Chainsaw Man|short black hair
Yoru|Chainsaw Man|black hair, ringed eyes
Raiden Shogun|Genshin Impact|long purple braid
Yae Miko|Genshin Impact|long pink hair, fox ears
Hu Tao|Genshin Impact|brown twintails, flower pupils
Ganyu|Genshin Impact|blue hair, horns
Keqing|Genshin Impact|purple twintails
Lumine|Genshin Impact|blonde hair, golden eyes
Fischl|Genshin Impact|long blonde hair, eyepatch
Mona|Genshin Impact|dark twintails
Jean|Genshin Impact|blonde ponytail
Lisa|Genshin Impact|brown hair
Eula|Genshin Impact|light blue hair
Shenhe|Genshin Impact|white hair
Yelan|Genshin Impact|dark blue hair
Nilou|Genshin Impact|red hair
Nahida|Genshin Impact|white green hair, elf ears
Furina|Genshin Impact|white blue hair, heterochromia
Clorinde|Genshin Impact|blue hair
Arlecchino|Genshin Impact|white hair with black tips, red eyes
Navia|Genshin Impact|blonde hair
Yanfei|Genshin Impact|pink hair, horns
March 7th|Honkai Star Rail|pink hair
Kafka|Honkai Star Rail|long magenta hair
Silver Wolf|Honkai Star Rail|grey hair
Bronya|Honkai Star Rail|grey twintails
Seele|Honkai Star Rail|long purple hair, red eyes
Himeko|Honkai Star Rail|long red hair
Jingliu|Honkai Star Rail|white hair, blindfold
Acheron|Honkai Star Rail|long purple hair
Firefly|Honkai Star Rail|silver hair
Robin|Honkai Star Rail|blue hair, wings
Topaz|Honkai Star Rail|white hair
Fu Xuan|Honkai Star Rail|pink hair
Shiroko|Blue Archive|grey hair, wolf ears
Hoshino|Blue Archive|pink hair
Aru|Blue Archive|red hair
Mutsuki|Blue Archive|orange twintails
Yuuka|Blue Archive|blue hair
Nonomi|Blue Archive|blonde hair
Serika|Blue Archive|black twintails
Karin|Blue Archive|black hair, glasses
Asuna|Blue Archive|long blonde hair
Miyako|Blue Archive|brown hair, rabbit ears
Rapi|Nikke|brown hair, red eyes
Anis|Nikke|blonde twintails
Neon|Nikke|blue hair
Alice|Nikke|pink hair
Marian|Nikke|white hair
Snow White|Nikke|white hair, hood
Rupee|Nikke|blonde hair
Saber|Fate|blonde hair in bun, green eyes
Rin Tohsaka|Fate|long black twintails, aqua eyes
Sakura Matou|Fate|long purple hair
Illyasviel|Fate|long silver hair, red eyes
Medusa|Fate|long purple hair, blindfold
Jeanne d'Arc|Fate|long blonde braid
Mash Kyrielight|Fate|short pink hair, glasses
Nero Claudius|Fate|blonde hair
Scathach|Fate|long purple hair, red eyes
Ishtar|Fate|long black hair, red eyes
Ereshkigal|Fate|long blonde hair
Kama|Fate|white hair, red eyes
Mordred|Fate|blonde hair
Jack the Ripper|Fate|white hair
Abigail Williams|Fate|blonde hair
Kiyohime|Fate|green hair
Tamamo no Mae|Fate|pink hair, fox ears
Meltryllis|Fate|purple hair
Musashi|Fate|pink hair
Raikou|Fate|purple hair
Shuten|Fate|purple hair, horns
Ibaraki|Fate|blonde hair, horns
Tomoe Gozen|Fate|red hair
Suzuka|Fate|pink hair, fox ears
Morgan|Fate|blonde hair
Barghest|Fate|red hair
Baobhan Sith|Fate|blonde hair
Melusine|Fate|white hair
Nitocris|Fate|purple hair
Cleopatra|Fate|dark hair
Okita Souji|Fate|blonde hair, haori
Reimu Hakurei|Touhou|black hair, red bow
Marisa Kirisame|Touhou|blonde hair, witch hat
Sakuya Izayoi|Touhou|silver hair, maid outfit
Remilia Scarlet|Touhou|light blue hair, bat wings
Flandre Scarlet|Touhou|blonde hair, side ponytail
Patchouli Knowledge|Touhou|purple hair, nightcap
Youmu Konpaku|Touhou|short silver hair
Yuyuko Saigyouji|Touhou|pink hair, fan
Cirno|Touhou|blue hair, ice wings
Aya Shameimaru|Touhou|black hair, tengu
Kaguya Houraisan|Touhou|long black hair
Chun-Li|Street Fighter|ox horn buns, blue qipao
Cammy White|Street Fighter|short blonde hair, green eyes
Juri Han|Street Fighter|black hair, eyepatch hairpin
Sakura Kasugano|Street Fighter|short brown hair, headband
Ibuki|Street Fighter|brown hair, ninja
Menat|Street Fighter|dark hair, crystal ball
Kolin|Street Fighter|white hair
Mai Shiranui|King of Fighters|long brown hair, red outfit
Athena Asamiya|King of Fighters|purple hair
Blue Mary|King of Fighters|blonde hair
Kasumi|Dead or Alive|brown ponytail
Marie Rose|Dead or Alive|blonde twintails, petite
Honoka|Dead or Alive|pink hair
Nyotengu|Dead or Alive|black hair, wings
Lili|Tekken|long blonde hair
Asuka Kazama|Tekken|brown ponytail
Tracer|Overwatch|short brown hair, goggles
D.Va|Overwatch|brown hair
Mercy|Overwatch|blonde ponytail, halo
Widowmaker|Overwatch|purple hair
Pharah|Overwatch|black hair
Mei|Overwatch|brown hair, glasses
Ashe|Overwatch|white hair
Kiriko|Overwatch|green hair
Ahri|League of Legends|long black hair, fox ears
Akali|League of Legends|black hair, green tips
Kai'Sa|League of Legends|dark hair
Jinx|League of Legends|blue braids
Lux|League of Legends|long blonde hair
Evelynn|League of Legends|long purple hair
Jett|Valorant|white hair
Reyna|Valorant|purple hair
Viper|Valorant|black hair, green eyes
Sage|Valorant|black hair
Killjoy|Valorant|blonde hair, glasses
Gwen Tennyson|Ben 10|orange hair, blue hair clip
Charmcaster|Ben 10|white hair
Julie Yamamoto|Ben 10|black hair
Elena Validus|Ben 10|dark hair
Sam Manson|Danny Phantom|black hair, goth
Jazz Fenton|Danny Phantom|red hair
Ember McLain|Danny Phantom|blue hair
Paulina|Danny Phantom|black hair
Valerie Gray|Danny Phantom|dark hair
Kim Possible|Kim Possible|long orange hair
Shego|Kim Possible|black hair, green glow
Bonnie Rockwaller|Kim Possible|brown hair
Monique|Kim Possible|dark hair
Sam|Totally Spies|blonde hair
Clover|Totally Spies|red hair
Alex|Totally Spies|dark hair
Raven|Teen Titans|purple hair, cloak
Starfire|Teen Titans|long red hair, orange skin
Terra|Teen Titans|blonde hair
Blackfire|Teen Titans|black hair, purple skin
Katara|Avatar|brown hair, blue eyes
Azula|Avatar|black hair, amber eyes
Ty Lee|Avatar|brown ponytail
Toph|Avatar|black hair, blind eyes
Marceline|Adventure Time|long black hair, pale skin
Princess Bubblegum|Adventure Time|pink hair
Angel Dust|Hazbin Hotel|white fur, pink accents
Charlie|Hazbin Hotel|blonde hair
Vaggie|Hazbin Hotel|white hair
Loona|Helluva Boss|grey fur, wolf
Millie|Helluva Boss|red skin
Verosika|Helluva Boss|pink skin
Velma|Scooby Doo|brown bob, glasses
Daphne|Scooby Doo|red hair, purple dress
She-Ra|She-Ra|blonde hair, tiara
Catra|She-Ra|tan fur, cat ears
Adora|She-Ra|blonde ponytail
Bloom|Winx Club|red hair
Stella|Winx Club|blonde hair
Star Butterfly|Star vs|blonde hair, hearts
Janna|Star vs|brown hair
Mandy|Grim Adventures|blonde hair
Frankie Foster|Foster's|red hair
Bubbles|Powerpuff Girls|blonde hair
Blossom|Powerpuff Girls|red hair
Buttercup|Powerpuff Girls|black hair
Callie|Splatoon|black tentacles
Marie|Splatoon|grey tentacles
Pearl|Splatoon|white tentacles
Marina|Splatoon|dark tentacles
Judy Hopps|Zootopia|grey fur, rabbit
Lara Croft|Tomb Raider|brown ponytail
Aloy|Horizon|red braids
Ellie|The Last of Us|auburn hair
Abby|The Last of Us|blonde braid
Tifa Lockhart|Final Fantasy VII|long black hair, red eyes
Aerith|Final Fantasy VII|long brown braid, green eyes
Yuffie|Final Fantasy VII|short black hair
Lightning|Final Fantasy XIII|pink hair
Yuna|Final Fantasy X|brown hair
Rikku|Final Fantasy X|blonde hair
Lulu|Final Fantasy X|black hair, fur collar
Rinoa|Final Fantasy VIII|long dark hair
Garnet|Final Fantasy IX|dark hair
Beatrix|Final Fantasy IX|blonde hair
Fran|Final Fantasy XII|bunny ears, white hair
Ashe|Final Fantasy XII|blonde hair
Penelo|Final Fantasy XII|blonde hair
Vanille|Final Fantasy XIII|orange hair
Fang|Final Fantasy XIII|dark hair
Serah|Final Fantasy XIII|pink hair
Lunafreya|Final Fantasy XV|blonde hair
Aranea|Final Fantasy XV|silver hair
Cindy|Final Fantasy XV|blonde hair
2B|Nier Automata|white hair, blindfold
A2|Nier Automata|long white hair
Kaine|Nier|white hair
Triss|Witcher|red hair
Yennefer|Witcher|black hair
Ciri|Witcher|ash blonde hair
Jill Valentine|Resident Evil|short brown hair
Claire Redfield|Resident Evil|red ponytail
Ada Wong|Resident Evil|short black bob, red dress
Ashley Graham|Resident Evil|blonde hair
Lady Dimitrescu|Resident Evil|black hair, very tall
Bela Dimitrescu|Resident Evil|blonde hair
Cassandra Dimitrescu|Resident Evil|black hair
Daniela Dimitrescu|Resident Evil|red hair
Yukiko Amagi|Persona 4|long black hair, red clothes
Rise Kujikawa|Persona 4|brown hair
Chie Satonaka|Persona 4|short brown hair
Naoto Shirogane|Persona 4|blue hair, cap
Ann Takamaki|Persona 5|blonde twintails
Makoto Niijima|Persona 5|brown hair, headband
Futaba Sakura|Persona 5|orange hair
Haru Okumura|Persona 5|fluffy brown hair
Kasumi Yoshizawa|Persona 5|red ponytail
Kyoko Kirigiri|Danganronpa|long purple hair
Chiaki Nanami|Danganronpa|pink hair, hoodie
Mukuro Ikusaba|Danganronpa|black hair, freckles
Junko Enoshima|Danganronpa|blonde twintails
Aoi Asahina|Danganronpa|brown hair, tan skin
Celestia Ludenberg|Danganronpa|black twintails
Black Widow|Marvel|red hair
Scarlet Witch|Marvel|auburn hair
Rogue|Marvel|hair with white streak
Storm|Marvel|white hair, dark skin
Jean Grey|Marvel|red hair
Emma Frost|Marvel|blonde hair
Psylocke|Marvel|purple hair
Spider-Gwen|Marvel|blonde hair, hood
Mary Jane|Marvel|red hair
Black Cat|Marvel|white hair
Wasp|Marvel|brown hair
Captain Marvel|Marvel|blonde hair
Kate Bishop|Marvel|black hair
Magik|Marvel|blonde hair
X-23|Marvel|black hair
Domino|Marvel|black hair, white patch
Jubilee|Marvel|black hair
Kitty Pryde|Marvel|brown hair
Polaris|Marvel|green hair
Dazzler|Marvel|blonde hair
Mystique|Marvel|blue skin, red hair
She-Hulk|Marvel|green skin, black hair
Spider-Woman|Marvel|black hair
Silk|Marvel|black hair
Medusa|Marvel|red hair
Crystal|Marvel|blonde hair
Nico Minoru|Marvel|black hair, streak
Karolina Dean|Marvel|blonde hair, glow
Gwenpool|Marvel|pink hair
Hela|Marvel|black hair, headdress
Enchantress|Marvel|blonde hair
Wonder Woman|DC|black hair, tiara
Harley Quinn|DC|blonde pigtails
Catwoman|DC|black hair, catsuit
Poison Ivy|DC|red hair, green skin
Supergirl|DC|blonde hair
Batgirl|DC|red hair
Zatanna|DC|black hair, top hat
Power Girl|DC|blonde hair
Batwoman|DC|red hair
Huntress|DC|black hair
Black Canary|DC|blonde hair
Hawkgirl|DC|brown hair, wings
Mera|DC|red hair
Donna Troy|DC|black hair
Star Sapphire|DC|violet skin
Bleez|DC|red skin
Crush|DC|grey skin, red hair
Cheetah|DC|brown hair
Circe|DC|purple hair
Livewire|DC|blue hair
Ahsoka Tano|Star Wars|orange skin, lekku
Rey|Star Wars|brown hair, buns
Leia Organa|Star Wars|brown hair, buns
Padme Amidala|Star Wars|dark hair, ornate
Asajj Ventress|Star Wars|pale skin, bald
Bo-Katan|Star Wars|red hair
Hera Syndulla|Star Wars|green twi'lek
Sabine Wren|Star Wars|colorful hair
Aayla Secura|Star Wars|blue twi'lek
Holo|Spice and Wolf|long brown hair, wolf ears
Rias Gremory|Highschool DxD|long crimson hair
Akeno Himejima|Highschool DxD|long black ponytail
Asia Argento|Highschool DxD|blonde hair
Koneko Toujou|Highschool DxD|white hair, cat ears
Kuroka|Highschool DxD|black hair, cat ears
Xenovia|Highschool DxD|blue hair
Irina|Highschool DxD|brown hair
Ravel Phenex|Highschool DxD|blonde hair
Serafall|Highschool DxD|black twintails
Grayfia|Highschool DxD|silver hair
Emilia|Re:Zero|long silver hair, purple eyes
Rem|Re:Zero|short blue hair
Ram|Re:Zero|short pink hair
Echidna|Re:Zero|long white hair
Megumin|Konosuba|brown hair, eyepatch
Aqua|Konosuba|long blue hair
Darkness|Konosuba|long blonde hair
Wiz|Konosuba|brown hair
Asuna|Sword Art Online|long chestnut hair
Sinon|Sword Art Online|blue hair
Leafa|Sword Art Online|blonde ponytail
Alice Zuberg|Sword Art Online|blonde hair
Yor Forger|Spy x Family|black hair, red eyes
Anya Forger|Spy x Family|pink hair
Ai Hoshino|Oshi no Ko|long purple hair, star eyes
Ruby Hoshino|Oshi no Ko|blonde hair, star eyes
Kaguya Shinomiya|Kaguya-sama|long black hair
Chika Fujiwara|Kaguya-sama|pink hair
Ai Hayasaka|Kaguya-sama|blonde hair
Miko Iino|Kaguya-sama|brown hair
Marin Kitagawa|My Dress-Up Darling|blonde hair
Nagatoro|Ijiranaide Nagatoro|long dark hair, tan skin
Komi Shouko|Komi-san|long black hair
Najimi|Komi-san|pink hair
Uzaki Hana|Uzaki-chan|short hair, fangs
Yui Hirasawa|K-On|brown hair
Mio Akiyama|K-On|long black hair
Azusa Nakano|K-On|black twintails
Ritsu Tainaka|K-On|brown hair, headband
Mugi|K-On|blonde hair, thick eyebrows
Hatsune Miku|Vocaloid|long turquoise twintails
Megurine Luka|Vocaloid|long pink hair
Kagamine Rin|Vocaloid|blonde bob
IA|Vocaloid|long white hair
Gumi|Vocaloid|green hair
Lily|Vocaloid|blonde hair
Uzuki Shimamura|Idolmaster|brown hair
Rin Shibuya|Idolmaster|brown hair
Honoka Kousaka|Love Live|orange hair
Kotori Minami|Love Live|grey hair
Umi Sonoda|Love Live|blue hair
Bayonetta|Bayonetta|black hair, glasses
Samus|Metroid|blonde hair, zero suit
Zelda|Zelda|blonde hair
Peach|Mario|blonde hair, crown
Daisy|Mario|brown hair, crown
Rosalina|Mario|blue hair
Morrigan|Darkstalkers|green hair, bat wings
Felicia|Darkstalkers|blue hair, cat
Taki|Soulcalibur|black hair, ninja
Ivy Valentine|Soulcalibur|dark hair, whip
Talim|Soulcalibur|dark hair
Tira|Soulcalibur|black hair, ring blade
Cortana|Halo|blue hologram
Max Caulfield|Life is Strange|brown hair
Chloe Price|Life is Strange|blue hair
Juliet Starling|Lollipop Chainsaw|blonde ponytail
Maka Albarn|Soul Eater|ash blonde twin tails
Blair|Soul Eater|blonde hair, cat
Medusa|Soul Eater|blonde hair, snakes
Lucy Heartfilia|Fairy Tail|long blonde hair
Erza Scarlet|Fairy Tail|long red hair
Mirajane|Fairy Tail|long white hair
Wendy Marvell|Fairy Tail|blue hair
Juvia Lockser|Fairy Tail|blue hair
Levy|Fairy Tail|blue hair, glasses
Yoko Littner|Gurren Lagann|long red hair, rifle
Nia Teppelin|Gurren Lagann|blue hair
Satsuki Kiryuin|Kill la Kill|long black hair
Ryuko Matoi|Kill la Kill|short black hair, red streak
Mako Mankanshoku|Kill la Kill|brown hair
Nonon Jakuzure|Kill la Kill|pink hair
Motoko Kusanagi|Ghost in the Shell|short dark hair
Revy|Black Lagoon|brown hair, tattoo
Shiki Ryougi|Kara no Kyoukai|long black hair
Usagi Tsukino|Sailor Moon|long blonde twintails
Ami Mizuno|Sailor Moon|short blue hair
Rei Hino|Sailor Moon|long black hair
Makoto Kino|Sailor Moon|brown ponytail
Minako Aino|Sailor Moon|long blonde hair
Setsuna Meiou|Sailor Moon|long black hair
Haruka Tenou|Sailor Moon|short blonde hair
Michiru Kaioh|Sailor Moon|teal hair
Madoka Kaname|Madoka Magica|pink twintails
Homura Akemi|Madoka Magica|long black hair
Mami Tomoe|Madoka Magica|blonde twintails
Kyoko Sakura|Madoka Magica|red ponytail
Sayaka Miki|Madoka Magica|blue hair
Kurumi Tokisaki|Date A Live|black hair, clock eye
Tohka Yatogami|Date A Live|purple hair
Origami Tobiichi|Date A Live|white hair
Yoshino|Date A Live|blue hair, bunny hood
Miku Izayoi|Date A Live|purple hair
Kotori Itsuka|Date A Live|red hair
Natsumi|Date A Live|brown hair
Ichika Nakano|Quintuplets|pink hair
Nino Nakano|Quintuplets|pink twintails
Miku Nakano|Quintuplets|brown hair, headphones
Yotsuba Nakano|Quintuplets|orange hair, ribbon
Itsuki Nakano|Quintuplets|red hair
Milim Nava|Slime|pink hair, horns
Shion|Slime|purple hair
Shuna|Slime|pink hair
Hinata Sakaguchi|Slime|purple hair
Treyni|Slime|green hair
Velzard|Slime|white hair
Velgrynd|Slime|red hair
Raphtalia|Shield Hero|brown hair, raccoon ears
Filo|Shield Hero|blonde hair, wings
Roxy Migurdia|Mushoku Tensei|blue hair
Eris Boreas Greyrat|Mushoku Tensei|red hair
Sylphiette|Mushoku Tensei|green hair
Albedo|Overlord|long blonde hair, horns
Shalltear|Overlord|silver hair, fangs
Aura Bella Fiora|Overlord|dark elf, blonde
Yuri Alpha|Overlord|black hair, maid
Shinobu Oshino|Monogatari|blonde hair
Hitagi Senjougahara|Monogatari|long purple hair
Nadeko Sengoku|Monogatari|brown hair
Suruga Kanbaru|Monogatari|brown hair
Tsubasa Hanekawa|Monogatari|black hair, white streaks
Asuka Langley|Evangelion|orange hair
Rei Ayanami|Evangelion|blue hair
Misato Katsuragi|Evangelion|purple hair
Mari Makinami|Evangelion|brown hair, glasses
Ritsuko Akagi|Evangelion|short blonde hair
Mikasa Ackerman|Attack on Titan|short black hair
Annie Leonhart|Attack on Titan|blonde hair in bun
Historia Reiss|Attack on Titan|blonde hair
Sasha Blouse|Attack on Titan|brown hair
Pieck Finger|Attack on Titan|black hair
Violet Evergarden|Violet Evergarden|long blonde hair
Tohru|Dragon Maid|blonde hair, horns
Kanna|Dragon Maid|white hair, horns
Elma|Dragon Maid|black hair, horns
Lucoa|Dragon Maid|blonde hair
Ilulu|Dragon Maid|pink hair, horns
Chizuru Mizuhara|Rent a Girlfriend|long brown hair
Ruka Sarashina|Rent a Girlfriend|short black hair
Mami Nanami|Rent a Girlfriend|blonde hair
Sumi Sakurasawa|Rent a Girlfriend|pink hair
Mai Sakurajima|Bunny Girl Senpai|long black hair
Rio Futaba|Bunny Girl Senpai|brown hair, glasses
Tomoe Koga|Bunny Girl Senpai|blonde hair
Kyoko Hori|Horimiya|long brown hair
Remi Ayasaki|Horimiya|blonde hair
Tsukasa Yuzaki|Tonikawa|long pink hair
Chitoge Kirisaki|Nisekoi|long blonde hair
Kosaki Onodera|Nisekoi|brown hair
Yukino Yukinoshita|Oregairu|long black hair
Yui Yuigahama|Oregairu|pinkish hair
Iroha Isshiki|Oregairu|brown hair
Kaori Miyazono|Your Lie in April|blonde hair
Mikoto Misaka|Railgun|brown hair
Kuroko Shirai|Railgun|brown twintails
Ruiko Saten|Railgun|black hair
Index|Index|silver hair, nun
Yumeko Jabami|Kakegurui|long black hair
Mary Saotome|Kakegurui|blonde twintails
Kirari Momobami|Kakegurui|long white hair
Runa Yomozuki|Kakegurui|pink hair
Midari Ikishima|Kakegurui|short black hair
Eru Chitanda|Hyouka|long black hair
Nagisa Furukawa|Clannad|brown hair
Tomoyo Sakagami|Clannad|silver hair
Kyou Fujibayashi|Clannad|purple hair
Haruhi Suzumiya|Haruhi|brown hair, yellow ribbon
Mikuru Asahina|Haruhi|brown hair, maid
Yuki Nagato|Haruhi|purple hair
Tsuruya|Haruhi|green hair
Marnie|Pokemon|black hair, punk
Nessa|Pokemon|dark skin, blue hair
Sonia|Pokemon|orange hair
Misty|Pokemon|orange hair, side ponytail
Serena|Pokemon|honey hair
Dawn|Pokemon|blue hair
May|Pokemon|brown hair, bandana
Lillie|Pokemon|blonde hair
Mallow|Pokemon|green hair
Lana|Pokemon|blue hair
Cynthia|Pokemon|blonde hair, black coat
Elesa|Pokemon|blonde hair
Skyla|Pokemon|red hair
Sabrina|Pokemon|dark hair
Erika|Pokemon|black hair
Lorelei|Pokemon|red hair
Palutena|Kid Icarus|green hair
Shantae|Shantae|purple hair, genie
Risky Boots|Shantae|purple hair, pirate
Rouge|Sonic|white fur, bat
Amy Rose|Sonic|pink hair
Blaze|Sonic|purple cat
Coco Bandicoot|Crash|blonde hair
Tawna|Crash|blonde hair
Carmelita Fox|Sly|blue fur
Regina|Dino Crisis|red hair
Aya Brea|Parasite Eve|brown hair
Faith Connors|Mirror's Edge|black hair, tattoo
Chell|Portal|brown ponytail
Alyx Vance|Half-Life|short black hair
Jade|Beyond Good and Evil|green skin
Nariko|Heavenly Sword|red hair
Rukia Kuchiki|Bleach|short black hair, violet eyes
Kaguya Shinomiya|Kaguya-sama|long black hair
"""

_vistos = set()
PERSONAJES = []
for _l in CATALOGO.strip().splitlines():
    _p = [x.strip() for x in _l.split("|")]
    if len(_p) == 3 and _p[0] and _p[0] not in _vistos:
        _vistos.add(_p[0])
        PERSONAJES.append(tuple(_p))

ACTOS = [
    ("doggystyle, man behind her, arched back", "duo"),
    ("doggystyle, ass up high, back arched, looking back at viewer", "duo"),
    ("masturbating, two fingers inside her pussy, legs spread wide", "solo"),
    ("rubbing her clit, hips bucking, toes curled", "solo"),
    ("dildo penetration, hand on the base", "solo"),
    ("presenting herself, ass up high, pussy and asshole visible", "solo"),
    ("lying on back, knees pulled up and spread wide, pussy exposed", "solo"),
    ("squatting over a toy, facing the viewer", "solo"),
    ("missionary penetration, legs lifted and spread", "duo"),
    ("cowgirl, riding, facing the viewer, hands on his chest", "duo"),
    ("standing fuck, lifted and pinned against a wall", "duo"),
    ("blowjob, kneeling, cock in her mouth, eyes up", "duo"),
    ("cumshot on her face, tongue out", "duo"),
    ("creampie, cum dripping from her pussy", "duo"),
    ("carried in his arms, impaled on his cock, feet off the ground", "duo"),
    ("sitting on his lap, cock buried inside her, arms around his neck", "duo"),
]

EXPRESIONES = [
    "blush, half-closed eyes, tongue out",
    "heavy blush, half-closed eyes, tongue out, sweat",
    "blush, biting lip, half-closed eyes",
    "ahegao, tongue out, sweat",
    "blush, wide eyes, open mouth",
]

FONDOS = [
    "white bed", "white bed", "white bedsheet", "white bed, flat cyan wall",
]

PAREJA = "one adult man, muscular, dark skin, short dark hair, big cock, size difference"


def _pe(s):
    return quote(str(s), safe="~")


def _firmar(metodo, url):
    o = {
        "oauth_consumer_key": CK, "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": AT, "oauth_version": "1.0",
    }
    orden = "&".join(f"{_pe(k)}={_pe(v)}" for k, v in sorted(o.items()))
    base = f"{metodo.upper()}&{_pe(url)}&{_pe(orden)}"
    clave = f"{_pe(CS)}&{_pe(ATS)}".encode()
    o["oauth_signature"] = base64.b64encode(
        hmac.new(clave, base.encode(), hashlib.sha1).digest()).decode()
    return {"Authorization": "OAuth " + ", ".join(
        f'{_pe(k)}="{_pe(v)}"' for k, v in sorted(o.items()))}


CABECERAS_IMG = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Referer": "https://catbox.moe/",
}


def _db():
    con = sqlite3.connect(DB_PATH, timeout=20)
    con.execute("CREATE TABLE IF NOT EXISTS log "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER, datos TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS reservas "
                "(mid TEXT PRIMARY KEY, personaje TEXT, acto TEXT, texto TEXT, "
                "alt TEXT, ts INTEGER, thumb TEXT)")
    return con


def _log(datos):
    try:
        con = _db()
        con.execute("INSERT INTO log (ts, datos) VALUES (?, ?)",
                    (int(time.time()), str(datos)))
        con.execute("DELETE FROM log WHERE id NOT IN "
                    "(SELECT id FROM log ORDER BY id DESC LIMIT 200)")
        con.commit()
        con.close()
    except Exception:
        pass


def _guardar_reserva(mid, personaje, acto, texto, alt, datos=None):
    try:
        con = _db()
        con.execute("INSERT OR REPLACE INTO reservas "
                    "(mid, personaje, acto, texto, alt, ts, thumb) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (mid, personaje, acto, texto, alt, int(time.time()),
                     _miniatura(datos)))
        con.execute("DELETE FROM reservas WHERE mid NOT IN "
                    "(SELECT mid FROM reservas ORDER BY ts DESC LIMIT 10)")
        con.commit()
        con.close()
    except Exception:
        pass


def _miniatura(datos):
    if not datos:
        return ""
    try:
        im = Image.open(io.BytesIO(datos)).convert("RGB")
        im.thumbnail((480, 480))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=65)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


def _poner_firma(datos, url):
    try:
        r = requests.get(url, headers=CABECERAS_IMG, timeout=30)
        if r.status_code != 200 or len(r.content) < 500:
            return datos

        base = Image.open(io.BytesIO(datos)).convert("RGBA")
        logo = Image.open(io.BytesIO(r.content)).convert("RGBA")

        ancho = int(base.width * 0.16)
        logo = logo.resize((ancho, int(logo.height * ancho / logo.width)), Image.LANCZOS)
        margen = int(base.width * 0.03)
        destino = (base.width - logo.width - margen, base.height - logo.height - margen)

        if logo.getextrema()[3][0] < 250:
            halo = logo.split()[3].filter(ImageFilter.MaxFilter(9))
            blanco = Image.new("RGBA", logo.size, (255, 255, 255, 255))
            blanco.putalpha(halo)
            base.alpha_composite(blanco, destino)
            base.alpha_composite(logo, destino)
        else:
            pad = int(ancho * 0.25)
            badge = Image.new("RGBA", (logo.width + pad * 2, logo.height + pad * 2),
                              (255, 255, 255, 240))
            mascara = Image.new("L", badge.size, 0)
            ImageDraw.Draw(mascara).rounded_rectangle(
                [0, 0, badge.width - 1, badge.height - 1], radius=int(pad * 0.8), fill=240)
            badge.putalpha(mascara)
            badge.paste(logo, (pad, pad), logo)
            base.alpha_composite(badge, (base.width - badge.width - margen,
                                         base.height - badge.height - margen))

        plano = Image.new("RGB", base.size, (255, 255, 255))
        plano.paste(base.convert("RGB"), (0, 0), base.split()[3])
        if plano.convert("L").getextrema()[1] < 12:
            return datos
        salida = io.BytesIO()
        plano.save(salida, "PNG")
        return salida.getvalue()
    except Exception:
        return datos


def _negro(b64):
    try:
        return Image.open(io.BytesIO(base64.b64decode(b64))).convert("L").getextrema()[1] < 12
    except Exception:
        return True


def _protegido():
    return not CLAVE or request.args.get("clave") == CLAVE


@app.route("/")
def inicio():
    return {"ok": True, "rutas": ["/generar", "/ver", "/log", "/modelos"]}


@app.route("/generar")
def generar():
    if not _protegido():
        return {"error": "clave"}, 401
    q = request.args
    dry = q.get("dry") == "1"
    excluir = q.get("excluir") or ""
    loli_on = (q.get("loli") or ("1" if MODO_LOLI else "0")) == "1"
    modelo = q.get("modelo") or MODELO
    variantes = int(q.get("variantes") or 1)
    usar_neg = q.get("neg") == "1"
    semilla = int(q.get("seed") or random.randint(1, 999999999))
    ancho = int(q.get("w") or ANCHO)
    alto = int(q.get("h") or ALTO)
    pasos = int(q["pasos"]) if q.get("pasos") else None
    cfg = float(q["cfg"]) if q.get("cfg") else None
    tope = 2 if variantes > 1 else 1

    pool = [p for p in PERSONAJES if p[0] != excluir] or PERSONAJES
    nombre, franquicia, rasgos = random.choice(pool)

    imagenes = []
    ultimo_error = None
    usados = []

    for _ in range(3):
        p_actos = ACTOS
        if loli_on and random.random() < 0.75:
            p_actos = [a for a in ACTOS if a[1] == "duo"]
        acto, tipo = random.choice(p_actos)
        usados.append(acto)
        expresion = random.choice(EXPRESIONES)
        fondo = random.choice(FONDOS)

        base_pj = f"{nombre} from {franquicia}, {rasgos}"
        if loli_on:
            base_pj = f"{base_pj}, {LOLI}"
        if tipo == "duo":
            base_pj = f"{base_pj}, 1boy, {PAREJA}"
        else:
            base_pj = base_pj.replace("hetero, ", "")

        prompt = q.get("prompt") or PLANTILLA.format(
            acto=acto, personaje=base_pj, fondo=fondo)

        cuerpo = {"model": modelo, "prompt": prompt, "width": ancho, "height": alto,
                  "format": FORMATO, "variants": variantes,
                  "safe_mode": False, "seed": semilla}
        if pasos:
            cuerpo["steps"] = pasos
        if cfg:
            cuerpo["cfg_scale"] = cfg
        if usar_neg and NEGATIVO:
            cuerpo["negative_prompt"] = NEGATIVO

        g = requests.post(
            "https://api.venice.ai/api/v1/image/generate",
            headers={"Authorization": f"Bearer {VK}", "Content-Type": "application/json"},
            json=cuerpo, timeout=240)

        if g.status_code == 200:
            lista = g.json().get("images") or []
            if lista:
                imagenes = lista[:tope]
                break
            ultimo_error = "respuesta sin imagen"
        else:
            ultimo_error = f"{g.status_code}: {g.text[:200]}"
            if g.status_code in (400, 401, 402, 403, 429):
                _log({"modo": "generacion", "estado": g.status_code, "error": ultimo_error})
                return {"etapa": "generacion", "status": g.status_code,
                        "detalle": g.text[:300]}

    modelos_probados = [modelo]
    if imagenes and _negro(imagenes[0]):
        prompt_simple = f"{FALLBACK_ESTILO}, {base_pj}, {acto}, {fondo}"
        plan = [(modelo, prompt_simple), ("chroma", prompt_simple),
                ("z-image-turbo", prompt_simple),
                (modelo, "1girl, naked, white bed")]
        for mod_fb, prom_fb in plan:
            cuerpo = {"model": mod_fb, "prompt": prom_fb, "width": ancho,
                      "height": alto, "format": FORMATO, "variants": variantes,
                      "safe_mode": False, "seed": random.randint(1, 999999999)}
            try:
                gf = requests.post(
                    "https://api.venice.ai/api/v1/image/generate",
                    headers={"Authorization": f"Bearer {VK}",
                             "Content-Type": "application/json"},
                    json=cuerpo, timeout=240)
            except Exception:
                modelos_probados.append(mod_fb + ":ex")
                continue
            if gf.status_code != 200:
                modelos_probados.append(f"{mod_fb}:{gf.status_code}")
                continue
            otra = (gf.json().get("images") or [])[:tope]
            modelos_probados.append(f"{mod_fb}:{len(otra)}")
            if otra and not _negro(otra[0]):
                imagenes = otra
                prompt = prom_fb
                modelo = mod_fb
                _log({"modo": "rescate", "modelo": mod_fb, "personaje": nombre})
                break
        else:
            imagenes = []
            ultimo_error = "todos los modelos devolvieron negro"

    if not imagenes:
        _log({"modo": "generacion", "estado": "sin_imagen", "error": ultimo_error,
              "personaje": nombre, "actos": usados, "modelos": modelos_probados})
        return {"etapa": "generacion", "error": ultimo_error,
                "personaje": nombre, "modelos_probados": modelos_probados}

    texto = f"{nombre}, loli, doggystyle.\n\n#hentai #AIart #NSFW"
    alt = f"{nombre} desnuda, {acto}, estilo cartoon de linea gruesa."

    def _preparar(b64):
        d = base64.b64decode(b64)
        if q.get("firma") != "0" and FIRMA_URL:
            d = _poner_firma(d, FIRMA_URL)
        return d

    principal = _preparar(imagenes[0])
    reserva = _preparar(imagenes[1]) if len(imagenes) > 1 else None

    if dry:
        im0 = Image.open(io.BytesIO(base64.b64decode(imagenes[0])))
        return {"etapa": "dry-run", "modelo": modelo, "modo": im0.mode,
                "tam": list(im0.size),
                "lum": im0.convert("L").getextrema(),
                "modelos_probados": modelos_probados, "prompt": prompt}

    url_up = "https://upload.twitter.com/1.1/media/upload.json"
    up = requests.post(url_up, headers=_firmar("POST", url_up),
                       files={"media": ("arte.png", principal)}, timeout=180)
    if up.status_code != 200:
        _log({"modo": "subida", "estado": up.status_code, "error": up.text[:200]})
        return {"etapa": "subida", "status": up.status_code, "detalle": up.text}
    mid = up.json()["media_id_string"]

    requests.post("https://upload.twitter.com/1.1/media/metadata/create.json",
                  headers=_firmar("POST",
                                  "https://upload.twitter.com/1.1/media/metadata/create.json"),
                  json={"media_id": mid, "alt_text": {"text": alt}}, timeout=30)

    if reserva:
        up2 = requests.post(url_up, headers=_firmar("POST", url_up),
                            files={"media": ("reserva.png", reserva)}, timeout=180)
        if up2.status_code == 200:
            _guardar_reserva(up2.json()["media_id_string"], nombre, acto,
                             texto, alt, reserva)

    url_tw = "https://api.twitter.com/2/tweets"
    r = requests.post(url_tw, headers=_firmar("POST", url_tw),
                      json={"text": texto, "media": {"media_ids": [mid]}}, timeout=30)

    _log({"modo": "publicacion", "estado": r.status_code, "personaje": nombre,
          "acto": acto, "media_id": mid, "tweet": r.text[:200]})

    return {"etapa": "publicado", "status": r.status_code, "personaje": nombre,
            "acto": acto, "respuesta": r.text}


@app.route("/ver")
def ver():
    con = _db()
    filas = con.execute("SELECT mid, personaje, acto, texto, ts, thumb "
                        "FROM reservas ORDER BY ts DESC").fetchall()
    con.close()
    html = "<meta charset='utf-8'><body style='background:#111;color:#eee;font:14px system-ui;padding:20px'><h1>Reservas</h1>"
    for mid, pj, acto, texto, ts, thumb in filas:
        img = (f"<img src='data:image/jpeg;base64,{thumb}' width=180>"
               if thumb else "sin miniatura")
        html += (f"<div style='display:flex;gap:14px;border-bottom:1px solid #333;padding:12px 0'>"
                 f"<div>{img}</div><div><b>{pj}</b><br><small>{acto}</small><br>"
                 f"<small>{time.strftime('%Y-%m-%d %H:%M', time.localtime(ts))}</small><br>"
                 f"<a style='color:#e06' href='/borrar?mid={mid}'>borrar</a></div></div>")
    html += f"<p><a style='color:#0f0' href='/reserva'>publicar la última</a></p></body>"
    return Response(html, mimetype="text/html")


@app.route("/borrar")
def borrar():
    if not _protegido():
        return {"error": "clave"}, 401
    con = _db()
    con.execute("DELETE FROM reservas WHERE mid = ?", (request.args.get("mid"),))
    con.commit()
    con.close()
    return {"ok": True}


@app.route("/reserva")
def reserva():
    if not _protegido():
        return {"error": "clave"}, 401
    con = _db()
    fila = con.execute("SELECT mid, texto FROM reservas ORDER BY ts DESC LIMIT 1").fetchone()
    if not fila:
        con.close()
        return {"error": "no hay reservas"}
    con.execute("DELETE FROM reservas WHERE mid = ?", (fila[0],))
    con.commit()
    con.close()
    url_tw = "https://api.twitter.com/2/tweets"
    r = requests.post(url_tw, headers=_firmar("POST", url_tw),
                      json={"text": fila[1], "media": {"media_ids": [fila[0]]}}, timeout=30)
    _log({"modo": "reserva", "estado": r.status_code})
    return {"etapa": "reserva", "status": r.status_code, "respuesta": r.text}


@app.route("/log")
def ver_log():
    if not _protegido():
        return {"error": "clave"}, 401
    con = _db()
    filas = con.execute("SELECT ts, datos FROM log ORDER BY id DESC LIMIT 50").fetchall()
    con.close()
    return {"log": [{"ts": t, "datos": d} for t, d in filas]}


@app.route("/modelos")
def modelos():
    if not _protegido():
        return {"error": "clave"}, 401
    r = requests.get("https://api.venice.ai/api/v1/models?type=image",
                     headers={"Authorization": f"Bearer {VK}"}, timeout=60)
    try:
        return {"modelos": [m.get("id") for m in r.json().get("data", [])]}
    except Exception:
        return {"status": r.status_code, "crudo": r.text[:400]}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
