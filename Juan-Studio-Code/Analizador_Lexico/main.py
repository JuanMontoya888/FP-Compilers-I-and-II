from SCAN import SCANNER 

# ============================================================
# PUNTO DE ENTRADA DEL PROGRAMA (MAIN)
# 
# Qué hace: Orquesta la ejecución inicial del analizador léxico.
# Componentes que usa: Instancia de la clase SCANNER.
# Interacción: Define la ruta del archivo fuente, arranca el
# motor de escaneo y notifica al usuario cuando el proceso
# ha finalizado.
# ============================================================
def main():
    path_file = "file.txt"
    print(f"Iniciando Analizador Léxico para el archivo: {path_file}...")
    
    #initialize scanner with path of file
    scanner = SCANNER(path_file)
    
    #start scanner to get tokens
    scanner.get_token()
    print("¡Análisis terminado!")

if __name__ == "__main__":
    main()