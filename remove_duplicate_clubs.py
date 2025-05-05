import pandas as pd
import random

# List of available clubs for morning and afternoon
morning_clubs = [
    'บาสเก็ตบอล', 'วอลเลย์บอล', 'ฟุตบอล', 'วิ่ง', 'แชร์บอล', 'DEVIL', 
    'ดนตรีไทย', 'เทนนิส', 'MUAN', 'CHORUS', 'Swimming (ชมรมว่ายน้ำและโปโลน้ำ)', 'ART', 'เปตอง'
]

afternoon_clubs = [
    'ปิงปอง', 'แบตมินตัน', 'Libir', 'Research', 'IMSU', 'ดนตรีสากล', 
    'Bridge', 'E-sport', 'หมอน้อย', 'พอช.', 'cheerleader', 'MCCC', 'CMSO', 'coverdance'
]



# Function to standardize club names
def standardize_club_name(name):
    if pd.isna(name):
        return name
    
    # Remove leading/trailing whitespace
    cleaned = str(name).strip()
    
    # Normalize Swimming club name
    if cleaned.startswith('Swimming'):
        return 'Swimming (ชมรมว่ายน้ำและโปโลน้ำ)'
    
    # Handle club names with parentheses (extract the main name)
    if '(' in cleaned:
        # Extract club name based on known formats
        for club in morning_clubs + afternoon_clubs:
            if club in cleaned:
                return club
    
    return cleaned

# Function to remove duplicate clubs and replace with alternative choices
def remove_duplicates(preferences, available_clubs):
    # Convert preferences to clean standard names
    clean_prefs = [standardize_club_name(pref) for pref in preferences if pd.notna(pref)]
    
    # Find duplicates
    seen = set()
    duplicates = set()
    duplicate_indices = []
    
    for i, club in enumerate(clean_prefs):
        if club in seen:
            duplicates.add(club)
            duplicate_indices.append(i)
        else:
            seen.add(club)
    
    # If no duplicates, return original preferences
    if not duplicates:
        return preferences
    
    # Replace duplicates with alternative clubs
    result = list(preferences)  # Make a copy to modify
    used_clubs = set(clean_prefs)  # Track all clubs already used
    
    # For each duplicate, find a replacement
    for idx in duplicate_indices:
        original_pref_idx = next((i for i, p in enumerate(preferences) if pd.notna(p) and 
                               standardize_club_name(p) == clean_prefs[idx]), None)
        
        # Find a replacement club that's not already used
        unused_clubs = [club for club in available_clubs if club not in used_clubs]
        
        if unused_clubs:
            replacement = random.choice(unused_clubs)
            result[original_pref_idx] = replacement
            used_clubs.add(replacement)
        else:
            # If no clubs are available, set to NaN
            result[original_pref_idx] = None
    
    return result

# Main function to remove duplicate clubs from the input file
def remove_duplicate_clubs(input_file, output_file):
    # Read the input data
    df = pd.read_csv(input_file)
    
    # Define column names for morning and afternoon preferences
    morning_cols = [f'ฐานเช้า อันดับที่ {i}' for i in range(1, 9)]
    afternoon_cols = [f'ฐานบ่าย อันดับที่ {i}' for i in range(1, 9)]
    
    # Process each student
    for index, row in df.iterrows():
        student_id = row['รหัสนักศึกษา']
        
        # Get current preferences
        morning_prefs = [row[col] for col in morning_cols]
        afternoon_prefs = [row[col] for col in afternoon_cols]
        
        # Remove duplicates
        new_morning_prefs = remove_duplicates(morning_prefs, morning_clubs)
        new_afternoon_prefs = remove_duplicates(afternoon_prefs, afternoon_clubs)
        
        # Verify no duplicates remain
        morning_std = [standardize_club_name(p) for p in new_morning_prefs if pd.notna(p)]
        afternoon_std = [standardize_club_name(p) for p in new_afternoon_prefs if pd.notna(p)]
        
        if len(morning_std) != len(set(morning_std)) or len(afternoon_std) != len(set(afternoon_std)):
            print(f"Warning: Student {student_id} still has duplicates after processing.")
        
        # Update the dataframe
        for i, col in enumerate(morning_cols):
            df.at[index, col] = new_morning_prefs[i]
        
        for i, col in enumerate(afternoon_cols):
            df.at[index, col] = new_afternoon_prefs[i]
    
    # Final verification pass for the entire dataset
    duplicates_remaining = 0
    for index, row in df.iterrows():
        student_id = row['รหัสนักศึกษา']
        
        # Check morning clubs
        morning_clubs_std = [standardize_club_name(row[col]) for col in morning_cols if pd.notna(row[col])]
        morning_dupes = len(morning_clubs_std) != len(set(morning_clubs_std))
        
        # Check afternoon clubs
        afternoon_clubs_std = [standardize_club_name(row[col]) for col in afternoon_cols if pd.notna(row[col])]
        afternoon_dupes = len(afternoon_clubs_std) != len(set(afternoon_clubs_std))
        
        if morning_dupes or afternoon_dupes:
            duplicates_remaining += 1
            
            # Make one final attempt to fix
            if morning_dupes:
                new_morning = remove_duplicates([row[col] for col in morning_cols], morning_clubs)
                for i, col in enumerate(morning_cols):
                    df.at[index, col] = new_morning[i]
            
            if afternoon_dupes:
                new_afternoon = remove_duplicates([row[col] for col in afternoon_cols], afternoon_clubs)
                for i, col in enumerate(afternoon_cols):
                    df.at[index, col] = new_afternoon[i]
    
    print(f"Fixed {duplicates_remaining} students with remaining duplicates in final pass")
    
    # Save the cleaned data
    df.to_csv(output_file, index=False)
    print(f"Cleaned data saved to {output_file}")

if __name__ == "__main__":
    input_file = "clubhopping_program_test_data.csv"
    output_file = "clubhopping_program_test_data_clean.csv"
    remove_duplicate_clubs(input_file, output_file)
