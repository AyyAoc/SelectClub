import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import random
import os

# Path to the input CSV file
file_path = "clubhopping_program_test_data.csv"

# Read data from CSV file
def read_data(file_path):
    df = pd.read_csv(file_path)
    return df

# Assign students to groups based on the last digit of their student ID
def assign_groups(df):
    df['group'] = df['รหัสนักศึกษา'].astype(str).str[-1]  # Students with the same last digit are in the same group
    df = df.sort_values(by='รหัสนักศึกษา')
    return df

# Get all unique clubs from the dataset
def get_all_clubs(df):
    morning_cols = [f'ฐานเช้า อันดับที่ {i}' for i in range(1, 9)]
    afternoon_cols = [f'ฐานบ่าย อันดับที่ {i}' for i in range(1, 9)]
    
    # Clean up function to standardize club names
    def clean_club_name(name):
        if pd.isna(name):
            return name
        # Remove leading/trailing whitespace
        cleaned = name.strip()
        # Normalize Swimming club name (both versions should be the same)
        if cleaned.startswith('Swimming'):
            return 'Swimming (ชมรมว่ายน้ำและโปโลน้ำ)'
        return cleaned
    
    # Apply cleanup to all club name columns
    for col in morning_cols + afternoon_cols:
        df[col] = df[col].apply(clean_club_name)
    
    # Get unique cleaned club names
    morning_clubs = set()
    afternoon_clubs = set()
    
    for col in morning_cols:
        morning_clubs.update(df[col].dropna().unique())
    
    for col in afternoon_cols:
        afternoon_clubs.update(df[col].dropna().unique())
    
    # Log clean club names for verification
    print("\nCleaned Morning Clubs:")
    for club in sorted(morning_clubs):
        print(f"  - {club}")
    
    print("\nCleaned Afternoon Clubs:")
    for club in sorted(afternoon_clubs):
        print(f"  - {club}")
    
    return {
        'morning': list(morning_clubs),
        'afternoon': list(afternoon_clubs)
    }

# Initialize time slots structure
def initialize_time_slots(clubs):
    time_slots = {}
    for period in ['morning', 'afternoon']:
        time_slots[period] = {}
        for slot in range(1, 5):
            time_slots[period][slot] = {}
            for club in clubs[period]:
                time_slots[period][slot][club] = []
    return time_slots

# Count students preferences for each club to determine popularity
def count_preferences(df):
    preference_counts = {
        'morning': defaultdict(int),
        'afternoon': defaultdict(int)
    }
    
    for _, row in df.iterrows():
        for i in range(1, 5):  # Count preferences for main choices (1-4)
            morning_club = row[f'ฐานเช้า อันดับที่ {i}']
            afternoon_club = row[f'ฐานบ่าย อันดับที่ {i}']
            
            if pd.notna(morning_club):
                preference_counts['morning'][morning_club] += 1
            
            if pd.notna(afternoon_club):
                preference_counts['afternoon'][afternoon_club] += 1
    
    return preference_counts

# Create student preferences structure for easier access
def create_student_preferences(df):
    students = {}
    
    for _, row in df.iterrows():
        student_id = row['รหัสนักศึกษา']
        group = row['group']
        
        morning_prefs = []
        afternoon_prefs = []
        
        # Get main preferences (1-4)
        for i in range(1, 5):
            morning_club = row[f'ฐานเช้า อันดับที่ {i}']
            afternoon_club = row[f'ฐานบ่าย อันดับที่ {i}']
            
            if pd.notna(morning_club):
                morning_prefs.append(morning_club)
            
            if pd.notna(afternoon_club):
                afternoon_prefs.append(afternoon_club)
        
        # Get backup preferences (5-8)
        morning_backups = []
        afternoon_backups = []
        
        for i in range(5, 9):
            morning_club = row[f'ฐานเช้า อันดับที่ {i}']
            afternoon_club = row[f'ฐานบ่าย อันดับที่ {i}']
            
            if pd.notna(morning_club):
                morning_backups.append(morning_club)
            
            if pd.notna(afternoon_club):
                afternoon_backups.append(afternoon_club)
        
        students[student_id] = {
            'group': group,
            'name': row['ชื่อ นามสกุล'],
            'preferences': {
                'morning': {
                    'main': morning_prefs,
                    'backup': morning_backups
                },
                'afternoon': {
                    'main': afternoon_prefs,
                    'backup': afternoon_backups
                }
            },
            'assignments': {
                'morning': {},
                'afternoon': {}
            }
        }
    
    return students

