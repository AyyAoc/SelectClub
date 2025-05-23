#ใช้วิธี global optimization คิดทีเดียวทุกคนไปพร้อมกันให้จบๆ
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import random
import os

# ค่าคงที่สำหรับการจัดสรร
MAX_STUDENTS_PER_CLUB = 20  # จำนวนนักศึกษาสูงสุดต่อชมรม
NUM_GROUPS = 10  # จำนวนกลุ่มทั้งหมด (กลุ่ม 0-9)
NUM_SLOTS_PER_PERIOD = 4  # จำนวนช่วงเวลาต่อคาบ (เช้า/บ่าย)

def read_data(file_path):
    """
    อ่านข้อมูลจากไฟล์ CSV
    """
    print(f"Reading data from {file_path}...")
    return pd.read_csv(file_path, encoding='utf-8-sig')

def assign_groups(df):
    """
    จัดนักศึกษาเข้ากลุ่มตามตัวเลขในรหัสนักศึกษา
    """
    # แปลงรหัสนักศึกษาเป็นสตริงและดึงตัวเลขกลุ่ม (ตัวเลขที่ระบุกลุ่ม)
    df['group'] = df['รหัสนักศึกษา'].astype(str).apply(lambda x: x[-1] if len(x) > 0 else '0')
    print(f"Students assigned to groups 0-9 based on the last digit of their ID")
    return df

def get_all_clubs(df):
    """
    รวบรวมชื่อชมรมทั้งหมดจากข้อมูล
    """
    morning_clubs = set()
    afternoon_clubs = set()
    
    # รวบรวมชมรมเช้า
    for i in range(1, 9):
        col_name = f'ฐานเช้า อันดับที่ {i}'
        if col_name in df.columns:
            clubs = df[col_name].dropna().unique()
            morning_clubs.update(clubs)
    
    # รวบรวมชมรมบ่าย
    for i in range(1, 9):
        col_name = f'ฐานบ่าย อันดับที่ {i}'
        if col_name in df.columns:
            clubs = df[col_name].dropna().unique()
            afternoon_clubs.update(clubs)
    
    # แปลงเป็น list และเรียงลำดับตามชื่อ
    morning_clubs = sorted(list(morning_clubs))
    afternoon_clubs = sorted(list(afternoon_clubs))
    
    print(f"Found {len(morning_clubs)} morning clubs and {len(afternoon_clubs)} afternoon clubs")
    
    return {'morning': morning_clubs, 'afternoon': afternoon_clubs}

def create_student_preferences(df):
    """
    สร้างโครงสร้างข้อมูลความชอบของนักศึกษา
    """
    students = {}
    
    for _, row in df.iterrows():
        student_id = str(row['รหัสนักศึกษา'])
        group = str(row['group'])
        
        # สร้างข้อมูลนักศึกษา
        students[student_id] = {
            'group': group,
            'preferences': {
                'morning': {
                    'main': [],    # 4 อันดับแรก
                    'backup': []   # 4 อันดับถัดมา
                },
                'afternoon': {
                    'main': [],    # 4 อันดับแรก
                    'backup': []   # 4 อันดับถัดมา
                }
            },
            'assignments': {
                'morning': {},     # ช่วงเวลา -> ชมรม
                'afternoon': {}    # ช่วงเวลา -> ชมรม
            },
            'changes': {
                'morning': 0,      # จำนวนการเปลี่ยนแปลงในช่วงเช้า
                'afternoon': 0     # จำนวนการเปลี่ยนแปลงในช่วงบ่าย
            }
        }
        
        # เก็บความชอบชมรมเช้า
        for i in range(1, 9):
            col_name = f'ฐานเช้า อันดับที่ {i}'
            if col_name in row and pd.notna(row[col_name]):
                if i <= 4:  # 4 อันดับแรกเป็นหลัก
                    students[student_id]['preferences']['morning']['main'].append(row[col_name])
                else:       # 4 อันดับถัดมาเป็นสำรอง
                    students[student_id]['preferences']['morning']['backup'].append(row[col_name])
        
        # เก็บความชอบชมรมบ่าย
        for i in range(1, 9):
            col_name = f'ฐานบ่าย อันดับที่ {i}'
            if col_name in row and pd.notna(row[col_name]):
                if i <= 4:  # 4 อันดับแรกเป็นหลัก
                    students[student_id]['preferences']['afternoon']['main'].append(row[col_name])
                else:       # 4 อันดับถัดมาเป็นสำรอง
                    students[student_id]['preferences']['afternoon']['backup'].append(row[col_name])
    
    print(f"Created preference data for {len(students)} students")
    return students

