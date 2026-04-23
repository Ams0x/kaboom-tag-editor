def detect_set(title, title_lower, handle):
    # 第一優先：括號內代號 【PRB-02】或 [SV9a] — 完全唔理卡號
    bracket_match = re.search(r'[\[【]([A-Za-z]{1,4}-?\d{1,2}[A-Za-z]?)[\]】]', title)
    if bracket_match:
        raw = bracket_match.group(1).replace('-', '').lower()
        if re.search(r'[a-z]', raw):
            if raw in SET_MAP:
                return SET_MAP[raw]
            return f'set-{raw}'
    
    # 第二優先：OPCG連字號格式 OP-13, PRB-02（只搵獨立單詞，唔係卡號一部分）
    opcg_match = re.search(r'(?<!\w)(op|eb|st|prb)-(\d{1,2})(?!\d*-\d{3})', title_lower)
    if opcg_match:
        prefix = opcg_match.group(1)
        num = opcg_match.group(2).zfill(2)
        set_code = f"{prefix}{num}"
        return SET_MAP.get(set_code, f'set-{set_code}')
    
    # 第三優先：PTCG系列
    ptcg_match = re.search(r'\b(sv\d+[a-z]?|s\d+[a-z]?|sm\d+[a-z]?)\b', title_lower)
    if ptcg_match:
        code = ptcg_match.group(1)
        return SET_MAP.get(code, f'set-{code}')
    
    # 第四優先：M系列括號
    m_match = re.search(r'[\[【](m\d+[a-z]?)[\]】]', title_lower)
    if m_match:
        code = m_match.group(1)
        return SET_MAP.get(code, f'set-{code}')
    
    # 終極防線：Handle
    parts = handle.split('-')
    if len(parts) >= 2:
        candidate = parts[1].lower()
        if (re.match(r'^[a-z0-9]+$', candidate) and
            candidate not in ['single', 'box', 'ptcg', 'tcg', 'jp', 'en', 'chi', 'opcg']):
            return SET_MAP.get(candidate, f'set-{candidate}')
    
    return None
