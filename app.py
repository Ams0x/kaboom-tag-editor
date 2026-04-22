import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="TCG CSV 終極本機直讀版", layout="wide")
st.title("🎯 TCG CSV 終極精準版 (支援 PTCG, OPCG, Lorcana)")
st.write("✅ 完美支援寶可夢、海賊王、迪士尼 Lorcana 專屬稀有度 | ✅ 自動反轉中日文排版")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📄 第一步：貼上卡表文字")
    st.info("💡 貼上卡表。程式已支援 `001/073` (PTCG), `OP01-001` (OPCG), `1/204` (Lorcana) 等格式。")
    pasted_data = st.text_area("在這裡貼上卡表：", height=250)

with col2:
    st.markdown("### 📂 第二步：上傳 Shopify CSV")
    uploaded_csv = st.file_uploader("上傳從 Shopify 匯出的 CSV 檔案", type=["csv"])

if st.button("🚀 開始 100% 精準匹配") and uploaded_csv and pasted_data:
    progress_bar = st.progress(0)
    status_text = st.empty()

    status_text.text("⚡ 正在瞬間分析卡表...")
    
    master_dict = {}
    
    # 🎯 升級版切割：支援 PTCG (001/073), Lorcana (1/204), 及 OPCG (OP01-001, ST10-001, P-001)
    chunks = re.split(r'\b([A-Za-z]{1,4}\d{0,2}-\d{3}|\d{1,3}/\d{1,3})\b', pasted_data)
    
    if len(chunks) < 3:
        st.error("❌ 找不到卡號 (例如 001/073, OP01-001, 1/204)。請確認貼上的內容格式正確。")
        st.stop()
        
    for i in range(1, len(chunks), 2):
        raw_num = chunks[i]
        chunk_content = chunks[i+1]
        
        rarity = None
        
        # 1. 優先搵括號入面嘅稀有度 (涵蓋三大 TCG 嘅代碼)
        rarity_match = re.search(r'\((SAR|SSR|CSR|CHR|RRR|ACE|SEC|SR|AR|UR|HR|RR|PR|TR|SP|UC|K|S|A|E|L|R|U|C)\)', chunk_content, re.IGNORECASE)
        if rarity_match:
            rarity = rarity_match.group(1).upper()
        else:
            # 2. 搵英文全寫 (加入 OPCG 同 Lorcana 關鍵字)
            if re.search(r'(Special Art Rare|Special Illustration Rare)', chunk_content, re.I): rarity = 'SAR'
            elif re.search(r'(Shiny Super Rare)', chunk_content, re.I): rarity = 'SSR'
            elif re.search(r'(Secret Rare)', chunk_content, re.I): rarity = 'SEC'
            elif re.search(r'(Legendary|Leader)', chunk_content, re.I): rarity = 'L'
            elif re.search(r'(Enchanted)', chunk_content, re.I): rarity = 'E'
            elif re.search(r'(Treasure Rare)', chunk_content, re.I): rarity = 'TR'
            elif re.search(r'(Special)', chunk_content, re.I): rarity = 'SP'
            elif re.search(r'(Art Rare|Illustration Rare)', chunk_content, re.I): rarity = 'AR'
            elif re.search(r'(Super Rare)', chunk_content, re.I): rarity = 'SR'
            elif re.search(r'(Ultra Rare|Hyper Rare)', chunk_content, re.I): rarity = 'UR'
            elif re.search(r'(Double Rare)', chunk_content, re.I): rarity = 'RR'
            elif re.search(r'\b(Rare)\b', chunk_content, re.I): rarity = 'R'
            elif re.search(r'\b(Uncommon)\b', chunk_content, re.I): rarity = 'U' # OPCG有時叫UC，統一判定為U，或者睇網頁寫咩
            elif re.search(r'\b(Common)\b', chunk_content, re.I): rarity = 'C'
            elif re.search(r'(Shiny)', chunk_content, re.I): rarity = 'S'
            elif re.search(r'^\s*[-—–]\s*$', chunk_content, re.MULTILINE): rarity = '-'

        if rarity:
            # 存入多種格式，確保無論 CSV 寫 "001/073" 定 "1" 都對得中
            master_dict[raw_num] = rarity
            master_dict[raw_num.upper()] = rarity
            if '/' in raw_num:
                prefix = raw_num.split('/')[0]
                master_dict[prefix] = rarity                # "001" 或 "1"
                master_dict[prefix.zfill(3)] = rarity       # "001"
                master_dict[str(int(prefix))] = rarity      # "1"

    if len(master_dict) == 0:
        st.error("❌ 找到卡號，但找不到稀有度。")
        st.stop()
        
    status_text.text(f"✅ 成功建立字典！共識別出 {len(master_dict)} 張卡。正在處理 CSV...")
    
    # --- 處理 CSV ---
    df = pd.read_csv(uploaded_csv)
    original_filename = uploaded_csv.name
    download_filename = f"Fixed_{original_filename}"

    col_set = '系列 (product.metafields.custom.set)'
    col_rarity = '稀有度 (product.metafields.custom.rarity)'

    for col in [col_set, col_rarity]:
        if col not in df.columns: df[col] = ""
        
    df['Product Category'] = "Arts & Entertainment > Hobbies & Creative Arts > Collectibles > Collectible Trading Cards > Gaming Cards"
    
    # 終極稀有度清單 (結合三大 TCG)
    all_rarities = ['SAR', 'SSR', 'CSR', 'CHR', 'RRR', 'ACE', 'SEC', 'SR', 'AR', 'UR', 'HR', 'RR', 'PR', 'TR', 'SP', 'UC', 'K', 'S', 'A', 'E', 'L', 'R', 'U', 'C']

    for index, row in df.iterrows():
        title = str(row.get('Title', ''))
        if pd.notna(title) and title != 'nan':
            # 🌟 升級版擷取系列 (支援中日文及三大 TCG 編號格式)
            set_match = re.search(r'^(.*?)\s+([A-Za-z]{1,4}\d{0,2}-\d{3}|\d{1,3}/\d{1,3})', title)
            if set_match: 
                raw_series = set_match.group(1).strip()
                # 🎯 自動修正日文排版 [系列名] 英文代號 -> [英文代號] 系列名
                flip_match = re.search(r'^\[(.*?)\]\s*([A-Za-z0-9\-]+)$', raw_series)
                if flip_match:
                    df.at[index, col_set] = f"[{flip_match.group(2).upper()}] {flip_match.group(1)}"
                else:
                    df.at[index, col_set] = raw_series
            else:
                backup_match = re.search(r'^(\[.*?\]\s*[^\s]+)', title)
                if backup_match: df.at[index, col_set] = backup_match.group(1).strip()

            # 擷取卡號並查字典
            card_num = None
            op_match = re.search(r'([A-Za-z]{1,4}\d{0,2}-\d{3})', title)
            slash_match = re.search(r'(\d{1,3})/\d{1,3}', title)
            
            if op_match:
                card_num = op_match.group(1).upper()
            elif slash_match:
                card_num = slash_match.group(1) # 只抽前綴，例如 001 或 1
                
            if card_num and card_num in master_dict:
                df.at[index, col_rarity] = master_dict[card_num]
            else:
                pokemon_name = re.sub(r'^(.*?)\s+([A-Za-z]{1,4}\d{0,2}-\d{3}|\d{1,3}/\d{1,3})\s*', '', title)
                rarity_match = re.search(r'\s(' + '|'.join(all_rarities) + r')$', title, re.IGNORECASE)
                
                if rarity_match: 
                    df.at[index, col_rarity] = rarity_match.group(1).upper()
                elif 'ex ' in pokemon_name.lower() or pokemon_name.lower().endswith('ex'): 
                    df.at[index, col_rarity] = 'RR'
                else: 
                    df.at[index, col_rarity] = '需手動檢查'

        progress_bar.progress((index + 1) / len(df))

    status_text.text("🎉 全部精準匹配完成！已支援 PTCG, OPCG, Lorcana！")
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(f"📥 下載 {download_filename}", csv, download_filename, "text/csv")