def initialize_time_slots(clubs):
    """
    สร้างโครงสร้างข้อมูลสำหรับเก็บการจัดสรรในแต่ละช่วงเวลา
    """
    time_slots = {
        'morning': {slot: {club: [] for club in clubs['morning']} for slot in range(1, NUM_SLOTS_PER_PERIOD + 1)},
        'afternoon': {slot: {club: [] for club in clubs['afternoon']} for slot in range(1, NUM_SLOTS_PER_PERIOD + 1)}
    }
    return time_slots

def count_preferences(df, clubs):
    """
    นับจำนวนความนิยมของแต่ละชมรม
    """
    club_counts = {
        'morning': {club: 0 for club in clubs['morning']},
        'afternoon': {club: 0 for club in clubs['afternoon']}
    }
    
    # นับจำนวนชมรมเช้าในสี่อันดับแรก
    for i in range(1, 5):
        col_name = f'ฐานเช้า อันดับที่ {i}'
        if col_name in df.columns:
            club_series = df[col_name].dropna()
            for club, count in club_series.value_counts().items():
                if club in club_counts['morning']:
                    club_counts['morning'][club] += count
    
    # นับจำนวนชมรมบ่ายในสี่อันดับแรก
    for i in range(1, 5):
        col_name = f'ฐานบ่าย อันดับที่ {i}'
        if col_name in df.columns:
            club_series = df[col_name].dropna()
            for club, count in club_series.value_counts().items():
                if club in club_counts['afternoon']:
                    club_counts['afternoon'][club] += count
    
    return club_counts

def calculate_satisfaction_score(student, club, period, slot):
    """
    คำนวณคะแนนความพึงพอใจของนักศึกษาที่ได้รับชมรมนั้นๆ
    ยิ่งคะแนนสูงยิ่งพึงพอใจมาก
    """
    score = 0
    
    # ตรวจสอบว่าชมรมนี้ได้รับการจัดสรรให้นักศึกษาคนนี้ไปแล้วหรือไม่ในช่วงเวลาอื่น
    # ถ้าเคยได้รับแล้ว ให้คะแนนติดลบมาก (ป้องกันไม่ให้ได้ชมรมซ้ำ)
    for existing_slot, existing_club in student['assignments'][period].items():
        if existing_club == club:
            return -10000  # ให้คะแนนติดลบมากพอที่จะไม่ถูกเลือก
    
    # ตรวจสอบว่าชมรมอยู่ในความต้องการหลักหรือไม่
    if club in student['preferences'][period]['main']:
        # ความต้องการหลักได้คะแนนสูง (อันดับ 1 คะแนนสูงสุด, อันดับ 2-4 ลดหลั่นลงมา)
        pref_rank = student['preferences'][period]['main'].index(club)
        score = 1000 - (pref_rank * 200)  # คะแนน: อันดับ 1 = 1000, อันดับ 2 = 800, อันดับ 3 = 600, อันดับ 4 = 400
    
    # ตรวจสอบว่าชมรมอยู่ในความต้องการสำรองหรือไม่
    elif club in student['preferences'][period]['backup']:
        # ความต้องการสำรองได้คะแนนปานกลาง
        pref_rank = student['preferences'][period]['backup'].index(club)
        score = 300 - (pref_rank * 50)  # คะแนน: อันดับ 5 = 300, อันดับ 6 = 250, อันดับ 7 = 200, อันดับ 8 = 150
    
    # ไม่อยู่ในความต้องการเลย
    else:
        score = 0  # ไม่ได้คะแนน
    
    # ถ้าเป็นช่วงเวลาที่ต้องการ (ช่วงเวลา slot ตรงกับอันดับการเลือก) ให้คะแนนเพิ่ม
    if slot <= len(student['preferences'][period]['main']):
        # ช่วงเวลา slot ที่ 1 ควรได้ชมรมอันดับ 1, ช่วงเวลาที่ 2 ควรได้ชมรมอันดับ 2 เป็นต้น
        target_club_for_slot = student['preferences'][period]['main'][slot-1]
        if club == target_club_for_slot:
            score += 500  # โบนัสพิเศษสำหรับการจัดช่วงเวลาที่ตรงกับความต้องการ
    
    return score