# Calculate fairness score for a student
def calculate_fairness_score(student, club, period, club_counts, represented_groups=None):
    # This score determines priority when a club is oversubscribed
    score = 0
    
    # If we're tracking group representation, heavily prioritize students from unrepresented groups
    if represented_groups is not None:
        if student['group'] not in represented_groups:
            score += 1000  # Extremely high priority for unrepresented groups
    
    # How many clubs has the student already been assigned to?
    assigned_count = len(student['assignments'][period])
    score -= assigned_count * 10  # Prioritize students with fewer assignments
    
    # Is this club in their top 4 preferences?
    if club in student['preferences'][period]['main']:
        pref_rank = student['preferences'][period]['main'].index(club) + 1
        score += (5 - pref_rank) * 5  # Higher rank = higher score
    elif club in student['preferences'][period]['backup']:
        pref_rank = student['preferences'][period]['backup'].index(club) + 1
        score += pref_rank  # Backup preferences worth less
    else:
        score -= 10  # Penalize if club not in preferences
    
    # Factor in club popularity (give advantage to less popular clubs)
    popularity = club_counts[period][club] / sum(club_counts[period].values())
    score -= popularity * 10
    
    return score

# Run a round of assignments for a specific time slot
def assign_time_slot(students, time_slots, period, slot, club_counts, clubs):
    # Track which club each student prefers for this slot
    slot_preferences = defaultdict(list)
    
    # Track which groups are represented in each club
    club_groups = {club: set() for club in clubs[period]}
    for student_id in students:
        group = students[student_id]['group']
        assigned_club = students[student_id]['assignments'][period].get(slot)
        if assigned_club:
            club_groups[assigned_club].add(group)
    
    # Collect all students' preferences for this slot
    for student_id, student in students.items():
        # Skip if student already has an assignment for this slot
        if slot in student['assignments'][period]:
            continue
        
        # Try to assign main preferences first
        main_prefs = student['preferences'][period]['main']
        if len(main_prefs) >= slot:  # Check if they have a preference for this slot
            preferred_club = main_prefs[slot-1]
            slot_preferences[preferred_club].append(student_id)
        
    # First pass: Ensure group representation
    # For each club, make sure there's at least one student from each group
    for club in clubs[period]:
        # Which groups are currently missing from this club?
        missing_groups = set('0123456789') - club_groups[club]
        if missing_groups and len(slot_preferences[club]) > 0:
            candidates_by_group = defaultdict(list)
            
            # Group candidates by their group
            for student_id in slot_preferences[club]:
                group = students[student_id]['group']
                if group in missing_groups:
                    candidates_by_group[group].append(student_id)
            
            # For each missing group, try to add a student
            for group in missing_groups:
                if candidates_by_group[group]:  # If we have candidates from this group
                    # Choose the best candidate (one with highest fairness score)
                    group_candidates = []
                    for student_id in candidates_by_group[group]:
                        score = calculate_fairness_score(students[student_id], club, period, club_counts)
                        group_candidates.append((student_id, score))
                    
                    group_candidates.sort(key=lambda x: x[1], reverse=True)
                    best_candidate = group_candidates[0][0]
                    
                    # Add this student to the club
                    time_slots[period][slot][club].append(best_candidate)
                    students[best_candidate]['assignments'][period][slot] = club
                    club_groups[club].add(group)  # Update group representation
                    
                    # Remove from slot_preferences to avoid adding twice
                    slot_preferences[club].remove(best_candidate)
    
    # Second pass: Handle regular assignments and oversubscribed clubs
    for club in clubs[period]:
        # Leave room for missing groups
        remaining_capacity = 20 - len(time_slots[period][slot][club])
        
        if len(slot_preferences[club]) > remaining_capacity and remaining_capacity > 0:
            print(f"Club {club} is oversubscribed in {period} slot {slot} with {len(slot_preferences[club])} students")
            
            # Calculate fairness scores for all students interested in this club
            candidates = []
            for student_id in slot_preferences[club]:
                # Consider existing group representation for fairness scoring
                group = students[student_id]['group']
                represented_groups = club_groups[club]
                
                fairness_score = calculate_fairness_score(
                    students[student_id], club, period, club_counts, represented_groups)
                candidates.append((student_id, fairness_score))
            
            # Sort by fairness score (highest to lowest)
            candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Add students up to the remaining capacity
            selected_students = [c[0] for c in candidates[:remaining_capacity]]
            
            # Assign them to this club
            for student_id in selected_students:
                time_slots[period][slot][club].append(student_id)
                students[student_id]['assignments'][period][slot] = club
                club_groups[club].add(students[student_id]['group'])  # Update group representation
            
            # Try to find alternate clubs for rejected students
            rejected_students = [c[0] for c in candidates[remaining_capacity:]]
            
            for student_id in rejected_students:
                # First try backup preferences
                backup_prefs = students[student_id]['preferences'][period]['backup']
                assigned = False
                
                for backup_club in backup_prefs:
                    if len(time_slots[period][slot][backup_club]) < 20:
                        time_slots[period][slot][backup_club].append(student_id)
                        students[student_id]['assignments'][period][slot] = backup_club
                        club_groups[backup_club].add(students[student_id]['group'])
                        assigned = True
                        break
                
                # If no backup club available, try any available club
                if not assigned:
                    available_clubs = [club for club in clubs[period] 
                                     if len(time_slots[period][slot][club]) < 20]
                    if available_clubs:
                        # Choose club with fewest students
                        available_clubs.sort(key=lambda c: len(time_slots[period][slot][c]))
                        chosen_club = available_clubs[0]
                        
                        time_slots[period][slot][chosen_club].append(student_id)
                        students[student_id]['assignments'][period][slot] = chosen_club
                        club_groups[chosen_club].add(students[student_id]['group'])
                        assigned = True
                    # If no club has space, assign to club with most space anyway (exceeding 20 if necessary)
                    else:
                        all_clubs = list(clubs[period])
                        all_clubs.sort(key=lambda c: len(time_slots[period][slot][c]))
                        chosen_club = all_clubs[0]  # Club with fewest students
                        
                        print(f"WARNING: Exceeding 20-student limit for {chosen_club} in {period} slot {slot} to assign student {student_id}")
                        time_slots[period][slot][chosen_club].append(student_id)
                        students[student_id]['assignments'][period][slot] = chosen_club
                        club_groups[chosen_club].add(students[student_id]['group'])
                        
        elif len(slot_preferences[club]) <= remaining_capacity:
            # If not oversubscribed, assign all students to their preferred club
            for student_id in slot_preferences[club]:
                time_slots[period][slot][club].append(student_id)
                students[student_id]['assignments'][period][slot] = club
                club_groups[club].add(students[student_id]['group'])
    
    # Assign remaining students who weren't assigned yet for various reasons
    for student_id, student in students.items():
        if slot not in student['assignments'][period]:
            # Try to find any available club with space
            available_clubs = [club for club in clubs[period] 
                              if len(time_slots[period][slot][club]) < 20]
            
            if available_clubs:
                # Prefer clubs with missing group representation
                group = student['group']
                
                # First check if there are clubs missing this group
                priority_clubs = [club for club in available_clubs if group not in club_groups[club]]
                
                if priority_clubs:
                    # Choose the club with fewest students
                    priority_clubs.sort(key=lambda c: len(time_slots[period][slot][c]))
                    chosen_club = priority_clubs[0]
                else:
                    # Choose the club with fewest students
                    available_clubs.sort(key=lambda c: len(time_slots[period][slot][c]))
                    chosen_club = available_clubs[0]
                
                time_slots[period][slot][chosen_club].append(student_id)
                students[student_id]['assignments'][period][slot] = chosen_club
                club_groups[chosen_club].add(group)
            # If no club has space, assign to club with most space anyway (exceeding 20 if necessary)
            else:
                group = student['group']
                all_clubs = list(clubs[period])
                all_clubs.sort(key=lambda c: len(time_slots[period][slot][c]))
                chosen_club = all_clubs[0]  # Club with fewest students
                
                print(f"WARNING: Exceeding 20-student limit for {chosen_club} in {period} slot {slot} to assign student {student_id}")
                time_slots[period][slot][chosen_club].append(student_id)
                students[student_id]['assignments'][period][slot] = chosen_club
                club_groups[chosen_club].add(group)
    
    return students, time_slots

