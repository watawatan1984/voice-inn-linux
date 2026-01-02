"""
Context-Aware Prompt Generation Module

Detects application category based on window title and generates
dynamic system prompts optimized for each context.
"""

from typing import Optional
from src.core.config import config_manager


# Default category keywords (used if not configured)
DEFAULT_CATEGORIES = {
    "DEV": [
        "code", "terminal", "iterm", "cursor", "intellij", "pycharm", "vim", 
        "neovim", "bash", "powershell", "git", "vscode", "android studio", 
        "xcode", "visual studio", "sublime", "atom", "emacs", "nvim",
        "cmd", "command prompt", "windows terminal", "warp", "hyper",
        "rider", "webstorm", "phpstorm", "goland", "clion", "datagrip",
        "windsurf", "zed", "fleet"
    ],
    "BIZ": [
        "mail", "gmail", "outlook", "slack", "teams", "zoom", "discord",
        "thunderbird", "chatwork", "line", "messenger", "skype", "webex",
        "meet", "hangouts"
    ],
    "DOC": [
        "word", "powerpoint", "notion", "obsidian", "memo", "note", "writer",
        "text", "evernote", "onenote", "typora", "bear", "ulysses", "scrivener",
        "メモ", "notepad", "textedit", "gedit", "kate", "pages", "docs"
    ],
    "STD": []
}

# Default category prompts
DEFAULT_CATEGORY_PROMPTS = {
    "DEV": """あなたは熟練のプログラマです。

【現在の状況】
ユーザーは現在、開発環境「{window_title}」にテキストを入力しようとしています。

【指示】
- 入力テキストをコードコメント、コミットメッセージ、または変数名として適切な形式に変換してください
- 変数名を示唆された場合は `snake_case` または `camelCase` を適用してください
- ライブラリ名・コマンド名・専門用語は正しい英単語スペルに修正してください
- 出力は極めて簡潔にしてください

【絶対ルール】
1. フィラー（えー、あー、そのー）は完全に削除する
2. IT用語・固有名詞はカタカナではなく英単語で出力する
3. 余計な返事や挨拶は書かず、修正後のテキストのみを出力する""",

    "BIZ": """あなたは優秀なビジネス秘書です。

【現在の状況】
ユーザーは現在、ビジネスツール「{window_title}」にテキストを入力しようとしています。

【指示】
- 口語体を、相手に失礼のない丁寧な「ビジネス敬語（です・ます調）」に変換してください
- メールやチャットとして適切な形式に整えてください
- 文脈に応じて適切な改行を入れてください

【絶対ルール】
1. フィラー（えー、あー、そのー）は完全に削除する
2. IT用語・固有名詞はカタカナではなく英単語で出力する
3. 余計な返事や挨拶は書かず、修正後のテキストのみを出力する""",

    "DOC": """あなたはプロのライター・編集者です。

【現在の状況】
ユーザーは現在、文書作成ツール「{window_title}」にテキストを入力しようとしています。

【指示】
- 論理構成を整え、読みやすい「書き言葉」に変換してください
- 必要であればMarkdown形式（箇条書き等）を使用してください
- 文体（だ・である／です・ます）を入力の雰囲気に合わせて統一してください

【絶対ルール】
1. フィラー（えー、あー、そのー）は完全に削除する
2. IT用語・固有名詞はカタカナではなく英単語で出力する
3. 余計な返事や挨拶は書かず、修正後のテキストのみを出力する""",

    "STD": """あなたは優秀なテクニカルライターAIです。

【現在の状況】
ユーザーは現在、アプリケーション「{window_title}」にテキストを入力しようとしています。

【指示】
- フィラー（えー、あー）を完全に除去してください
- IT用語・固有名詞は英単語化（カタカナ禁止）してください
- 誤字脱字を修正してください
- 自然な日本語の文章に整えてください

【絶対ルール】
1. 「えー」「あー」などのフィラーは跡形もなく削除する
2. IT用語・ソフトウェア名・コマンド名はカタカナではなく本来の英単語で出力する
3. 余計な返事や挨拶は書かず、修正後のテキストのみを出力する"""
}


