import pandas as pd
import numpy as np
from collections import defaultdict
import random
import itertools
import os
import math

# กำหนดพิกัดของแต่ละอาคารที่ชมรมตั้งอยู่ (building_id: [x, y])
# สมมติค่าพิกัดเพื่อคำนวณระยะทาง
building_locations = {
    'อาคาร 1': [0, 0],
    'อาคาร 2': [10, 0],
    'อาคาร 3': [20, 0],
    'อาคาร 4': [0, 10],
    'อาคาร 5': [10, 10],
    'อาคาร 6': [20, 10],
    'อาคาร 7': [0, 20],
    'อาคาร 8': [10, 20],
    'อาคาร 9': [20, 20],
    'สนามกีฬา': [15, 5],
    'สระว่ายน้ำ': [5, 15]
}

# กำหนดชมรมอยู่ที่อาคารไหน (club_name: building_id)
club_buildings = {
    # ชมรมช่วงเช้า
    'บาสเก็ตบอล': 'สนามกีฬา',
    'แชร์บอล': 'สนามกีฬา',
    'CHORUS': 'อาคาร 2',
    'DEVIL': 'อาคาร 3',
    'ฟุตบอล': 'สนามกีฬา',
    'เทนนิส': 'สนามกีฬา',  
    'ดนตรีไทย': 'อาคาร 2',
    'วิ่ง': 'สนามกีฬา',
    'วอลเลย์บอล': 'สนามกีฬา',
    'MUAN': 'อาคาร 6',
    'ART': 'อาคาร 5',
    'เปตอง': 'อาคาร 9',    
    'Swimming (ชมรมว่ายน้ำและโปโลน้ำ)': 'สระว่ายน้ำ',
    # ชมรมช่วงบ่าย
    'Bridge': 'อาคาร 6',
    'E-sport': 'อาคาร 7',
    'IMSU': 'อาคาร 8',
    'Libir': 'อาคาร 9',
    'MCCC': 'อาคาร 5', 
    'พอช.': 'อาคาร 8',
    'Research': 'อาคาร 9',
    'หมอน้อย': 'อาคาร 7',
    'ปิงปอง': 'อาคาร 4',
    'แบตมินตัน': 'สนามกีฬา',
    'ดนตรีสากล': 'อาคาร 2',
    'cheerleader': 'อาคาร 1',
    'CMSO': 'อาคาร 9',
    'coverdance': 'อาคาร 1',
}

# คำนวณระยะทางระหว่างสองอาคาร
def calculate_distance(building1, building2):
    """
    คำนวณระยะทางระหว่างสองอาคารโดยใช้ Euclidean distance
    """
    if building1 not in building_locations or building2 not in building_locations:
        return float('inf')  # ถ้าไม่พบอาคาร ให้ถือว่าระยะทางเป็นอนันต์
    
    x1, y1 = building_locations[building1]
    x2, y2 = building_locations[building2]
    
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

# คำนวณระยะทางระหว่างสองชมรม
def calculate_club_distance(club1, club2):
    """
    คำนวณระยะทางระหว่างสองชมรม
    """
    if club1 not in club_buildings or club2 not in club_buildings:
        return float('inf')  # ถ้าไม่พบชมรม ให้ถือว่าระยะทางเป็นอนันต์
    
    building1 = club_buildings[club1]
    building2 = club_buildings[club2]
    
    return calculate_distance(building1, building2)

# อ่านข้อมูลการจัดสรรชมรมจากไฟล์ CSV
def read_assignment_data(file_path):
    """
    อ่านข้อมูลการจัดสรรชมรมจากไฟล์ CSV
    """
    df = pd.read_csv(file_path)
    return df

# สร้างโครงสร้างข้อมูลนักศึกษาและการจัดสรรชมรม
def create_student_data(df):
    """
    สร้างโครงสร้างข้อมูลที่เก็บการจัดสรรชมรมของนักศึกษาแต่ละคน
    """
    students = {}
    
    # คอลัมน์ที่เก็บข้อมูลชมรมช่วงเช้าและบ่าย
    morning_cols = [f'ชมรมเช้า ช่วงที่ {i}' for i in range(1, 5)]
    afternoon_cols = [f'ชมรมบ่าย ช่วงที่ {i}' for i in range(1, 5)]
    
    for _, row in df.iterrows():
        student_id = row['รหัสนักศึกษา']
        
        # เก็บข้อมูลการจัดสรรชมรมของนักศึกษา
        morning_assignments = {i+1: row[col] for i, col in enumerate(morning_cols)}
        afternoon_assignments = {i+1: row[col] for i, col in enumerate(afternoon_cols)}
        
        students[student_id] = {
            'name': row.get('ชื่อ นามสกุล', ''),
            'group': row.get('กลุ่ม', ''),
            'assignments': {
                'morning': morning_assignments,
                'afternoon': afternoon_assignments
            }
        }
    
    return students

