import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="KaBoom TCG 官方 Tag 神器", layout="wide")
st.title("🏷️ KaBoom TCG 官方 Tag 自動化神器 (V3 標準)")
st.write("✅ 嚴格根據《KaBoom_Tag指引_完整版_v3》| ✅ 自動補齊英文 Filter Tag | ✅ 絕對保留原有中文 Tag")

uploaded_csv = st.file_uploader("📂 上傳 Shopify 產品 CSV", type=["csv"])

if st.button("🚀 根據 V3 指引一鍵補齊 Tags") and uploaded_csv:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("⚡ 正在分析及生成標籤...")
    
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
            
            # ==========================================
            # 1. 遊戲類別 (Game) & 鑑定卡 (Graded)
            # ==========================================
            is_psa = 'psa' in title_lower or '鑑定' in title_lower [cite: 52]
            if is_psa:
                new_tags.add('game-graded') [cite: 52]
                if 'psa' in title_lower: new_tags.add('graded-psa') [cite: 52]
            
            if 'lorcana' in title_lower:
                new_tags.add('game-lorcana') [cite: 52]
            elif 'opcg' in title_lower or '海賊王' in title_lower or 'one piece' in title_lower or re.search(r'\bop\d{2}\b', title_lower):
                new_tags.add('game-opcg') [cite: 50]
            elif '遊戲王' in title_lower or 'yugioh' in title_lower:
                new_tags.add('game-yugioh') [cite: 52]
            elif not ('卡套' in title_lower or '卡墊' in title_lower or '卡盒' in title_lower):
                # 預設大宗為 PTCG
                new_tags.add('game-ptcg') [cite: 46]

            # ==========================================
            # 2. 語言/版本 (Language) - PTCG 必填
            # ==========================================
            if any(kw in title_lower for kw in ['繁中', '中文']) or handle.upper().startswith('CHI-'):
                new_tags.add('lang-tc') [cite: 46]
            elif any(kw in title_lower for kw in ['日版', '日文']) or handle.upper().startswith('JPN-'):
                new_tags.add('lang-jp') [cite: 46]
            elif any(kw in title_lower for kw in ['美版', '英文']) or handle.upper().startswith('ENG-'):
                new_tags.add('lang-en') [cite: 46]

            # ==========================================
            # 3. 產品類型 (Product Type) & 配件品牌
            # ==========================================
            if any(kw in title_lower for kw in ['原盒', 'booster box', 'box']):
                new_tags.add('type-boosterbox') [cite: 46]
            elif any(kw in title_lower for kw in ['單卡', 'single']):
                new_tags.add('type-single') [cite: 46]
            elif '禮盒' in title_lower:
                new_tags.add('type-giftbox') [cite: 46]
            elif any(kw in title_lower for kw in ['卡組', '預組', 'deck']):
                new_tags.add('type-deckset') [cite: 46]
            elif any(kw in title_lower for kw in ['卡套', 'sleeve']):
                new_tags.add('type-sleeve') [cite: 52]
            elif any(kw in title_lower for kw in ['卡墊', 'mat', 'playmat']):
                new_tags.add('type-mat') [cite: 52]
            elif any(kw in title_lower for kw in ['卡盒', 'deckbox']):
                new_tags.add('type-deckbox') [cite: 52]
            
            # 如果標題冇寫「單卡」，但格式似單卡 (例如有 001/190 編號)，智能補齊 type-single
            if not any(t in new_tags for t in ['type-boosterbox', 'type-giftbox', 'type-deckset', 'type-sleeve', 'type-mat', 'type-deckbox']):
                if re.search(r'\d{3}/\d{3}', title) or is_psa:
                    new_tags.add('type-single')
                    
            # 品牌
            if 'dragon shield' in title_lower or 'dragonshield' in title_lower:
                new_tags.add('brand-dragonshield') [cite: 52]
            if '寶可夢' in title_lower and ('卡套' in title_lower or '卡墊' in title_lower):
                new_tags.add('brand-pokemon') [cite: 52]

            # ==========================================
            # 4. 系列代號 (Set)
            # ==========================================
            set_code = None
            # 優先搵中括號 [SV9a], [M2]
            set_match = re.search(r'\[([A-Za-z0-9]+)\]', title)
            if set_match:
                set_code = set_match.group(1).lower()
            else:
                # 搵 OPCG 嘅 OP13
                op_match = re.search(r'\b(op\d{2})\b', title_lower)
                if op_match: set_code = op_match.group(1).lower()
                else:
                    # 搵 PTCG 嘅 sv9, sv11b (無括號情況)
                    sv_match = re.search(r'\b(sv\d+[a-z]?)\b', title_lower)
                    if sv_match: set_code = sv_match.group(1).lower()
                    else:
                        # 終極防線：從 Handle 抽 (通常 Shopify Handle 第二格係系列)
                        handle_parts = handle.split('-')
                        if len(handle_parts) >= 2:
                            possible_set = handle_parts[1].lower()
                            if re.match(r'^[a-z0-9]+$', possible_set) and possible_set not in ['single', 'box', 'ptcg']:
                                set_code = possible_set
            
            if set_code:
                new_tags.add(f'set-{set_code}') [cite: 44]

            # ==========================================
            # 5. 嚴格合併 (保留中文舊 Tag，新增英文 Tag)
            # ==========================================
            existing_tags = []
            if existing_tags_str != 'nan' and existing_tags_str.strip():
                # 拆分現有 Tags 並清理首尾空白
                existing_tags = [t.strip() for t in existing_tags_str.split(',') if t.strip()] [cite: 57]
            
            # 過濾出需要加入嘅「新英文 Tag」，避免重複 (不分大小楷比對)
            existing_tags_lower = [t.lower() for t in existing_tags]
            tags_to_add = [t for t in new_tags if t.lower() not in existing_tags_lower]
            
            # 最終結果：舊 Tags 排前面，新 Tags 排後面，用逗號分隔
            final_tags = existing_tags + sorted(tags_to_add) [cite: 57]
            df.at[index, 'Tags'] = ", ".join(final_tags) [cite: 57]

        progress_bar.progress((index + 1) / len(df))

    status_text.text("🎉 全部處理完成！已完全按照 V3 規範打好 Tags！")
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(f"📥 下載 {download_filename}", csv, download_filename, "text/csv")
