import pandas as pd
import os
import sys
from collections import defaultdict

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def load_assignment_results(file_path):
    """
    โหลดข้อมูลการจัดสรรชมรมจากไฟล์ CSV
    """
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    # กรองเฉพาะแถวที่เป็นข้อมูลนักศึกษาจริง (ไม่ใช่แถวหัวกลุ่ม)
    df = df[~df['รหัสนักศึกษา'].astype(str).str.contains('กลุ่ม')]
    return df

def count_club_members(df):
    """
    นับจำนวนนักศึกษาในแต่ละชมรมในแต่ละช่วงเวลา
    """
    morning_clubs = defaultdict(lambda: defaultdict(int))
    afternoon_clubs = defaultdict(lambda: defaultdict(int))
    
    # นับจำนวนนักศึกษาในชมรมเช้า
    for slot in range(1, 5):
        col_name = f'ชมรมเช้า ช่วงที่ {slot}'
        for club in df[col_name].dropna().unique():
            count = df[df[col_name] == club].shape[0]
            morning_clubs[club][slot] = count
    
    # นับจำนวนนักศึกษาในชมรมบ่าย
    for slot in range(1, 5):
        col_name = f'ชมรมบ่าย ช่วงที่ {slot}'
        for club in df[col_name].dropna().unique():
            count = df[df[col_name] == club].shape[0]
            afternoon_clubs[club][slot] = count
    
    return morning_clubs, afternoon_clubs

def print_club_stats(morning_clubs, afternoon_clubs):
    """
    แสดงผลสถิติชมรมในแต่ละช่วงเวลา
    """
    max_club_name_length = max(
        max([len(club) for club in morning_clubs.keys()], default=0),
        max([len(club) for club in afternoon_clubs.keys()], default=0)
    )
    
    # ฟังก์ชันช่วยในการแสดงผล
    def print_period_stats(period_name, clubs_data):
        print(f"\n{'='*20} ชมรม{period_name} {'='*20}")
        print(f"{'ชื่อชมรม':<{max_club_name_length+2}} | {'ช่วงที่ 1':^10} | {'ช่วงที่ 2':^10} | {'ช่วงที่ 3':^10} | {'ช่วงที่ 4':^10} | {'รวม':^10}")
        print(f"{'-'*(max_club_name_length+2)}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")
        
        # เรียงชมรมตามชื่อ
        for club in sorted(clubs_data.keys()):
            slots = clubs_data[club]
            slot1 = slots.get(1, 0)
            slot2 = slots.get(2, 0)
            slot3 = slots.get(3, 0)
            slot4 = slots.get(4, 0)
            total = slot1 + slot2 + slot3 + slot4
            
            # เพิ่มเครื่องหมายเตือนถ้าจำนวนเกิน 20
            def format_count(count):
                if count > 20:
                    return f"{count} ⚠️"
                elif count == 0:
                    return f"{count} ❌"
                else:
                    return f"{count}"
            
            print(f"{club:<{max_club_name_length+2}} | {format_count(slot1):^10} | {format_count(slot2):^10} | {format_count(slot3):^10} | {format_count(slot4):^10} | {total:^10}")
    
    # แสดงผลชมรมเช้า
    print_period_stats("เช้า", morning_clubs)
    
    # แสดงผลชมรมบ่าย
    print_period_stats("บ่าย", afternoon_clubs)
    
    # แสดงสถิติรวม
    morning_over_limit = sum(1 for club in morning_clubs.values() for slot, count in club.items() if count > 20)
    afternoon_over_limit = sum(1 for club in afternoon_clubs.values() for slot, count in club.items() if count > 20)
    
    print("\n===== สรุปสถิติ =====")
    print(f"จำนวนช่วงเวลา-ชมรมเช้าที่เกิน 20 คน: {morning_over_limit}")
    print(f"จำนวนช่วงเวลา-ชมรมบ่ายที่เกิน 20 คน: {afternoon_over_limit}")
    print(f"จำนวนรวมช่วงเวลา-ชมรมที่เกิน 20 คน: {morning_over_limit + afternoon_over_limit}")
    
    # สถิติกลุ่มชมรมขนาดเล็ก
    morning_under_10 = sum(1 for club in morning_clubs.values() for slot, count in club.items() if 0 < count < 10)
    afternoon_under_10 = sum(1 for club in afternoon_clubs.values() for slot, count in club.items() if 0 < count < 10)
    
    print(f"จำนวนช่วงเวลา-ชมรมเช้าที่มีนักศึกษาน้อยกว่า 10 คน: {morning_under_10}")
    print(f"จำนวนช่วงเวลา-ชมรมบ่ายที่มีนักศึกษาน้อยกว่า 10 คน: {afternoon_under_10}")
    print(f"จำนวนรวมช่วงเวลา-ชมรมที่มีนักศึกษาน้อยกว่า 10 คน: {morning_under_10 + afternoon_under_10}")

def main():
    file_path = "club_assignment_results_optimal.csv"
    if not os.path.exists(file_path):
        print(f"ไม่พบไฟล์ {file_path} กรุณาตรวจสอบชื่อไฟล์")
        return
    
    print(f"กำลังอ่านข้อมูลจาก {file_path}...")
    df = load_assignment_results(file_path)
    print(f"พบข้อมูลนักศึกษาทั้งหมด {df.shape[0]} คน")
    
    morning_clubs, afternoon_clubs = count_club_members(df)
    print_club_stats(morning_clubs, afternoon_clubs)

if __name__ == "__main__":
    main()
