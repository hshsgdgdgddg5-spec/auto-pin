import os
import json
import re
import hashlib
import random
import urllib.request
import urllib.error

# Türkçe -> 100% İngilizce Kelime Sözlüğü
TURKISH_TO_ENGLISH = {
    "mutfak": "Kitchen",
    "sebze": "Vegetable",
    "meyve": "Fruit",
    "meyveleri": "Fruit",
    "dograyici": "Chopper Slicer",
    "doğrayıcı": "Chopper Slicer",
    "dograma": "Chopper Slicer",
    "doğrama": "Chopper Slicer",
    "kesici": "Cutter Slicer",
    "kesen": "Slicer",
    "kes": "Slicer",
    "dilimleyici": "Slicer",
    "dilimleme": "Slicer",
    "portakal": "Orange Citrus",
    "greyfurt": "Grapefruit",
    "limon": "Lemon",
    "muz": "Banana",
    "seftali": "Peach",
    "şeftali": "Peach",
    "elma": "Apple",
    "peynir": "Cheese",
    "tereyag": "Butter",
    "tereyağ": "Butter",
    "sarimsak": "Garlic",
    "sarmısak": "Garlic",
    "sogan": "Onion",
    "soğan": "Onion",
    "yumurta": "Egg",
    "patates": "Potato",
    "domates": "Tomato",
    "temizleme": "Cleaning",
    "temizlik": "Cleaning",
    "bez": "Cloth",
    "tel": "Wire",
    "draht": "Wire",
    "firca": "Brush",
    "fırça": "Brush",
    "sunger": "Sponge",
    "sünger": "Sponge",
    "rende": "Grater",
    "rendeleme": "Grater",
    "soyucu": "Peeler",
    "soyma": "Peeler",
    "sise": "Bottle",
    "şişe": "Bottle",
    "kapak": "Cap Lid",
    "acacak": "Opener",
    "açacak": "Opener",
    "yagdanlik": "Oil Dispenser",
    "yağdanlık": "Oil Dispenser",
    "yag": "Oil",
    "yağ": "Oil",
    "sprey": "Sprayer",
    "bicak": "Knife",
    "bıçak": "Knife",
    "bileme": "Sharpener",
    "bileyici": "Sharpener",
    "lavabo": "Sink",
    "musluk": "Faucet",
    "sabunluk": "Soap Dispenser",
    "sabun": "Soap",
    "duzenleyici": "Organizer",
    "düzenleyici": "Organizer",
    "kutu": "Box",
    "raf": "Rack Shelf",
    "aski": "Hanger",
    "askı": "Hanger",
    "suzgac": "Colander",
    "süzgeç": "Colander Strainer",
    "termos": "Thermal Mug",
    "bardak": "Cup Mug",
    "kahve": "Coffee",
    "cay": "Tea",
    "çay": "Tea",
    "lamba": "Lamp Light",
    "isik": "Light",
    "ışık": "Light",
    "masaj": "Massager",
    "canta": "Bag",
    "çanta": "Bag",
    "banyo": "Bathroom",
    "ev": "Home",
    "oda": "Room",
    "akilli": "Smart",
    "akıllı": "Smart",
    "pratik": "Practical",
    "kolay": "Easy",
    "otomatik": "Automatic",
    "tasinabilir": "Portable",
    "taşınabilir": "Portable",
    "katlanabilir": "Foldable",
    "silikon": "Silicone",
    "celik": "Steel",
    "çelik": "Steel",
    "paslanmaz": "Stainless"
}

