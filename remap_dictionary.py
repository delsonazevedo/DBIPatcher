import re
import os

def read_file_robust(filepath):
    """Reads a file trying multiple encodings."""
    encodings = ['utf-16', 'utf-8', 'cp1252', 'latin1']
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Error reading {filepath} with {enc}: {e}")
            break
    print(f"Failed to read {filepath} with supported encodings.")
    return None

def parse_scan_output(filepath, filter_cyrillic=True):
    """
    Parses the scan output file to create a map of Text -> KeyIndex.
    Format: at 0x0063B0C8 key 0x8b3b83f7a395ab95 / 2602     [34 ]: 'Text'
    """
    text_to_key = {}
    
    if not os.path.exists(filepath):
        print(f"Warning: File not found: {filepath}")
        return {}

    content = read_file_robust(filepath)
    if content is None:
        return {}
        
    # Regex to capture key index and text
    # Matches: key ... / <KeyIndex> ... : '<Text>'
    pattern = re.compile(r"key 0x[0-9a-f]+ / (\d+)\s+\[\d+\s*\]: '(.*?)'")
    
    # Regex for Russian characters (Cyrillic)
    russian_pattern = re.compile(r"[а-яА-Я]")
    
    for match in pattern.finditer(content):
        key_index = int(match.group(1))
        text = match.group(2)
        
        # Unescape common sequences
        text = text.replace(r"\n", "\n")
        text = text.replace(r"\'", "'")
        
        # Filter logic
        if filter_cyrillic:
            if russian_pattern.search(text):
                text_to_key[text] = key_index
        else:
            # For English/General, accept everything (or maybe filter garbage if needed)
            # For now, accept all to catch mixed content
            text_to_key[text] = key_index
        
    return text_to_key

def parse_dict(filepath):
    """
    Parses the existing dictionary to get ID -> Text map.
    Format: ID;KeyIndex;Text
    """
    id_to_text = {}
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return {}
    
    # Dictionary is likely UTF-8
    content = read_file_robust(filepath)
    if content is None:
        return {}

    for line in content.splitlines():
        parts = line.strip().split(';', 2)
        if len(parts) == 3:
            entry_id, _, text = parts
            # Skip comments or invalid lines
            if entry_id.startswith("//") or not entry_id:
                continue
            # Unescape newlines in dictionary text for matching
            text_val = text.replace(r"\n", "\n")
            id_to_text[entry_id] = text_val
    return id_to_text

def generate_new_dict(id_to_text, text_to_key, output_path):
    """
    Generates the new dictionary with updated key indices.
    """
    found_count = 0
    missing_count = 0
    
    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        # Create a normalized map for fallback lookups
        # Map: normalized_text -> (original_text, key_index)
        normalized_map = {}
        for t, k in text_to_key.items():
            norm = t.strip().lower()
            if norm not in normalized_map:
                normalized_map[norm] = (t, k)

        # Track which texts from the binary have been used
        used_texts = set()

        for entry_id, text in id_to_text.items():
            match_found = False
            new_key_index = -1
            matched_text = ""
            match_type = ""

            # 1. Exact match
            if text in text_to_key:
                new_key_index = text_to_key[text]
                matched_text = text
                match_type = "EXACT"
                match_found = True
            
            # 2. Normalized match (ignore whitespace/case)
            if not match_found:
                norm_text = text.strip().lower()
                if norm_text in normalized_map:
                    matched_text, new_key_index = normalized_map[norm_text]
                    match_type = "NORM"
                    match_found = True
            
            # 3. Substring/Partial match (Conservative)
            # Only if length difference is small to avoid false positives
            if not match_found:
                for t, k in text_to_key.items():
                    # Check if one contains the other
                    if (text in t or t in text):
                        # Calculate length ratio
                        len_ratio = len(t) / len(text) if len(text) > 0 else 0
                        if 0.8 < len_ratio < 1.2: # Allow 20% length variation
                            new_key_index = k
                            matched_text = t
                            match_type = "FUZZY"
                            match_found = True
                            break

            if match_found:
                # Mark as used
                used_texts.add(matched_text)
                
                # Write back with escaped newlines if needed
                text_out = matched_text.replace("\n", r"\n")
                f.write(f"{entry_id};{new_key_index};{text_out}\n")
                found_count += 1
            else:
                # For now, just mark as missing
                text_out = text.replace("\n", r"\n")
                f.write(f"// MISSING: {entry_id};?;{text_out}\n")
                missing_count += 1
        
        # Process new strings found in binary but not in dictionary
        new_strings_count = 0
        new_id_counter = 1
        
        f.write("\n// NEW STRINGS FOUND IN BINARY\n")
        
        for text, key_index in text_to_key.items():
            if text not in used_texts:
                # Generate a new ID
                new_id = f"NEW_{new_id_counter:04d}"
                new_id_counter += 1
                
                text_out = text.replace("\n", r"\n")
                f.write(f"{new_id};{key_index};{text_out}\n")
                new_strings_count += 1
                
    print(f"Generated dictionary: {found_count} matched, {missing_count} missing, {new_strings_count} new strings added.")

