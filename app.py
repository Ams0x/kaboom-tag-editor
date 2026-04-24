import streamlit as st
import pandas as pd
import re
import unicodedata

st.set_page_config(page_title="KaBoom TCG 官方 Tag 神器", layout="wide")
st.title("🏷️ KaBoom TCG 官方 Tag 自動化神器 (V4.8)")
st.write("✅ 修復OP11直接格式識別 | ✅ 寶可夢中文產品自動加lang-tc | ✅ PRB-02正確識別OPCG")

SET_MAP = {
    'm1l': 'set-m1l', 'm1s': 'set-m1s', 'm2': 'set-m2', 'm2a': 'set-m2a',
    'm3': 'set-m3', 'm4': 'set-m4',
    'sv1s': 'set-sv1s', 'sv1v': 'set-sv1v',
    'sv2d': 'set-sv2d', 'sv2p': 'set-sv2p',
    'sv3': 'set-sv3', 'sv3a': 'set-sv3a',
    'sv4a': 'set-sv4a', 'sv4k': 'set-sv4k', 'sv4m': 'set-sv4m',
    'sv5a': 'set-sv5a', 'sv5af': 'set-sv5a', 'sv5k': 'set-sv5k', 'sv5m': 'set-sv5m',
    'sv6': 'set-sv6', 'sv6a': 'set-sv6a',
    'sv7': 'set-sv7', 'sv7a': 'set-sv7a',
    'sv8': 'set-sv8', 'sv8a': 'set-sv8a',
    'sv9': 'set-sv9', 'sv9a': 'set-sv9a',
    'sv10': 'set-sv10',
    'sv11b': 'set-sv11b', 'sv11w': 'set-sv11w',
    'ac2a': 'set-ac2a', 'ac2b': 'set-ac2b',
    's1a': 'set-s1a', 's1h': 'set-s1h', 's1w': 'set-s1w',
    's2a': 'set-s2a', 's3a': 'set-s3a', 's4a': 'set-s4a',
    's5a': 'set-s5a', 's5r': 'set-s5r', 's6a': 'set-s6a',
    's7d': 'set-s7d', 's7r': 'set-s7r', 's8a': 'set-s8a',
    's8b': 'set-s8b', 's9a': 'set-s9a', 's10a': 'set-s10a',
    's10b': 'set-s10b', 's10d': 'set-s10d', 's10p': 'set-s10p',
    's12a': 'set-s12a',
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

NON_TCG_KEYWORDS = [
    'dice', 'd6', 'd20', 'd4', 'd8', 'd10', 'd12',
    'chessex', 'diceski', 'life counter', 'coin', 'token',
    'topper', 'toploader', 'card stand', 'card gard',
]

ACCESSORY_BRANDS = [
    'dragon shield', 'dragonshield', 'ultra pro', 'ultrapro',
    'ultimate guard', 'broccoli', 'bushiroad', 'bcw',
    'the gard', 'card gard',
]

BRAND_MAP = {
    'brand-dragonshield':  ['dragon shield', 'dragonshield'],
    'brand-broccoli':      ['broccoli'],
    'brand-bushiroad':     ['bushiroad'],
    'brand-ultrapro':      ['ultra pro', 'ultrapro'],
    'brand-ultimateguard': ['ultimate guard'],
    'brand-chessex':       ['chessex', 'diceski'],
    'brand-bcw':           ['bcw'],
}

# 繁中版識別關鍵字
LANG_TC_KEYWORDS = [
    '繁中', '中文', '繁體', '寶可夢集換式卡牌遊戲', '換式卡牌',
    '朱&紫', '朱＆紫', '劍&盾', '劍＆盾', '太陽&月亮', '太陽＆月亮',
]

OPCG_DIRECT_PATTERN = re.compile(
    r'\b(op|eb|st|prb)\d{2}\b', re.IGNORECASE
)
OPCG_BRACKET_PATTERN = re.compile(
    r'[\[【](op|eb|st|prb)-?\d{1,2}[\]】]', re.IGNORECASE
)


def normalize(text):
    return unicodedata.normalize('NFKC', text)


def is_opcg_text(text_lower):
    return (
        'opcg' in text_lower or
        '海賊王' in text_lower or
        'one piece' in text_lower or
        bool(OPCG_BRACKET_PATTERN.search(text_lower)) or
        bool(OPCG_DIRECT_PATTERN.search(text_lower))
    )


def detect_game(combined_lower):
    if any(kw in combined_lower for kw in NON_TCG_KEYWORDS):
        return set()
    if any(kw in combined_lower for kw in ACCESSORY_BRANDS):
        return set()

    is_psa = 'psa' in combined_lower or '鑑定' in combined_lower
    games = set()

    if is_psa:
        games.add('game-graded')
        if 'psa' in combined_lower:
            games.add('graded-psa')

    if 'lorcana' in combined_lower:
        games.add('game-lorcana')
    elif is_opcg_text(combined_lower):
        games.add('game-opcg')
    elif '遊戲王' in combined_lower or 'yugioh' in combined_lower:
        games.add('game-yugioh')
    elif not any(kw in combined_lower for kw in ['卡套', '卡墊', '卡盒']):
        games.add('game-ptcg')

    return games


def detect_set(combined, combined_lower, combined_norm_lower, handle):
    # PSA鑑定卡唔加set tag
    if 'psa' in combined_lower or '鑑定' in combined_lower:
        return None

    # 非TCG配件唔加set
    if any(kw in combined_lower for kw in NON_TCG_KEYWORDS):
        return None
    if any(kw in combined_lower for kw in ACCESSORY_BRANDS):
        return None

    # 第一優先：括號內代號 — 必須係英文字母開頭，排除中文括號如[500年後的未来]
    bracket_match = re.search(r'[\[【]([A-Za-z]{1,4})-?(\d{1,2}[A-Za-z]?)[\]】]', combined)
    if bracket_match:
        raw = (bracket_match.group(1) + bracket_match.group(2)).lower()
        # 確保係純英數，唔含中文
        if re.match(r'^[a-z0-9]+$', raw):
            return SET_MAP.get(raw, f'set-{raw}')

    # normalize版本括號（解決全寬字）
    norm_bracket = re.search(r'[\[【]([A-Za-z]{1,4})-?(\d{1,2}[A-Za-z]?)[\]】]', normalize(combined))
    if norm_bracket:
        raw = (norm_bracket.group(1) + norm_bracket.group(2)).lower()
        if re.match(r'^[a-z0-9]+$', raw):
            return SET_MAP.get(raw, f'set-{raw}')

    # 第二優先：OPCG連字號格式 OP-13, PRB-02（排除卡號如OP10-119）
    opcg_match = re.search(r'(?<!\w)(op|eb|st|prb)-(\d{1,2})(?!\d*-\d{3})\b', combined_lower)
    if opcg_match:
        prefix = opcg_match.group(1)
        num = opcg_match.group(2).zfill(2)
        set_code = f"{prefix}{num}"
        return SET_MAP.get(set_code, f'set-{set_code}')

    # 第三優先：PTCG SV系列
    for t in [combined_lower, combined_norm_lower]:
        ptcg_match = re.search(r'\b(sv\d+[a-z]{0,2})\b', t)
        if ptcg_match:
            code = ptcg_match.group(1)
            return SET_MAP.get(code, f'set-{code}')

    # 第四優先：舊系列 Ac2a, S1a 等
    old_match = re.search(r'\b(ac\d+[a-z]?|s\d+[a-z]{0,2})\b', combined_norm_lower)
    if old_match:
        code = old_match.group(1)
        if code in SET_MAP:
            return SET_MAP[code]

    # 第五優先：M系列括號
    m_match = re.search(r'[\[【](m\d+[a-z]?)[\]】]', combined_lower)
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


def detect_type(combined_lower, is_psa):
    if any(kw in combined_lower for kw in ['原盒', 'booster box', 'box', '原箱', '散包']):
        return 'type-boosterbox'
    elif any(kw in combined_lower for kw in ['單卡', 'single']):
        return 'type-single'
    elif '禮盒' in combined_lower or '收藏箱' in combined_lower or '紀念箱' in combined_lower:
        return 'type-giftbox'
    elif any(kw in combined_lower for kw in ['卡組', '預組', 'deck']):
        return 'type-deckset'
    elif any(kw in combined_lower for kw in ['卡套', 'sleeve', 'protector']):
        return 'type-sleeve'
    elif any(kw in combined_lower for kw in ['卡墊', 'mat', 'playmat', '桌墊']):
        return 'type-mat'
    elif any(kw in combined_lower for kw in ['卡盒', 'deckbox', '收納盒']):
        return 'type-deckbox'
    elif any(kw in combined_lower for kw in NON_TCG_KEYWORDS):
        return 'type-other'
    elif re.search(r'([A-Za-z]{1,4}\d{0,2}-\d{3}|\d{1,3}/\d{1,3})', combined_lower) or is_psa:
        return 'type-single'
    return None


def detect_lang(title, combined_lower, handle):
    title_lower = title.lower()
    # 繁中關鍵字（title優先）
    if any(kw in title for kw in LANG_TC_KEYWORDS):
        return 'lang-tc'
    if any(kw in title_lower for kw in ['繁中', '中文', '繁體']):
        return 'lang-tc'
    # combined搵繁中
    if any(kw in combined_lower for kw in ['繁中', '中文', '繁體', '繁體中文版', '換式卡牌遊戲']):
        return 'lang-tc'
    # Handle
    if handle.upper().startswith('CHI-'):
        return 'lang-tc'
    # 日版
    if any(kw in title_lower for kw in ['日版', '日文']) or handle.upper().startswith('JPN-'):
        return 'lang-jp'
    # 美版
    if any(kw in title_lower for kw in ['美版', '英文']) or handle.upper().startswith('ENG-'):
        return 'lang-en'
    return None


def detect_brands(combined_lower):
    brands = set()
    for brand_tag, keywords in BRAND_MAP.items():
        if any(kw in combined_lower for kw in keywords):
            brands.add(brand_tag)
    if '寶可夢' in combined_lower and any(kw in combined_lower for kw in ['卡套', '卡墊', '卡盒', '收納盒']):
        brands.add('brand-pokemon')
    return brands


def process_row(title, handle, existing_tags_str):
    existing_tags_clean = str(existing_tags_str) if str(existing_tags_str) not in ['nan', ''] else ''
    combined = title + ' ' + existing_tags_clean
    combined_lower = combined.lower()
    combined_norm = normalize(combined)
    combined_norm_lower = combined_norm.lower()

    new_tags = set()

    existing_tags = []
    if existing_tags_clean:
        existing_tags = [t.strip() for t in existing_tags_clean.split(',') if t.strip()]
    existing_tags_lower = [t.lower() for t in existing_tags]

    # 遊戲類別
    new_tags.update(detect_game(combined_lower))

    # 語言
    lang = detect_lang(title, combined_lower, handle)
    if lang:
        new_tags.add(lang)

    # 產品類型
    is_psa = 'psa' in combined_lower or '鑑定' in combined_lower
    type_tag = detect_type(combined_lower, is_psa)
    if type_tag:
        new_tags.add(type_tag)

    # 品牌
    new_tags.update(detect_brands(combined_lower))

    # 系列
    set_tag = detect_set(combined, combined_lower, combined_norm_lower, handle)
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
    test_title = st.text_input("輸入產品標題測試",
        placeholder="例如：寶可夢集換式卡牌遊戲 - 劍&盾 - 25週年黃金紀念箱")
with col2:
    test_handle = st.text_input("Handle（可空）", placeholder="opcg-prb02-xxx")

test_existing = st.text_input("現有Tags（可空）",
    placeholder="例如：高級補充包ONE PIECE CARD THE BEST【PRB-02】")

if test_title:
    result = process_row(test_title, test_handle or '', test_existing or '')
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