# Genişletilmiş ve Kategorilere Ayrılmış Ürün Çeviri & Tespit Sözlüğü
PRODUCT_KEYWORDS = [
    # (Regex pattern, Clean Product Name, Category)
    (r'\b(butter|tereyag|tereyağ)\b', "Butter Slicer & Storage Dispenser", "kitchen"),
    (r'\b(cheese|peynir)\b', "Rotary Cheese Grater & Slicer", "kitchen"),
    (r'\b(peach|seftali|şeftali)\b', "Fruit & Peach Divider Slicer Tool", "kitchen"),
    (r'\b(orange|portakal|citrus|narenciye|grapefruit|greyfurt|limon|lemon)\b', "Citrus Fruit Peeler & Squeezer", "kitchen"),
    (r'\b(sebze|vegetable|veggie)\b', "Multifunctional Vegetable Chopper Slicer", "kitchen"),
    (r'\b(muz|banana)\b', "Quick Banana & Soft Fruit Slicer", "kitchen"),
    (r'\b(meyve|fruit|elma|apple)\b', "Multi-Blade Fruit Peeler & Corer Tool", "kitchen"),
    (r'\b(dograma|doğrama|dograyici|doğrayıcı|chopper|slicer)\b', "High-Speed Kitchen Food Chopper & Slicer", "kitchen"),
    (r'\b(temizleme|temizlik|cleaning|bez|cloth|draht|tel|sponge|sunger|sünger)\b', "Stainless Steel Wire Cleaning Cloth", "cleaning"),
    (r'\b(rende|rendeleme|grater)\b', "Multipurpose Kitchen Grater & Shredder", "kitchen"),
    (r'\b(soyucu|soyma|peeler)\b', "Ergonomic Vegetable & Potato Peeler", "kitchen"),
    (r'\b(sise|şişe|bottle|kapak|acacak|açacak|opener)\b', "Universal Multi-Function Jar & Bottle Opener", "kitchen"),
    (r'\b(yagdanlik|yağdanlık|yag|yağ|oil|sprey|sprayer|dispenser)\b', "2-in-1 Glass Oil Dispenser & Sprayer", "kitchen"),
    (r'\b(bicak|bıçak|knife|sharpener|bileme|bileyici)\b', "Professional 3-Stage Kitchen Knife Sharpener", "kitchen"),
    (r'\b(sarimsak|sarmısak|garlic)\b', "Heavy Duty Stainless Garlic Press Crusher", "kitchen"),
    (r'\b(yumurta|egg)\b', "Auto-Rolling Refrigerator Egg Dispenser", "kitchen"),
    (r'\b(silikon|silicone|kapak|lid)\b', "Reusable Silicone Stretch Food Covers Lids", "kitchen"),
    (r'\b(tava|pan|pot|tencere)\b', "Non-Stick Multi-Section Breakfast Pan", "kitchen"),
    (r'\b(firca|fırça|brush)\b', "Dispensing Palm Dish Washing Brush", "cleaning"),
    (r'\b(lavabo|musluk|sink|faucet)\b', "360 Rotating Faucet Aerator Extender", "kitchen"),
    (r'\b(sabunluk|soap)\b', "Automatic Touchless Liquid Soap Dispenser", "bathroom"),
    (r'\b(organizer|duzenleyici|düzenleyici|kutu|box|raf|rack)\b', "Multi-Layer Countertop Organizer Rack", "organization"),
    (r'\b(aski|askı|hanger|hook)\b', "Wall Mount Space-Saving Utility Hook", "organization"),
    (r'\b(suzgac|süzgeç|colander|strainer)\b', "Snap-On Pot Food Strainer Colander", "kitchen"),
    (r'\b(termos|thermal|bardak|mug|cup)\b', "Insulated Stainless Steel Travel Mug", "lifestyle"),
    (r'\b(kahve|coffee|cay|çay)\b', "Electric Portable Milk Frother & Foamer", "kitchen"),
    (r'\b(lamba|lamp|isik|ışık|light)\b', "Wireless Magnetic Motion Sensor LED Light", "home"),
    (r'\b(masaj|massager)\b', "Deep Tissue Portable Muscle Massager", "wellness"),
    (r'\b(canta|çanta|bag)\b', "Large Capacity Travel Hanging Toiletry Bag", "lifestyle"),
    (r'\b(banyo|bathroom)\b', "Non-Slip Quick-Drying Diatomite Bath Mat", "bathroom"),
]

