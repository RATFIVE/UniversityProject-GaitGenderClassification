import json
import os

def split_json_file(input_file, max_size_mb=90):
    """
    Teilt eine JSON-Datei in kleinere Dateien auf.
    
    Args:
        input_file: Pfad zur Eingabedatei
        max_size_mb: Maximale Größe pro Datei in MB (Standard: 90MB für Sicherheit)
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    
    # JSON-Datei laden
    print(f"Lade {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Prüfen ob es eine Liste ist
    if not isinstance(data, list):
        print("Warnung: JSON enthält keine Liste. Versuche mit dict.values()...")
        data = list(data.values()) if isinstance(data, dict) else [data]
    
    total_items = len(data)
    print(f"Gesamtanzahl Einträge: {total_items}")
    
    # Dateien erstellen
    output_dir = os.path.dirname(input_file) or '.'
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    
    part = 1
    start_idx = 0
    current_chunk = []
    
    while start_idx < total_items:
        # Füge Items hinzu bis Größenlimit erreicht
        temp_chunk = []
        for i in range(start_idx, total_items):
            temp_chunk.append(data[i])
            
            # Prüfe Größe nach jedem 100. Item oder am Ende
            if len(temp_chunk) % 100 == 0 or i == total_items - 1:
                test_json = json.dumps(temp_chunk, indent=2)
                if len(test_json.encode('utf-8')) > max_size_bytes:
                    # Letztes Item entfernen wenn Limit überschritten
                    if len(temp_chunk) > 1:
                        temp_chunk.pop()
                    break
        
        if not temp_chunk:
            temp_chunk = [data[start_idx]]  # Mindestens 1 Item
        
        output_file = os.path.join(output_dir, f"{base_name}_part{part}.json")
        
        with open(output_file, 'w') as f:
            json.dump(temp_chunk, f, indent=2)
        
        file_size = os.path.getsize(output_file)
        print(f"Erstellt: {output_file} ({file_size / (1024*1024):.2f} MB, {len(temp_chunk)} Einträge)")
        
        start_idx += len(temp_chunk)
        part += 1
    
    print(f"\nFertig! {part-1} Dateien erstellt.")

if __name__ == "__main__":
    split_json_file("data/data_filtered.json", max_size_mb=90)