def initial_assignment(students, clubs):
    """
    จัดสรรชมรมเบื้องต้นตามความต้องการหลัก (4 อันดับแรก)
    """
    # สร้างโครงสร้างข้อมูลสำหรับเก็บผลการจัดสรรเบื้องต้น
    time_slots = initialize_time_slots(clubs)
    
    print("Performing initial club assignment based on main preferences...")
    
    # ทำการจัดสรรชมรมเช้าและบ่ายแยกกัน
    for period in ['morning', 'afternoon']:
        for slot in range(1, NUM_SLOTS_PER_PERIOD + 1):
            # จัดสรรชมรมสำหรับช่วงเวลานี้ให้กับทุกนักศึกษา
            for student_id, student in students.items():
                # ตรวจสอบว่ามีความต้องการหลักสำหรับช่วงเวลานี้หรือไม่
                if slot <= len(student['preferences'][period]['main']):
                    preferred_club = student['preferences'][period]['main'][slot-1]
                    
                    # จัดสรรชมรมตามความต้องการเบื้องต้น (ยังไม่คำนึงถึงขีดจำกัดจำนวนและการแทนกลุ่ม)
                    students[student_id]['assignments'][period][slot] = preferred_club
                    time_slots[period][slot][preferred_club].append(student_id)
    
    # แสดงสถิติเบื้องต้นหลังการจัดสรร
    print("Initial assignment complete.")
    count_over_limit = 0
    for period in ['morning', 'afternoon']:
        for slot in range(1, NUM_SLOTS_PER_PERIOD + 1):
            for club in clubs[period]:
                club_members = time_slots[period][slot][club]
                if len(club_members) > MAX_STUDENTS_PER_CLUB:
                    count_over_limit += 1
    print(f"Number of club slots exceeding the limit of {MAX_STUDENTS_PER_CLUB} students: {count_over_limit}")
    
    return time_slots

def check_group_representation(students, time_slots, clubs):
    """
    ตรวจสอบว่าทุกชมรมมีตัวแทนจากทุกกลุ่มหรือไม่
    """
    print("Checking group representation in each club...")
    missing_representation = {}
    
    for period in ['morning', 'afternoon']:
        missing_representation[period] = {}
        
        for slot in range(1, NUM_SLOTS_PER_PERIOD + 1):
            missing_representation[period][slot] = {}
            
            for club in clubs[period]:
                # เริ่มต้นโดยสมมติว่าทุกกลุ่มยังไม่มีตัวแทน
                groups_represented = {str(i): False for i in range(NUM_GROUPS)}
                
                # ตรวจสอบว่ามีตัวแทนจากกลุ่มใดบ้างในชมรมนี้
                for student_id in time_slots[period][slot][club]:
                    group = students[student_id]['group']
                    groups_represented[group] = True
                
                # เก็บกลุ่มที่ยังไม่มีตัวแทน
                missing_groups = [group for group, present in groups_represented.items() if not present]
                
                if missing_groups:
                    missing_representation[period][slot][club] = missing_groups
    
    # สรุปผล
    total_missing = 0
    for period in missing_representation:
        for slot in missing_representation[period]:
            for club in missing_representation[period][slot]:
                total_missing += len(missing_representation[period][slot][club])
    
    print(f"Found {total_missing} instances where a group is not represented in a club")
    return missing_representation

