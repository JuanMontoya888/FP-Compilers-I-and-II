import os
import json
import html
import webbrowser

def node_to_dict(node):
    """Recursively converts an ASTNode into a JSON-serializable dictionary."""
    if not node:
        return None
    
    children_list = []
    if hasattr(node, 'children') and node.children:
        for child in node.children:
            if child:
                c_dict = node_to_dict(child)
                if c_dict:
                    children_list.append(c_dict)
                    
    return {
        "name": getattr(node, 'name', 'Node'),
        "value": str(getattr(node, 'value', '')) if getattr(node, 'value', '') is not None else '',
        "line": getattr(node, 'line', '?'),
        "col": getattr(node, 'col', '?'),
        "dtype": getattr(node, 'dtype', ''),
        "const_value": str(getattr(node, 'const_value', '')) if getattr(node, 'const_value', None) is not None else '',
        "has_error": getattr(node, 'has_error', False),
        "children": children_list
    }

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>__TITLE__ - Juan Studio Code</title>
    <style>
        :root {
            --bg-color: #1e1e1e;
            --panel-bg: #252526;
            --header-bg: #181818;
            --border-color: #383838;
            --node-border: #4ec9b0;
            --node-error-border: #f44747;
            --node-error-bg: #381a1a;
            --text-color: #cccccc;
            --text-bold: #e0e0e0;
            --accent-val: #ce9178;
            --accent-type: #9cdcfe;
            --accent-meta: #858585;
            --highlight: #dcdcaa;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, Consolas, sans-serif;
            user-select: none;
        }

        body, html {
            width: 100%;
            height: 100%;
            background-color: var(--bg-color);
            color: var(--text-color);
            overflow: hidden;
        }

        #topbar {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 52px;
            background: var(--header-bg);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.4);
        }

        .title-area {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .title-badge {
            background: #007acc;
            color: #fff;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 0.5px;
        }

        .title-text {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-bold);
        }

        .toolbar {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .search-box {
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 12px;
            width: 220px;
            outline: none;
            transition: border 0.2s;
        }
        .search-box:focus {
            border-color: #007acc;
        }

        button.btn {
            background: var(--panel-bg);
            color: var(--text-color);
            border: 1px solid var(--border-color);
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.15s;
        }

        button.btn:hover {
            background: #333333;
            color: #ffffff;
            border-color: #555555;
        }

        button.btn:active {
            background: #007acc;
            color: #fff;
        }

        #viewport {
            width: 100%;
            height: calc(100% - 52px);
            margin-top: 52px;
            cursor: grab;
            overflow: hidden;
            position: relative;
        }

        #viewport:active {
            cursor: grabbing;
        }

        #tree-svg {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: all;
        }

        .link {
            fill: none;
            stroke: #404040;
            stroke-width: 1.5px;
            transition: stroke 0.2s;
        }

        .link.error-link {
            stroke: var(--node-error-border);
            stroke-width: 2px;
        }

        .node-group {
            cursor: pointer;
        }

        .node-rect {
            fill: var(--panel-bg);
            stroke: var(--node-border);
            stroke-width: 1.5px;
            rx: 6px;
            ry: 6px;
            filter: drop-shadow(0 3px 6px rgba(0,0,0,0.35));
            transition: transform 0.15s, stroke 0.2s, fill 0.2s;
        }

        .node-group:hover .node-rect {
            stroke: #7fe6d3;
            filter: drop-shadow(0 4px 10px rgba(78, 201, 176, 0.4));
        }

        .node-group.error-node .node-rect {
            fill: var(--node-error-bg);
            stroke: var(--node-error-border);
        }

        .node-group.error-node:hover .node-rect {
            filter: drop-shadow(0 4px 10px rgba(244, 71, 71, 0.5));
        }

        .node-group.search-match .node-rect {
            stroke: var(--highlight) !important;
            stroke-width: 2.5px !important;
            filter: drop-shadow(0 0 10px var(--highlight));
        }

        .node-title {
            fill: var(--text-bold);
            font-size: 11px;
            font-weight: 700;
            font-family: Consolas, "Courier New", monospace;
            text-anchor: middle;
        }

        .node-value {
            fill: var(--accent-val);
            font-size: 11px;
            font-weight: bold;
            font-family: Consolas, "Courier New", monospace;
            text-anchor: middle;
        }

        .node-type {
            fill: var(--accent-type);
            font-size: 10px;
            font-family: Consolas, "Courier New", monospace;
            text-anchor: middle;
        }

        .node-coord {
            fill: var(--accent-meta);
            font-size: 9px;
            font-family: Consolas, "Courier New", monospace;
            text-anchor: middle;
        }

        #tooltip {
            position: absolute;
            background: #181818;
            border: 1px solid #454545;
            padding: 8px 12px;
            border-radius: 4px;
            color: #d4d4d4;
            font-size: 11px;
            pointer-events: none;
            display: none;
            z-index: 2000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            font-family: Consolas, monospace;
            line-height: 1.4;
        }

        #error-banner {
            position: absolute;
            bottom: 16px;
            left: 16px;
            background: rgba(45, 20, 20, 0.95);
            border: 1px solid var(--node-error-border);
            padding: 10px 14px;
            border-radius: 6px;
            max-width: 450px;
            max-height: 200px;
            overflow-y: auto;
            color: #ff8888;
            font-size: 11px;
            font-family: Consolas, monospace;
            z-index: 999;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            display: none;
        }

        #error-banner h4 {
            margin-bottom: 6px;
            color: #ff5555;
            font-weight: bold;
            font-size: 12px;
        }
    </style>