# Ensure each group has at least one student in each club, prioritize representation over club size limits
def ensure_group_representation(students, time_slots, clubs):
    # Step 1: Ensure at least one representative from each group (0-9) in each club
    # This is the highest priority - even if it means clubs exceeding 20 students
    
    # Track which groups are represented in which clubs
    representation = {
        'morning': {club: set() for club in clubs['morning']},
        'afternoon': {club: set() for club in clubs['afternoon']}
    }
    
    # Check current representation
    for period in ['morning', 'afternoon']:
        for slot in range(1, 5):
            for club in clubs[period]:
                for student_id in time_slots[period][slot][club]:
                    group = students[student_id]['group']
                    representation[period][club].add(group)
    
    # For each club missing representation from any group, try to add a student
    for period in ['morning', 'afternoon']:
        for club in clubs[period]:
            # Check which groups are missing
            missing_groups = set('0123456789') - representation[period][club]
            if not missing_groups:
                continue  # All groups are represented
            
            print(f"Club {club} ({period}) is missing students from groups: {missing_groups}")
            
            for group in missing_groups:
                # Find students from this group
                group_students = [s_id for s_id, s in students.items() if s['group'] == group]
                
                # Prioritize students who have this club in their preferences (main or backup)
                prioritized_students = []
                other_students = []
                
                for s_id in group_students:
                    student = students[s_id]
                    main_prefs = student['preferences'][period]['main']
                    backup_prefs = student['preferences'][period]['backup']
                    
                    if club in main_prefs:
                        # Higher priority for main preferences
                        priority = 2  # Highest priority
                        rank = main_prefs.index(club) + 1
                        prioritized_students.append((s_id, priority, rank))
                    elif club in backup_prefs:
                        # Medium priority for backup preferences
                        priority = 1  # Medium priority
                        rank = backup_prefs.index(club) + 1
                        prioritized_students.append((s_id, priority, rank))
                    else:
                        # Lowest priority for students who didn't choose this club
                        other_students.append(s_id)
                
                # Sort prioritized students by priority (higher first) and then by rank (lower first)
                prioritized_students.sort(key=lambda x: (-x[1], x[2]))  # Sort by priority desc, then rank asc
                prioritized_student_ids = [s[0] for s in prioritized_students]
                
                # Only use random order for students who didn't select this club
                random.shuffle(other_students)
                
                # Final ordered list: prioritized students first, then random others
                group_students = prioritized_student_ids + other_students
                
                # Try to find a slot where we can add the student
                assigned = False
                
                # First try: Find an empty slot for the student
                for student_id in group_students:
                    for slot in range(1, 5):
                        # Skip if student already has this club in any slot
                        if any(students[student_id]['assignments'][period].get(s) == club 
                              for s in range(1, 5)):
                            continue
                            
                        # If student doesn't have an assignment for this slot, add them
                        if slot not in students[student_id]['assignments'][period]:
                            time_slots[period][slot][club].append(student_id)
                            students[student_id]['assignments'][period][slot] = club
                            representation[period][club].add(group)
                            print(f"  Added student {student_id} (group {group}) to {club} ({period} slot {slot}) - free slot")
                            assigned = True
                            break
                    
                    if assigned:
                        break
                
                # If still not assigned, try swapping from another club
                if not assigned:
                    for student_id in group_students:
                        for slot in range(1, 5):
                            # Skip if student already has this club
                            if any(students[student_id]['assignments'][period].get(s) == club 
                                  for s in range(1, 5)):
                                continue
                                
                            # If student has another assignment for this slot
                            if slot in students[student_id]['assignments'][period]:
                                current_club = students[student_id]['assignments'][period][slot]
                                
                                # Only swap if current club has multiple students from this group
                                # or representation from this group in other slots
                                same_group_in_slot = [s for s in time_slots[period][slot][current_club] 
                                                      if students[s]['group'] == group]
                                
                                if len(same_group_in_slot) > 1:
                                    # Remove from current club
                                    time_slots[period][slot][current_club].remove(student_id)
                                    
                                    # Add to new club
                                    time_slots[period][slot][club].append(student_id)
                                    students[student_id]['assignments'][period][slot] = club
                                    representation[period][club].add(group)
                                    print(f"  Added student {student_id} (group {group}) to {club} ({period} slot {slot}) - swapped from {current_club}")
                                    assigned = True
                                    break
                        
                        if assigned:
                            break
                
                # Last resort: If still not assigned, force an assignment
                if not assigned:
                    # Find the slot with fewest students for this club
                    slot_counts = [(slot, len(time_slots[period][slot][club])) for slot in range(1, 5)]
                    slot_counts.sort(key=lambda x: x[1])  # Sort by count
                    
                    target_slot = slot_counts[0][0]  # Slot with fewest students
                    
                    for student_id in group_students:
                        # If student already has an assignment for this slot
                        if target_slot in students[student_id]['assignments'][period]:
                            current_club = students[student_id]['assignments'][period][target_slot]
                            
                            # Remove from current club
                            time_slots[period][target_slot][current_club].remove(student_id)
                            
                            # Add to new club (even if it exceeds 20)
                            time_slots[period][target_slot][club].append(student_id)
                            students[student_id]['assignments'][period][target_slot] = club
                            representation[period][club].add(group)
                            print(f"  FORCED: Added student {student_id} (group {group}) to {club} ({period} slot {target_slot}) - removed from {current_club}")
                            assigned = True
                            break
                        elif not any(students[student_id]['assignments'][period].get(s) == club 
                                    for s in range(1, 5)):
                            # If student doesn't have this club and doesn't have an assignment for this slot
                            time_slots[period][target_slot][club].append(student_id)
                            students[student_id]['assignments'][period][target_slot] = club
                            representation[period][club].add(group)
                            print(f"  FORCED: Added student {student_id} (group {group}) to {club} ({period} slot {target_slot}) - unassigned slot")
                            assigned = True
                            break
                            
                    if not assigned:
                        print(f"  WARNING: Could not assign any student from group {group} to {club} ({period})")
    
    return students, time_slots