# İsimsiz, Rastgele Sayılı veya Generic Videolar İçin 60+ Viral Popüler Ürün Havuzu
VIRAL_PRODUCT_CATALOG = [
    ("Multifunctional 14-in-1 Vegetable Chopper", "kitchen"),
    ("Electric Rechargeable Garlic & Herb Chopper", "kitchen"),
    ("Stainless Steel Wire Cleaning Cloth Pack", "cleaning"),
    ("2-in-1 Glass Olive Oil Sprayer & Dispenser", "kitchen"),
    ("Universal Silicone Stretch Food Storage Lids", "kitchen"),
    ("Rotary Drum Cheese Grater with Hand Crank", "kitchen"),
    ("Adjustable Jar & Bottle Opener Gripper", "kitchen"),
    ("Auto-Rolling Double Tier Refrigerator Egg Holder", "kitchen"),
    ("Snap-On Silicone Heat-Resistant Pot Strainer", "kitchen"),
    ("Ergonomic 3-in-1 Avocado Slicer & Pitter", "kitchen"),
    ("Touchless Automatic Sensor Liquid Soap Dispenser", "bathroom"),
    ("Flexible 1080-Degree Swivel Faucet Extender", "kitchen"),
    ("Heavy-Duty Professional Knife Sharpener Tool", "kitchen"),
    ("Collapsible Space-Saving Kitchen Cutting Board", "kitchen"),
    ("Silicone Kitchen Faucet Sink Splash Guard", "kitchen"),
    ("Under-Cabinet Slide-Out Spice Rack Organizer", "organization"),
    ("Electric Milk Frother & Handheld Drink Whisk", "kitchen"),
    ("Magnetic Knife & Utensil Wall Strip Bar", "organization"),
    ("Portable Mini Bag Sealer for Snack Freshness", "kitchen"),
    ("Self-Draining Silicone Sponge & Soap Holder", "cleaning"),
    ("Herb Scissors with 5 Stainless Steel Blades", "kitchen"),
    ("Compact Fresh Citrus Lemon Juice Squeezer", "kitchen"),
    ("Multi-Layer Stackable Refrigerator Storage Bin", "organization"),
    ("Durable Stainless Steel Watermelon Cube Slicer", "kitchen"),
    ("Smart Motion Sensor LED Closet Night Light", "home"),
    ("Quick Defrosting Tray for Frozen Meat & Food", "kitchen"),
    ("Non-Stick 4-Cup Fried Egg & Pancake Pan", "kitchen"),
    ("Telescopic Sink Sponge Storage Rack Holder", "cleaning"),
    ("Silicone Air Fryer Reusable Liner Baskets", "kitchen"),
    ("Handheld Fruit & Vegetable Spiralizer Tool", "kitchen"),
    ("Microfiber Gap Duster with Extendable Pole", "cleaning"),
    ("360 Degree Rotating Turntable Spice Organizer", "organization"),
    ("Double-Sided Extra Absorbent Microfiber Towel", "cleaning"),
    ("Silicone Ice Cube Tray with Easy Release Push", "kitchen"),
    ("Automatic Toothpaste Dispenser & Toothbrush Holder", "bathroom"),
    ("Leak-Proof Oil Pourer with Auto Flip Cap", "kitchen"),
    ("Banana Slicer Cutter for Easy Healthy Snacks", "kitchen"),
    ("Universal Car Air Vent Phone Mount Holder", "lifestyle"),
    ("Stainless Steel Multi-Blade Apple Corer Slicer", "kitchen"),
    ("Portable USB Rechargeable Mini Smoothie Blender", "lifestyle"),
    ("Multi-Functional Meat Claws for Pulled Pork", "kitchen"),
    ("Soap Dispensing Dish Wand with Sponge Scrubber", "cleaning"),
    ("Silicone Dish Drying Mat Heat Resistant Trivet", "kitchen"),
    ("Stackable Can Dispenser Organizer for Pantry", "organization"),
    ("Stainless Steel Kitchen Shears & Herb Cutter", "kitchen"),
    ("Fast Heat-Sealing Food Bag Resealer Machine", "kitchen"),
    ("Non-Slip Ergonomic Garlic Press Rocker Peeler", "kitchen"),
    ("Expandable Over-The-Sink Colander Basket", "kitchen"),
    ("Wall Mounted Cereal & Dry Food Dispenser", "organization"),
    ("Silicone Heat-Proof Oven Mitts Gloves Set", "kitchen")
]

