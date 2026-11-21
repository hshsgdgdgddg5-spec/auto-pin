# 📌 Pinterest Video Paylaşım Otomasyonu (7/24 Kesintisiz)

Bu web uygulaması, belirlediğiniz video arşivini sıraya alarak **her 1 dakikada bir** (veya belirlediğiniz aralıkla) otomatik olarak Pinterest hesabınızda paylaşır. Paylaşılan videonun ürün adı/türüne göre **%100 ürüne özel** başlık, açıklama, hashtag ve arama etiketleri (Etiketlenen konular) oluşturur.

---

## 🌟 Öne Çıkan Özellikler

1. **Görseldeki Formata %100 Uyumlu İçerik:**
   - **Başlık:** Pinin ne hakkında olduğunu anlatan, ürüne özel, tıklanma odaklı SEO başlığı.
   - **Açıklama & Hashtagler:** Ürünün faydalarını anlatan ve sonuna sadece o ürünle ilgili hashtagler içeren metin.
   - **Bağlantı:** Ürününüzün satış veya web sitesi linki.
   - **Pano:** Paylaşılacak hedef pano (Örn: `Sosyal` panosu).
   - **Etiketlenen Konular (Tags):** Pinterest aramalarında öne çıkaran ürün kategorileri ve arama terimleri.
2. **1 Dakikada Bir Otomatik Paylaşım:** Arka planda çalışan kuyruk motoru sayesinde her 1 dakikada sıradaki videoyu işler ve Pinterest'e pin olarak yükler.
3. **Toplu Video Yükleme & Klasör Tarama:** Bilgisayarınızdan tek tek video yükleyebilir veya bir klasör yolu vererek yüzlerce videoyu tek tıkla sıraya ekleyebilirsiniz.
4. **Bilgisayar Kapalıyken 7/24 Çalışma:** Docker ve Bulut (Render, Railway, Fly.io, VPS) desteği ile bilgisayarınızı kapatsanız bile sunucuda çalışmaya devam eder.

---

## 🚀 1. Kendi Bilgisayarınızda Çalıştırma

Terminal veya PowerShell'de proje klasörüne gidin:

```bash
cd C:\Users\hsn10\.gemini\antigravity\scratch\pinterest-video-auto
python app.py
```

Tarayıcınızı açın ve gidin:
👉 `http://localhost:8080`

---

## ☁️ 2. BİLGİSAYAR KAPALIYKEN ÇALIŞMASI İÇİN (7/24 Bulut Kurulumu)

Bilgisayarınız kapalıyken otomasyonun durmaması için projeyi ücretsiz bir bulut sunucusuna yükleyebilirsiniz:

### A) Render.com ile 2 Dakikada Ücretsiz Dağıtım (Önerilen)
1. Bu proje klasörünü kendi GitHub hesabınıza bir repo olarak yükleyin (örn: `pinterest-auto`).
2. [Render.com](https://render.com) sitesine ücretsiz üye olun.
3. **"New +" -> "Web Service"** seçin ve GitHub reponuzu bağlayın.
4. Render ayarları otomatik algılayacaktır (`render.yaml` ve `Procfile` hazır):
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. **"Deploy Web Service"** butonuna tıklayın.
6. Size `https://pinterest-video-auto-xxxx.onrender.com` şeklinde 7/24 açık kalan bir web paneli adresi verecektir. Artık telefonunuzdan veya herhangi bir cihazdan girip "Otomasyonu Başlat" diyebilir, bilgisayarınızı tamamen kapatabilirsiniz!

### B) Railway.app veya Fly.io
- Proje içerisindeki `Dockerfile` sayesinde Railway veya Fly.io üzerinde tek tıkla `Deploy Dockerfile` seçeneğiyle de 7/24 çalıştırabilirsiniz.

---

## 🔑 3. Pinterest Hesabını Bağlama

1. [Pinterest Developers Portal](https://developers.pinterest.com/) adresine gidin ve hesabınızla giriş yapın.
2. Yeni bir uygulama oluşturun veya mevcut uygulamanızdan **Access Token** oluşturun.
   - İzinler (Scopes): `boards:read`, `pins:write`, `pins:read`, `user_accounts:read`.
3. Web panelimizde sağ üstteki **"Ayarlar & Hesap"** butonuna tıklayın.
4. **Pinterest Access Token** kısmına tokenınızı yapıştırın.
5. Hedef Pano kısmına panonuzun adını (Örn: `Sosyal`) yazın ve kaydedin.
   *(Test etmek isterseniz token kısmına `demo_token` yazıp sistemi hemen simülasyon modunda deneyebilirsiniz)*

---

## 💡 4. Videoları Paylaşma Adımları

1. **Videoları Ekleyin:** Paneldeki **"Video Yükle"** butonundan videolarınızı seçin veya **"Klasörden Toplu Çek"** ile bilgisayarınızdaki klasör yolunu verin.
2. Yapay zeka videoların isimlerinden ürünü anlayıp başlık, açıklama ve etiketleri otomatik olarak oluşturacaktır. İsterseniz **"Düzenle"** diyerek kendiniz de değiştirebilirsiniz.
3. Yeşil **"Otomasyonu Başlat (1 Dakikada 1)"** butonuna tıklayın.
4. Sistem her 1 dakikada sıradaki videoyu alıp Pinterest'te paylaşacaktır!