# Main function to run the allocation algorithm
def allocate_clubs():
    print("Starting club allocation process...")
    
    # Read and prepare data
    print("Reading data from CSV...")
    df = read_data(file_path)
    df = assign_groups(df)
    
    # Get all clubs and initialize structures
    clubs = get_all_clubs(df)
    print(f"Found {len(clubs['morning'])} morning clubs and {len(clubs['afternoon'])} afternoon clubs")
    
    time_slots = initialize_time_slots(clubs)
    club_counts = count_preferences(df)
    students = create_student_preferences(df)
    
    print("Allocating students to clubs...")
    
    # First pass: Assign students to clubs for each time slot
    for period in ['morning', 'afternoon']:
        for slot in range(1, 5):
            print(f"Processing {period} slot {slot}...")
            students, time_slots = assign_time_slot(students, time_slots, period, slot, club_counts, clubs)
    
    # Second pass: Ensure all groups are represented in all clubs
    print("Ensuring group representation in all clubs...")
    students, time_slots = ensure_group_representation(students, time_slots, clubs)
    
    # Final pass: Verify that all students have assignments for every time slot
    print("Verifying all students have complete assignments...")
    for period in ['morning', 'afternoon']:
        for slot in range(1, 5):
            for student_id, student in students.items():
                if slot not in student['assignments'][period]:
                    print(f"WARNING: Student {student_id} missing assignment for {period} slot {slot}. Assigning to club with fewest students.")
                    # Find club with fewest students
                    all_clubs = list(clubs[period])
                    all_clubs.sort(key=lambda c: len(time_slots[period][slot][c]))
                    chosen_club = all_clubs[0]  # Club with fewest students
                    
                    # Assign student to this club
                    time_slots[period][slot][chosen_club].append(student_id)
                    student['assignments'][period][slot] = chosen_club
    
    # Create results DataFrame
    print("Creating results...")
    results = []
    
    # Track club swaps
    swaps = []
    
    # Group students by their group number (0-9)
    students_by_group = {g: [] for g in '0123456789'}
    for student_id, student in students.items():
        students_by_group[student['group']].append(student_id)
    
    # Process each group
    for group in '0123456789':
        group_students = sorted(students_by_group[group])
        
        for student_id in group_students:
            student = students[student_id]
            result = {
                'รหัสนักศึกษา': student_id,
                'ชื่อ นามสกุล': student['name'],
                'กลุ่ม': student['group']
            }
            
            # Track club changes
            student_swaps = []
            
            # Add morning assignments and check for swaps
            for slot in range(1, 5):
                assigned_club = student['assignments']['morning'].get(slot, None)
                result[f'ชมรมเช้า ช่วงที่ {slot}'] = assigned_club
                
                # Check if this was their preference
                preferences = student['preferences']['morning']['main']
                if slot <= len(preferences) and assigned_club != preferences[slot-1]:
                    original = preferences[slot-1] if slot <= len(preferences) else "ไม่ได้เลือก"
                    swap_info = f"เช้า ช่วงที่ {slot}: {original} → {assigned_club}"
                    student_swaps.append(swap_info)
            
            # Add afternoon assignments and check for swaps
            for slot in range(1, 5):
                assigned_club = student['assignments']['afternoon'].get(slot, None)
                result[f'ชมรมบ่าย ช่วงที่ {slot}'] = assigned_club
                
                # Check if this was their preference
                preferences = student['preferences']['afternoon']['main']
                if slot <= len(preferences) and assigned_club != preferences[slot-1]:
                    original = preferences[slot-1] if slot <= len(preferences) else "ไม่ได้เลือก"
                    swap_info = f"บ่าย ช่วงที่ {slot}: {original} → {assigned_club}"
                    student_swaps.append(swap_info)
            
            # Add swap information
            if student_swaps:
                result['การเปลี่ยนชมรม'] = ', '.join(student_swaps)
                swaps.append({
                    'รหัสนักศึกษา': student_id,
                    'ชื่อ นามสกุล': student['name'],
                    'กลุ่ม': student['group'],
                    'การเปลี่ยนชมรม': ', '.join(student_swaps)
                })
            else:
                result['การเปลี่ยนชมรม'] = 'ไม่มีการเปลี่ยนแปลง'
            
            # Add original preferences for reference
            for period in ['morning', 'afternoon']:
                prefix = 'ฐานเช้า' if period == 'morning' else 'ฐานบ่าย'
                
                for i in range(1, 5):
                    if i <= len(student['preferences'][period]['main']):
                        result[f'{prefix} อันดับที่ {i}'] = student['preferences'][period]['main'][i-1]
                    else:
                        result[f'{prefix} อันดับที่ {i}'] = None
                
                for i in range(5, 9):
                    backup_idx = i - 5
                    if backup_idx < len(student['preferences'][period]['backup']):
                        result[f'{prefix} อันดับที่ {i}'] = student['preferences'][period]['backup'][backup_idx]
                    else:
                        result[f'{prefix} อันดับที่ {i}'] = None
            
            # Add this student to results
            results.append(result)
            
        # Add empty row between groups (except after the last group)
        if group != '9':
            empty_row = {col: '' for col in results[0].keys()}
            empty_row['รหัสนักศึกษา'] = f'--- จบกลุ่ม {group} ---'
            results.append(empty_row)
    
    # Create main results DataFrame
    results_df = pd.DataFrame(results)
    
    # Create swaps DataFrame if there are any swaps
    if swaps:
        swaps_df = pd.DataFrame(swaps)
        swaps_output_path = "club_assignment_swaps.csv"
        swaps_df.to_csv(swaps_output_path, index=False, encoding='utf-8-sig')
        print(f"Swap information saved to {swaps_output_path}")
    
    # Calculate statistics
    stats = calculate_statistics(students, clubs)
    
    # Add detailed statistics by time slot
    detailed_stats = calculate_detailed_statistics(students, time_slots, clubs)
    
    # Print statistics
    print_statistics(stats, detailed_stats, students, clubs)
    
    # Save to CSV
    output_path = "club_assignment_results_improved.csv"
    results_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Results saved to {output_path}")
    
    return results_df, stats

