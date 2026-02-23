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
from PySide6.QtWidgets import (QApplication, QSizePolicy, QWidget)

class Ui_Widget(object):
    def setupUi(self, Widget):
        if not Widget.objectName():
            Widget.setObjectName(u"Widget")
        Widget.resize(800, 600)
        Widget.setStyleSheet(u"/* --- ESTILOS GENERALES (Global) --- */\n"
"\n"
"/* Fondo general de la aplicaci\u00f3n y fuente */\n"
"QWidget {\n"
"    background-color: #1e1e1e;\n"
"    color: #d4d4d4;\n"
"    font-family: \"Consolas\", \"Courier New\", monospace;\n"
"    font-size: 14px;\n"
"}\n"
"\n"
"/* --- BARRA LATERAL (Project Explorer) --- */\n"
"/* Suponiendo que usas un QTreeView o QListWidget para los archivos */\n"
"\n"
"QTreeView {\n"
"    background-color: #252526;  /* Fondo de la barra lateral */\n"
"    border: none;\n"
"    padding: 5px;\n"
"    outline: 0;\n"
"}\n"
"\n"
"QTreeView::item {\n"
"    padding: 5px;\n"
"    color: #cccccc;\n"
"}\n"
"\n"
"QTreeView::item:hover {\n"
"    background-color: #2a2d2e; /* Color al pasar el mouse */\n"
"    border-radius: 3px;       /* Bordes redondeados como en la imagen */\n"
"}\n"
"\n"
"QTreeView::item:selected {\n"
"    background-color: #37373d; /* Color del archivo seleccionado */\n"
"    color: #ffffff;\n"
"    border-left: 2px solid #007acc; /* Una l\u00ednea azul a la izquier"
                        "da al seleccionar */\n"
"}\n"
"\n"
"/* Scrollbar estilo moderno (para quitar la fea de Windows/Linux por defecto) */\n"
"QScrollBar:vertical {\n"
"    border: none;\n"
"    background: #1e1e1e;\n"
"    width: 10px;\n"
"    margin: 0px 0px 0px 0px;\n"
"}\n"
"QScrollBar::handle:vertical {\n"
"    background: #424242;\n"
"    min-height: 20px;\n"
"    border-radius: 5px;\n"
"}\n"
"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n"
"    background: none;\n"
"}\n"
"\n"
"/*\n"
"Estilos para buttons\n"
"*/\n"
"QToolButton {\n"
"    background-color: transparent;\n"
"    color: #cccccc;\n"
"    border: none;\n"
"}\n"
"QToolButton:hover {\n"
"    background-color: #3e3e42;\n"
"    border-radius: 3px;\n"
"}\n"
"\n"
"/*\n"
"Styles for edit text box\n"
"*/\n"
"\n"
"QPlainTextEdit {\n"
"    background-color: #1e1e1e;\n"
"    color: #d4d4d4;\n"
"    font-family: \"Consolas\", \"Courier New\", monospace;\n"
"    font-size: 14px;\n"
"    border: none;\n"
"    padding-left: 10px;\n"
"    selection-background-col"
                        "or: #264f78;\n"
"}")

        self.retranslateUi(Widget)

        QMetaObject.connectSlotsByName(Widget)
    # setupUi

    def retranslateUi(self, Widget):
        Widget.setWindowTitle(QCoreApplication.translate("Widget", u"Widget", None))
    # retranslateUi

