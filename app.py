import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="KaBoom TCG 官方 Tag 神器", layout="wide")
st.title("🏷️ KaBoom TCG 官方 Tag 自動化神器 (V4)")
st.write("✅ 正確識別 PRB-02 / EB-01 / ST系列 | ✅ 防止錯誤套用OPCG系列號做PTCG")

# ==========================================
# 已知系列對照表（括號代號 → tag）
# ==========================================
SET_MAP = {
    # PTCG 繁中
    'm1l': 'set-m1l', 'm1s': 'set-m1s', 'm2': 'set-m2', 'm2a': 'set-m2a',
    'm3': 'set-m3', 'm4': 'set-m4',
    'sv1s': 'set-sv1s', 'sv1v': 'set-sv1v',
    'sv2d': 'set-sv2d', 'sv2p': 'set-sv2p',
    'sv3': 'set-sv3', 'sv3a': 'set-sv3a',
    'sv4a': 'set-sv4a', 'sv4k': 'set-sv4k', 'sv4m': 'set-sv4m',
    'sv5a': 'set-sv5a', 'sv5k': 'set-sv5k', 'sv5m': 'set-sv5m',
    'sv6': 'set-sv6', 'sv6a': 'set-sv6a',
    'sv7': 'set-sv7', 'sv7a': 'set-sv7a',
    'sv8': 'set-sv8', 'sv8a': 'set-sv8a',
    'sv9': 'set-sv9', 'sv9a': 'set-sv9a',
    'sv10': 'set-sv10',
    'sv11b': 'set-sv11b', 'sv11w': 'set-sv11w',
    # OPCG 補充包
    'op01': 'set-op01', 'op02': 'set-op02', 'op03': 'set-op03',
    'op04': 'set-op04', 'op05': 'set-op05', 'op06': 'set-op06',
    'op07': 'set-op07', 'op08': 'set-op08', 'op09': 'set-op09',
    'op10': 'set-op10', 'op11': 'set-op11', 'op12': 'set-op12',
    'op13': 'set-op13',
    # OPCG 特別系列
    'prb01': 'set-prb01', 'prb02': 'set-prb02', 'prb03': 'set-prb03',
    'eb01': 'set-eb01', 'eb02': 'set-eb02',
    'st01': 'set-st01', 'st02': 'set-st02', 'st03': 'set-st03',
    'st04': 'set-st04', 'st05': 'set-st05', 'st06': 'set-st06',
    'st07': 'set-st07', 'st08': 'set-st08', 'st09': 'set-st09',
    'st10': 'set-st10', 'st11': 'set-st11', 'st12': 'set-st12',
    'st13': 'set-st13', 'st14': 'set-st14', 'st15': 'set-st15',
    'st16': 'set-st16', 'st17': 'set-st17', 'st18': 'set-st18',
    'st19': 'set-st19', 'st20': 'set-st20',
}

# OPCG系列前綴
OPCG_PREFIXES = {'op', 'eb', 'st', 'prb'}
# PTCG系列前綴
PTCG_PREFIXES = {'sv', 's', 'sm', 'ac', 'sc', 'm'}

def detect_game(title_lower, existing_tags_lower):
    """判斷遊戲類別"""
    is_psa = 'psa' in title_lower or '鑑定' in title_lower
    is_opcg = ('opcg' in title_lower or '海賊王' in title_lower or 
               'one piece' in title_lower or
               re.search(r'[\[【](op|eb|st|prb)\d{2}[\]】]', title_lower))
    
    games = set()
    if is_psa:
        games.add('game-graded')
        if 'psa' in title_lower:
            games.add('graded-psa')
    
    if 'lorcana' in title_lower:
        games.add('game-lorcana')
    elif is_opcg:
        games.add('game-opcg')
    elif '遊戲王' in title_lower or 'yugioh' in title_lower:
        games.add('game-yugioh')
    elif not any(kw in title_lower for kw in ['卡套', '卡墊', '卡盒']):
        games.add('game-ptcg')
    
    return games

def detect_set(title, title_lower, handle):
    """判斷系列 - 核心改進邏輯"""
    set_code = None
    
    # 第一優先：搵括號內嘅代號 [SV9a] 或 【PRB-02】
    bracket_match = re.search(r'[\[【]([A-Za-z]{1,4}-?\d{1,2}[A-Za-z]?)[\]】]', title)
    if bracket_match:
        raw = bracket_match.group(1).replace('-', '').lower()
        if re.search(r'[a-z]', raw):
            set_code = raw
    
    # 第二優先：搵 OPCG 連字號格式 OP-13, PRB-02, EB-01
    if not set_code:
        opcg_match = re.search(r'\b(op|eb|st|prb)-?(\d{1,2})\b', title_lower)
        if opcg_match:
            prefix = opcg_match.group(1)
            num = opcg_match.group(2).zfill(2)
            set_code = f"{prefix}{num}"
    
    # 第三優先：搵 PTCG 系列 sv9a, sv11b
    if not set_code:
        ptcg_match = re.search(r'\b(sv\d+[a-z]?|s\d+[a-z]?|sm\d+[a-z]?)\b', title_lower)
        if ptcg_match:
            set_code = ptcg_match.group(1)
    
    # 第四優先：搵 M 系列 [M2], [M3], [M4]
    if not set_code:
        m_match = re.search(r'[\[【](m\d+[a-z]?)[\]】]', title_lower)
        if m_match:
            set_code = m_match.group(1)
    
    # 第五：從卡號拆解 PRB-019 -> prb, OP10-119 -> op10
    if not set_code:
        card_match = re.search(r'\b(op\d{2}|prb\d{2}|eb\d{2}|st\d{2})-\d{3}\b', title_lower)
        if card_match:
            set_code = card_match.group(1)
    
    # 終極防線：Handle
    if not set_code:
        parts = handle.split('-')
        if len(parts) >= 2:
            candidate = parts[1].lower()
            if (re.match(r'^[a-z0-9]+$', candidate) and 
                candidate not in ['single', 'box', 'ptcg', 'tcg', 'jp', 'en', 'chi', 'opcg']):
                set_code = candidate
    
    # 用對照表驗證
    if set_code:
        set_code = set_code.replace('-', '').lower()
        if set_code in SET_MAP:
            return SET_MAP[set_code]
        else:
            # 唔喺對照表但格式正確，都加上
            return f'set-{set_code}'
    
    return None