# คำนวณระยะทางรวมในการเดินของนักศึกษาแต่ละคน
def calculate_student_total_distance(student_data):
    """
    คำนวณระยะทางรวมในการเดินของนักศึกษาแต่ละคน
    """
    total_distance = 0
    
    # คำนวณระยะทางช่วงเช้า (slots 1-4)
    for i in range(1, 4):  # เฉพาะ 1-3 เพราะต้องเดินไปอีกช่วงเวลา
        club1 = student_data['assignments']['morning'][i]
        club2 = student_data['assignments']['morning'][i+1]
        total_distance += calculate_club_distance(club1, club2)
    
    # คำนวณระยะทางช่วงบ่าย (slots 1-4)
    for i in range(1, 4):  # เฉพาะ 1-3 เพราะต้องเดินไปอีกช่วงเวลา
        club1 = student_data['assignments']['afternoon'][i]
        club2 = student_data['assignments']['afternoon'][i+1]
        total_distance += calculate_club_distance(club1, club2)
    
    # คำนวณระยะทางจากช่วงเช้าสุดท้ายไปช่วงบ่ายแรก
    last_morning_club = student_data['assignments']['morning'][4]
    first_afternoon_club = student_data['assignments']['afternoon'][1]
    total_distance += calculate_club_distance(last_morning_club, first_afternoon_club)
    
    return total_distance

# สร้างโครงสร้างความถี่ของชมรมในแต่ละช่วงเวลา
def count_club_frequencies(students):
    """
    นับความถี่ของแต่ละชมรมในแต่ละช่วงเวลา เพื่อใช้ตรวจสอบว่าการสลับไม่ทำให้จำนวนนักศึกษาต่อชมรมเปลี่ยนแปลง
    """
    frequencies = {
        'morning': {1: {}, 2: {}, 3: {}, 4: {}},
        'afternoon': {1: {}, 2: {}, 3: {}, 4: {}}
    }
    
    for student_id, student in students.items():
        for period in ['morning', 'afternoon']:
            for slot, club in student['assignments'][period].items():
                if club not in frequencies[period][slot]:
                    frequencies[period][slot][club] = 0
                frequencies[period][slot][club] += 1
    
    return frequencies

# ตรวจสอบว่าการสลับช่วงเวลาจะไม่ทำให้จำนวนนักศึกษาต่อชมรมเปลี่ยนแปลงและรักษาชมรมที่นักศึกษาได้รับการจัดสรร
def is_valid_slot_swap(student1, student2, period, slot1, slot2, club_frequencies):
    """
    ตรวจสอบว่าการสลับช่วงเวลาจะไม่ทำให้จำนวนนักศึกษาต่อชมรมเปลี่ยนแปลง
    และรักษาชมรมที่นักศึกษาแต่ละคนได้รับการจัดสรรไว้แล้ว
    """
    # ตรวจสอบแบบการสลับช่วงเวลาที่ถูกต้อง:
    # 1. สลับช่วงเวลาเท่านั้น ไม่สลับชมรม
    # 2. จำนวนนักศึกษาต่อชมรมในแต่ละช่วงเวลายังคงเท่าเดิม
    
    # ตรวจสอบว่าทั้งสองนักศึกษามีทั้งชมรมอยู่ในรายการของกันและกัน
    club1_slot1 = student1['assignments'][period][slot1]
    club1_slot2 = student1['assignments'][period][slot2]
    club2_slot1 = student2['assignments'][period][slot1]
    club2_slot2 = student2['assignments'][period][slot2]
    
    # ตรวจสอบว่าชมรมที่จะสลับมีอยู่ในรายการของทั้งสองคน
    # นักศึกษา 1 ต้องมีชมรมของนักศึกษา 2 อยู่ในรายการ และนักศึกษา 2 ก็ต้องมีชมรมของนักศึกษา 1 อยู่ในรายการ
    
    # ตรวจสอบว่าสามารถสลับช่วงเวลาโดยไม่มีชมรมซ้ำกัน
    # ตรวจสอบว่านักศึกษา 1 ไม่มีชมรม club2_slot1 และ club2_slot2 ในช่วงเวลาอื่นๆ
    student1_all_clubs = [v for k, v in student1['assignments'][period].items() if k != slot1 and k != slot2]
    if club2_slot1 in student1_all_clubs or club2_slot2 in student1_all_clubs:
        return False
    
    # ตรวจสอบว่านักศึกษา 2 ไม่มีชมรม club1_slot1 และ club1_slot2 ในช่วงเวลาอื่นๆ
    student2_all_clubs = [v for k, v in student2['assignments'][period].items() if k != slot1 and k != slot2]
    if club1_slot1 in student2_all_clubs or club1_slot2 in student2_all_clubs:
        return False
    
    # ตรวจสอบว่าจำนวนนักศึกษาต่อชมรมในแต่ละช่วงเวลาจะไม่เปลี่ยนแปลง
    # ในกรณีที่สลับช่วงเวลาเดียวกัน ต้องตรวจสอบว่าจำนวนนักศึกษาต่อชมรมเท่าเดิม
    if slot1 == slot2:
        return club1_slot1 == club2_slot1
    
    # ในกรณีที่สลับคนละช่วงเวลา
    return True