def adjust_assignments(students, time_slots, clubs, missing_representation):
    """
    ปรับปรุงการจัดสรรเพื่อให้มีตัวแทนจากทุกกลุ่มในทุกชมรม
    และจำนวนนักศึกษาไม่เกินขีดจำกัด
    """
    print("Adjusting assignments to ensure group representation and club size limits...")
    
    for period in ['morning', 'afternoon']:
        for slot in range(1, NUM_SLOTS_PER_PERIOD + 1):
            # จัดการปัญหาการแทนกลุ่มก่อน
            for club, missing_groups in missing_representation[period][slot].items():
                for missing_group in missing_groups:
                    # หาค่า suitability score สำหรับการย้ายนักศึกษาจากกลุ่มที่หายไปเข้ามาในชมรมนี้
                    candidates = []
                    
                    # ดูทุกคนในกลุ่มที่ขาดตัวแทน
                    for student_id, student in students.items():
                        if student['group'] == missing_group:
                            # ตรวจสอบว่าเขาอยู่ชมรมไหนในช่วงเวลานี้
                            current_club = student['assignments'][period].get(slot)
                            
                            if current_club and current_club != club:  # มีการจัดสรรไว้แล้วและไม่ใช่ชมรมเดียวกัน
                                # คำนวณคะแนนความเหมาะสมในการย้าย
                                # คะแนนสูง = ไม่ค่อยเสียความพึงพอใจเมื่อย้าย
                                old_score = calculate_satisfaction_score(student, current_club, period, slot)
                                new_score = calculate_satisfaction_score(student, club, period, slot)
                                change_score = new_score - old_score
                                
                                # พิจารณาจำนวนการเปลี่ยนแปลงที่เกิดขึ้นกับนักศึกษาคนนี้
                                change_penalty = student['changes'][period] * 100
                                
                                # คะแนนรวมสำหรับการย้าย (ค่ายิ่งสูงยิ่งควรเลือกย้าย)
                                move_score = change_score - change_penalty
                                
                                candidates.append((student_id, move_score, current_club))
                    
                    # เรียงลำดับคนที่เหมาะจะย้ายมากที่สุด (เสียความพึงพอใจน้อยที่สุด)
                    candidates.sort(key=lambda x: x[1], reverse=True)  # เรียงจากคะแนนมากไปน้อย
                    
                    # ย้ายคนที่เหมาะสมที่สุด
                    if candidates:
                        student_id, _, old_club = candidates[0]
                        
                        # ลบออกจากชมรมเดิม
                        time_slots[period][slot][old_club].remove(student_id)
                        
                        # เพิ่มเข้าชมรมใหม่
                        time_slots[period][slot][club].append(student_id)
                        
                        # อัปเดตข้อมูลนักศึกษา
                        students[student_id]['assignments'][period][slot] = club
                        students[student_id]['changes'][period] += 1
                        
                        print(f"Moved student {student_id} from group {missing_group} from {old_club} to {club} in {period} slot {slot}")
            
            # จัดการปัญหาจำนวนเกิน
            for club in clubs[period]:
                club_members = time_slots[period][slot][club]
                
                while len(club_members) > MAX_STUDENTS_PER_CLUB:
                    # หาคนที่เหมาะสมจะย้ายออก (คนที่เสียประโยชน์น้อยที่สุด)
                    move_candidates = []
                    
                    for student_id in club_members:
                        student = students[student_id]
                        
                        # ตรวจสอบว่าถ้าย้ายคนนี้ออกไป กลุ่มยังมีตัวแทนอยู่ไหม
                        group = student['group']
                        group_members = [sid for sid in club_members if students[sid]['group'] == group]
                        
                        # ถ้าเป็นคนสุดท้ายของกลุ่ม ห้ามย้าย
                        if len(group_members) <= 1:
                            continue
                        
                        # ความพึงพอใจปัจจุบัน
                        current_score = calculate_satisfaction_score(student, club, period, slot)
                        
                        # หาชมรมทางเลือกที่จะย้ายไป
                        alternatives = []
                        for alt_club in clubs[period]:
                            if alt_club != club and len(time_slots[period][slot][alt_club]) < MAX_STUDENTS_PER_CLUB:
                                alt_score = calculate_satisfaction_score(student, alt_club, period, slot)
                                score_diff = alt_score - current_score
                                alternatives.append((alt_club, score_diff))
                        
                        # เรียงลำดับทางเลือกจากดีที่สุด (เสียประโยชน์น้อย/ได้ประโยชน์มาก)
                        alternatives.sort(key=lambda x: x[1], reverse=True)
                        
                        # ถ้ามีทางเลือก จะพิจารณาย้าย
                        if alternatives:
                            best_alt_club, score_diff = alternatives[0]
                            
                            # คำนวณคะแนนการย้าย (คะแนนต่ำ = เหมาะสมที่จะย้ายออก)
                            # พิจารณาทั้งความเสียประโยชน์และจำนวนครั้งที่เคยย้าย
                            change_penalty = student['changes'][period] * 100
                            move_score = score_diff - change_penalty
                            
                            move_candidates.append((student_id, move_score, best_alt_club))
                    
                    # เรียงลำดับคนที่ควรย้ายออก (คนที่เสียประโยชน์น้อยที่สุด)
                    if not move_candidates:
                        # ไม่สามารถย้ายใครได้ อาจต้องยอมให้เกินขีดจำกัด
                        print(f"WARNING: Could not reduce club size for {club} in {period} slot {slot}. Current size: {len(club_members)}")
                        break
                    
                    # เรียงจากคนที่เสียประโยชน์น้อยที่สุด (คะแนนสูงสุด) ไปหามากที่สุด
                    move_candidates.sort(key=lambda x: x[1], reverse=True)
                    
                    # ย้ายคนที่เหมาะสมที่สุด
                    student_id, _, new_club = move_candidates[0]
                    
                    # ลบออกจากชมรมเดิม
                    club_members.remove(student_id)
                    
                    # เพิ่มเข้าชมรมใหม่
                    time_slots[period][slot][new_club].append(student_id)
                    
                    # อัปเดตข้อมูลนักศึกษา
                    students[student_id]['assignments'][period][slot] = new_club
                    students[student_id]['changes'][period] += 1
                    
                    print(f"Moved student {student_id} from {club} to {new_club} in {period} slot {slot} due to overcrowding")
    
    # ตรวจสอบอีกครั้งว่ามีตัวแทนทุกกลุ่มหรือไม่
    missing_after = check_group_representation(students, time_slots, clubs)
    
    # สรุปจำนวนที่เกินขีดจำกัด
    over_limit_count = 0
    for period in ['morning', 'afternoon']:
        for slot in range(1, NUM_SLOTS_PER_PERIOD + 1):
            for club in clubs[period]:
                count = len(time_slots[period][slot][club])
                if count > MAX_STUDENTS_PER_CLUB:
                    over_limit_count += 1
                    print(f"Club {club} in {period} slot {slot} still has {count} students (over limit)")
    
    print(f"After adjustments: {over_limit_count} club slots still exceed the student limit")
    
    return time_slots

