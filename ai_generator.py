import os
import json
import re
import urllib.request
import urllib.error

def clean_filename_to_product(filename):
    """
    Dosya adından tüm gereksiz sayıları, kayıt etiketlerini, zaman damgalarını,
    Türkçe ve yabancı yabancı kelimeleri temizleyip 100% AKICI İNGİLİZCE ürün adı çıkarır.
    """
    name = os.path.splitext(filename)[0]
    # Parantez içindeki sayıları temizle: (1), (2), (8) vb.
    name = re.sub(r'\(\d+\)', '', name)
    # Alt çizgi, tire ve noktaları boşluk yap
    name = re.sub(r'[\-_+.]+', ' ', name)
    # Çözünürlük, en-boy ve süre (720p, 1080p, 9x16, 16x9, 6s, 15s, 60fps)
    name = re.sub(r'\b\d+x\d+\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\b\d+p\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\b\d+s\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\b\d+fps\b', '', name, flags=re.IGNORECASE)
    # Tarih ve saat kalıpları (Örn: 2026 11 04, 11 04 20 51...)
    name = re.sub(r'\b\d{2,4}\s+\d{2}\s+\d{2}.*?\b', '', name)
    # 2 basamaktan büyük tüm sayıları temizle
    name = re.sub(r'\b\d{2,}\b', '', name)
    
    # Video jenerik, platform ve çöp kelimeler
    junk_words = (
        r'\b(flow|asmr|video|vid|temp|copy|kopya|final|hd|mp4|urun|promo|reels|'
        r'shorts|tiktok|viral|trend|snapinsta|kayıt|kayit|project|prototype|request|'
        r'production|usage|instructions|showing|show|making|make|unboxing|bana|bu|'
        r'hakda|hakkinda|hakkında|nasil|nasıl|nedir|icin|için|olan|ile|olsun|cekimi|'
        r'çekimi|videosu|tarzi|rehberi|is|fuer|fur|muehelose)\b'
    )
    name = re.sub(junk_words, '', name, flags=re.IGNORECASE)
    # Kalan tekil sayıları temizle
    name = re.sub(r'\b\d+\b', '', name)
    # Özel sembolleri ve fazla boşlukları temizle
    name = re.sub(r'[^a-zA-ZçğıöşüÇĞİÖŞÜäöüÄÖÜß\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()

    # Türkçe ve Almanca Kelimeleri 100% İngilizceye Çevir
    translations = {
        "üret": "Smart Maker",
        "uret": "Smart Maker",
        "farklı": "Multi-Use",
        "farkli": "Multi-Use",
        "mekan": "Kitchen Gadget",
        "sebze": "Vegetable",
        "muz": "Banana",
        "kesen": "Slicer Cutter",
        "kes": "Slicer",
        "dograma": "Chopper Slicer",
        "doğrama": "Chopper Slicer",
        "dograyici": "Chopper Slicer",
        "doğrayıcı": "Chopper Slicer",
        "taze": "Fresh",
        "peynir": "Cheese",
        "yapimi": "Maker",
        "yapımı": "Maker",
        "portakal": "Orange",
        "greyfurt": "Grapefruit",
        "meyve": "Fruit",
        "meyveleri": "Fruit",
        "degis": "Multi-Tool",
        "değiş": "Multi-Tool",
        "alet": "Gadget Tool",
        "arac": "Tool",
        "araç": "Tool",
        "gerec": "Gadget",
        "gereç": "Gadget",
        "temizleme": "Cleaning",
        "temizlik": "Cleaning",
        "bez": "Cloth Cleaner",
        "draht": "Wire",
        "drahtreinigungstücher": "Wire Cleaning Cloth",
        "sauberkeit": "Effortless Cleaning",
        "pratik": "Practical",
        "kolay": "Easy",
        "akilli": "Smart",
        "akıllı": "Smart",
        "ev": "Home",
        "banyo": "Bathroom",
        "oda": "Room",
        "lamba": "Lamp Light",
        "isik": "Light",
        "ışık": "Light",
        "sise": "Bottle",
        "şişe": "Bottle",
        "kapak": "Cap Lid",
        "acacak": "Opener",
        "açacak": "Opener",
        "rende": "Grater Slicer",
        "rendeleme": "Grater",
        "soyucu": "Peeler",
        "soyma": "Peeler",
        "tutucu": "Holder Stand",
        "aski": "Hanger",
        "askı": "Hanger",
        "firca": "Brush",
        "fırça": "Brush",
        "sunger": "Sponge",
        "sünger": "Sponge",
        "kutu": "Organizer Box",
        "duzenleyici": "Organizer",
        "düzenleyici": "Organizer",
        "raf": "Rack Shelf",
        "canta": "Bag",
        "çanta": "Bag",
        "kilif": "Case Cover",
        "kılıf": "Case Cover",
        "masaj": "Massager",
        "sac": "Hair",
        "saç": "Hair",
        "kurutucu": "Dryer",
        "duzlestirici": "Straightener",
        "düzleştirici": "Straightener",
        "termos": "Thermal Cup",
        "bardak": "Cup Mug",
        "kahve": "Coffee",
        "cay": "Tea",
        "çay": "Tea",
        "demlik": "Brewer",
        "tava": "Pan",
        "tencere": "Pot",
        "bicak": "Knife",
        "bıçak": "Knife",
        "bileme": "Sharpener",
        "bileyici": "Sharpener",
        "yagdanlik": "Oil Dispenser",
        "yağdanlık": "Oil Dispenser",
        "sprey": "Sprayer",
        "sabunluk": "Soap Dispenser",
        "musluk": "Faucet",
        "baslik": "Nozzle",
        "başlık": "Nozzle",
        "su": "Water",
        "gecirmez": "Waterproof",
        "geçirmez": "Waterproof",
        "sarjli": "Rechargeable",
        "şarjlı": "Rechargeable",
        "kablosuz": "Wireless",
        "otomatik": "Automatic",
        "tasinabilir": "Portable",
        "taşınabilir": "Portable",
        "katlanabilir": "Foldable",
        "silikon": "Silicone",
        "paslanmaz": "Stainless Steel",
        "celik": "Steel",
        "çelik": "Steel"
    }

    words = name.split()
    translated_words = []
    for w in words:
        w_lower = w.lower()
        if w_lower in translations:
            translated_words.append(translations[w_lower])
        elif len(w) > 1 and re.match(r'^[a-zA-Z]+$', w):
            translated_words.append(w)

    name = " ".join(translated_words)
    # Fazla kelimeleri temizle (örn. tek harfler)
    valid_words = [w for w in name.split() if len(w) > 1 or w.lower() == 'a']
    name = " ".join(valid_words).strip()

    # Eğer isim çok kısa veya anlamsız kaldıysa (Örn: "Product I" veya "Db B F")
    if not name or len(name) < 4 or name.lower() in ["product i", "db b f", "special design product"]:
        return "Viral Smart Home & Kitchen Gadget"

    return name.title()

def generate_with_gemini(api_key, product_name):
    """Google Gemini API ile 100% İNGİLİZCE ürüne özel Pinterest içerikleri üretir"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt = f"""You are a professional Pinterest E-Commerce Marketing & SEO Specialist.
Create high-converting Pinterest pin content for this product in 100% ENGLISH.

CRITICAL RULES:
1. MUST BE 100% ENGLISH ONLY. Never use Turkish or any other language.
2. STRICTLY RELEVANT TO THE PRODUCT. No generic spam, no numbers, no timestamps, no technical video terms.
3. Title: Catchy, clickable, high-converting Pinterest SEO title (under 80 characters).
4. Description: Persuasive copy highlighting benefits and problem-solving features, inviting viewers to shop via the link, followed by 4-5 relevant English hashtags.
5. Tags: 4-6 English Pinterest search topics/keywords strictly about this product category.

PRODUCT: "{product_name}"

Return ONLY a valid JSON object. Format:
{{
  "title": "Engaging Product Title in English",
  "description": "Compelling product benefits description. Click the link to shop now! #amazonfinds #kitchengadgets #musthaves...",
  "tags": ["Topic 1", "Topic 2", "Topic 3", "Topic 4"]
}}"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "responseMimeType": "application/json"
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            data = json.loads(text)
            return {
                "title": data.get("title", f"{product_name} - Must-Have Gadget! ✨"),
                "description": data.get("description", f"Upgrade your daily routine with the all-new {product_name}! Super practical and durable. Click the link to shop now!\n\n#amazonfinds #viralproducts #musthaves"),
                "tags": ", ".join(data.get("tags", [product_name, "Home Gadgets", "Amazon Finds", "Must Haves"]))
            }
    except Exception as e:
        print(f"Gemini API error ({e}), switching to local English SEO engine.")
        return generate_local_seo(product_name)

def generate_local_seo(product_name):
    """100% İNGİLİZCE Akıllı Yerel SEO Motoru"""
    clean_name = product_name.strip()
    words = clean_name.split()

    # İngilizce Başlık
    title = f"{clean_name} You Didn't Know You Needed! ✨"
    if len(title) > 90:
        title = f"{clean_name} - Smart Viral Find! ✨"

    # İngilizce Hashtagler
    slug_words = [re.sub(r'[^a-zA-Z0-9]', '', w).lower() for w in words if len(w) > 2]
    tags_list = []
    if slug_words:
        tags_list.append(f"#{slug_words[0]}")
        if len(slug_words) > 1:
            tags_list.append(f"#{slug_words[1]}")
    tags_list.extend(["#amazonfinds", "#viralproducts", "#musthaves", "#tiktokmademebuyit"])
    hashtags_str = " ".join(tags_list[:5])

    # İngilizce Açıklama ve Call-to-Action
    description = (
        f"Upgrade your routine with the amazing {clean_name}! "
        f"Designed to make your life easier, faster, and more convenient. "
        f"High quality, viral favorite, and the perfect gift idea. "
        f"Click the link to shop now and get yours today!\n\n{hashtags_str}"
    )

    # İngilizce Pinterest Arama Konuları (Etiketler)
    pinterest_tags = [
        clean_name,
        "Amazon Finds",
        "Must Have Gadgets",
        "Viral Products",
        "Home Favorites"
    ]

    return {
        "title": title,
        "description": description,
        "tags": ", ".join(pinterest_tags)
    }

def generate_product_content(product_name, api_key=None):
    """Ana fonksiyon: 100% İngilizce içerik üretir"""
    if not product_name or not product_name.strip():
        product_name = "Viral Smart Gadget"

    if api_key and len(api_key.strip()) > 10:
        return generate_with_gemini(api_key.strip(), product_name)
    else:
        return generate_local_seo(product_name)