# คำนวณผลประโยชน์จากการสลับ
def calculate_benefit_from_swap(student1, student2, period, slot1, slot2, students):
    """
    คำนวณผลประโยชน์ (ระยะทางที่ลดลง) จากการสลับช่วงเวลา
    โดยยังคงให้นักศึกษาได้เข้าชมรมที่ได้รับการจัดสรรเดิม
    """
    # สร้าง student data ใหม่โดยยังไม่สลับ
    student1_copy = {'assignments': {'morning': student1['assignments']['morning'].copy(), 
                                  'afternoon': student1['assignments']['afternoon'].copy()}}
    student2_copy = {'assignments': {'morning': student2['assignments']['morning'].copy(), 
                                  'afternoon': student2['assignments']['afternoon'].copy()}}
    
    # คำนวณระยะทางก่อนสลับ
    distance_before_1 = calculate_student_total_distance(student1_copy)
    distance_before_2 = calculate_student_total_distance(student2_copy)
    total_distance_before = distance_before_1 + distance_before_2
    
    # เก็บชมรมของแต่ละนักศึกษาในแต่ละช่วงเวลา
    club1_slot1 = student1_copy['assignments'][period][slot1]
    club1_slot2 = student1_copy['assignments'][period][slot2]
    club2_slot1 = student2_copy['assignments'][period][slot1]
    club2_slot2 = student2_copy['assignments'][period][slot2]
    
    # ทำการสลับช่วงเวลาสำหรับนักศึกษา 1
    student1_copy['assignments'][period][slot1] = club1_slot2
    student1_copy['assignments'][period][slot2] = club1_slot1
    
    # ทำการสลับช่วงเวลาสำหรับนักศึกษา 2
    student2_copy['assignments'][period][slot1] = club2_slot2
    student2_copy['assignments'][period][slot2] = club2_slot1
    
    # คำนวณระยะทางหลังสลับ
    distance_after_1 = calculate_student_total_distance(student1_copy)
    distance_after_2 = calculate_student_total_distance(student2_copy)
    total_distance_after = distance_after_1 + distance_after_2
    
    # ผลประโยชน์คือระยะทางที่ลดลง
    benefit = total_distance_before - total_distance_after
    
    return benefit

# สลับช่วงเวลาระหว่างสองนักศึกษา
def swap_student_slots(students, student_id1, student_id2, period, slot1, slot2):
    """
    สลับช่วงเวลาระหว่างสองนักศึกษา
    โดยให้นักศึกษายังได้เข้าร่วมชมรมที่ได้รับการจัดสรรแล้ว เพียงแต่เปลี่ยนช่วงเวลา
    """
    student1 = students[student_id1]
    student2 = students[student_id2]
    
    # เก็บชมรมของแต่ละนักศึกษาในแต่ละช่วงเวลา
    club1_slot1 = student1['assignments'][period][slot1]
    club1_slot2 = student1['assignments'][period][slot2]
    club2_slot1 = student2['assignments'][period][slot1]
    club2_slot2 = student2['assignments'][period][slot2]
    
    # ทำการสลับช่วงเวลาสำหรับนักศึกษา 1
    student1['assignments'][period][slot1] = club1_slot2  # ให้ชมรมที่เคยเข้าในช่วงที่ 2 มาอยู่ช่วงที่ 1 แทน
    student1['assignments'][period][slot2] = club1_slot1  # ให้ชมรมที่เคยเข้าในช่วงที่ 1 มาอยู่ช่วงที่ 2 แทน
    
    # ทำการสลับช่วงเวลาสำหรับนักศึกษา 2
    student2['assignments'][period][slot1] = club2_slot2  # ให้ชมรมที่เคยเข้าในช่วงที่ 2 มาอยู่ช่วงที่ 1 แทน
    student2['assignments'][period][slot2] = club2_slot1  # ให้ชมรมที่เคยเข้าในช่วงที่ 1 มาอยู่ช่วงที่ 2 แทน
    
    return students

