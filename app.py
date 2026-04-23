import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="KaBoom TCG 官方 Tag 神器", layout="wide")
st.title("🏷️ KaBoom TCG 官方 Tag 自動化神器 (V3 完美除錯版)")
st.write("✅ 已完美支援 OPCG (OP/EB/ST) 格式 | ✅ 自動修正錯誤遊戲 Tag | ✅ 準確補齊 type-single")

uploaded_csv = st.file_uploader("📂 上傳 Shopify 產品 CSV", type=["csv"])

if st.button("🚀 根據 V3 指引一鍵補齊 Tags") and uploaded_csv:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("⚡ 正在深入分析及生成標籤...")
    
    df = pd.read_csv(uploaded_csv)
    original_filename = uploaded_csv.name
    download_filename = f"V3_Tagged_{original_filename}"

    if 'Tags' not in df.columns:
        df['Tags'] = ""

    for index, row in df.iterrows():
        title = str(row.get('Title', ''))
        handle = str(row.get('Handle', ''))
        existing_tags_str = str(row.get('Tags', ''))
        
        if pd.notna(title) and title.strip() != 'nan' and title.strip() != '':
            title_lower = title.lower()
            new_tags = set()
            
            # 先讀取舊有 Tags，方便做自動修正
            existing_tags = []
            if existing_tags_str != 'nan' and existing_tags_str.strip():
                existing_tags = [t.strip() for t in existing_tags_str.split(',') if t.strip()]
            existing_tags_lower = [t.lower() for t in existing_tags]

            # ==========================================
            # 1. 遊戲類別 (Game) & 鑑定卡 (Graded)
            # ==========================================
            is_psa = 'psa' in title_lower or '鑑定' in title_lower
            if is_psa:
                new_tags.add('game-graded')
                if 'psa' in title_lower: new_tags.add('graded-psa')
            
            is_opcg = 'opcg' in title_lower or '海賊王' in title_lower or 'one piece' in title_lower or re.search(r'\b(op\d{2}|eb\d{2}|st\d{2}|prb\d{2})\b', title_lower)
            
            if 'lorcana' in title_lower:
                new_tags.add('game-lorcana')
            elif is_opcg:
                new_tags.add('game-opcg')
                # 防呆：如果之前錯落咗 ptcg，即刻刪除
                if 'game-ptcg' in existing_tags_lower:
                    existing_tags = [t for t in existing_tags if t.lower() != 'game-ptcg']
            elif '遊戲王' in title_lower or 'yugioh' in title_lower:
                new_tags.add('game-yugioh')
            elif not ('卡套' in title_lower or '卡墊' in title_lower or '卡盒' in title_lower):
                new_tags.add('game-ptcg')

            # ==========================================
            # 2. 語言/版本 (Language)
            # ==========================================
            if any(kw in title_lower for kw in ['繁中', '中文']) or handle.upper().startswith('CHI-'):
                new_tags.add('lang-tc')
            elif any(kw in title_lower for kw in ['日版', '日文']) or handle.upper().startswith('JPN-'):
                new_tags.add('lang-jp')
            elif any(kw in title_lower for kw in ['美版', '英文']) or handle.upper().startswith('ENG-'):
                new_tags.add('lang-en')

            # ==========================================
            # 3. 產品類型 (Product Type) & 配件品牌
            # ==========================================
            if any(kw in title_lower for kw in ['原盒', 'booster box', 'box', '原箱']):
                new_tags.add('type-boosterbox')
            elif any(kw in title_lower for kw in ['單卡', 'single']):
                new_tags.add('type-single')
            elif '禮盒' in title_lower:
                new_tags.add('type-giftbox')
            elif any(kw in title_lower for kw in ['卡組', '預組', 'deck']):
                new_tags.add('type-deckset')
            elif any(kw in title_lower for kw in ['卡套', 'sleeve']):
                new_tags.add('type-sleeve')
            elif any(kw in title_lower for kw in ['卡墊', 'mat', 'playmat']):
                new_tags.add('type-mat')
            elif any(kw in title_lower for kw in ['卡盒', 'deckbox']):
                new_tags.add('type-deckbox')
            
            # 🎯 終極補底：如果無被歸類為原盒、卡套等周邊，並且有卡號格式，就係單卡！
            # 支援格式：001/073 (PTCG), 1/204 (Lorcana), OP10-119, EB02-061 (OPCG)
            if not any(t in new_tags for t in ['type-boosterbox', 'type-giftbox', 'type-deckset', 'type-sleeve', 'type-mat', 'type-deckbox']):
                if re.search(r'([A-Za-z]{1,4}\d{0,2}-\d{3}|\d{1,3}/\d{1,3})', title) or is_psa or 'sp卡' in title_lower or 'sr卡' in title_lower:
                    new_tags.add('type-single')
                    
            # 品牌
            if 'dragon shield' in title_lower or 'dragonshield' in title_lower:
                new_tags.add('brand-dragonshield')
            if '寶可夢' in title_lower and ('卡套' in title_lower or '卡墊' in title_lower):
                new_tags.add('brand-pokemon')

            # ==========================================
            # 4. 系列代號 (Set)
            # ==========================================
            set_code = None
            set_match = re.search(r'\[([A-Za-z0-9]+)\]', title)
            if set_match:
                set_code = set_match.group(1).lower()
            else:
                op_match = re.search(r'\b(op\d{2}|eb\d{2}|st\d{2}|prb\d{2})\b', title_lower)
                if op_match: set_code = op_match.group(1).lower()
                else:
                    sv_match = re.search(r'\b(sv\d+[a-z]?)\b', title_lower)
                    if sv_match: set_code = sv_match.group(1).lower()
                    else:
                        handle_parts = handle.split('-')
                        if len(handle_parts) >= 2:
                            possible_set = handle_parts[1].lower()
                            if re.match(r'^[a-z0-9]+$', possible_set) and possible_set not in ['single', 'box', 'ptcg']:
                                set_code = possible_set
            
            if set_code:
                new_tags.add(f'set-{set_code}')

            # ==========================================
            # 5. 嚴格合併 (保留中文舊 Tag，新增英文 Tag)
            # ==========================================
            tags_to_add = [t for t in new_tags if t.lower() not in [et.lower() for et in existing_tags]]
            final_tags = existing_tags + sorted(tags_to_add)
            df.at[index, 'Tags'] = ", ".join(final_tags)

        progress_bar.progress((index + 1) / len(df))

    status_text.text("🎉 全部處理完成！所有海賊王單卡已完美打上 type-single！")
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(f"📥 下載 {download_filename}", csv, download_filename, "text/csv")