# 30+ Dinamik ve Tıklanabilir Pinterest Başlık Şablonu
TITLE_TEMPLATES = [
    "Why Everyone Is Obsessed With This {product}! 🔥",
    "The Viral {product} You Never Knew You Needed ✨",
    "Say Goodbye To Kitchen Hassle With This {product} 🙌",
    "This {product} Makes Daily Life 10x Easier! 💡",
    "The Viral Amazon Find You Seriously Need: {product} 🛒",
    "This Genius {product} Will Save You So Much Time ⏳",
    "Must-Have Home Find: The All-New {product} ✨",
    "How Did I Live Without This {product} Before? 🤩",
    "10/10 Highly Recommend This Clever {product}! 💯",
    "The Secret To Effortless Meal Prep: {product} 🥗",
    "Upgrade Your Space With This Viral {product} 🌿",
    "TikTok Made Me Buy It: The Ultimate {product}! 🛍️",
    "This Viral {product} Is An Absolute Game Changer! ⚡",
    "The Smartest Hack For Your Home: {product} 🏠",
    "Compact, Durable & Super Practical: {product} ⭐",
    "The Coolest {product} That Actually Works Wonders 🎯",
    "Found My New Favorite Daily Essential: {product} 💎",
    "No More Mess! This {product} Keeps Things Spotless 🧹",
    "Level Up Your Daily Routine With The Smart {product} 🥑",
    "The Perfect Problem-Solver: Meet The {product} 👏",
    "Why You Need This Viral {product} In Your Daily Routine 🌟",
    "Affordable & Brilliant: The Best {product} Review 🔥",
    "Clean & Aesthetic: The Must-Have {product} For Home 🌸",
    "The #1 Life Hack Product Everyone Is Loving: {product} 🏆",
    "Save Time & Effort Every Single Day With {product} ⏱️",
    "Pure Genius: The Modern {product} That Does It All 💎",
    "Top Rated Home Discovery: The Amazing {product} ✨",
    "Transform Your Routine Today With This {product} 🚀",
    "Super Handy & Easy To Clean: Meet The {product} 🧼",
    "The One {product} Every Household Needs Right Now 📌"
]

# 15+ Dinamik Açıklama Giriş Cümlesi (Hooks)
HOOKS = [
    "Upgrade your daily routine with the all-new {product}!",
    "Tired of spending extra time on everyday chores? Meet the {product}!",
    "This simple yet brilliant {product} is going completely viral for a reason!",
    "Say goodbye to daily hassle and hello to convenience with this {product}!",
    "Honestly one of the most satisfying and useful finds I've discovered this year: the {product}!",
    "If you love smart gadgets that solve real everyday problems, you need this {product} in your life.",
    "The easiest way to save time, reduce effort, and keep everything effortlessly organized!",
    "Make your daily tasks feel 100% effortless with the viral {product}.",
    "Looking for a practical upgrade or a clever gift idea? Look no further than this {product}!",
    "This compact, high-efficiency {product} delivers flawless performance every single time."
]

# 10+ Fayda ve Özellik Cümlesi (Benefits)
BENEFITS = [
    "Engineered with premium, durable materials designed for smooth and reliable daily use.",
    "Compact, lightweight, and modern — it fits seamlessly anywhere and is super easy to clean.",
    "Designed for maximum efficiency, safety, and ultimate convenience in your daily routine.",
    "Saves valuable space while making your preparation and cleanup 5x faster.",
    "A viral favorite that combines clean aesthetic design with practical problem-solving functionality.",
    "Say goodbye to clutter and frustration with a tool that actually works exactly as advertised.",
    "Ergonomic, heat-resistant, and built to withstand heavy daily use with zero hassle."
]

# 8+ Eyleme Çağrı Cümlesi (Call-To-Action)
CALLS_TO_ACTION = [
    "Tap the link in this pin to check price and shop now with fast shipping! 🛍️",
    "Click the link to check current discounts, colors, and order yours today! ✨",
    "Ready to make your life easier? Tap the link to shop now before it sells out! 🛒",
    "Find it easily at the link above — grab yours today with fast, secure delivery! 🚚",
    "Click the product link to explore details and shop this viral favorite now! 🔗",
    "Limited stock available — tap the link to shop yours today! ⚡"
]

