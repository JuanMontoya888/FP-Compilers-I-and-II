# This Python file uses the following encoding: utf-8
import sys
import os
import traceback
from PySide6.QtWidgets import QApplication, QWidget, QSplitter
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from ui_form import Ui_Widget
from treeManager import TreeManager
from codeEditorManager import CodeEditorManager
from shortcuts import Shortcuts
from terminalManager import TerminalManager

# ============================================================
# CLASE PRINCIPAL: WIDGET (ORQUESTADOR DEL IDE)
# Esta clase actúa como el núcleo central de la aplicación,
# encargada de la inicialización coordinada de la interfaz
# de usuario y la integración de los gestores lógicos.
#
# Responsabilidades:
# - Cargar la definición de la interfaz (UI).
# - Configurar la arquitectura de paneles (Splitters).
# - Instanciar los gestores de archivos, editor y consola.
# - Vincular la interactividad de la barra de herramientas.
# ============================================================
class Widget(QWidget):

    # ============================================================
    # MÉTODO: __init__
    # Qué hace: Constructor de la clase y punto de inicio del Widget.
    # Qué componentes usa: ui_form (Ui_Widget).
    # Cómo interactúa: Establece la secuencia obligatoria de
    # configuración para asegurar que los componentes se creen en
    # el orden jerárquico correcto.
    # ============================================================
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Widget()
        self.ui.setupUi(self)

        # Mantenemos el __init__ compacto llamando a los métodos de configuración
        self.setup_icons()
        self.setup_layout()
        self.setup_components()
        self.setup_connections()

    # ============================================================
    # MÉTODO: setup_icons
    # Qué hace: Gestiona la carga y asignación de recursos visuales.
    # Qué componentes usa: QIcon, QSize, OS Path.
    # Cómo interactúa: Localiza la carpeta de recursos del proyecto
    # para dotar de identidad visual a la "Activity Bar" lateral.
    # ============================================================
    def setup_icons(self):
        """ ------ CONFIGURACIÓN DE ÍCONOS DE LA ACTIVITY BAR ------ """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(base_dir, "icons")
        icon_size = QSize(24, 24)

        # Asignación de iconos SVG a los botones de control y análisis
        self.ui.lexicoButton.setIcon(QIcon(os.path.join(icons_dir, "lexico.svg")))
        self.ui.lexicoButton.setIconSize(icon_size)

        self.ui.sintacticoButton.setIcon(QIcon(os.path.join(icons_dir, "sintactico.svg")))
        self.ui.sintacticoButton.setIconSize(icon_size)

        self.ui.semanticoButton.setIcon(QIcon(os.path.join(icons_dir, "semantico.svg")))
        self.ui.semanticoButton.setIconSize(icon_size)

        self.ui.codIntButton.setIcon(QIcon(os.path.join(icons_dir, "intermedio.svg")))
        self.ui.codIntButton.setIconSize(icon_size)

        self.ui.runButton_.setIcon(QIcon(os.path.join(icons_dir, "play.svg")))
        self.ui.runButton_.setIconSize(icon_size)

        self.ui.errorButton.setIcon(QIcon(os.path.join(icons_dir, "bug.svg")))
        self.ui.errorButton.setIconSize(icon_size)

    # ============================================================
    # MÉTODO: setup_components
    # Qué hace: Instancia los "Managers" o cerebros lógicos del programa.
    # Qué componentes usa: CodeEditorManager, TreeManager, Shortcuts.
    # Cómo interactúa: Realiza una inyección de dependencias pasando
    # referencias de la UI y de otros managers para permitir la
    # comunicación entre el sistema de archivos y el editor.
    # ============================================================
    def setup_components(self):
        """ ------ Configuraciones de componentes y atajos ------ """
        # Gestión de documentos y pestañas
        self.editor_manager = CodeEditorManager(self.ui.tabWidget)

        # Gestión del sistema de archivos vinculado a la terminal y editor
        self.explorer = TreeManager(self.ui.treeView, self.ui, self.editor_manager, self.terminal_manager)

        # Registro de manejadores de eventos de teclado globales
        self.atajos = Shortcuts(self, self.explorer, self.editor_manager)

    # ============================================================
    # MÉTODO: setup_layout
    # Qué hace: Define la jerarquía visual y el comportamiento elástico de los paneles.
    # Qué componentes usa: QSplitter, TerminalManager.
    # Cómo interactúa: Organiza la UI en dos grandes ejes: un divisor
    # horizontal para el explorador y un divisor vertical para el área
    # de edición y la consola de salida.
    # ============================================================
    def setup_layout(self):
        """ ------ Configuraciones de los splitters y la terminal ------ """
        # Control del factor de estiramiento para el panel lateral (Explorer)
        self.ui.splitter.setStretchFactor(0, 0)
        self.ui.splitter.setStretchFactor(1, 1)

        # Construcción de la arquitectura vertical (Editor arriba, Terminal abajo)
        self.v_splitter = QSplitter(Qt.Vertical)
        self.v_splitter.addWidget(self.ui.tabWidget)

        self.terminal_manager = TerminalManager()
        self.v_splitter.addWidget(self.terminal_manager)

        # Estado inicial del panel inferior
        self.terminal_manager.hide()

        # Priorizamos el espacio del editor sobre el de la terminal
        self.v_splitter.setStretchFactor(0, 1)
        self.v_splitter.setStretchFactor(1, 0)

        # Integración del layout vertical en el contenedor principal
        self.ui.splitter.addWidget(self.v_splitter)
        self.ui.splitter.setSizes([200, 800])

    # ============================================================
    # MÉTODO: setup_connections
    # Qué hace: Establece el sistema de Señales y Slots (Eventos).
    # Qué componentes usa: QPushButton/QToolButton de la UI.
    # Cómo interactúa: Conecta los clics de la barra de herramientas
    # lateral con el panel inferior, permitiendo cambiar de pestaña
    # según el tipo de análisis solicitado.
    # ============================================================
    def setup_connections(self):
        """ ------ Conexión de botones a sus respectivas acciones ------ """
        # Mapeo de botones hacia índices específicos de la terminal/consola
        self.ui.runButton_.clicked.connect(lambda: self.open_bottom_panel(0))      # Abre Terminal
        self.ui.lexicoButton.clicked.connect(lambda: self.open_bottom_panel(1))    # Abre Análisis Léxico
        self.ui.sintacticoButton.clicked.connect(lambda: self.open_bottom_panel(2))# Abre Análisis Sintáctico
        self.ui.semanticoButton.clicked.connect(lambda: self.open_bottom_panel(3)) # Abre Análisis Semántico
        self.ui.codIntButton.clicked.connect(lambda: self.open_bottom_panel(4))    # Abre Código Intermedio

    # ============================================================
    # MÉTODO: open_bottom_panel
    # Qué hace: Gestiona la visibilidad y enfoque del panel inferior.
    # Qué componentes usa: terminal_manager (QTabWidget personalizado).
    # Cómo interactúa: Es invocado por las conexiones de la UI para
    # asegurar que el usuario vea el resultado de sus acciones.
    # ============================================================
    def open_bottom_panel(self, tab_index):
        """Muestra el panel inferior y selecciona la pestaña indicada."""
        self.terminal_manager.setCurrentIndex(tab_index)
        if not self.terminal_manager.isVisible():
            self.terminal_manager.show()

# ============================================================
# BLOQUE PRINCIPAL DE EJECUCIÓN (ENTRY POINT)
# Este bloque inicializa el bucle de eventos de Qt y proporciona
# un mecanismo de captura de errores críticos para facilitar
# el debugging en entornos de producción.
# ============================================================
if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        widget = Widget()
        widget.showMaximized()
        sys.exit(app.exec())
    except Exception as e:
        # Sistema de diagnóstico de fallos catastróficos
        print("\n" + "="*50)
        print("ERROR CRÍTICO AL INICIAR LA APLICACIÓN")
        print("="*50)
        traceback.print_exc()
        print("="*50 + "\n")
        input("Presiona Enter para cerrar...")