</head>
<body>

    <div id="topbar">
        <div class="title-area">
            <span class="title-badge">AST</span>
            <span class="title-text">__TITLE__</span>
        </div>
        <div class="toolbar">
            <input type="text" id="search-input" class="search-box" placeholder="Search node, type or value...">
            <button class="btn" id="btn-fit" title="Fit to Screen">Fit</button>
            <button class="btn" id="btn-reset" title="Reset Zoom">1:1</button>
            <button class="btn" id="btn-zoom-in" title="Zoom In">+</button>
            <button class="btn" id="btn-zoom-out" title="Zoom Out">-</button>
        </div>
    </div>

    <div id="viewport">
        <svg id="tree-svg">
            <g id="canvas-group">
                <g id="links-group"></g>
                <g id="nodes-group"></g>
            </g>
        </svg>
    </div>

    <div id="tooltip"></div>
    <div id="error-banner"></div>

    <script>
        const treeData = __TREE_DATA__;
        const errorsList = __ERRORS_LIST__;

        const MIN_NODE_W = 120;
        const MIN_NODE_H = 50;
        const H_SPACING = 30;
        const V_SPACING = 70;

        let scale = 1;
        let panX = 0;
        let panY = 50;
        let isDragging = false;
        let startX, startY;

        const viewport = document.getElementById('viewport');
        const canvasGroup = document.getElementById('canvas-group');
        const nodesGroup = document.getElementById('nodes-group');
        const linksGroup = document.getElementById('links-group');
        const tooltip = document.getElementById('tooltip');
        const searchInput = document.getElementById('search-input');
        const errorBanner = document.getElementById('error-banner');

        if (errorsList && errorsList.length > 0) {
            errorBanner.style.display = 'block';
            errorBanner.innerHTML = '<h4>Compiler Errors (' + errorsList.length + '):</h4>' + 
                errorsList.map(e => '<div>• ' + escapeHtml(e) + '</div>').join('');
        }

        function escapeHtml(text) {
            return String(text)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        function measureNode(node) {
            const lines = [];
            if (node.name) {
                node.name.split('\\n').forEach(l => lines.push(l));
            }
            if (node.value) {
                lines.push("'" + node.value + "'");
            }
            if (node.line !== undefined && node.line !== '?') {
                lines.push('(Ln ' + node.line + ', Col ' + node.col + ')');
            }

            let maxLen = 0;
            lines.forEach(l => { if (l.length > maxLen) maxLen = l.length; });

            const width = Math.max(MIN_NODE_W, maxLen * 8.5 + 24);
            const height = Math.max(MIN_NODE_H, lines.length * 15 + 18);
            node._boxW = width;
            node._boxH = height;

            node._lines = lines;
        }

        function computeLayout(node) {
            measureNode(node);

            const children = (node.children || []).filter(c => !!c);
            if (children.length === 0) {
                node._subtreeW = node._boxW;
                return;
            }

            let totalW = 0;
            children.forEach((child, i) => {
                computeLayout(child);
                totalW += child._subtreeW;
                if (i < children.length - 1) totalW += H_SPACING;
            });

            node._subtreeW = Math.max(node._boxW, totalW);
        }

        function assignPositions(node, x, y) {
            node._x = x;
            node._y = y;

            const children = (node.children || []).filter(c => !!c);
            if (children.length === 0) return;

            let totalChildrenW = children.reduce((acc, c) => acc + c._subtreeW, 0) + (children.length - 1) * H_SPACING;
            let currentX = x - totalChildrenW / 2;

            children.forEach(child => {
                const childCenterX = currentX + child._subtreeW / 2;
                assignPositions(child, childCenterX, y + node._boxH + V_SPACING);
                currentX += child._subtreeW + H_SPACING;
            });
        }

        function drawTree(node, inheritedError = false) {
            const isError = node.has_error || inheritedError;

            const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            g.setAttribute('class', 'node-group' + (isError ? ' error-node' : ''));
            g.setAttribute('data-name', (node.name || '').toLowerCase());
            g.setAttribute('data-value', (node.value || '').toLowerCase());

            const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            rect.setAttribute('class', 'node-rect');
            rect.setAttribute('x', node._x - node._boxW / 2);
            rect.setAttribute('y', node._y);
            rect.setAttribute('width', node._boxW);
            rect.setAttribute('height', node._boxH);
            g.appendChild(rect);

            const startY = node._y + 16;
            (node._lines || []).forEach((line, idx) => {
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', node._x);
                text.setAttribute('y', startY + idx * 14);

                if (idx === 0) {
                    text.setAttribute('class', 'node-title');
                } else if (line.startsWith("'")) {
                    text.setAttribute('class', 'node-value');
                } else if (line.startsWith('(')) {
                    text.setAttribute('class', 'node-coord');
                } else {
                    text.setAttribute('class', 'node-type');
                }
                text.textContent = line;
                g.appendChild(text);
            });

            // Hover tooltip
            g.addEventListener('mouseenter', (e) => {
                tooltip.style.display = 'block';
                tooltip.innerHTML = '<strong>' + escapeHtml(node.name) + '</strong>' +
                    (node.value ? '<br>Value: <span style="color:#ce9178;">' + escapeHtml(node.value) + '</span>' : '') +
                    (node.dtype ? '<br>Type: <span style="color:#9cdcfe;">' + escapeHtml(node.dtype) + '</span>' : '') +
                    (node.const_value ? '<br>Computed: <span style="color:#b5cea8;">' + escapeHtml(node.const_value) + '</span>' : '') +
                    '<br>Location: Ln ' + node.line + ', Col ' + node.col;
            });
            g.addEventListener('mousemove', (e) => {
                tooltip.style.left = (e.clientX + 14) + 'px';
                tooltip.style.top = (e.clientY + 14) + 'px';
            });
            g.addEventListener('mouseleave', () => {
                tooltip.style.display = 'none';
            });

            nodesGroup.appendChild(g);

            const children = (node.children || []).filter(c => !!c);
            children.forEach(child => {
                const pX = node._x;
                const pY = node._y + node._boxH;
                const cX = child._x;
                const cY = child._y;

                // Orthogonal routing
                const midY = pY + V_SPACING / 2;
                const d = `M ${pX} ${pY} L ${pX} ${midY} L ${cX} ${midY} L ${cX} ${cY}`;

                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('class', 'link' + (isError ? ' error-link' : ''));
                path.setAttribute('d', d);
                linksGroup.appendChild(path);

                drawTree(child, isError);
            });
        }

        function updateTransform() {
            canvasGroup.setAttribute('transform', `translate(${panX}, ${panY}) scale(${scale})`);
        }

        function fitToScreen() {
            if (!treeData) return;
            const bbox = canvasGroup.getBBox();
            if (bbox.width === 0 || bbox.height === 0) return;

            const vpW = viewport.clientWidth;
            const vpH = viewport.clientHeight;

            const scaleX = (vpW - 80) / bbox.width;
            const scaleY = (vpH - 80) / bbox.height;
            scale = Math.min(1.2, Math.max(0.2, Math.min(scaleX, scaleY)));

            panX = (vpW / 2) - ((bbox.x + bbox.width / 2) * scale);
            panY = 40 - (bbox.y * scale);
            updateTransform();
        }

        // Mouse pan
        viewport.addEventListener('mousedown', (e) => {
            isDragging = true;
            startX = e.clientX - panX;
            startY = e.clientY - panY;
        });
        window.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            panX = e.clientX - startX;
            panY = e.clientY - startY;
            updateTransform();
        });
        window.addEventListener('mouseup', () => {
            isDragging = false;
        });

        // Mouse wheel zoom
        viewport.addEventListener('wheel', (e) => {
            e.preventDefault();
            const zoomFactor = 1.15;
            const mouseX = e.clientX;
            const mouseY = e.clientY - 52;

            let newScale = e.deltaY < 0 ? scale * zoomFactor : scale / zoomFactor;
            newScale = Math.min(3.0, Math.max(0.1, newScale));

            panX = mouseX - (mouseX - panX) * (newScale / scale);
            panY = mouseY - (mouseY - panY) * (newScale / scale);
            scale = newScale;
            updateTransform();
        }, { passive: false });

        // Search highlight
        searchInput.addEventListener('input', (e) => {
            const q = e.target.value.trim().toLowerCase();
            const allGroups = document.querySelectorAll('.node-group');
            allGroups.forEach(g => {
                if (!q) {
                    g.classList.remove('search-match');
                    return;
                }
                const name = g.getAttribute('data-name') || '';
                const val = g.getAttribute('data-value') || '';
                if (name.includes(q) || val.includes(q)) {
                    g.classList.add('search-match');
                } else {
                    g.classList.remove('search-match');
                }
            });
        });

        // Toolbar buttons
        document.getElementById('btn-zoom-in').onclick = () => {
            scale = Math.min(3.0, scale * 1.2);
            updateTransform();
        };
        document.getElementById('btn-zoom-out').onclick = () => {
            scale = Math.max(0.1, scale / 1.2);
            updateTransform();
        };
        document.getElementById('btn-reset').onclick = () => {
            scale = 1.0;
            fitToScreen();
        };
        document.getElementById('btn-fit').onclick = fitToScreen;

        // Initial render
        if (treeData) {
            computeLayout(treeData);
            assignPositions(treeData, viewport.clientWidth / 2, 30);
            drawTree(treeData);
            setTimeout(fitToScreen, 60);
        }
    </script>
