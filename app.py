import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="KaBoom TCG 官方 Tag 神器", layout="wide")
st.title("🏷️ KaBoom TCG 官方 Tag 自動化神器 (V4.2)")
st.write("✅ 正確識別 PRB-02 / EB-01 / ST系列 | ✅ 配件細分分類 | ✅ 品牌自動識別")

SET_MAP = {
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
    'op01': 'set-op01', 'op02': 'set-op02', 'op03': 'set-op03',
    'op04': 'set-op04', 'op05': 'set-op05', 'op06': 'set-op06',
    'op07': 'set-op07', 'op08': 'set-op08', 'op09': 'set-op09',
    'op10': 'set-op10', 'op11': 'set-op11', 'op12': 'set-op12',
    'op13': 'set-op13',
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

# 非TCG配件關鍵字
NON_TCG_KEYWORDS = [
    'dice', 'd6', 'd20', 'd4', 'd8', 'd10', 'd12',
    'chessex', 'diceski', 'life counter', 'coin', 'token',
    'topper', 'deck box divider', 'card stand',
]

# 品牌對照
BRAND_MAP = {
    'brand-dragonshield': ['dragon shield', 'dragonshield'],
    'brand-broccoli':     ['broccoli'],
    'brand-bushiroad':    ['bushiroad'],
    'brand-ultrapro':     ['ultra pro', 'ultrapro'],
    'brand-chessex':      ['chessex', 'diceski'],
    'brand-konami':       ['konami'],
    'brand-nintendo':     ['nintendo'],
    'brand-pokemon':      [],  # 寶可夢特殊處理
}


def detect_game(title_lower):
    if any(kw in title_lower for kw in NON_TCG_KEYWORDS):
        return set()

    is_psa = 'psa' in title_lower or '鑑定' in title_lower
    is_opcg = (
        'opcg' in title_lower or '海賊王' in title_lower or
        'one piece' in title_lower or
        bool(re.search(r'[\[【](op|eb|st|prb)\d{1,2}[\]】]', title_lower))
    )

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
    if any(kw in title_lower for kw in NON_TCG_KEYWORDS):
        return None

    # 第一優先：括號內代號 【PRB-02】或 [SV9a]
    bracket_match = re.search(r'[\[【]([A-Za-z]{1,4}-?\d{1,2}[A-Za-z]?)[\]】]', title)
    if bracket_match:
        raw = bracket_match.group(1).replace('-', '').lower()
        if re.search(r'[a-z]', raw):
            return SET_MAP.get(raw, f'set-{raw}')

    # 第二優先：OPCG連字號格式 OP-13, PRB-02（排除卡號如OP10-119）
    opcg_match = re.search(r'(?<!\w)(op|eb|st|prb)-(\d{1,2})(?!\d*-\d{3})\b', title_lower)
    if opcg_match:
        prefix = opcg_match.group(1)
        num = opcg_match.group(2).zfill(2)
        set_code = f"{prefix}{num}"
        return SET_MAP.get(set_code, f'set-{set_code}')

    # 第三優先：PTCG SV系列
    ptcg_match = re.search(r'\b(sv\d+[a-z]?|s\d+[a-z]?|sm\d+[a-z]?)\b', title_lower)
    if ptcg_match:
        code = ptcg_match.group(1)
        return SET_MAP.get(code, f'set-{code}')

    # 第四優先：M系列括號
    m_match = re.search(r'[\[【](m\d+[a-z]?)[\]】]', title_lower)
    if m_match:
        code = m_match.group(1)
        return SET_MAP.get(code, f'set-{code}')

    # 終極防線：Handle — 只信任已知對照表
    parts = handle.split('-')
    if len(parts) >= 2:
        candidate = parts[1].lower()
        if candidate in SET_MAP:
            return SET_MAP[candidate]

    return None


def detect_type(title_lower, is_psa):
    if any(kw in title_lower for kw in ['原盒', 'booster box', 'box', '原箱', '散包']):
        return 'type-boosterbox'
    elif any(kw in title_lower for kw in ['單卡', 'single']):
        return 'type-single'
    elif '禮盒' in title_lower:
        return 'type-giftbox'
    elif any(kw in title_lower for kw in ['卡組', '預組', 'deck']):
        return 'type-deckset'
    elif any(kw in title_lower for kw in ['卡套', 'sleeve', 'protector']):
        return 'type-sleeve'
    elif any(kw in title_lower for kw in ['卡墊', 'mat', 'playmat', '桌墊']):
        return 'type-mat'
    elif any(kw in title_lower for kw in ['卡盒', 'deckbox', '收納盒']):
        return 'type-deckbox'
    elif any(kw in title_lower for kw in NON_TCG_KEYWORDS):
        return 'type-other'
    elif re.search(r'([A-Za-z]{1,4}\d{0,2}-\d{3}|\d{1,3}/\d{1,3})', title_lower) or is_psa:
        return 'type-single'
    return None


def detect_brands(title_lower):
    brands = set()
    for brand_tag, keywords in BRAND_MAP.items():
        if brand_tag == 'brand-pokemon':
            continue
        if any(kw in title_lower for kw in keywords):
            brands.add(brand_tag)

    # 寶可夢品牌：只有係配件先加
    if '寶可夢' in title_lower and any(kw in title_lower for kw in ['卡套', '卡墊', '卡盒', '收納盒']):
        brands.add('brand-pokemon')

    return brands


def process_row(title, handle, existing_tags_str):
    title_lower = title.lower()
    new_tags = set()

    existing_tags = []
    if existing_tags_str and existing_tags_str not in ['nan', '']:
        existing_tags = [t.strip() for t in existing_tags_str.split(',') if t.strip()]
    existing_tags_lower = [t.lower() for t in existing_tags]

    # 遊戲類別
    new_tags.update(detect_game(title_lower))

    # 語言
    if any(kw in title_lower for kw in ['繁中', '中文']) or handle.upper().startswith('CHI-'):
        new_tags.add('lang-tc')
    elif any(kw in title_lower for kw in ['日版', '日文']) or handle.upper().startswith('JPN-'):
        new_tags.add('lang-jp')
    elif any(kw in title_lower for kw in ['美版', '英文']) or handle.upper().startswith('ENG-'):
        new_tags.add('lang-en')

    # 產品類型
    is_psa = 'psa' in title_lower or '鑑定' in title_lower
    type_tag = detect_type(title_lower, is_psa)
    if type_tag:
        new_tags.add(type_tag)

    # 品牌
    new_tags.update(detect_brands(title_lower))

    # 系列
    set_tag = detect_set(title, title_lower, handle)
    if set_tag:
        new_tags.add(set_tag)

    # 合併保留原有tag
    tags_to_add = [t for t in new_tags if t.lower() not in existing_tags_lower]
    final_tags = existing_tags + sorted(tags_to_add)
    return ", ".join(final_tags)


# ==========================================
# UI
# ==========================================
uploaded_csv = st.file_uploader("📂 上傳 Shopify 產品 CSV", type=["csv"])

st.subheader("🔍 單一產品測試")
col1, col2 = st.columns([3, 1])
with col1:
    test_title = st.text_input("輸入產品標題測試", placeholder="例如：高級補充包ONE PIECE CARD THE BEST【PRB-02】")
with col2:
    test_handle = st.text_input("Handle（可空）", placeholder="opcg-prb02-xxx")

if test_title:
    result = process_row(test_title, test_handle or '', '')
    st.success(f"**生成Tags：** `{result}`")

st.divider()

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
        st.warning(f"⚠️ {len(errors)} 個錯誤：{errors[:5]}")

    status_text.text("🎉 完成！")
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(f"📥 下載 {download_filename}", csv, download_filename, "text/csv")

    st.subheader("預覽結果（首20行）")
    st.dataframe(df[['Title', 'Tags']].head(20))
