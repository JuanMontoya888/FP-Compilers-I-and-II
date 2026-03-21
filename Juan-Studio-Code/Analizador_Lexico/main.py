from SCAN import SCANNER 

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