</body>
</html>
"""

def export_ast_to_html(ast_root, errors=None, title="AST Visualization", filename="ast_view.html"):
    """
    Renders the AST into a standalone, non-blocking HTML file.
    Saves to the compiler_output directory.
    """
    if not ast_root:
        return None
        
    tree_json = json.dumps(node_to_dict(ast_root))
    errors_json = json.dumps(errors or [])
    
    html_content = HTML_TEMPLATE.replace("__TITLE__", title)
    html_content = html_content.replace("__TREE_DATA__", tree_json)
    html_content = html_content.replace("__ERRORS_LIST__", errors_json)
    
    # Locate compiler_output directory
    curr_dir = os.path.dirname(os.path.abspath(__file__)) # ide/components
    project_root = os.path.dirname(os.path.dirname(curr_dir)) # Juan-Studio-Code
    output_dir = os.path.join(project_root, "compiler_output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    out_file = os.path.join(output_dir, filename)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return out_file

def open_ast_in_browser(ast_root, errors=None, title="AST Visualization", filename="ast_view.html"):
    """
    Exports the AST to HTML and opens it in the default system browser.
    Completely non-blocking: spawns independently in the user's browser.
    """
    out_file = export_ast_to_html(ast_root, errors, title, filename)
    if out_file and os.path.exists(out_file):
        webbrowser.open("file://" + os.path.abspath(out_file))
        return out_file
    return None
