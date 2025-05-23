import sys
import pandas as pd
from collections import defaultdict, Counter

# ตั้งค่าเพื่อให้แสดงผลภาษาไทยใน terminal ได้
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

MAX_STUDENTS_PER_CLUB = 20
NUM_GROUPS = 10

def load_assignments(file_path):
    """
    โหลดข้อมูลการจัดสรรชมรมจากไฟล์ CSV
    """
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    # กรองเฉพาะแถวที่เป็นข้อมูลนักศึกษาจริง (ไม่ใช่แถวหัวกลุ่ม)
    df = df[~df['รหัสนักศึกษา'].astype(str).str.contains('กลุ่ม')]
    return df

def analyze_club_distribution(df):
    """
    วิเคราะห์การกระจายตัวของนักศึกษาในแต่ละชมรมและแต่ละกลุ่ม
    """
    # เก็บข้อมูลการกระจายตัว
    morning_distribution = {i: defaultdict(lambda: defaultdict(list)) for i in range(1, 5)}
    afternoon_distribution = {i: defaultdict(lambda: defaultdict(list)) for i in range(1, 5)}
    
    # ตรวจสอบว่ามีคอลัมน์กลุ่มหรือไม่
    if 'กลุ่ม' not in df.columns:
        # พยายามแปลงจากรหัสนักศึกษาถ้าไม่มีคอลัมน์กลุ่ม
        if 'รหัสนักศึกษา' in df.columns:
            df['กลุ่ม'] = df['รหัสนักศึกษา'].astype(str).str[-1]
        else:
            print("ไม่พบคอลัมน์ 'กลุ่ม' และไม่สามารถสร้างจากรหัสนักศึกษาได้")
            return morning_distribution, afternoon_distribution
    
    # วิเคราะห์ข้อมูลช่วงเช้า
    for slot in range(1, 5):
        column_name = f'ชมรมเช้า ช่วงที่ {slot}'
        if column_name in df.columns:
            for _, row in df.iterrows():
                club = row[column_name]
                group = str(row['กลุ่ม']) # แปลงเป็น string เพื่อให้แน่ใจว่าใช้เป็น key ได้
                student_id = row['รหัสนักศึกษา']
                if pd.notna(club) and club != '':
                    morning_distribution[slot][club][group].append(student_id)
    
    # วิเคราะห์ข้อมูลช่วงบ่าย
    for slot in range(1, 5):
        column_name = f'ชมรมบ่าย ช่วงที่ {slot}'
        if column_name in df.columns:
            for _, row in df.iterrows():
                club = row[column_name]
                group = str(row['กลุ่ม']) # แปลงเป็น string เพื่อให้แน่ใจว่าใช้เป็น key ได้
                student_id = row['รหัสนักศึกษา']
                if pd.notna(club) and club != '':
                    afternoon_distribution[slot][club][group].append(student_id)
    
    return morning_distribution, afternoon_distribution

def print_distribution_report(morning_dist, afternoon_dist, time_period="morning"):
    """
    แสดงผลรายงานการกระจายตัวของนักศึกษาในแต่ละชมรม แยกตามกลุ่ม
    """
    distribution = morning_dist if time_period == "morning" else afternoon_dist
    period_name = "MORNING" if time_period == "morning" else "AFTERNOON"
    
    print(f"\n{period_name} TIME SLOTS:\n")
    
    for slot in range(1, 5):
        print(f"  Slot {slot}:")
        
        # เตรียมข้อมูลสำหรับการแสดงผล
        club_data = []
        max_club_name_length = 0
        
        for club, groups in distribution[slot].items():
            if not club or pd.isna(club):
                continue
                
            max_club_name_length = max(max_club_name_length, len(club))
            
            # นับจำนวนนักศึกษาในแต่ละกลุ่ม
            group_counts = {str(i): len(groups.get(str(i), [])) for i in range(NUM_GROUPS)}
            total_students = sum(group_counts.values())
            
            club_data.append({
                'club': club,
                'total': total_students,
                'groups': group_counts,
                'over_limit': total_students > MAX_STUDENTS_PER_CLUB
            })
        
        # เรียงลำดับตามชื่อชมรม
        club_data.sort(key=lambda x: x['club'])
        
        # กำหนดความกว้างของคอลัมน์ให้พอดีกับข้อมูล
        club_col_width = max(max_club_name_length, 30) + 10
        
        # พิมพ์หัวตาราง
        print(f"  {'Club':{club_col_width}} Total | ", end="")
        for i in range(NUM_GROUPS):
            print(f" {i}", end="")
        print()
        
        # พิมพ์เส้นคั่น
        print(f"  {'-' * club_col_width} ----- | {'-' * 20}")
        
        # พิมพ์แถวข้อมูล
        for data in club_data:
            club_name = data['club']
            total = data['total']
            over_marker = " [OVER]" if data['over_limit'] else ""
            
            print(f"  {club_name:{club_col_width}} {total:5d} | ", end="")
            
            # แสดงการกระจายตัวตามกลุ่ม
            for i in range(NUM_GROUPS):
                count = data['groups'].get(str(i), 0)
                print(f" {count}", end="")
            
            print(over_marker)
        
        print()

def main():
    """
    ฟังก์ชันหลัก
    """
    # รับชื่อไฟล์จาก command line argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "club_assignment_results_optimal.csv"
    
    try:
        print(f"กำลังอ่านข้อมูลจากไฟล์ {input_file}...")
        df = load_assignments(input_file)
        print(f"พบข้อมูลนักศึกษาทั้งหมด {df.shape[0]} คน")
        
        # วิเคราะห์การกระจายตัว
        morning_dist, afternoon_dist = analyze_club_distribution(df)
        
        # แสดงรายงาน
        print_distribution_report(morning_dist, afternoon_dist, "morning")
        print_distribution_report(morning_dist, afternoon_dist, "afternoon")
        
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    main()
