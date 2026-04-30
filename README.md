Analizador Léxico y Entorno de Desarrollo (IDE) - Proyecto Compiladores

Este proyecto implementa un Analizador Léxico (Scanner) construido desde cero en Python, integrado dentro de un Entorno de Desarrollo Integrado (IDE) personalizado utilizando PySide6. El analizador procesa código fuente (similar a C/C++), extrae los lexemas y los clasifica en tokens utilizando un Autómata Finito Determinista (DFA), reportando errores léxicos con precisión de línea y columna.
Características Principales

    Autómata Finito Determinista (DFA): Motor léxico basado en transiciones de estado (match-case en Python 3.10+) para una lectura eficiente de un solo paso (O(N)).

    Reconocimiento de Operadores Compuestos: Lógica avanzada de lookahead que permite identificar operadores de dos caracteres (++, --, ==, &&, ||, etc.) incluso tolerando saltos de línea intermedios según reglas específicas.

    Cadenas y Caracteres: Estados dedicados para capturar constantes de cadena ("...") y de carácter ('...'), reportando errores si no se cierran antes del fin de línea o archivo.

    Filtrado de Comentarios: Reconoce y descarta comentarios de una línea (//) y de bloque múltiple (/* ... */).

    Manejo de Errores Estricto (Greedy): Capacidad de recuperación ante lexemas mal formados. Por ejemplo, al leer 32.algo, el escáner aísla el error 32. y continúa evaluando algo como un identificador válido, evitando fallos en cascada.

    IDE Interactivo (PySide6):

        Consola de Salida Coloreada: Formateo de texto enriquecido (QTextCharFormat) para resaltar errores en rojo.

        Salto a Código (Jump-to-Error): Al hacer clic en un error en la terminal, el cursor del editor de código salta automáticamente a la línea y columna exactas.

        Procesamiento Asíncrono: Ejecución del análisis léxico en un hilo secundario (QThread) para evitar que la interfaz de usuario se congele con archivos grandes.

Arquitectura del Proyecto

El proyecto está modularizado siguiendo principios de separación de responsabilidades:

    GLOBALS.py: Define el vocabulario del compilador. Contiene las enumeraciones TokenType (identificadores, palabras reservadas, operadores) y State (estados del autómata).

    scanner.py (SCANNER): El núcleo del analizador. Lee el archivo fuente, gestiona los punteros espaciales (_get_next_char, _unget_char) y genera el archivo de salida estructurado tokens.txt.

    main.py (Widget): El orquestador principal de la interfaz gráfica. Inicializa el Splitter, los íconos y coordina la comunicación entre los submódulos.

    terminalManager.py: Gestiona las pestañas inferiores del IDE. Se encarga de mostrar la salida del analizador, filtrar los errores con expresiones regulares (Regex) y enviar señales al editor de código.

    codeEditorManager.py: Administra las pestañas del editor de texto, el resaltado de sintaxis (Highlighter) y la numeración de líneas.

Requisitos e Instalación

    Python 3.10 o superior (Requerido para la estructura match-case).

    Librería PySide6 para la interfaz gráfica.

Bash

pip install PySide6

Uso

Para ejecutar el IDE y probar el analizador léxico:

    Clona el repositorio y asegúrate de que todos los módulos estén en el mismo directorio.

    Ejecuta el archivo principal:

Bash

python main.py

    En la interfaz, abre o escribe código en C/C++ en el editor.

    Haz clic en el botón de Análisis Léxico en la barra de herramientas lateral.

    Revisa los resultados:

        La pestaña Lexical Analysis mostrará los tokens limpios.

        La pestaña Errors (si hay errores) mostrará la posición exacta en rojo. Haz clic en ellos para navegar por el código.

Archivo de Salida (tokens.txt)

El analizador serializa los resultados en un archivo de texto con un formato tabular legible por humanos, ideal para depuración o para alimentar la siguiente fase (Análisis Sintáctico):
Plaintext

## TOKEN LEXEMA POSITION

INT int
MAIN main
LPAREN (
RPAREN )
LBRACE {
ID contador
ASSIGN =
NUM_INT 0
SEMI ;
ERROR 32. Ln 5, Col 15

Lógica de Estados (DFA)

El autómata transita entre los siguientes estados principales:

    START: Clasifica el primer carácter e ignora espacios en blanco.

    INID: Acumula letras, números y _ para identificar variables o buscar en la tabla Hash de palabras reservadas.

    INNUM_INT / INNUM_FLOAT: Valida la construcción de números, detectando puntos flotantes mal ubicados.

    INSTRING / INCHAR: Captura literales delimitados por comillas.

    INCOMMENT_LINE / INCOMMENT_BLOCK: Absorbe caracteres hasta encontrar las secuencias de cierre \n o */.

Fase 1 completada. Siguiente paso: Análisis Sintáctico (AST).