# Calculate statistics about the assignments
def calculate_statistics(students, clubs):
    stats = {
        'morning': {
            'main_assignments': 0,
            'backup_assignments': 0,
            'other_assignments': 0,
            'club_distribution': {club: 0 for club in clubs['morning']}
        },
        'afternoon': {
            'main_assignments': 0,
            'backup_assignments': 0,
            'other_assignments': 0,
            'club_distribution': {club: 0 for club in clubs['afternoon']}
        },
        'group_representation': {
            'morning': {club: set() for club in clubs['morning']},
            'afternoon': {club: set() for club in clubs['afternoon']}
        }
    }
    
    # Count types of assignments and club distribution
    for student_id, student in students.items():
        group = student['group']
        
        for period in ['morning', 'afternoon']:
            for slot, club in student['assignments'][period].items():
                # Count by type
                if club in student['preferences'][period]['main']:
                    stats[period]['main_assignments'] += 1
                elif club in student['preferences'][period]['backup']:
                    stats[period]['backup_assignments'] += 1
                else:
                    stats[period]['other_assignments'] += 1
                
                # Count by club
                stats[period]['club_distribution'][club] += 1
                
                # Add group representation
                stats['group_representation'][period][club].add(group)
    
    return stats

# Calculate detailed statistics by time slot and group
def calculate_detailed_statistics(students, time_slots, clubs):
    detailed_stats = {
        'slots': {
            'morning': {slot: {club: [] for club in clubs['morning']} for slot in range(1, 5)},
            'afternoon': {slot: {club: [] for club in clubs['afternoon']} for slot in range(1, 5)}
        },
        'group_slots': {
            'morning': {slot: {club: {g: 0 for g in '0123456789'} for club in clubs['morning']} for slot in range(1, 5)},
            'afternoon': {slot: {club: {g: 0 for g in '0123456789'} for club in clubs['afternoon']} for slot in range(1, 5)}
        }
    }
    
    # Count number of students in each club for each time slot
    for period in ['morning', 'afternoon']:
        for slot in range(1, 5):
            for club in clubs[period]:
                for student_id in time_slots[period][slot][club]:
                    student_group = students[student_id]['group']
                    detailed_stats['slots'][period][slot][club].append(student_id)
                    detailed_stats['group_slots'][period][slot][club][student_group] += 1
    
    return detailed_stats

