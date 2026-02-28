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
    QSplitter, QTabWidget, QToolButton, QTreeWidget,
    QTreeWidgetItem, QWidget)

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
"    font-family: \"Segoe UI\", \"Consolas\", sans-serif;\n"
"    font-size: 13px;\n"
"}\n"
"\n"
"/* --- BARRA SUPERIOR (Men\u00fa simulado) --- */\n"
"QToolButton {\n"
"    background-color: transparent;\n"
"    color: #cccccc;\n"
"    border: none;\n"
"    padding: 5px 10px;\n"
"    margin: 2px;\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"    background-color: #3e3e42; /* Gris m\u00e1s claro al pasar el mouse */\n"
"    border-radius: 4px;\n"
"    color: #ffffff;\n"
"}\n"
"\n"
"/* --- ACTIVITY BAR (Extrema izquierda, si decides agregarla) --- */\n"
"/* Asumiendo que le pones un objectName como 'activityBar' a su contenedor */\n"
"#activityBar QToolButton {\n"
"    padding: 10px;\n"
"    margin: 0px;\n"
"    border-radius: 0px;\n"
"}\n"
"#activityBar QToolButton:checked {\n"
"    border-left: 2px solid #007acc; /* L\u00ednea azul de selecci\u00f3n */\n"
"}\n"
"\n"
"/* --- SPLITTER (Divisor arrastrable) --- *"
                        "/\n"
"QSplitter::handle {\n"
"    background-color: #1e1e1e;\n"
"    border-left: 1px solid #252526;\n"
"    border-right: 1px solid #2b2b2b;\n"
"    width: 2px;\n"
"}\n"
"QSplitter::handle:hover {\n"
"    background-color: #007acc; /* Se ilumina de azul al intentar arrastrar */\n"
"}\n"
"\n"
"/* --- BARRA LATERAL (Project Explorer) --- */\n"
"QTreeWidget {\n"
"    background-color: #252526;\n"
"    border: none;\n"
"    padding-top: 5px;\n"
"    outline: none; /* Quita el borde punteado al hacer clic */\n"
"}\n"
"\n"
"QTreeWidget::item {\n"
"    padding: 4px;\n"
"    color: #cccccc;\n"
"}\n"
"\n"
"QTreeWidget::item:hover {\n"
"    background-color: #2a2d2e;\n"
"}\n"
"\n"
"QTreeWidget::item:selected {\n"
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
"    background-color: #2d2d2d;\n"
"    color: #969696;\n"
"    padding: 8px 15px;\n"
""
                        "    border: none;\n"
"    border-right: 1px solid #252526;\n"
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
"}\n"
"\n"
"/* --- EDITOR DE TEXTO --- */\n"
"QPlainTextEdit {\n"
"    background-color: #1e1e1e;\n"
"    color: #d4d4d4;\n"
"    font-family: \"Consolas\", \"Courier New\", monospace;\n"
"    font-size: 14px;\n"
"    border: none;\n"
"    padding: 10px;\n"
"    selection-background-color: #264f78; /* Color de selecci\u00f3n de texto t\u00edpico de VS Code */\n"
"}\n"
"\n"
"/* --- SCROLLBARS --- */\n"
"QScrollBar:vertical, QScrollBar:horizontal {\n"
"    border: none;\n"
"    background: #1e1e1e;\n"
"    width: 14px;\n"
"    height: 14px;\n"
"}\n"
"\n"
"QScrollBar::handle:vertical, QScrollBar::handle:horizontal {\n"
"    background: #424242;\n"
"    border-radius: 7px;\n"
"    min-height:"
                        " 20px;\n"
"    min-width: 20px;\n"
"    margin: 2px;\n"
"}\n"
"\n"
"QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {\n"
"    background: #4f4f4f; /* Se aclara ligeramente al pasar el mouse */\n"
"}\n"
"\n"
"QScrollBar::add-line, QScrollBar::sub-line {\n"
"    background: none;\n"
"    border: none;\n"
"}")
        self.gridLayout_2 = QGridLayout(Widget)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.runButton = QToolButton(Widget)
        self.runButton.setObjectName(u"runButton")

        self.gridLayout_2.addWidget(self.runButton, 0, 5, 1, 1)

        self.goButton = QToolButton(Widget)
        self.goButton.setObjectName(u"goButton")

        self.gridLayout_2.addWidget(self.goButton, 0, 4, 1, 1)

        self.toolsButton = QToolButton(Widget)
        self.toolsButton.setObjectName(u"toolsButton")

        self.gridLayout_2.addWidget(self.toolsButton, 0, 6, 1, 1)

        self.selButton = QToolButton(Widget)
        self.selButton.setObjectName(u"selButton")

        self.gridLayout_2.addWidget(self.selButton, 0, 2, 1, 1)

        self.fileButton = QToolButton(Widget)
        self.fileButton.setObjectName(u"fileButton")

        self.gridLayout_2.addWidget(self.fileButton, 0, 0, 1, 1)

        self.editButton = QToolButton(Widget)
        self.editButton.setObjectName(u"editButton")

        self.gridLayout_2.addWidget(self.editButton, 0, 1, 1, 1)

        self.viewButton = QToolButton(Widget)
        self.viewButton.setObjectName(u"viewButton")

        self.gridLayout_2.addWidget(self.viewButton, 0, 3, 1, 1)

        self.splitter = QSplitter(Widget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.treeWidget = QTreeWidget(self.splitter)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"1");
        self.treeWidget.setHeaderItem(__qtreewidgetitem)
        self.treeWidget.setObjectName(u"treeWidget")
        self.splitter.addWidget(self.treeWidget)
        self.tabWidget = QTabWidget(self.splitter)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        self.splitter.addWidget(self.tabWidget)

        self.gridLayout_2.addWidget(self.splitter, 1, 0, 1, 9)


        self.retranslateUi(Widget)

        QMetaObject.connectSlotsByName(Widget)
    # setupUi

    def retranslateUi(self, Widget):
        Widget.setWindowTitle(QCoreApplication.translate("Widget", u"Widget", None))
        self.runButton.setText(QCoreApplication.translate("Widget", u"Run", None))
        self.goButton.setText(QCoreApplication.translate("Widget", u"Go", None))
        self.toolsButton.setText(QCoreApplication.translate("Widget", u"...", None))
        self.selButton.setText(QCoreApplication.translate("Widget", u"Selection", None))
        self.fileButton.setText(QCoreApplication.translate("Widget", u"File", None))
        self.editButton.setText(QCoreApplication.translate("Widget", u"Edit", None))
        self.viewButton.setText(QCoreApplication.translate("Widget", u"View", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("Widget", u"Tab 1", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("Widget", u"Tab 2", None))
    # retranslateUi

