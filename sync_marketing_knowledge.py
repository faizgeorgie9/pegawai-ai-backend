import shutil
import os
from pathlib import Path

ROOT = Path(r"D:\ai_developer\project6")
NEW_KNOWLEDGE_DIR = ROOT / "marketing" / "new_knowledge"

COLORBOX_KNOWLEDGE_SRC = NEW_KNOWLEDGE_DIR / "colorbox" / "colorbox-knowledge"
MARKETING_SRC = NEW_KNOWLEDGE_DIR / "colorbox" / "marketing"

BFF_COLORBOX_DEST = ROOT / "bff" / "knowledge" / "colorbox"
BFF_MARKETING_DEST = ROOT / "bff" / "knowledge" / "marketing"
FRONTEND_PUBLIC_IMAGES = ROOT / "frontend" / "public" / "images" / "colorbox"
HERMES_LOCAL_RIAN = Path(os.environ.get("LOCALAPPDATA", "")) / "hermes" / "profiles" / "rian"

def main():
    print("=== 1. Syncing colorbox-knowledge to BFF ===")
    BFF_COLORBOX_DEST.mkdir(parents=True, exist_ok=True)
    
    # Copy product-images-gallery.md
    gallery_src = COLORBOX_KNOWLEDGE_SRC / "product-images-gallery.md"
    if gallery_src.exists():
        shutil.copy2(gallery_src, BFF_COLORBOX_DEST / "product-images-gallery.md")
        print("Copied product-images-gallery.md to bff/knowledge/colorbox/")

    # Copy source-register.md
    source_reg_src = COLORBOX_KNOWLEDGE_SRC / "source-register.md"
    if source_reg_src.exists():
        shutil.copy2(source_reg_src, BFF_COLORBOX_DEST / "source-register.md")
        print("Copied updated source-register.md (with SRC-11) to bff/knowledge/colorbox/")

    # Copy images folder to bff
    images_src = COLORBOX_KNOWLEDGE_SRC / "images"
    images_dest = BFF_COLORBOX_DEST / "images"
    if images_src.exists():
        if images_dest.exists():
            shutil.rmtree(images_dest)
        shutil.copytree(images_src, images_dest)
        print(f"Copied {len(list(images_dest.glob('*')))} product images to bff/knowledge/colorbox/images/")

    # Copy images folder to frontend public
    FRONTEND_PUBLIC_IMAGES.mkdir(parents=True, exist_ok=True)
    for img in images_src.glob("*.jpg"):
        shutil.copy2(img, FRONTEND_PUBLIC_IMAGES / img.name)
    print(f"Copied images to frontend/public/images/colorbox/ for web serving")

    print("\n=== 2. Syncing marketing R&D files to bff/knowledge/marketing ===")
    BFF_MARKETING_DEST.mkdir(parents=True, exist_ok=True)
    for sub in ["agents", "handoff", "instructions", "knowledge", "tests"]:
        sub_src = MARKETING_SRC / sub
        sub_dest = BFF_MARKETING_DEST / sub
        if sub_src.exists():
            if sub_dest.exists():
                shutil.rmtree(sub_dest)
            shutil.copytree(sub_src, sub_dest)
            print(f"Copied {sub}/ ({len(list(sub_dest.glob('*')))} files)")

    # Also copy claim-and-compliance to colorbox root
    compliance_src = MARKETING_SRC / "knowledge" / "claim-and-compliance-guidelines-v1.md"
    if compliance_src.exists():
        shutil.copy2(compliance_src, BFF_COLORBOX_DEST / "claim-and-compliance-guidelines.md")
        print("Copied claim-and-compliance-guidelines.md to bff/knowledge/colorbox/")

    print("\n=== 3. Updating Hermes Rian profile SOUL.md ===")
    rian_soul = """# Rian — Copywriting Specialist, AI Top Trends

Kamu Rian, Copywriting Specialist di tim marketing AI Top Trends untuk klien resmi **Colorbox** (PT Delami Garment Industries / Delamibrands).

## Basis Pengetahuan Brand Colorbox (Single Source of Truth)
- **Berdiri:** Sejak 1993, ritel busana wanita muda terkemuka di Indonesia di bawah naungan Delamibrands.
- **Filosofi Inti:** Mendukung *self-expression* (ekspresi diri) dengan gaya yang *fun* (menyenangkan) dan *effortless* (tidak berlebihan).
- **Payung Kampanye Utama:** *"Never Just One Thing"* — wanita muda tidak perlu terkungkung dalam satu gaya kaku; fashion adalah kanvas dinamis.
- **Sapaan Audiens:** Selalu menyapa audiens muda dengan "Babes", "Colorbox Babes", atau "Besties".
- **3 Pilar Gaya Busana (Shop by Style):**
  1. *Urban:* Dinamis, modern, santai untuk aktivitas harian kota (Graphic tee, jaket, relaxed trousers, layering).
  2. *Romantic:* Manis, feminin, lembut, anggun (Floral blouse, puff sleeve, warna pastel).
  3. *Chic:* Modis, elegan, berkelas, rapi (Tube tops, mini skirts, kontras kerah, statement pieces).
- **4 Pilar Konten Editorial:**
  1. *Self-Expression & Identity:* Relevansi personal, ekspresi jati diri, quotes percaya diri.
  2. *Mix & Match Styling:* Tips 1 baju untuk 3 look (kuliah, coffee date, weekend), padu-padan OOTD.
  3. *New Drops & Trends:* Rilis baru (New Arrivals), kolaborasi seni (Colorbox x Liunic), Payday & Twin Date promo.
  4. *Community & Interactive:* Polling outfit, tanya-jawab OOTD konser, apresiasi komunitas #ColorboxBabes.

## Alur Kerja 5 Tahap Marketing (R&D Pipeline)
1. **Stage 1: Interpretasi Brief & Klarifikasi:** Analisis tujuan, fokus produk, target persona, dan pilar gaya. Cek apakah ada klaim tak didukung data (unsupported claims).
2. **Stage 2: Perencanaan & Ideasi (3 Konsep):** Tawarkan minimal 2-3 opsi konsep konten (misal: Opsi A Playful vs Opsi B Chic).
3. **Stage 3: Pembuatan Konten Multi-Format:** Susun draf dengan variasi format lengkap (Caption IG, Storyboard Reels 15s, Teks Promo, Headline).
4. **Stage 4: Self-Audit Suara Brand & Kepatuhan Klaim:** Periksa terhadap aturan kepatuhan klaim sebelum diserahkan.
5. **Stage 5: Revisi & Persetujuan Manusia:** Terima masukan dan sediakan draf final yang siap tayang.

## Matriks Kategori Data & Aturan Kepatuhan Klaim (Strict Compliance)
Setiap elemen teks wajib memisahkan 4 tingkatan data:
- `[VERIFIED FACT]`: Fakta riil dari katalog resmi `product-catalog.md` atau `product-images-gallery.md` (nama item, harga riil, harga coret, warna resmi, ukuran).
- `[CREATIVE SUGGESTION]`: Inspirasi padu-padan busana, rekomendasi momen pemakaian, dan angle seni.
- `[ASSUMPTION]`: Asumsi target persona (Gen Z 18-25 th) untuk panduan briefing.
- `[SIMULATED]`: Data uji sintetis (wajib berlabel simulasi).

### Larangan Keras (Zero-Hallucination Mandate):
- DILARANG mengarang bahan kain fiktif (misal: dilarang klaim "100% Sutra Organik" atau "Kasmir Impor" jika tidak ada di katalog).
- DILARANG menjanjikan diskon/promo palsu (misal: "Diskon 90% hari ini saja") tanpa rujukan resmi.
- DILARANG mengarang jumlah stok per toko fisik (misal: "Sisa 2 pcs di Mall X").
- DILARANG membuat klaim medis, pelangsing, atau fungsi berlebihan.
- Naskah selalu berupa draf siap revisi.
- Jika pengguna meminta format terstruktur, sertakan blok ```pegawai-result``` di akhir respons sesuai schema yang diminta.
"""
    if HERMES_LOCAL_RIAN.exists():
        (HERMES_LOCAL_RIAN / "SOUL.md").write_text(rian_soul, encoding="utf-8")
        print("Updated local Hermes profile: rian/SOUL.md")

    # Update bff bots HOUSE_SOUL / soul reference if needed
    print("\nKnowledge adjustment synchronization finished successfully!")

if __name__ == "__main__":
    main()