def optimize_club_allocation(file_path):
    """
    ฟังก์ชันหลักสำหรับการจัดสรรชมรมแบบองค์รวม
    """
    # 1. อ่านข้อมูลจากไฟล์ CSV
    df = read_data(file_path)
    
    # 2. จัดกลุ่มนักศึกษาตามตัวเลขสุดท้ายของรหัสนักศึกษา
    df = assign_groups(df)
    
    # 3. รวบรวมชมรมทั้งหมดจากข้อมูล
    clubs = get_all_clubs(df)
    
    # 4. สร้างโครงสร้างข้อมูลความชอบของนักศึกษา
    students = create_student_preferences(df)
    
    # 5. นับจำนวนความนิยมของชมรมทั้งหมด
    club_counts = count_preferences(df, clubs)
    
    # 6. ทำการจัดสรรชมรมเบื้องต้น
    time_slots = initial_assignment(students, clubs)
    
    # 7. ตรวจสอบการแทนกลุ่ม
    missing_representation = check_group_representation(students, time_slots, clubs)
    
    # 8. ปรับปรุงการจัดสรรเพื่อให้ได้การแทนกลุ่มและจำนวนที่เหมาะสม
    time_slots = adjust_assignments(students, time_slots, clubs, missing_representation)
    
    # 9. คืนค่าผลลัพธ์การจัดสรร
    return students, time_slots, clubs

