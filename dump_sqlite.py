#!/usr/bin/env python3

import sqlite3
import os
import sys
import json

def dump_sqlite_db(db_path, output_dir="sqlite_dump"):
    """
    Dump all content from the SQLite database into text files for easy searching.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row['name'] for row in cursor.fetchall()]
    
    print(f"Found {len(tables)} tables: {', '.join(tables)}")
    
    # Create a directory for each table
    for table in tables:
        table_dir = os.path.join(output_dir, table)
        if not os.path.exists(table_dir):
            os.makedirs(table_dir)
            
        print(f"\nDumping table: {table}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) as count FROM {table};")
        row_count = cursor.fetchone()['count']
        print(f"  Table has {row_count} rows")
        
        # Get all rows
        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()
        
        # Save table structure
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        schema = []
        for col in columns:
            schema.append({
                "cid": col["cid"],
                "name": col["name"],
                "type": col["type"],
                "notnull": col["notnull"],
                "default_value": col["dflt_value"],
                "pk": col["pk"]
            })
            
        with open(os.path.join(table_dir, "00_schema.json"), "w") as f:
            json.dump(schema, f, indent=2)
            
        # Save a list of all keys for reference
        if 'key' in schema[0]['name']:
            with open(os.path.join(table_dir, "01_all_keys.txt"), "w") as f:
                for row in rows:
                    f.write(f"{row['key']}\n")
        
        # Process each row
        for i, row in enumerate(rows):
            # Create JSON of row metadata
            row_meta = {}
            for key in row.keys():
                if isinstance(row[key], bytes):
                    row_meta[key] = f"<BINARY DATA: {len(row[key])} bytes>"
                else:
                    row_meta[key] = row[key]
            
            # Use key as filename if available, otherwise use row number
            if 'key' in row.keys():
                safe_key = row['key'].replace('/', '_').replace('\\', '_').replace('.', '_')
                if len(safe_key) > 100:  # Truncate very long keys
                    safe_key = safe_key[:100]
                base_filename = f"{safe_key}"
            else:
                base_filename = f"row_{i:05d}"
                
            # Save row metadata
            with open(os.path.join(table_dir, f"{base_filename}_meta.json"), "w") as f:
                json.dump(row_meta, f, indent=2)
                
            # Process binary data if present
            for key in row.keys():
                if isinstance(row[key], bytes):
                    # Save raw binary
                    with open(os.path.join(table_dir, f"{base_filename}_{key}.bin"), "wb") as f:
                        f.write(row[key])
                    
                    # Try to decode as text
                    try:
                        text_value = row[key].decode('utf-8', errors='ignore')
                        with open(os.path.join(table_dir, f"{base_filename}_{key}.txt"), "w", encoding="utf-8") as f:
                            f.write(text_value)
                    except:
                        pass
                    
                    # Try to decode as JSON
                    try:
                        json_data = json.loads(row[key])
                        with open(os.path.join(table_dir, f"{base_filename}_{key}.json"), "w", encoding="utf-8") as f:
                            json.dump(json_data, f, indent=2)
                    except:
                        pass
    
    # Create a simple index file
    with open(os.path.join(output_dir, "index.html"), "w") as f:
        f.write("<html><head><title>SQLite Database Dump</title></head><body>\n")
        f.write("<h1>SQLite Database Dump</h1>\n")
        
        for table in tables:
            f.write(f"<h2>Table: {table}</h2>\n")
            f.write("<ul>\n")
            
            # List all keys if available
            keys_file = os.path.join(table, "01_all_keys.txt")
            if os.path.exists(os.path.join(output_dir, keys_file)):
                with open(os.path.join(output_dir, keys_file), "r") as keys:
                    for key in keys:
                        key = key.strip()
                        if key:
                            f.write(f"<li>{key}</li>\n")
            
            f.write("</ul>\n")
        
        f.write("</body></html>\n")
        
    conn.close()
    print(f"\nDatabase dump complete. All files saved to {output_dir}")
    print(f"You can now search through the text files for your content.")
    print(f"To search for specific text: grep -r 'your search term' {output_dir}/")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dump_sqlite.py <path_to_state.vscdb> [output_directory]")
        sys.exit(1)
    
    db_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) >= 3 else "sqlite_dump"
    
    dump_sqlite_db(db_path, output_dir) 