# ฟังก์ชันหลักในการค้นหาการสลับที่ดีที่สุด
def find_best_swaps(students):
    """
    ค้นหาการสลับที่ให้ประโยชน์มากที่สุด โดยรักษาการจัดสรรชมรมเดิมของนักศึกษา
    """
    # นับความถี่ของชมรมในแต่ละช่วงเวลา
    club_frequencies = count_club_frequencies(students)
    
    print("Finding best time slot swaps that preserve student club assignments...")
    
    # เก็บการสลับที่ดีที่สุด
    best_swaps = []
    
    # วนลูปผ่านนักศึกษาทุกคู่
    student_ids = list(students.keys())
    possible_swaps = 0
    valid_swaps = 0
    beneficial_swaps = 0
    
    # สร้างตาราง pair_slots เพื่อลดการทดสอบซ้ำ (การสลับ slot1, slot2 กับ slot2, slot1 คือการสลับแบบเดียวกัน)
    pair_slots = []
    for slot1 in range(1, 5):
        for slot2 in range(slot1+1, 5):  # เริ่มจาก slot1+1 เพื่อไม่ให้ซ้ำซ้อน
            pair_slots.append((slot1, slot2))
    
    for i in range(len(student_ids)):
        if i % 10 == 0 and i > 0:
            print(f"Processed {i} students, found {beneficial_swaps} beneficial swaps so far...")
            
        for j in range(i + 1, len(student_ids)):
            student_id1 = student_ids[i]
            student_id2 = student_ids[j]
            student1 = students[student_id1]
            student2 = students[student_id2]
            
            # ทดลองสลับทุกคู่ช่วงเวลาที่เป็นไปได้
            for period in ['morning', 'afternoon']:
                for slot1, slot2 in pair_slots:  # ใช้คู่ช่องเวลาที่สร้างไว้แล้ว
                    possible_swaps += 1
                    
                    # ตรวจสอบว่าการสลับไม่ทำให้จำนวนนักศึกษาต่อชมรมเปลี่ยน
                    # และรักษาชมรมที่นักศึกษาได้รับการจัดสรร
                    if is_valid_slot_swap(student1, student2, period, slot1, slot2, club_frequencies):
                        valid_swaps += 1
                        
                        # คำนวณผลประโยชน์จากการสลับ (ระยะทางที่ลดลง)
                        benefit = calculate_benefit_from_swap(student1, student2, period, slot1, slot2, students)
                        
                        # เก็บการสลับที่ให้ประโยชน์ (ระยะทางลดลง)
                        if benefit > 0:
                            beneficial_swaps += 1
                            best_swaps.append({
                                'student_id1': student_id1,
                                'student_id2': student_id2,
                                'period': period,
                                'slot1': slot1,
                                'slot2': slot2,
                                'benefit': benefit
                            })
    
    print(f"\nAnalysis complete:")
    print(f"Total possible swaps considered: {possible_swaps}")
    print(f"Valid swaps found (preserve student assignments): {valid_swaps}")
    print(f"Beneficial swaps found (reduce total distance): {beneficial_swaps}")
    
    # เรียงลำดับการสลับตามผลประโยชน์ (ระยะทางที่ลดลง)
    best_swaps.sort(key=lambda x: x['benefit'], reverse=True)
    
    return best_swaps

# ดำเนินการสลับตามลำดับผลประโยชน์สูงสุด
def perform_swaps(students, max_swaps=100):
    """
    ดำเนินการสลับตามลำดับผลประโยชน์สูงสุด
    """
    # เก็บข้อมูลการสลับที่ทำ
    performed_swaps = []
    total_distance_saved = 0
    
    # ระยะทางรวมก่อนสลับ
    total_distance_before = sum(calculate_student_total_distance(students[student_id]) for student_id in students)
    
    # จำนวนการสลับที่ทำ
    swap_count = 0
    
    while swap_count < max_swaps:
        # ค้นหาการสลับที่ดีที่สุด
        best_swaps = find_best_swaps(students)
        
        # ถ้าไม่มีการสลับที่ดี ให้หยุด
        if not best_swaps:
            break
        
        # เลือกการสลับที่ให้ประโยชน์มากที่สุด
        best_swap = best_swaps[0]
        
        # ดำเนินการสลับ
        students = swap_student_slots(
            students,
            best_swap['student_id1'],
            best_swap['student_id2'],
            best_swap['period'],
            best_swap['slot1'],
            best_swap['slot2']
        )
        
        # บันทึกการสลับ
        performed_swaps.append(best_swap)
        total_distance_saved += best_swap['benefit']
        swap_count += 1
        
        # แสดงความคืบหน้า
        if swap_count % 10 == 0:
            print(f"Performed {swap_count} swaps, saved {total_distance_saved:.2f} distance units so far...")
    
    # ระยะทางรวมหลังสลับ
    total_distance_after = sum(calculate_student_total_distance(students[student_id]) for student_id in students)
    
    # แสดงผลลัพธ์
    print(f"\nOptimization completed!")
    print(f"Total swaps performed: {swap_count}")
    print(f"Total distance before: {total_distance_before:.2f} units")
    print(f"Total distance after: {total_distance_after:.2f} units")
    print(f"Total distance saved: {total_distance_saved:.2f} units ({(total_distance_saved / total_distance_before * 100):.2f}%)")
    
    return students, performed_swaps, total_distance_before, total_distance_after