def calculate_statistics(students, time_slots, clubs):
    """
    คำนวณสถิติต่างๆ จากผลการจัดสรรชมรม
    """
    statistics = {
        'total_students': len(students),
        'change_counts': {'morning': {}, 'afternoon': {}},
        'club_sizes': {'morning': {}, 'afternoon': {}},
        'satisfaction_scores': [],
        'group_representation': {'morning': {}, 'afternoon': {}}
    }
    
    # นับจำนวนการเปลี่ยนแปลง
    for student_id, student in students.items():
        for period in ['morning', 'afternoon']:
            changes = student['changes'][period]
            if changes not in statistics['change_counts'][period]:
                statistics['change_counts'][period][changes] = 0
            statistics['change_counts'][period][changes] += 1
    
    # นับขนาดชมรม
    for period in ['morning', 'afternoon']:
        for slot in range(1, NUM_SLOTS_PER_PERIOD + 1):
            if slot not in statistics['club_sizes'][period]:
                statistics['club_sizes'][period][slot] = {}
            
            for club in clubs[period]:
                club_size = len(time_slots[period][slot][club])
                statistics['club_sizes'][period][slot][club] = club_size
    
    # นับการแทนกลุ่ม
    for period in ['morning', 'afternoon']:
        for slot in range(1, NUM_SLOTS_PER_PERIOD + 1):
            if slot not in statistics['group_representation'][period]:
                statistics['group_representation'][period][slot] = {}
            
            for club in clubs[period]:
                group_counts = {str(i): 0 for i in range(NUM_GROUPS)}
                for student_id in time_slots[period][slot][club]:
                    group = students[student_id]['group']
                    group_counts[group] += 1
                statistics['group_representation'][period][slot][club] = group_counts
    
    # คำนวณคะแนนความพึงพอใจโดยรวม
    total_satisfaction = 0
    for student_id, student in students.items():
        student_satisfaction = 0
        for period in ['morning', 'afternoon']:
            for slot, club in student['assignments'][period].items():
                student_satisfaction += calculate_satisfaction_score(student, club, period, slot)
        
        statistics['satisfaction_scores'].append({
            'student_id': student_id,
            'score': student_satisfaction,
            'group': student['group']
        })
        total_satisfaction += student_satisfaction
    
    statistics['average_satisfaction'] = total_satisfaction / len(students) if students else 0
    
    return statistics

def save_results(students, clubs, statistics, output_file):
    """
    บันทึกผลลัพธ์การจัดสรรลงไฟล์ CSV โดยแบ่งตามกลุ่ม
    """
    # แยกนักศึกษาตามกลุ่ม
    students_by_group = {str(i): [] for i in range(NUM_GROUPS)}
    for student_id, student in students.items():
        group = student['group']
        students_by_group[group].append((student_id, student))
    
    # เรียงลำดับนักศึกษาในแต่ละกลุ่มตามรหัสนักศึกษา
    for group in students_by_group:
        students_by_group[group].sort(key=lambda x: x[0])
    
    results = []
    
    # เพิ่มข้อมูลนักศึกษาตามกลุ่ม
    for group in sorted(students_by_group.keys()):
        group_students = students_by_group[group]
        
        # เพิ่มหัวกลุ่ม
        if group_students:  # ในกรณีที่กลุ่มมีนักศึกษา
            results.append({
                'รหัสนักศึกษา': f'*** กลุ่ม {group} ({len(group_students)} คน) ***',
                'กลุ่ม': group
            })
            
            # เพิ่มข้อมูลนักศึกษาแต่ละคนในกลุ่ม
            for student_id, student in group_students:
                row = {
                    'รหัสนักศึกษา': student_id,
                    'กลุ่ม': student['group'],
                    'การเปลี่ยนแปลงชมรมเช้า': student['changes']['morning'],
                    'การเปลี่ยนแปลงชมรมบ่าย': student['changes']['afternoon']
                }
                
                # เพิ่มความต้องการหลักและสำรอง
                for period in ['morning', 'afternoon']:
                    for i, club in enumerate(student['preferences'][period]['main']):
                        row[f'ฐาน{"เช้า" if period == "morning" else "บ่าย"} อันดับที่ {i+1}'] = club
                    
                    for i, club in enumerate(student['preferences'][period]['backup']):
                        row[f'ฐาน{"เช้า" if period == "morning" else "บ่าย"} อันดับที่ {i+5}'] = club
                
                # เพิ่มการจัดสรร
                for period in ['morning', 'afternoon']:
                    for slot in range(1, NUM_SLOTS_PER_PERIOD + 1):
                        assigned_club = student['assignments'][period].get(slot, "")
                        row[f'ชมรม{"เช้า" if period == "morning" else "บ่าย"} ช่วงที่ {slot}'] = assigned_club
                
                results.append(row)
    
    # บันทึกไฟล์ CSV
    pd.DataFrame(results).to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Results saved to {output_file} with students grouped by their group number")