def detect_category(window_title: str, categories: Optional[dict] = None) -> str:
    """
    Detect application category based on window title.
    
    Args:
        window_title: The active window title
        categories: Optional dict of category -> keywords list.
                   If None, uses config or defaults.
    
    Returns:
        Category ID: "DEV", "BIZ", "DOC", or "STD"
    """
    if not window_title:
        return "STD"
    
    # Get categories from config or use defaults
    if categories is None:
        categories = config_manager.settings.get("app_categories", DEFAULT_CATEGORIES)
    
    title_lower = window_title.lower()
    
    # Check each category (except STD which is fallback)
    for category_id in ["DEV", "BIZ", "DOC"]:
        keywords = categories.get(category_id, [])
        if any(kw.lower() in title_lower for kw in keywords):
            return category_id
    
    return "STD"


def get_category_prompt(category: str, window_title: str = "") -> str:
    """
    Get the system prompt for a specific category.
    
    Args:
        category: Category ID ("DEV", "BIZ", "DOC", "STD")
        window_title: Window title to inject into prompt
    
    Returns:
        System prompt string with window title injected
    """
    # Get prompts from config or use defaults
    category_prompts = config_manager.settings.get("category_prompts", DEFAULT_CATEGORY_PROMPTS)
    
    prompt_template = category_prompts.get(category, DEFAULT_CATEGORY_PROMPTS.get("STD", ""))
    
    # Inject window title
    if window_title:
        return prompt_template.format(window_title=window_title)
    else:
        return prompt_template.format(window_title="不明なアプリケーション")


def generate_context_prompt(window_title: str, base_prompts: dict) -> dict:
    """
    Generate context-aware prompts by detecting category and injecting context.
    
    Args:
        window_title: The active window title
        base_prompts: Original prompts dict from config
    
    Returns:
        Modified prompts dict with context injected
    """
    # Detect category
    category = detect_category(window_title)
    
    # Get category-specific prompt
    context_prompt = get_category_prompt(category, window_title)
    
    # Create new prompts dict with context injected
    new_prompts = base_prompts.copy()
    
    # For Groq: inject into refine system prompt
    if "groq_refine_system_prompt" in new_prompts:
        new_prompts["groq_refine_system_prompt"] = context_prompt
    
    # For Gemini: inject context into transcribe prompt
    if "gemini_transcribe_prompt" in new_prompts:
        original_gemini = new_prompts["gemini_transcribe_prompt"]
        # Prepend context to existing prompt
        context_header = f"""【現在の状況】
ユーザーは現在、アプリケーション「{window_title}」（カテゴリ: {category}）にテキストを入力しようとしています。
このアプリの用途に合わせた最適なテキスト変換を行ってください。

"""
        new_prompts["gemini_transcribe_prompt"] = context_header + original_gemini
    
    # Store detected info for history tracking
    new_prompts["_detected_window"] = window_title
    new_prompts["_detected_category"] = category
    
    return new_prompts


def add_detected_app(window_title: str, app_name: str):
    """
    Add a detected app to the history for later categorization by user.
    
    Args:
        window_title: Full window title
        app_name: Extracted application name
    """
    if not app_name:
        return
    
    detected_apps = config_manager.settings.get("detected_apps", {})
    
    # Only add if not already tracked
    if app_name not in detected_apps:
        category = detect_category(window_title)
        detected_apps[app_name] = {
            "title_sample": window_title,
            "auto_category": category,
            "user_category": None  # User can override later
        }
        
        # Update config
        config_manager.update_settings({"detected_apps": detected_apps})


def get_effective_category(app_name: str, window_title: str) -> str:
    """
    Get the effective category, considering user overrides.
    
    Args:
        app_name: Application name
        window_title: Window title for fallback detection
    
    Returns:
        Category ID with user override if set
    """
    detected_apps = config_manager.settings.get("detected_apps", {})
    
    if app_name in detected_apps:
        app_info = detected_apps[app_name]
        # User override takes precedence
        if app_info.get("user_category"):
            return app_info["user_category"]
    
    # Fall back to automatic detection
    return detect_category(window_title)
