# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
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
    QSplitter, QTabWidget, QToolButton, QTreeView,
    QWidget)

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
"/* --- BARRA SUPERIOR (Men\u00fa simulado) --- */\n"
"QToolButton {\n"
"    background-color: transparent;\n"
"    color: #cccccc;\n"
"    border: none;\n"
"    padding: 6px 12px;\n"
"    margin: 2px;\n"
"    border-radius: 4px; /* Bordes redondeados sutiles */\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"    background-color: #3e3e42; /* Gris m\u00e1s claro al pasar el mouse */\n"
"    color: #ffffff;\n"
"}\n"
"\n"
"/* Quita la flecha por defecto de los men\u00fas desplegables */\n"
"QToolButton::menu-indicator {\n"
"    image: none; \n"
"}\n"
"\n"
"/* --- SPLITTER (Divisor arrastrable) --- */\n"
"QSplitter::handle {\n"
"    background-color: #1e1e1e;\n"
"}\n"
"/* Diferenciamos si arrastras vertical u horizontalmente */\n"
"QSplitter::handle:horizontal {\n"
"    border-left: 1px solid #252526;\n"
"    width:"
                        " 2px;\n"
"}\n"
"QSplitter::handle:vertical {\n"
"    border-top: 1px solid #252526;\n"
"    height: 2px;\n"
"}\n"
"QSplitter::handle:hover {\n"
"    background-color: #007acc; /* Azul VS Code al pasar el mouse */\n"
"}\n"
"\n"
"/* --- BARRA LATERAL (Project Explorer) --- */\n"
"/* \u00a1CORREGIDO A QTreeView! */\n"
"QTreeView {\n"
"    background-color: #252526; /* Un tono ligeramente distinto al editor */\n"
"    color: #cccccc;\n"
"    border: none;\n"
"    outline: none; /* Quita el borde punteado horrible de Windows al hacer clic */\n"
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
"/* --- PESTA\u00d1AS (QTabWidget) --- */\n"
"QTabWidget::pane {\n"
"    border: none;\n"
"    background-color: #1e1e1e;\n"
"}\n"
"\n"
"QTabBar::tab {\n"
"    background-color: #2d2d2d;"
                        "\n"
"    color: #858585;\n"
"    padding: 8px 20px;\n"
"    border: none;\n"
"    border-right: 1px solid #1e1e1e; /* Separador entre pesta\u00f1as */\n"
"}\n"
"\n"
"QTabBar::tab:selected {\n"
"    background-color: #1e1e1e;\n"
"    color: #ffffff;\n"
"    border-top: 2px solid #007acc; /* L\u00ednea azul en la pesta\u00f1a activa */\n"
"}\n"
"\n"
"QTabBar::tab:hover:!selected {\n"
"    background-color: #333333;\n"
"    color: #cccccc;\n"
"}\n"
"\n"
"/* --- EDITOR DE C\u00d3DIGO --- */\n"
"QPlainTextEdit {\n"
"    background-color: #1e1e1e;\n"
"    color: #d4d4d4;\n"
"    font-family: \"Consolas\", \"Courier New\", monospace;\n"
"    font-size: 14px;\n"
"    border: none;\n"
"    padding: 5px;\n"
"    selection-background-color: #264f78; /* Color azul transparente al seleccionar texto */\n"
"}\n"
"\n"
"/* --- SCROLLBARS NIVEL DIOS --- */\n"
"QScrollBar:vertical, QScrollBar:horizontal {\n"
"    border: none;\n"
"    background: transparent; /* Fondo invisible */\n"
"    width: 12px;\n"
"    height: 12px;\n"
" "
                        "   margin: 0px;\n"
"}\n"
"\n"
"QScrollBar::handle:vertical, QScrollBar::handle:horizontal {\n"
"    background: #424242;\n"
"    border-radius: 5px; /* Scrollbars redondeados */\n"
"    min-height: 20px;\n"
"    min-width: 20px;\n"
"    margin: 2px; /* Margen para que floten y no toquen el borde */\n"
"}\n"
"\n"
"QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {\n"
"    background: #4f4f4f; \n"
"}\n"
"\n"
"/* Ocultamos las flechitas de los extremos (nadie las usa en un IDE moderno) */\n"
"QScrollBar::add-line, QScrollBar::sub-line {\n"
"    background: none;\n"
"    border: none;\n"
"    height: 0px;\n"
"    width: 0px;\n"
"}\n"
"QScrollBar::add-page, QScrollBar::sub-page {\n"
"    background: none;\n"
"}")
        self.gridLayout_2 = QGridLayout(Widget)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
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

        self.gridLayout_2.addWidget(self.splitter, 1, 0, 1, 12)

        self.editButton = QToolButton(Widget)
        self.editButton.setObjectName(u"editButton")

        self.gridLayout_2.addWidget(self.editButton, 0, 1, 1, 1)

        self.runButton = QToolButton(Widget)
        self.runButton.setObjectName(u"runButton")

        self.gridLayout_2.addWidget(self.runButton, 0, 6, 1, 1)

        self.terminalButton = QToolButton(Widget)
        self.terminalButton.setObjectName(u"terminalButton")

        self.gridLayout_2.addWidget(self.terminalButton, 0, 7, 1, 1)

        self.goButton = QToolButton(Widget)
        self.goButton.setObjectName(u"goButton")

        self.gridLayout_2.addWidget(self.goButton, 0, 5, 1, 1)

        self.toolsButton = QToolButton(Widget)
        self.toolsButton.setObjectName(u"toolsButton")

        self.gridLayout_2.addWidget(self.toolsButton, 0, 8, 1, 1)

        self.selButton = QToolButton(Widget)
        self.selButton.setObjectName(u"selButton")

        self.gridLayout_2.addWidget(self.selButton, 0, 3, 1, 1)

        self.viewButton = QToolButton(Widget)
        self.viewButton.setObjectName(u"viewButton")

        self.gridLayout_2.addWidget(self.viewButton, 0, 2, 1, 1)

        self.fileButton = QToolButton(Widget)
        self.fileButton.setObjectName(u"fileButton")

        self.gridLayout_2.addWidget(self.fileButton, 0, 0, 1, 1)

        self.toolButton = QToolButton(Widget)
        self.toolButton.setObjectName(u"toolButton")

        self.gridLayout_2.addWidget(self.toolButton, 0, 4, 1, 1)


        self.retranslateUi(Widget)

        self.tabWidget.setCurrentIndex(-1)


        QMetaObject.connectSlotsByName(Widget)
    # setupUi

    def retranslateUi(self, Widget):
        Widget.setWindowTitle(QCoreApplication.translate("Widget", u"Juan Studio Code", None))
        self.editButton.setText(QCoreApplication.translate("Widget", u"Edit", None))
        self.runButton.setText(QCoreApplication.translate("Widget", u"Run", None))
        self.terminalButton.setText(QCoreApplication.translate("Widget", u"Terminal", None))
        self.goButton.setText(QCoreApplication.translate("Widget", u"Go", None))
        self.toolsButton.setText(QCoreApplication.translate("Widget", u"...", None))
        self.selButton.setText(QCoreApplication.translate("Widget", u"Selection", None))
        self.viewButton.setText(QCoreApplication.translate("Widget", u"View", None))
        self.fileButton.setText(QCoreApplication.translate("Widget", u"File", None))
        self.toolButton.setText(QCoreApplication.translate("Widget", u"Window", None))
    # retranslateUi