def generate_club_size_report(time_slots, clubs, output_file):
    """
    สร้างรายงานจำนวนนักศึกษาในแต่ละชมรมในแต่ละช่วงเวลา
    """
    # สร้างข้อมูลสำหรับรายงาน
    report_data = []
    
    # เพิ่มหัวข้อรายงาน
    report_data.append({
        'ช่วงเวลา': '*** รายงานจำนวนนักศึกษาในแต่ละชมรม ***',
        'ชมรม': '',
        'จำนวนนักศึกษา': '',
        'สถานะ': ''
    })
    
    # รายงานจำนวนนักศึกษาในแต่ละชมรม
    for period in ['morning', 'afternoon']:
        # เพิ่มหัวข้อช่วงเช้า/บ่าย
        period_display = "เช้า" if period == "morning" else "บ่าย"
        report_data.append({
            'ช่วงเวลา': f'========== ชมรม{period_display} ==========',
            'ชมรม': '',
            'จำนวนนักศึกษา': '',
            'สถานะ': ''
        })
        
        for slot in range(1, NUM_SLOTS_PER_PERIOD + 1):
            # เพิ่มหัวข้อช่วงเวลาย่อย
            report_data.append({
                'ช่วงเวลา': f'--- ช่วงที่ {slot} ---',
                'ชมรม': '',
                'จำนวนนักศึกษา': '',
                'สถานะ': ''
            })
            
            # เรียงชมรมตามจำนวนนักศึกษาจากมากไปน้อย
            club_sizes = [(club, len(time_slots[period][slot][club])) for club in clubs[period]]
            club_sizes.sort(key=lambda x: x[1], reverse=True)
            
            for club, size in club_sizes:
                # กำหนดสถานะตามจำนวนนักศึกษา
                status = "OK"
                if size > MAX_STUDENTS_PER_CLUB:
                    status = f"\u26a0️ เกินขีดจำกัด {MAX_STUDENTS_PER_CLUB} คน"
                elif size < 10:
                    status = f"ℹ️ น้อยกว่า 10 คน"
                
                report_data.append({
                    'ช่วงเวลา': f'[ช่วง {slot}]',
                    'ชมรม': club,
                    'จำนวนนักศึกษา': size,
                    'สถานะ': status
                })
    
    # บันทึกรายงานลงไฟล์ CSV
    report_filename = output_file.replace('.csv', '_club_sizes.csv')
    pd.DataFrame(report_data).to_csv(report_filename, index=False, encoding='utf-8-sig')
    print(f"Club size report saved to {report_filename}")
    
    # สรุปสถิติ
    over_limit_count = 0
    clubs_count = 0
    for period in ['morning', 'afternoon']:
        for slot in range(1, NUM_SLOTS_PER_PERIOD + 1):
            for club in clubs[period]:
                clubs_count += 1
                if len(time_slots[period][slot][club]) > MAX_STUDENTS_PER_CLUB:
                    over_limit_count += 1
    
    print(f"Club size summary: {over_limit_count} out of {clubs_count} club slots exceed the limit of {MAX_STUDENTS_PER_CLUB} students ({over_limit_count/clubs_count*100:.2f}%)")
    
    return report_filename

if __name__ == "__main__":
    print("Starting club allocation process...")
    input_file = "test_250.csv"  # ถ้ามีไฟล์อื่นให้เปลี่ยนชื่อไฟล์ตรงนี้
    output_file = "club_assignment_results_optimal.csv"
    
    # รันอัลกอริทึมการจัดสรร
    students, time_slots, clubs = optimize_club_allocation(input_file)
    
    # คำนวณสถิติ
    statistics = calculate_statistics(students, time_slots, clubs)
    
    # แสดงสถิติบางส่วน
    print(f"\n===== Club Allocation Statistics =====")
    print(f"Total students: {statistics['total_students']}")
    print(f"Average satisfaction score: {statistics['average_satisfaction']:.2f}")
    
    print("\nMorning club change statistics:")
    for changes, count in sorted(statistics['change_counts']['morning'].items()):
        print(f"  {changes} changes: {count} students ({count/statistics['total_students']*100:.2f}%)")
    
    print("\nAfternoon club change statistics:")
    for changes, count in sorted(statistics['change_counts']['afternoon'].items()):
        print(f"  {changes} changes: {count} students ({count/statistics['total_students']*100:.2f}%)")
    
    # บันทึกผลลัพธ์การจัดสรร
    save_results(students, clubs, statistics, output_file)
    
    # สร้างรายงานจำนวนนักศึกษาในแต่ละชมรม
    generate_club_size_report(time_slots, clubs, output_file)
    
    print(f"\nClub allocation completed successfully!")