def process_row(title, handle, existing_tags_str):
    title_lower = title.lower()
    new_tags = set()
    
    existing_tags = []
    if existing_tags_str and existing_tags_str != 'nan':
        existing_tags = [t.strip() for t in existing_tags_str.split(',') if t.strip()]
    existing_tags_lower = [t.lower() for t in existing_tags]
    
    # 遊戲類別
    game_tags = detect_game(title_lower, existing_tags_lower)
    new_tags.update(game_tags)
    
    # 語言
    if any(kw in title_lower for kw in ['繁中', '中文']) or handle.upper().startswith('CHI-'):
        new_tags.add('lang-tc')
    elif any(kw in title_lower for kw in ['日版', '日文']) or handle.upper().startswith('JPN-'):
        new_tags.add('lang-jp')
    elif any(kw in title_lower for kw in ['美版', '英文']) or handle.upper().startswith('ENG-'):
        new_tags.add('lang-en')
    
    # 產品類型
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
    elif any(kw in title_lower for kw in ['卡墊', 'mat', 'playmat']):
        new_tags.add('type-mat')
    elif any(kw in title_lower for kw in ['卡盒', 'deckbox', '收納盒']):
        new_tags.add('type-deckbox')
    
    if not any(t in new_tags for t in ['type-boosterbox', 'type-giftbox', 'type-deckset', 
                                        'type-sleeve', 'type-mat', 'type-deckbox']):
        is_psa = 'psa' in title_lower or '鑑定' in title_lower
        if re.search(r'([A-Za-z]{1,4}\d{0,2}-\d{3}|\d{1,3}/\d{1,3})', title) or is_psa:
            new_tags.add('type-single')
    
    # 品牌
    if 'dragon shield' in title_lower or 'dragonshield' in title_lower:
        new_tags.add('brand-dragonshield')
    if '寶可夢' in title_lower and any(kw in title_lower for kw in ['卡套', '卡墊', '卡盒']):
        new_tags.add('brand-pokemon')
    
    # 系列
    set_tag = detect_set(title, title_lower, handle)
    if set_tag:
        new_tags.add(set_tag)
    
    # 合併
    tags_to_add = [t for t in new_tags if t.lower() not in existing_tags_lower]
    final_tags = existing_tags + sorted(tags_to_add)
    return ", ".join(final_tags)

# ==========================================
# UI
# ==========================================
uploaded_csv = st.file_uploader("📂 上傳 Shopify 產品 CSV", type=["csv"])

# 測試工具
st.subheader("🔍 單一產品測試")
test_title = st.text_input("輸入產品標題測試", placeholder="例如：高級補充包ONE PIECE CARD THE BEST【PRB-02】")
if test_title:
    result = process_row(test_title, '', '')
    st.success(f"**生成Tags：** {result}")

if st.button("🚀 一鍵補齊全部 Tags") and uploaded_csv:
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.text("⚡ 正在分析...")
    
    df = pd.read_csv(uploaded_csv)
    original_filename = uploaded_csv.name
    download_filename = f"V4_Tagged_{original_filename}"
    
    if 'Tags' not in df.columns:
        df['Tags'] = ""
    
    errors = []
    for index, row in df.iterrows():
        title = str(row.get('Title', ''))
        handle = str(row.get('Handle', ''))
        existing_tags_str = str(row.get('Tags', ''))
        
        if pd.notna(title) and title.strip() not in ['', 'nan']:
            try:
                df.at[index, 'Tags'] = process_row(title, handle, existing_tags_str)
            except Exception as e:
                errors.append(f"Row {index}: {e}")
        
        progress_bar.progress((index + 1) / len(df))
    
    if errors:
        st.warning(f"⚠️ {len(errors)} 個錯誤：{errors[:3]}")
    
    status_text.text("🎉 完成！")
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(f"📥 下載 {download_filename}", csv, download_filename, "text/csv")
    
    # 預覽
    st.subheader("預覽結果（首20行）")
    st.dataframe(df[['Title', 'Tags']].head(20))
