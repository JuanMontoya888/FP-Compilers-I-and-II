import sys
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser

# =====================================================================
# CORE MODULE: AST VISUALIZER
# Handles the generation and rendering of the AST in a graphical web view.
# Architecture: Uses native QTextBrowser for stable, lightweight rendering.
# =====================================================================

# =====================================================================
# CLASS: ASTHtmlGenerator
# What it does: Converts an ASTNode hierarchy into a stylized HTML document.
# Architecture: Uses static methods to recursively traverse the AST
# and build HTML4 tables to simulate a branched graphic tree structure
# compatible with Qt's Rich Text rendering engine.
# =====================================================================
class ASTHtmlGenerator:
    
    @staticmethod
    def arbol_a_html(ast_root, errors=None):
        """
        Generates the complete HTML skeleton and triggers recursive node building.
        """
        html = """
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
        <html>
        <head>
            <style type="text/css">
                body {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 13px;
                }
                h2 {
                    color: #c586c0;
                    text-align: center;
                }
                .node-box {
                    border: 2px solid #404040;
                    background-color: #252526;
                    padding: 8px 15px;
                    border-radius: 8px;
                    margin: 5px 15px;
                    text-align: center;
                    white-space: nowrap;
                }
                .node-name { color: #56b6c2; font-weight: bold; font-size: 14px; }
                .node-val { color: #ce9178; font-weight: bold; }
                .node-pos { color: #858585; font-size: 11px; }
                .error-box {
                    background-color: #3c1f1f;
                    color: #ff5555;
                    border: 1px solid #ff5555;
                    padding: 10px;
                    margin: 10px auto;
                    width: 80%;
                }
                .error-text { color: #ff5555; font-weight: bold; }
            </style>
        </head>
        <body>
            <h2>Graphical Abstract Syntax Tree</h2>
            <hr>
        """
        
        if errors and len(errors) > 0:
            html += "<div class='error-box'><h3>Syntax Errors detected:</h3><ul>"
            for err in errors:
                html += f"<li class='error-text'>{err}</li>"
            html += "</ul></div><br>"
            
        html += "<div align='center'>"
        html += ASTHtmlGenerator._nodo_html(ast_root)
        html += "</div></body></html>"
        
        return html

    @staticmethod
    def _nodo_html(node):
        """
        Recursively converts an ASTNode and its children into an HTML4 table,
        creating a perfect top-down branched graphical hierarchy.
        """
        import html
        if not node:
            return ""
        
        # Build node display text - explicitly accepting non-digit fallbacks like '?'
        line_str = f"(Ln {node.line}, Col {node.col})" if hasattr(node, 'line') and str(node.line) != "?" else ""
        
        safe_name = html.escape(str(node.name))
        
        # Render the node box
        node_content = f"<div class='node-box'><span class='node-name'>{safe_name}</span>"
        if hasattr(node, 'value') and node.value:
            safe_val = html.escape(str(node.value))
            node_content += f"<br><span class='node-val'>'{safe_val}'</span>"
        if line_str:
            node_content += f"<br><span class='node-pos'>{line_str}</span>"
        node_content += "</div>"
        
        children = node.children if hasattr(node, 'children') else []
        n = len(children)
        
        # Leaf Node: Base case
        if n == 0:
            return f"""
            <table border="0" cellspacing="0" cellpadding="0" align="center">
                <tr><td align="center">{node_content}</td></tr>
            </table>
            """
            
        colspan = n * 2
        
        # Branch Node: Recursive rendering
        # Row 1: The Parent Node
        res = f"""
        <table border="0" cellspacing="0" cellpadding="0" align="center">
            <tr>
                <td colspan="{colspan}" align="center">{node_content}</td>
            </tr>
        """
        
        # Row 2: Vertical stem dropping down from the parent node
        res += f"""
            <tr>
                <td colspan="{colspan}" align="center">
                    <table border="0" cellspacing="0" cellpadding="0">
                        <tr><td width="2" height="15" bgcolor="#555555"></td></tr>
                    </table>
                </td>
            </tr>
        """
        
        # Row 3: Horizontal connecting branch bridging all children
        if n == 1:
            # Single child implies a straight vertical line without horizontal spreading
            res += f"""
            <tr>
                <td colspan="2" align="center">
                    <table border="0" cellspacing="0" cellpadding="0">
                        <tr><td width="2" height="15" bgcolor="#555555"></td></tr>
                    </table>
                </td>
            </tr>
            """
        else:
            res += "<tr>"
            for i in range(n):
                # Calculate border logic to draw perfect L and T connector joints
                left_border = "0px" if i == 0 else "2px solid #555555"
                right_border = "0px" if i == n - 1 else "2px solid #555555"
                
                # The right border of the left cell forms the vertical drop to the child
                res += f"""
                <td align="center" width="20" style="border-top: {left_border}; border-right: 2px solid #555555; min-width: 20px;" valign="top">&nbsp;</td>
                <td align="center" width="20" style="border-top: {right_border}; min-width: 20px;" valign="top">&nbsp;</td>
                """
            res += "</tr>"
            
        # Row 4: Recursive sub-trees for each child
        res += "<tr>"
        for child in children:
            child_html = ASTHtmlGenerator._nodo_html(child)
            res += f'<td colspan="2" align="center" valign="top">{child_html}</td>'
        res += "</tr>"
        
        res += "</table>"
        
        return res


# =====================================================================
# CLASS: ASTVisualizerDialog
# What it does: A custom QDialog that embeds a QTextBrowser to render the HTML.
# Architecture: Configures a dedicated window strictly for the visualizer natively.
# =====================================================================
class ASTVisualizerDialog(QDialog):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AST Graphical Visualization")
        self.resize(1000, 800)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.web_view = QTextBrowser()
        self.web_view.setLineWrapMode(QTextBrowser.NoWrap)
        # Set dark background directly to the widget as a fallback for the text browser view
        self.web_view.setStyleSheet("QTextBrowser { background-color: #1e1e1e; border: none; padding: 20px; }")
        self.layout.addWidget(self.web_view)

    def load_html_content(self, html_string):
        """
        Injects the generated HTML string into the QTextBrowser natively.
        """
        self.web_view.setHtml(html_string)
