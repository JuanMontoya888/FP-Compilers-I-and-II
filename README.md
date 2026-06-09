# IDE Compiladores - Proyecto de Análisis Sintáctico

Este proyecto implementa un compilador modular de alto rendimiento integrado en un Entorno de Desarrollo Integrado (IDE) personalizado mediante **PySide6**. El sistema procesa código fuente similar a C/C++, transformándolo desde su representación léxica hasta una estructura jerárquica compleja.

## Características Principales

### Motor de Análisis

* **Analizador Léxico (DFA):** Motor basado en transiciones de estado para una lectura eficiente de un solo paso (O(N)).
* **Analizador Sintáctico (Parser):** Implementación de descenso recursivo (LL(1)) para la validación gramatical.
* **Generación de AST:** Construcción de un Árbol Sintáctico Abstracto (AST) que organiza las estructuras de control, expresiones y declaraciones en una jerarquía lógica.
* **Manejo de Errores (Panic-Mode):** Sistema defensivo que identifica errores sintácticos, reporta su ubicación exacta y sincroniza el flujo para continuar con el análisis, evitando colapsos o bucles infinitos.
* **Jerarquía de Precedencia:** Soporte completo para operadores lógicos, relacionales y aritméticos (incluyendo exponenciación).

### Entorno de Desarrollo (IDE)

* **Consola de Salida Coloreada:** Formateo de texto enriquecido para identificar errores léxicos y sintácticos en tiempo real.
* **Jump-to-Error:** Navegación automática: al hacer clic en un error de la terminal, el cursor del editor se posiciona y subraya (Wave Underline) la ubicación exacta del fallo.
* **Procesamiento Asíncrono:** Ejecución del análisis en hilos secundarios (QThread) para garantizar una interfaz fluida.
* **Gestión de Documentos:** Editor con pestañas, numeración de líneas, resaltado de sintaxis dinámico y persistencia de archivos.

## Estructura del Proyecto

```text
Juan-Studio-Code/
├── Analizador_Lexico/          # DFA y Tabla de Tokens
├── Analizador_Sintactico/      # Parser LL(1) y construcción del AST
├── components/                 # Módulos UI (Menús contextuales, utils)
├── compiler_output/            # Salida estructurada (tokens.txt, tree.txt)
├── ASTNode.py                  # Estructuras de datos para el Árbol Sintáctico
├── main.py                     # Punto de entrada de la aplicación
├── widget.py                   # Orquestador de la interfaz principal
├── terminalManager.py          # Gestión asíncrona de reportes y errores
└── codeEditorManager.py        # Motor de edición y resaltado sintáctico

```

## Flujo de Procesamiento

1. **Análisis Léxico:** El scanner identifica lexemas y los clasifica en `TokenType`, descartando comentarios y detectando errores de caracteres mal formados.
2. **Análisis Sintáctico:** El parser consume el flujo de tokens y valida las reglas gramaticales (EBNF), construyendo recursivamente el árbol sintáctico.
3. **Construcción del AST:** Cada regla gramatical (expresiones, iteraciones, condicionales) genera nodos vinculados que representan la jerarquía del programa.
4. **Visualización:** El árbol resultante es serializado en `compiler_output/tree.txt` para su depuración.

## Requisitos e Instalación

1. **Python 3.10 o superior** (requerido para la estructura `match-case`).
2. **PySide6**:
```bash
pip install PySide6

```



## Uso

1. Ejecuta el IDE con: `python widget.py`
2. Escribe o abre un archivo fuente con sintaxis C/C++.
3. Utiliza los botones de análisis en la barra lateral.
4. **Resultados:** * La pestaña **Lexical Analysis** muestra los tokens generados.
* La pestaña **Errors** permite navegación directa al código fuente.
* El árbol generado se guarda automáticamente en `compiler_output/tree.txt`.



---

*Proyecto de Compiladores I & II | Juan-Studio-Code*
