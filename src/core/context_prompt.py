"""
Context-Aware Prompt Generation Module

Detects application category based on window title and generates
dynamic system prompts optimized for each context.
"""

from typing import Optional
from src.core.config import config_manager
from src.core.const import (
    DEFAULT_APP_CATEGORIES,
    DEFAULT_CATEGORY_PROMPTS
)

# 後方互換性のためのエイリアス
DEFAULT_CATEGORIES = DEFAULT_APP_CATEGORIES



import re

def _matches_keyword(keyword: str, title_lower: str) -> bool:
    """
    キーワードがウィンドウタイトルに含まれるかを判定する。
    英数字のみで構成されるキーワードの場合は単語境界を考慮し、
    'meet' が 'meeting' や 'sheet' に誤爆するのを防止する。
    """
    kw = keyword.strip().lower()
    if not kw:
        return False
    if re.match(r'^[a-zA-Z0-9_\-]+$', kw):
        pattern = r'(?<![a-zA-Z0-9])' + re.escape(kw) + r'(?![a-zA-Z0-9])'
        return bool(re.search(pattern, title_lower))
    return kw in title_lower

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
        if any(_matches_keyword(kw, title_lower) for kw in keywords):
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
