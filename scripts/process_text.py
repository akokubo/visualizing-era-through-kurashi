import argparse
import re
import uuid

def extract_protected_regions(text):
    """
    HTMLタグやMarkdownのリンク(URL)部分を一時退避。
    """
    protected = {}
    
    # HTMLタグ（<img>など）
    def tag_replacer(match):
        key = f"__HTML_TAG_{uuid.uuid4().hex}__"
        protected[key] = match.group()
        return key

    text = re.sub(r'<[^<>]+>', tag_replacer, text)

    # Markdownの画像・リンク
    def markdown_link_replacer(match):
        key = f"__MARKDOWN_LINK_{uuid.uuid4().hex}__"
        protected[key] = match.group()
        return key

    text = re.sub(r'!\[[^\]]*\]\([^\)]*\)', markdown_link_replacer, text)
    text = re.sub(r'\[[^\]]+\]\([^\)]+\)', markdown_link_replacer, text)

    return text, protected

def restore_protected_regions(text, protected):
    for key, original in protected.items():
        text = text.replace(key, original)
    return text

# ① 半角記号 → 全角記号に変換
def convert_escaped_halfwidth_to_fullwidth(text):
    escape_map = {
        '(': '（',
        ')': '）',
        '?': '？',
        '!': '！',
        '-': '－',
        ',': '，',
        '.': '．',
        ':': '：',
        ';': '；',
        '[': '［',
        ']': '］',
        '{': '｛',
        '}': '｝',
        '<': '〈',
        '>': '〉',
        '#': '＃',
        '&': '＆',
        '*': '＊',
        '%': '％',
        '=': '＝',
        '+': '＋',
        '/': '／',
        '\\': '＼',  # 注意：バックスラッシュそのもの
        '|': '｜',
        '^': '＾',
        '~': '～',
        '"': '＂',
        "'": '＇',
    }

    # バックスラッシュ + 半角記号を正規表現で検索し、変換
    def replacer(match):
        symbol = match.group(1)
        return escape_map.get(symbol, symbol)

    return re.sub(r'\\([!-/:-@[-`{-~])', replacer, text)

# ② 特定記号の変換
def convert_specific_symbols(text):
    text = text.replace('·', '・')
    text = text.replace('──', '⸺')
    text = text.replace('––', '⸺')
    text = text.replace('...', '…')
    text = text.replace('?', '？')
    text = text.replace('？ ', '？')
    return text

# ③ 一文字だけの半角英数字 → 全角英数字
def convert_single_halfwidth_alnum_to_fullwidth(text):
    def to_fullwidth(match):
        char = match.group(0)
        return chr(ord(char) + 0xFEE0)

    # 1文字の英数字（前後が英数字でない場合）
    return re.sub(r'(?<![A-Za-z0-9])([A-Za-z0-9])(?![A-Za-z0-9])', to_fullwidth, text)

# ④ 全角文字に挟まれた「？」や「！」→ そのあとに全角スペースを追加
def add_fullwidth_space_after_question_exclamation(text):
    return re.sub(r'(?<=[\u3000-\u9FFF])[？！](?=[\u3000-\u9FFF])',
                  lambda m: m.group() + '　', text)

# ⑤「全角スペース（　）」の後に続く「全角の閉じカギ括弧（」）」を「スペースなしの 」」に変換
def remove_fullwidth_space_before_closing_quote(text):
    return re.sub(r'　(?=」)', '', text)

# ⑥HTMLのimg要素をMarkdownに変換
def convert_img_to_markdown(text):
    def replacer(match):
        tag = match.group()
        # src属性を取り出す
        src_match = re.search(r'src\s*=\s*["\']([^"\']+)["\']', tag)
        if src_match:
            src = src_match.group(1)
            return f"![]({src})"
        return tag  # srcがなければ変換しない

    return re.sub(r'<img\s+[^>]*>', replacer, text, flags=re.IGNORECASE)

# ⑦HTMLの空要素をXHTMLに変換
def convert_html_void_tags_to_xhtml(text):
    void_tags = [
        'area', 'base', 'br', 'col', 'embed', 'hr',
        'img', 'input', 'link', 'meta', 'param',
        'source', 'track', 'wbr'
    ]

    # 各タグを <tag> → <tag /> に変換
    for tag in void_tags:
        # 末尾に / がない <tag> を <tag /> に変換（属性ありにも対応）
        pattern = rf'<{tag}(\s[^<>]*?)?>'  # `<br>` or `<br attr="x">`
        replacement = rf'<{tag}\1 />'
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text

def replace_br_tag(text):
    return text.replace('<br>', '\n\n')


def replace_tag_to_symbol(text):
    return text.replace('<', '〈').replace('>', '〉？')

def process_text(text):
    text = convert_img_to_markdown(text)
    text = replace_br_tag(text)
    text = replace_tag_to_symbol(text)

    text, protected = extract_protected_regions(text)  # 保護

    text = convert_escaped_halfwidth_to_fullwidth(text)
    text = convert_specific_symbols(text)
    text = convert_single_halfwidth_alnum_to_fullwidth(text)
    text = add_fullwidth_space_after_question_exclamation(text)
    text = remove_fullwidth_space_before_closing_quote(text)
    text = convert_html_void_tags_to_xhtml(text)

    text = restore_protected_regions(text, protected)  # 復元

    return text

# コマンドライン対応部分
def main():
    parser = argparse.ArgumentParser(description='テキスト整形ツール')
    parser.add_argument('input', help='入力ファイルのパス')
    parser.add_argument('output', help='出力ファイルのパス')

    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    processed = process_text(text)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(processed)

if __name__ == '__main__':
    main()