# Print statistics about the assignments
def print_statistics(stats, detailed_stats, students, clubs):
    total_students = len(students)
    total_slots = total_students * 4  # 4 slots per period
    
    print("\n--- Assignment Statistics ---")
    
    for period in ['morning', 'afternoon']:
        print(f"\n{period.upper()} ASSIGNMENTS:")
        
        main_pct = stats[period]['main_assignments'] / total_slots * 100
        backup_pct = stats[period]['backup_assignments'] / total_slots * 100
        other_pct = stats[period]['other_assignments'] / total_slots * 100
        
        print(f"  Main preferences (1-4): {stats[period]['main_assignments']} ({main_pct:.1f}%)")
        print(f"  Backup preferences (5-8): {stats[period]['backup_assignments']} ({backup_pct:.1f}%)")
        print(f"  Other assignments: {stats[period]['other_assignments']} ({other_pct:.1f}%)")
        
        print("\n  Most popular clubs:")
        sorted_clubs = sorted(stats[period]['club_distribution'].items(), 
                            key=lambda x: x[1], reverse=True)
        for club, count in sorted_clubs[:5]:
            print(f"    - {club}: {count} students")
        
        print("\n  Least popular clubs:")
        for club, count in sorted_clubs[-5:]:
            print(f"    - {club}: {count} students")
    
    print("\n--- Detailed Time Slot Assignment ---")
    oversubscribed = False
    
    # Print detailed student counts for each club in each time slot
    for period in ['morning', 'afternoon']:
        print(f"\n{period.upper()} TIME SLOTS:")
        
        for slot in range(1, 5):
            print(f"\n  Slot {slot}:")
            print(f"  {'Club':<40} {'Total':>5} | {'0 1 2 3 4 5 6 7 8 9':>20}")
            print(f"  {'-'*40} {'-'*5} | {'-'*20}")
            
            for club in sorted(clubs[period]):
                student_count = len(detailed_stats['slots'][period][slot][club])
                group_counts = [str(detailed_stats['group_slots'][period][slot][club][g]) for g in '0123456789']
                group_distribution = ' '.join(group_counts)
                
                # Highlight if a club has more than 20 students
                status = "" if student_count <= 20 else "[OVER]" 
                if student_count > 20:
                    oversubscribed = True
                
                print(f"  {club:<40} {student_count:>5} | {group_distribution:>20} {status}")
    
    if oversubscribed:
        print("\n[OVER] indicates clubs that exceed the 20 student limit")
    
    print("\n--- Group Representation ---")
    missing_representation = False
    
    # Check if each group has at least one member in each club for each time slot
    for period in ['morning', 'afternoon']:
        for slot in range(1, 5):
            for club in sorted(clubs[period]):
                missing_groups = []
                for group in '0123456789':
                    if detailed_stats['group_slots'][period][slot][club][group] == 0:
                        missing_groups.append(group)
                
                if missing_groups:
                    missing_representation = True
                    missing_str = ', '.join(missing_groups)
                    print(f"  {club} ({period} slot {slot}) is missing students from groups: {missing_str}")
    
    if not missing_representation:
        print("  All clubs have representation from all groups in all time slots!")
    else:
        print("  Warning: Some clubs are missing representation from certain groups!")

# Run the program if executed directly
if __name__ == "__main__":
    results_df, stats = allocate_clubs()
