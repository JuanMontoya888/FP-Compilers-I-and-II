from PySide6.QtWidgets import QDialog, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainter
from PySide6.QtCore import Qt, QRectF

# =====================================================================
# CORE MODULE: GRAPHICAL TREE VISUALIZER (Hardware Accelerated)
# Architecture: Uses QGraphicsView/Scene for instant rendering of 
# massive graphs without blocking the UI thread.
# =====================================================================

class GraphicalTreeVisualizer(QDialog):
    def __init__(self, parent=None, title="Graphical Tree Visualization"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(1000, 700)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # High-performance 2D Canvas
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(QColor("#1e1e1e")))
        
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setOptimizationFlags(QGraphicsView.DontSavePainterState)
        self.view.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        
        # Enable zooming with mouse wheel (handled via a small event filter override later)
        self.layout.addWidget(self.view)

        # Style Constants
        self.MIN_NODE_WIDTH = 100
        self.MIN_NODE_HEIGHT = 45
        self.H_SPACING = 30
        self.V_SPACING = 60

    def render_tree(self, root_node, errors=None):
        """Builds the tree using Qt Graphics Items"""
        self.scene.clear()
        
        if not root_node:
            return
            
        # 1. Calculate the bounding widths and box sizes of all subtrees
        self._calculate_widths(root_node)
        
        # 2. Draw nodes and connections recursively
        self._draw_node(root_node, x=0, y=0)
        
        # Show errors on top if any
        if errors:
            err_text = "Syntax Errors:\n" + "\n".join(errors)
            t_item = self.scene.addText(err_text)
            t_item.setDefaultTextColor(QColor("#ff5555"))
            t_item.setPos(-self.MIN_NODE_WIDTH/2, -100)

    def _get_node_html(self, node):
        import html
        safe_name = html.escape(str(node.name))
        text_html = f"<div align='center' style='font-family: Consolas; font-size: 9pt;'>"
        text_html += f"<span style='color: #d4d4d4; font-weight: bold;'>{safe_name}</span>"
        if hasattr(node, 'value') and node.value:
            safe_val = html.escape(str(node.value))
            text_html += f"<br><span style='color: #ce9178; font-weight: bold;'>'{safe_val}'</span>"
        if hasattr(node, 'line') and str(node.line) != "?":
            text_html += f"<br><span style='color: #858585; font-size: 8pt;'>(Ln {node.line}, Col {node.col})</span>"
        text_html += "</div>"
        return text_html

    def _calculate_widths(self, node):
        """Post-order traversal: calculates dynamic box sizes and subtree widths."""
        # Calculate text bounding box dynamically using HTML
        temp_item = QGraphicsTextItem()
        temp_item.setHtml(self._get_node_html(node))
        br = temp_item.boundingRect()
        
        node._box_width = max(self.MIN_NODE_WIDTH, br.width() + 20)
        node._box_height = max(self.MIN_NODE_HEIGHT, br.height() + 10)

        children = node.children if hasattr(node, 'children') else []
        valid_children = [c for c in children if c]
        
        if not valid_children:
            node._tree_width = node._box_width
            return
            
        total_children_width = 0
        for idx, child in enumerate(valid_children):
            self._calculate_widths(child)
            total_children_width += child._tree_width
            if idx < len(valid_children) - 1:
                total_children_width += self.H_SPACING
                    
        node._tree_width = max(node._box_width, total_children_width)

    def _draw_node(self, node, x, y, inherited_error=False):
        """Pre-order traversal: draws the dynamic node and routes edges to children."""
        
        is_error_path = getattr(node, 'has_error', False) or inherited_error
        
        border_color = QColor("#ff5555") if is_error_path else QColor("#56b6c2")
        bg_color = QColor("#3c1f1f") if is_error_path else QColor("#252526")
        edge_color = QColor("#ff5555") if is_error_path else QColor("#404040")

        # --- Draw Node Box ---
        rect = QGraphicsRectItem(x - node._box_width/2, y, node._box_width, node._box_height)
        rect.setBrush(QBrush(bg_color))
        rect.setPen(QPen(border_color, 1.5))
        self.scene.addItem(rect)
        
        # --- Draw Text ---
        text_item = QGraphicsTextItem()
        text_item.setHtml(self._get_node_html(node))
        
        # Center text inside the dynamically sized box
        br = text_item.boundingRect()
        text_item.setPos(x - br.width()/2, y + (node._box_height - br.height())/2)
        self.scene.addItem(text_item)
        
        # --- Recursive Children & Edge Routing ---
        children = node.children if hasattr(node, 'children') else []
        valid_children = [c for c in children if c]
        if not valid_children:
            return
            
        total_children_width = sum(c._tree_width for c in valid_children) + (len(valid_children) - 1) * self.H_SPACING
        current_x = x - total_children_width / 2
        
        parent_bottom_center_x = x
        parent_bottom_center_y = y + node._box_height
        
        # --- Orthogonal Routing (Comb Style) for large groups ---
        mid_y = parent_bottom_center_y + self.V_SPACING / 2
        
        # Parent vertical drop
        line = QGraphicsLineItem(parent_bottom_center_x, parent_bottom_center_y, parent_bottom_center_x, mid_y)
        line.setPen(QPen(edge_color, 1.5))
        line.setZValue(-1)
        self.scene.addItem(line)
        
        # Horizontal Spine
        first_child_x = current_x + (valid_children[0]._tree_width / 2)
        last_child_x = current_x + total_children_width - (valid_children[-1]._tree_width / 2)
        
        spine = QGraphicsLineItem(first_child_x, mid_y, last_child_x, mid_y)
        spine.setPen(QPen(edge_color, 1.5))
        spine.setZValue(-1)
        self.scene.addItem(spine)
        
        # Children vertical drops
        for child in valid_children:
            child_center_x = current_x + (child._tree_width / 2)
            child_top_y = y + node._box_height + self.V_SPACING
            
            drop = QGraphicsLineItem(child_center_x, mid_y, child_center_x, child_top_y)
            drop.setPen(QPen(edge_color, 1.5))
            drop.setZValue(-1)
            self.scene.addItem(drop)
            
            self._draw_node(child, child_center_x, child_top_y, inherited_error=is_error_path)
            current_x += child._tree_width + self.H_SPACING


    def wheelEvent(self, event):
        """Allows zooming with mouse scroll"""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.view.scale(zoom_factor, zoom_factor)