def main():
    new_ru_path = "translate/new_ru_849.txt"
    new_en_path = "translate/new_en_849.txt" 
    dict_path = "translate/dict.txt"
    output_path = "translate/dict.849.txt"
    
    text_to_key = {}
    
    print(f"Reading Russian strings from {new_ru_path}...")
    ru_map = parse_scan_output(new_ru_path, filter_cyrillic=True)
    text_to_key.update(ru_map)
    print(f"Found {len(ru_map)} valid Russian strings.")
    
    print(f"Reading English/Other strings from {new_en_path}...")
    en_map = parse_scan_output(new_en_path, filter_cyrillic=False)
    # Merge English strings, overwriting if duplicates (should be same key anyway)
    # But prioritize Russian if we want to be sure? Actually key index is what matters.
    # If same text appears, key index should be identical.
    text_to_key.update(en_map)
    print(f"Found {len(en_map)} strings in English scan.")
    
    print(f"Total unique strings found: {len(text_to_key)}")
    
    print(f"Reading existing dictionary from {dict_path}...")
    id_to_text = parse_dict(dict_path)
    print(f"Found {len(id_to_text)} dictionary entries.")
    
    print(f"Generating new dictionary at {output_path}...")
    generate_new_dict(id_to_text, text_to_key, output_path)
    
    # Debug missing entries
    print("Analyzing missing entries...")
    missing_ids = [eid for eid, text in id_to_text.items() if text not in text_to_key]
    
    with open("missing_debug.txt", "w", encoding="utf-8") as f:
        f.write(f"Total missing: {len(missing_ids)}\n")
        f.write("="*50 + "\n")
        
        for eid in missing_ids:
            text = id_to_text[eid]
            f.write(f"ID: {eid}\nText: '{text}'\n")
            
            # Try to find close matches
            potential_matches = []
            for scanned_text in text_to_key.keys():
                # Check for substring match
                if text in scanned_text or scanned_text in text:
                    potential_matches.append(f"Substring: '{scanned_text}'")
                # Check for normalized match (ignore whitespace/case)
                elif text.strip().lower() == scanned_text.strip().lower():
                    potential_matches.append(f"Normalized: '{scanned_text}'")
                # Check for very close Levenshtein-like (simple version: differing by few chars)
                # (Skipping complex fuzzy match for speed, sticking to containment/normalization)
            
            if potential_matches:
                f.write("Potential matches found in scan:\n")
                for pm in potential_matches[:5]: # Limit to 5 matches
                    f.write(f"  - {pm}\n")
            else:
                f.write("  No obvious matches found.\n")
            f.write("-" * 20 + "\n")
            
    print(f"Debug info written to missing_debug.txt")
    print("Done.")

if __name__ == "__main__":
    main()
