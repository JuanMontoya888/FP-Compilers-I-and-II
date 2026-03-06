# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QHeaderView, QSizePolicy,
    QSpacerItem, QSplitter, QTabWidget, QToolButton,
    QTreeView, QVBoxLayout, QWidget)

class Ui_Widget(object):
    def setupUi(self, Widget):
        if not Widget.objectName():
            Widget.setObjectName(u"Widget")
        Widget.setEnabled(True)
        Widget.resize(800, 600)
        Widget.setStyleSheet(u"/* --- ESTILOS GENERALES --- */\n"
"QWidget {\n"
"    background-color: #1e1e1e;\n"
"    color: #cccccc;\n"
"    font-family: \"Segoe UI\", \"San Francisco\", sans-serif;\n"
"    font-size: 13px;\n"
"}\n"
"\n"
"/* --- BARRA SUPERIOR --- */\n"
"QToolButton {\n"
"    background-color: transparent;\n"
"    color: #cccccc;\n"
"    border: none;\n"
"    padding: 6px 12px;\n"
"    margin: 2px;\n"
"    border-radius: 4px;\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"    background-color: #3e3e42;\n"
"    color: #ffffff;\n"
"}\n"
"\n"
"QToolButton::menu-indicator {\n"
"    image: none; \n"
"}\n"
"\n"
"/* --- SPLITTER --- */\n"
"QSplitter::handle {\n"
"    background-color: #1e1e1e;\n"
"}\n"
"QSplitter::handle:horizontal {\n"
"    border-left: 1px solid #252526;\n"
"    width: 2px;\n"
"}\n"
"QSplitter::handle:vertical {\n"
"    border-top: 1px solid #252526;\n"
"    height: 2px;\n"
"}\n"
"QSplitter::handle:hover {\n"
"    background-color: #007acc;\n"
"}\n"
"\n"
"/* --- BARRA LATERAL (Project Explorer) --- */\n"
"QTreeView {"
                        "\n"
"    background-color: #252526;\n"
"    color: #cccccc;\n"
"    border: none;\n"
"    outline: none;\n"
"}\n"
"\n"
"QTreeView::item {\n"
"    padding: 4px;\n"
"    border-radius: 3px;\n"
"}\n"
"\n"
"QTreeView::item:hover {\n"
"    background-color: #2a2d2e;\n"
"    color: #ffffff;\n"
"}\n"
"\n"
"QTreeView::item:selected {\n"
"    background-color: #37373d;\n"
"    color: #ffffff;\n"
"}\n"
"\n"
"/* --- PESTA\u00d1AS PRINCIPALES (EDITOR) --- */\n"
"QTabWidget::pane {\n"
"    border: none;\n"
"    background-color: #1e1e1e;\n"
"}\n"
"\n"
"QTabBar::tab {\n"
"    background-color: #2d2d2d;\n"
"    color: #858585;\n"
"    padding: 8px 20px;\n"
"    border: none;\n"
"    border-right: 1px solid #1e1e1e;\n"
"}\n"
"\n"
"QTabBar::tab:selected {\n"
"    background-color: #1e1e1e;\n"
"    color: #ffffff;\n"
"    border-top: 2px solid #007acc;\n"
"}\n"
"\n"
"QTabBar::tab:hover:!selected {\n"
"    background-color: #333333;\n"
"    color: #cccccc;\n"
"}\n"
"\n"
"/* --- EDITOR DE C\u00d3DIGO --- */\n"
"QPlainTextEdit {\n"
""
                        "    background-color: #1e1e1e;\n"
"    color: #d4d4d4;\n"
"    font-family: \"Consolas\", \"Courier New\", monospace;\n"
"    font-size: 14px;\n"
"    border: none;\n"
"    padding: 5px;\n"
"    selection-background-color: #264f78;\n"
"}\n"
"\n"
"/* --- PANEL INFERIOR (Terminal y An\u00e1lisis) --- */\n"
"QTabWidget#bottomTabs::pane {\n"
"    border: none;\n"
"    background-color: #181818;\n"
"}\n"
"\n"
"QTabWidget#bottomTabs QTabBar {\n"
"    background-color: #1e1e1e;\n"
"}\n"
"\n"
"QTabWidget#bottomTabs QTabBar::tab {\n"
"    background-color: #2d2d2d;\n"
"    color: #858585;\n"
"    padding: 5px 15px;\n"
"    font-size: 11px;\n"
"    border-right: 1px solid #181818;\n"
"    border-top: none;\n"
"}\n"
"\n"
"QTabWidget#bottomTabs QTabBar::tab:selected {\n"
"    background-color: #181818;\n"
"    color: white;\n"
"    border-bottom: 2px solid #007acc;\n"
"}\n"
"\n"
"QTabWidget#bottomTabs QPlainTextEdit {\n"
"    background-color: #181818;\n"
"    padding: 10px;\n"
"}\n"
"\n"
"/* --- SCROLLBARS --- */\n"
"QSc"
                        "rollBar:vertical, QScrollBar:horizontal {\n"
"    border: none;\n"
"    background: transparent;\n"
"    width: 12px;\n"
"    height: 12px;\n"
"    margin: 0px;\n"
"}\n"
"\n"
"QScrollBar::handle:vertical, QScrollBar::handle:horizontal {\n"
"    background: #424242;\n"
"    border-radius: 5px;\n"
"    min-height: 20px;\n"
"    min-width: 20px;\n"
"    margin: 2px;\n"
"}\n"
"\n"
"QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {\n"
"    background: #4f4f4f; \n"
"}\n"
"\n"
"QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {\n"
"    background: none;\n"
"    border: none;\n"
"    height: 0px;\n"
"    width: 0px;\n"
"}\n"
"\n"
"/* --- ACTIVITY BAR --- */\n"
"QToolButton {\n"
"    background-color: transparent;\n"
"    border: none;\n"
"    padding: 8px;\n"
"    border-radius: 4px;\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"    background-color: #333333; \n"
"}\n"
"\n"
"QToolButton:checked {\n"
"    border-left: 2px solid #007acc; \n"
"    background-color: #1"
                        "e1e1e;\n"
"}\n"
"/* --- BARRA DE ESTADO DEL EDITOR (Ln, Col, UTF-8) --- */\n"
"QWidget#editorStatusBar {\n"
"    background-color: #1e1e1e; /* Mismo fondo que el editor de c\u00f3digo */\n"
"    border-top: 1px solid #2d2d2d; /* L\u00ednea divisoria s\u00faper fina y elegante */\n"
"}\n"
"\n"
"QWidget#editorStatusBar QLabel {\n"
"    color: #858585; /* Gris tenue en lugar de blanco para no distraer la vista */\n"
"    font-family: \"Segoe UI\", \"San Francisco\", sans-serif;\n"
"    font-size: 11px;\n"
"    padding: 2px 6px;\n"
"}\n"
"\n"
"QWidget#editorStatusBar QLabel:hover {\n"
"    background-color: #2d2d2d; /* Fondo gris sutil al pasar el mouse */\n"
"    color: #cccccc; /* El texto se aclara ligeramente para dar feedback interactivo */\n"
"    border-radius: 3px;\n"
"}")
        self.gridLayout_2 = QGridLayout(Widget)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.fileButton = QToolButton(Widget)
        self.fileButton.setObjectName(u"fileButton")

        self.gridLayout_2.addWidget(self.fileButton, 0, 1, 1, 1)

        self.terminalButton = QToolButton(Widget)
        self.terminalButton.setObjectName(u"terminalButton")

        self.gridLayout_2.addWidget(self.terminalButton, 0, 4, 1, 1)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.lexicoButton = QToolButton(Widget)
        self.lexicoButton.setObjectName(u"lexicoButton")

        self.verticalLayout.addWidget(self.lexicoButton)

        self.sintacticoButton = QToolButton(Widget)
        self.sintacticoButton.setObjectName(u"sintacticoButton")

        self.verticalLayout.addWidget(self.sintacticoButton)

        self.semanticoButton = QToolButton(Widget)
        self.semanticoButton.setObjectName(u"semanticoButton")

        self.verticalLayout.addWidget(self.semanticoButton)

        self.codIntButton = QToolButton(Widget)
        self.codIntButton.setObjectName(u"codIntButton")

        self.verticalLayout.addWidget(self.codIntButton)

        self.runButton_ = QToolButton(Widget)
        self.runButton_.setObjectName(u"runButton_")

        self.verticalLayout.addWidget(self.runButton_)

        self.errorButton = QToolButton(Widget)
        self.errorButton.setObjectName(u"errorButton")

        self.verticalLayout.addWidget(self.errorButton)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.gridLayout_2.addLayout(self.verticalLayout, 0, 0, 2, 1)

        self.toolsButton = QToolButton(Widget)
        self.toolsButton.setObjectName(u"toolsButton")

        self.gridLayout_2.addWidget(self.toolsButton, 0, 5, 1, 1)

        self.splitter = QSplitter(Widget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.treeView = QTreeView(self.splitter)
        self.treeView.setObjectName(u"treeView")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.treeView.sizePolicy().hasHeightForWidth())
        self.treeView.setSizePolicy(sizePolicy)
        self.splitter.addWidget(self.treeView)
        self.tabWidget = QTabWidget(self.splitter)
        self.tabWidget.setObjectName(u"tabWidget")
        self.splitter.addWidget(self.tabWidget)

        self.gridLayout_2.addWidget(self.splitter, 1, 1, 1, 8)

        self.editButton = QToolButton(Widget)
        self.editButton.setObjectName(u"editButton")

        self.gridLayout_2.addWidget(self.editButton, 0, 2, 1, 1)

        self.compileButton = QToolButton(Widget)
        self.compileButton.setObjectName(u"compileButton")

        self.gridLayout_2.addWidget(self.compileButton, 0, 3, 1, 1)


        self.retranslateUi(Widget)

        self.tabWidget.setCurrentIndex(-1)


        QMetaObject.connectSlotsByName(Widget)
    # setupUi

    def retranslateUi(self, Widget):
        Widget.setWindowTitle(QCoreApplication.translate("Widget", u"Juan Studio Code", None))
        self.fileButton.setText(QCoreApplication.translate("Widget", u"File", None))
        self.terminalButton.setText(QCoreApplication.translate("Widget", u"Terminal", None))
        self.lexicoButton.setText(QCoreApplication.translate("Widget", u"...", None))
        self.sintacticoButton.setText(QCoreApplication.translate("Widget", u"...", None))
        self.semanticoButton.setText(QCoreApplication.translate("Widget", u"...", None))
        self.codIntButton.setText(QCoreApplication.translate("Widget", u"...", None))
        self.runButton_.setText(QCoreApplication.translate("Widget", u"...", None))
        self.errorButton.setText(QCoreApplication.translate("Widget", u"...", None))
        self.toolsButton.setText(QCoreApplication.translate("Widget", u"...", None))
        self.editButton.setText(QCoreApplication.translate("Widget", u"Edit", None))
        self.compileButton.setText(QCoreApplication.translate("Widget", u"Compile", None))
    # retranslateUi