# Kategoriye Özel Hashtag Setleri
CATEGORY_HASHTAGS = {
    "kitchen": [
        "#kitchengadgets", "#kitchenhacks", "#homecooking", "#amazonkitchen", 
        "#foodprep", "#kitchenfinds", "#cookingtools", "#cookingtips"
    ],
    "cleaning": [
        "#cleaninghacks", "#cleanwithme", "#kitchencleaning", "#homeclean", 
        "#cleaningmotivation", "#cleaningtips", "#tidyhome", "#cleanhouse"
    ],
    "organization": [
        "#homeorganization", "#pantryorganization", "#organizationhacks", "#declutter", 
        "#tidyhome", "#storagesolutions", "#organizedhome", "#closetorganization"
    ],
    "bathroom": [
        "#bathroomdecor", "#bathroomorganization", "#selfcare", "#bathhacks", 
        "#cleanaesthetic", "#dailyroutine", "#homeimprovement"
    ],
    "home": [
        "#homedecor", "#smarthome", "#homeessentials", "#aestheticdecor", 
        "#roomdecor", "#cozyhome", "#homefinds"
    ],
    "lifestyle": [
        "#amazonfinds", "#musthaves", "#tiktokmademebuyit", "#lifehacks", 
        "#viralproducts", "#travelessentials", "#gadgetlover"
    ]
}

def clean_filename_to_product(filename, video_id=None):
    """
    Dosya adından 100% İngilizce, ürüne özel, anlamlı ve temiz ürün adı çıkarır.
    Eğer dosya adı bir hash/sayı ise, her videoya özel viral ürün kataloğundan
    benzersiz bir ürün eşler.
    """
    raw_name = os.path.splitext(filename)[0]
    # Önce alt çizgi, tire ve noktaları boşluk yap (kelime sınırları düzgün çalışsın)
    space_name = re.sub(r'[\-_+.]+', ' ', raw_name).lower()
    
    # 1. Anahtar kelime taraması (Ürünü tespit et)
    for pattern, prod_name, cat in PRODUCT_KEYWORDS:
        if re.search(pattern, space_name, flags=re.IGNORECASE):
            return prod_name, cat

    # 2. Dosya adındaki Türkçe kelimeleri İngilizceye çevir
    clean_words = []
    for w in space_name.split():
        # Çöp kelimeleri at
        if w in ["asmr", "video", "videos", "videosu", "vid", "temp", "copy", "kopya", "final", "hd", "mp4", 
                 "urun", "ürün", "promo", "reels", "shorts", "tiktok", "viral", "snapinsta", "kayit", 
                 "kayıt", "project", "demonstration", "creation", "request", "tarzi", "tarzı", "rehberi",
                 "kullanimi", "kullanımı", "kullanma", "icin", "için", "olan", "ile"]:
            continue
        if re.match(r'^\d+$', w):
            continue
        if w in TURKISH_TO_ENGLISH:
            clean_words.append(TURKISH_TO_ENGLISH[w])
        elif len(w) > 2 and re.match(r'^[a-z]+$', w):
            clean_words.append(w.title())

    # Eğer 1'den fazla anlamlı kelime kaldıysa ve hash değilse
    if len(clean_words) >= 1 and not raw_name.lower().startswith(('aq', '1101', '62d0', '78cd', '8d45', '3312')):
        prod_title = " ".join(clean_words).title()
        if "Tool" not in prod_title and "Gadget" not in prod_title:
            prod_title += " Gadget Tool"
        return prod_title, "kitchen"

    # 3. Eğer dosya adı Instagram hash'i veya numaraysa (Örn: 1101 (1).mp4, AQMZu2...):
    # Deterministic (sabit) hash kullanarak her videoya benzersiz bir viral ürün ata
    seed_str = filename
    if video_id is not None:
        seed_str = f"{video_id}_{filename}"
    hash_val = int(hashlib.md5(seed_str.encode('utf-8')).hexdigest(), 16)
    idx = hash_val % len(VIRAL_PRODUCT_CATALOG)
    prod_name, cat = VIRAL_PRODUCT_CATALOG[idx]
    return prod_name, cat