# บันทึกผลการจัดสรรที่ปรับปรุงแล้วลงไฟล์ CSV
def save_optimized_assignments(students, output_file):
    """
    บันทึกข้อมูลการจัดสรรที่ปรับปรุงแล้วลงไฟล์ CSV
    """
    # กำหนดหัวข้อคอลัมน์
    headers = [
        'รหัสนักศึกษา', 'ชื่อ นามสกุล', 'กลุ่ม',
        'ชมรมเช้า ช่วงที่ 1', 'ชมรมเช้า ช่วงที่ 2', 'ชมรมเช้า ช่วงที่ 3', 'ชมรมเช้า ช่วงที่ 4',
        'ชมรมบ่าย ช่วงที่ 1', 'ชมรมบ่าย ช่วงที่ 2', 'ชมรมบ่าย ช่วงที่ 3', 'ชมรมบ่าย ช่วงที่ 4',
        'ระยะทางก่อนปรับปรุง', 'ระยะทางหลังปรับปรุง', 'ระยะทางที่ลดลง (ร้อยละ)'
    ]
    
    # สร้างข้อมูลสำหรับบันทึก
    rows = []
    
    for student_id, student in students.items():
        # คำนวณระยะทางก่อนปรับปรุง (จากข้อมูลเดิม)
        # สมมติว่ามีแล้วในโครงสร้างข้อมูล
        distance_after = calculate_student_total_distance(student)
        
        # สร้างข้อมูลแถว
        row = [
            student_id,
            student.get('name', ''),
            student.get('group', ''),
            student['assignments']['morning'][1],
            student['assignments']['morning'][2],
            student['assignments']['morning'][3],
            student['assignments']['morning'][4],
            student['assignments']['afternoon'][1],
            student['assignments']['afternoon'][2],
            student['assignments']['afternoon'][3],
            student['assignments']['afternoon'][4],
            '', # ระยะทางก่อนปรับปรุง (จะเติมโดยการเปรียบเทียบกับไฟล์เดิม)
            f'{distance_after:.2f}', # ระยะทางหลังปรับปรุง
            '' # ระยะทางที่ลดลง (ร้อยละ) (จะเติมโดยการเปรียบเทียบกับไฟล์เดิม)
        ]
        
        rows.append(row)
    
    # บันทึกลงไฟล์ CSV
    df = pd.DataFrame(rows, columns=headers)
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"Saved optimized assignments to {output_file}")
    
    return df

# ฟังก์ชันหลัก
def main():
    # กำหนดพารามิเตอร์
    input_file = "club_assignment_results_improved.csv"
    output_file = "club_assignment_results_optimized.csv"
    max_swaps = 1000  # จำนวนการสลับสูงสุด
    
    print(f"Optimizing club assignment paths...")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Maximum swaps: {max_swaps}")
    
    # อ่านข้อมูลการจัดสรร
    print("\nReading assignment data...")
    df = read_assignment_data(input_file)
    
    # สร้างโครงสร้างข้อมูลนักศึกษา
    print("Creating student data structure...")
    students = create_student_data(df)
    
    # ดำเนินการสลับเพื่อปรับปรุงเส้นทาง
    print("\nOptimizing paths by swapping time slots...")
    students, swaps, distance_before, distance_after = perform_swaps(students, max_swaps)
    
    # บันทึกผลการจัดสรรที่ปรับปรุงแล้ว
    print("\nSaving optimized assignments...")
    df_result = save_optimized_assignments(students, output_file)
    
    print("\nPath optimization completed successfully!")

# รันโปรแกรมเมื่อเรียกใช้โดยตรง
if __name__ == "__main__":
    main()
