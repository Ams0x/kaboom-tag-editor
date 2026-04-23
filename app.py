import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="KaBoom TCG 官方 Tag 神器", layout="wide")
st.title("🏷️ KaBoom TCG 官方 Tag 自動化神器 (V3 全系列補齊版)")
st.write("✅ 完美捕捉歷代 PTCG (sv/s/sm/ac/sc) | ✅ 智能拆解 OPCG 卡號 | ✅ 自動修正錯誤遊戲 Tag")

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
            if any(kw in title_lower for kw in ['原盒', 'booster box', 'box', '原箱', '散包']):
                new_tags.add('type-boosterbox')
            elif any(kw in title_lower for kw in ['單卡', 'single']):
                new_tags.add('type-single')
            elif '禮盒' in title_lower:
                new_tags.add('type-giftbox')
            elif any(kw in title_lower for kw in ['卡組', '預組', 'deck']):
                new_tags.add('type-deckset')
            elif any(kw in title_lower for kw in ['卡套', 'sleeve', 'protector']):
                new_tags.add('type-sleeve')
            elif any(kw in title_lower for kw in ['卡墊', 'mat', 'playmat', '桌墊']):
                new_tags.add('type-mat')
            elif any(kw in title_lower for kw in ['卡盒', 'deckbox', '收納盒']):
                new_tags.add('type-deckbox')
            
            # 🎯 終極補底：如果無被歸類為周邊等，並且有卡號格式，就係單卡
            if not any(t in new_tags for t in ['type-boosterbox', 'type-giftbox', 'type-deckset', 'type-sleeve', 'type-mat', 'type-deckbox']):
                if re.search(r'([A-Za-z]{1,4}\d{0,2}-\d{3}|\d{1,3}/\d{1,3})', title) or is_psa or 'sp卡' in title_lower or 'sr卡' in title_lower:
                    new_tags.add('type-single')
                    
            # 品牌
            if 'dragon shield' in title_lower or 'dragonshield' in title_lower:
                new_tags.add('brand-dragonshield')
            if '寶可夢' in title_lower and any(kw in title_lower for kw in ['卡套', '卡墊', '卡盒', '收納盒']):
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
                if op_match: 
                    set_code = op_match.group(1).lower()
                else:
                    # 🌟 升級：完美支援所有 PTCG 世代 (sv, s, sm, ac, sc 及其擴充包如 sv5af)
                    ptcg_match = re.search(r'\b((?:sv|s|sm|ac|sc)\d+[a-z]{0,2})\b', title_lower)
                    if ptcg_match: 
                        set_code = ptcg_match.group(1).lower()
                    else:
                        # 🌟 升級：智能拆解 OPCG 卡號 (例如 OP10-119 -> op10, P-001 -> p)
                        card_match = re.search(r'\b([A-Za-z]{1,4}\d{0,2})-\d{3}\b', title)
                        if card_match:
                            set_code = card_match.group(1).lower()
                        else:
                            # 終極防線：透過 Shopify 網址 Handle 提取
                            handle_parts = handle.split('-')
                            if len(handle_parts) >= 2:
                                possible_set = handle_parts[1].lower()
                                if re.match(r'^[a-z0-9]+$', possible_set) and possible_set not in ['single', 'box', 'ptcg', 'tcg', 'jp', 'en', 'chi']:
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

    status_text.text("🎉 全部處理完成！所有漏網之魚（舊系列 / 特殊擴充包）已完美打上 set-！")
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(f"📥 下載 {download_filename}", csv, download_filename, "text/csv")
