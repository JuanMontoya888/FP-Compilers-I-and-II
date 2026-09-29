# =====================================================================
# MODULE: THEME CONSTANTS
# Centralizes all color palettes and styling properties for the IDE.
# This makes it easy to switch between Light/Dark themes in the future.
# =====================================================================

class Theme:
    # ---------------------------------
    # Editor Colors
    # ---------------------------------
    EDITOR_BG = "#1e1e1e"
    GUTTER_BG = "#1e1e1e"
    GUTTER_TEXT = "#858585"
    CURRENT_LINE_BG = "#2d2d30"
    ERROR_SQUIGGLY = "red"
    
    # ---------------------------------
    # Syntax Highlighting Colors
    # ---------------------------------
    SYNTAX_KEYWORD = "#ff6480"
    SYNTAX_TYPE = "#56b6c2"
    SYNTAX_NUMBER = "#B5CEA8"
    SYNTAX_STRING = "#e5c07b"
    SYNTAX_OPERATOR = "#AAAAAA"
    SYNTAX_COMMENT = "#6A9955"
    SYNTAX_LIBRARY = "#C586C0"
    
    # ---------------------------------
    # Terminal & UI Colors
    # ---------------------------------
    TERMINAL_ERROR = "#ff5555"
    TERMINAL_INFO = "#56b6c2"
    TERMINAL_SUCCESS = "#B5CEA8"