def generate_local_seo(product_name, category="kitchen", seed_idx=0):
    """
    Her defasında FARKLI, 100% İngilizce, zengin ve dikkat çekici
    Pinterest Başlığı, Açıklaması ve Hashtaglerini üretir.
    """
    # Deterministic veya rastgele çeşitlilik indeksi
    t_idx = (seed_idx + 3) % len(TITLE_TEMPLATES)
    h_idx = (seed_idx + 1) % len(HOOKS)
    b_idx = (seed_idx + 5) % len(BENEFITS)
    c_idx = (seed_idx + 7) % len(CALLS_TO_ACTION)

    # 1. Başlık (Pinterest Pini İçin Başlık)
    title = TITLE_TEMPLATES[t_idx].format(product=product_name)
    if len(title) > 95:
        title = f"{product_name} - Smart Viral Find! ✨"

    # 2. Hashtagler (Ürüne ve Kategoriye Özel)
    cat_tags = CATEGORY_HASHTAGS.get(category, CATEGORY_HASHTAGS["kitchen"])
    # 3 kategori hashtagi seç
    selected_cat_tags = [cat_tags[(seed_idx + i) % len(cat_tags)] for i in range(3)]
    
    # Ürün adından hashtag üret
    clean_slug = re.sub(r'[^a-zA-Z0-9]', '', product_name.split()[0]).lower()
    product_hashtag = f"#{clean_slug}" if len(clean_slug) > 2 else "#smartgadgets"

    # Genel popüler hashtagler
    general_tags = ["#amazonfinds", "#musthaves", "#tiktokmademebuyit", "#lifehacks"]
    selected_gen_tags = [general_tags[(seed_idx + i) % len(general_tags)] for i in range(2)]

    hashtags_list = [product_hashtag] + selected_cat_tags + selected_gen_tags
    hashtags_str = " ".join(hashtags_list[:6])

    # 3. Açıklama (Persuasive Copy + Call to Action + Hashtags)
    hook = HOOKS[h_idx].format(product=product_name)
    benefit = BENEFITS[b_idx]
    cta = CALLS_TO_ACTION[c_idx]

    description = f"{hook} {benefit}\n\n{cta}\n\n{hashtags_str}"

    # 4. Pinterest Arama Konuları (Tags)
    tags_pool = [
        product_name,
        f"{category.title()} Gadgets",
        "Amazon Finds",
        "Must Have Products",
        "Viral Kitchen",
        "Life Hacks"
    ]
    pinterest_tags = ", ".join(tags_pool[:5])

    return {
        "title": title,
        "description": description,
        "tags": pinterest_tags
    }

def generate_product_content(product_name_or_filename, api_key=None, video_id=None):
    """
    Ana fonksiyon: Dosya adını veya ürün adını tarar;
    Her video için tamamen FARKLI ve ürününe uygun başlık, açıklama ve etiket üretir.
    """
    product_name, category = clean_filename_to_product(product_name_or_filename, video_id=video_id)
    seed_idx = video_id if (video_id is not None) else random.randint(0, 1000)
    return generate_local_seo(product_name, category=category, seed_idx=seed_idx)

if __name__ == "__main__":
    test_files = [
        "mutfak_sebze_dograyici_pro.mp4",
        "ASMR_butter_cutting_video_creation_20261015223716.mp4",
        "ASMR_cheese_slicing_video_creation_20261015223726.mp4",
        "ASMR_portakal_doğrama_videosu_is…_20261012230633.mp4",
        "1101 (1)(1).mp4",
        "AQMZu2V7KQvaVpZgZW3XkO6u8y6Kkf51NBx.mp4"
    ]
    for i, tf in enumerate(test_files):
        res = generate_product_content(tf, video_id=i+1)
        print(f"--- TEST {i+1}: {tf} ---")
        print(f"TITLE: {res['title']}")
        print(f"DESC : {res['description'][:110]}...")
        print(f"TAGS : {res['tags']}")
        print()
