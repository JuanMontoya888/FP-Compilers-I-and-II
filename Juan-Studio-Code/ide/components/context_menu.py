import os
import shutil
from PySide6.QtWidgets import QMenu, QMessageBox, QInputDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard, QGuiApplication

# =====================================================================
# CLASS: ExplorerContextMenuManager
# Handles right-click context menu actions on the file explorer.
# Operations: Open, Copy Path, Rename, Delete.
# =====================================================================
class ExplorerContextMenuManager:
    def __init__(self, tree_view, model, tree_manager):
        self.tree = tree_view
        self.model = model
        self.tree_manager = tree_manager

        # Enable custom context menu policy on the tree view
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):
        index = self.tree.indexAt(position)
        if not index.isValid():
            return

        file_path = self.model.filePath(index)
        is_dir = self.model.isDir(index)

        menu = QMenu(self.tree)
        
        # Action: Open (only for files)
        if not is_dir:
            action_open = menu.addAction("Open")
            action_open.triggered.connect(lambda: self.tree_manager.on_file_selected(index))

        # Action: Copy Path
        action_copy = menu.addAction("Copy Path")
        action_copy.triggered.connect(lambda: self.copy_path(file_path))

        menu.addSeparator()

        # Action: Rename
        action_rename = menu.addAction("Rename")
        action_rename.triggered.connect(lambda: self.rename_item(file_path, index))

        # Action: Delete
        action_delete = menu.addAction("Delete")
        action_delete.triggered.connect(lambda: self.delete_item(file_path, is_dir))

        menu.exec_(self.tree.viewport().mapToGlobal(position))

    def copy_path(self, file_path):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(os.path.normpath(file_path))

    def rename_item(self, file_path, index):
        old_name = os.path.basename(file_path)
        dir_name = os.path.dirname(file_path)
        
        new_name, ok = QInputDialog.getText(
            self.tree, "Rename", f"Enter new name for '{old_name}':", text=old_name
        )
        
        if ok and new_name and new_name != old_name:
            new_path = os.path.join(dir_name, new_name)
            try:
                os.rename(file_path, new_path)
            except Exception as e:
                QMessageBox.critical(self.tree, "Rename Error", f"Could not rename '{old_name}':\n{str(e)}")

    def delete_item(self, file_path, is_dir):
        item_name = os.path.basename(file_path)
        reply = QMessageBox.question(
            self.tree, "Confirm Delete", 
            f"Are you sure you want to delete '{item_name}'?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if is_dir:
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
            except Exception as e:
                QMessageBox.critical(self.tree, "Delete Error", f"Could not delete '{item_name}':\n{str(e)}")
