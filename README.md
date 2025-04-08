# ระบบจัดสรรชมรมนักศึกษา (Club Allocation System)

โปรแกรมนี้เป็นระบบจัดสรรนักศึกษาเข้าชมรมต่างๆ ตามความต้องการของนักศึกษา ภายใต้ข้อจำกัดด้านจำนวนและความหลากหลายของกลุ่ม

## วัตถุประสงค์

- จัดสรรนักศึกษาเข้าชมรมตามความต้องการ (ทั้งตัวเลือกหลักและตัวเลือกสำรอง)
- รับประกันว่าทุกกลุ่ม (0-9 ตามเลขท้ายรหัสนักศึกษา) มีตัวแทนในทุกชมรม
- ควบคุมจำนวนนักศึกษาในแต่ละชมรมไม่เกิน 20 คน (ยกเว้นกรณีที่จำเป็นต้องเพิ่มเพื่อให้มีตัวแทนกลุ่ม)
- สร้างความเป็นธรรมในการจัดสรรชมรมที่มีความนิยมสูง

## ข้อมูลนำเข้า

โปรแกรมใช้ไฟล์ CSV ที่มีรูปแบบดังนี้:

1. `รหัสนักศึกษา`: รหัสประจำตัวนักศึกษา
2. `ชื่อ นามสกุล`: ชื่อของนักศึกษา
3. คอลัมน์ `ฐานเช้า อันดับที่ 1-8`: ชื่อชมรมที่นักศึกษาต้องการเข้าร่วมช่วงเช้า (1-4 เป็นชมรมหลัก, 5-8 เป็นชมรมสำรอง)
4. คอลัมน์ `ฐานบ่าย อันดับที่ 1-8`: ชื่อชมรมที่นักศึกษาต้องการเข้าร่วมช่วงบ่าย (1-4 เป็นชมรมหลัก, 5-8 เป็นชมรมสำรอง)

## ขั้นตอนการทำงาน

โปรแกรมทำงานตามลำดับขั้นตอนดังนี้:

### 1. การเตรียมข้อมูล

1. **อ่านข้อมูลจากไฟล์ CSV**: ใช้ `read_data()` เพื่ออ่านข้อมูลจาก CSV
2. **แบ่งกลุ่มนักศึกษา**: ใช้ `assign_groups()` เพื่อแบ่งกลุ่มตามเลขท้ายรหัสนักศึกษา (0-9)
3. **รวบรวมรายชื่อชมรม**: ใช้ `get_all_clubs()` เพื่อดึงรายชื่อชมรมทั้งหมด:
   - ทำความสะอาดชื่อชมรม (ตัดช่องว่าง, แก้ไขชื่อซ้ำ)
   - แยกชมรมเช้าและบ่าย
4. **สร้างโครงสร้างข้อมูล**: ใช้ `initialize_time_slots()` สร้างโครงสร้างของช่วงเวลา
5. **วิเคราะห์ความนิยม**: ใช้ `count_preferences()` นับความนิยมของแต่ละชมรม
6. **สร้างข้อมูลความต้องการ**: ใช้ `create_student_preferences()` รวบรวมความต้องการของนักศึกษา

### 2. การจัดสรรชมรม

การจัดสรรชมรมทำเป็น 2 รอบ:

#### รอบที่ 1: การจัดสรรตามความต้องการ (`assign_time_slot()`):

1. **เตรียมข้อมูลการจัดสรร**:
   - ตรวจสอบกลุ่มที่มีตัวแทนในแต่ละชมรมแล้ว
   - รวบรวมความต้องการของนักศึกษาในแต่ละชมรมและช่วงเวลา

2. **การจัดสรรตัวแทนกลุ่ม (First Pass)**:
   - สำหรับแต่ละชมรม ตรวจสอบว่ากลุ่มใดยังไม่มีตัวแทน
   - สำหรับกลุ่มที่ขาดตัวแทน เลือกนักศึกษาที่เหมาะสมที่สุดมาเป็นตัวแทน โดยพิจารณาจาก:
     - ความต้องการของนักศึกษา (ลำดับการเลือก)
     - จำนวนชมรมที่ได้รับแล้ว
     - ความเป็นไปได้ในการจัดสรร

3. **การจัดสรรปกติ (Second Pass)**:
   - สำหรับชมรมที่มีผู้สนใจมากกว่า 20 คน:
     - คำนวณคะแนนความยุติธรรม (fairness score) สำหรับแต่ละนักศึกษา
     - เลือกนักศึกษาที่มีคะแนนสูงสุด 20 คนแรก
     - พยายามจัดสรรนักศึกษาที่เหลือไปยังชมรมสำรอง
   - สำหรับชมรมที่มีผู้สนใจไม่เกิน 20 คน:
     - จัดสรรทุกคนตามความต้องการ

4. **การจัดสรรนักศึกษาที่เหลือ**:
   - สำหรับนักศึกษาที่ยังไม่ได้รับการจัดสรรในช่วงเวลานั้น:
     - พยายามจัดสรรไปยังชมรมที่ยังมีที่ว่าง
     - ให้ความสำคัญกับชมรมที่ยังขาดตัวแทนจากกลุ่มของนักศึกษา

#### รอบที่ 2: การรับประกันตัวแทนกลุ่ม (`ensure_group_representation()`):

1. **ตรวจสอบการมีตัวแทน**:
   - ตรวจสอบว่าทุกกลุ่มมีตัวแทนในทุกชมรมหรือไม่
   
2. **เพิ่มตัวแทนกลุ่มที่ขาด**:
   - สำหรับกลุ่มที่ยังไม่มีตัวแทนในชมรมใด:
     - พยายามหานักศึกษาจากกลุ่มนั้นที่ยังไม่มีการจัดสรรในช่วงเวลาใดเวลาหนึ่ง
     - หากไม่มี พยายามสลับนักศึกษาจากชมรมอื่นที่มีตัวแทนกลุ่มเดียวกันหลายคน
     - หากจำเป็น บังคับสลับนักศึกษาแม้จะทำให้ชมรมมีคนเกิน 20 คน

### 3. การจัดสรรตัวแทนกลุ่มและระบบคะแนนโดยละเอียด

#### 3.1 ระบบคะแนนความยุติธรรม (Fairness Score)

ฟังก์ชัน `calculate_fairness_score()` คำนวณคะแนนเพื่อตัดสินใจว่านักศึกษาคนใดควรได้รับการจัดสรรก่อน โดยมีองค์ประกอบของคะแนนดังนี้:

```python
def calculate_fairness_score(student, club, period, club_counts, represented_groups=None):
    # เริ่มต้นที่คะแนน 0
    score = 0
    
    # 1. การเป็นตัวแทนกลุ่ม (มีน้ำหนักมากที่สุด)
    if represented_groups is not None:
        if student['group'] not in represented_groups:
            score += 1000  # ให้คะแนนพิเศษมากหากเป็นกลุ่มที่ยังไม่มีตัวแทน
    
    # 2. จำนวนชมรมที่ได้รับแล้ว (น้อยคือดี)
    assigned_count = len(student['assignments'][period])
    score -= assigned_count * 10  # ลดคะแนนลงตามจำนวนชมรมที่ได้แล้ว
    
    # 3. ลำดับความต้องการ (คะแนนลดลงตามลำดับ)
    if club in student['preferences'][period]['main']:
        pref_rank = student['preferences'][period]['main'].index(club) + 1
        score += (5 - pref_rank) * 5  # อันดับที่ 1 = +20, อันดับที่ 4 = +5
    elif club in student['preferences'][period]['backup']:
        pref_rank = student['preferences'][period]['backup'].index(club) + 1
        score += pref_rank  # ชมรมสำรองได้คะแนนน้อยกว่า
    else:
        score -= 10  # หากไม่ได้เลือกไว้เลย ลดคะแนน
    
    # 4. ความนิยมของชมรม (คะแนนลดลงตามความนิยม)
    popularity = club_counts[period][club] / sum(club_counts[period].values())
    score -= popularity * 10  # ชมรมยอดนิยมได้คะแนนน้อยกว่า
    
    return score
```

**การคิดคะแนน**:
1. **กลุ่มตัวแทน** (+1000 คะแนน): ปัจจัยที่มีน้ำหนักมากที่สุด หากนักศึกษาอยู่ในกลุ่มที่ยังไม่มีตัวแทนในชมรมนั้น จะได้คะแนนพิเศษมาก ทำให้มีโอกาสสูงที่จะได้รับจัดสรร

2. **จำนวนชมรมที่ได้รับแล้ว** (-10 คะแนนต่อชมรม): นักศึกษาที่ได้รับการจัดสรรชมรมน้อยกว่าจะได้คะแนนสูงกว่า ตัวอย่างเช่น:
   - นักศึกษา A ได้รับจัดสรร 0 ชมรม → ไม่ถูกหักคะแนน
   - นักศึกษา B ได้รับจัดสรร 2 ชมรม → ถูกหัก 20 คะแนน
   - นักศึกษา C ได้รับจัดสรร 4 ชมรม → ถูกหัก 40 คะแนน

3. **ลำดับความต้องการ** (สูงสุด +20 คะแนน): ชมรมที่อยู่ในลำดับสูงจะได้คะแนนมากกว่า
   - ความต้องการหลัก (อันดับ 1-4):
     - อันดับ 1: +20 คะแนน
     - อันดับ 2: +15 คะแนน
     - อันดับ 3: +10 คะแนน
     - อันดับ 4: +5 คะแนน
   - ความต้องการสำรอง (อันดับ 5-8):
     - อันดับ 5: +4 คะแนน
     - อันดับ 6: +3 คะแนน
     - อันดับ 7: +2 คะแนน
     - อันดับ 8: +1 คะแนน
   - ไม่ได้เลือกไว้: -10 คะแนน

4. **ความนิยมของชมรม** (สูงสุด -10 คะแนน): ชมรมที่มีความนิยมสูงจะได้คะแนนน้อยกว่า เพื่อให้นักศึกษามีแนวโน้มจะได้ชมรมที่นิยมน้อยกว่า ลดการแข่งขัน
   - คำนวณจากสัดส่วนความนิยม: ความนิยม = จำนวนคนเลือกชมรมนี้ / จำนวนการเลือกทั้งหมด
   - หักคะแนน = ความนิยม * 10

**ตัวอย่างการคำนวณ**:

สมมติมีนักศึกษา A และ B ที่สนใจชมรมเดียวกัน:

**นักศึกษา A**:
- เป็นกลุ่มที่ยังไม่มีตัวแทน: +1000
- ได้รับจัดสรรแล้ว 2 ชมรม: -20
- ชมรมนี้เป็นความต้องการอันดับ 3: +10
- ชมรมมีความนิยม 15%: -1.5
- รวมคะแนน: 988.5

**นักศึกษา B**:
- เป็นกลุ่มที่มีตัวแทนแล้ว: +0
- ได้รับจัดสรรแล้ว 1 ชมรม: -10
- ชมรมนี้เป็นความต้องการอันดับ 1: +20
- ชมรมมีความนิยม 15%: -1.5
- รวมคะแนน: 8.5

ในกรณีนี้ นักศึกษา A จะได้รับการจัดสรรก่อนเนื่องจากมีคะแนนสูงกว่ามาก (เพราะเป็นตัวแทนกลุ่มที่ยังขาด)

#### 3.2 กระบวนการจัดสรรเมื่อชมรมมีคนเกิน 20 คน

**ขั้นตอนที่ 1: ทำความเข้าใจสถานการณ์**
```python
# ตรวจสอบว่าชมรมมีคนเกินหรือไม่
remaining_capacity = 20 - len(time_slots[period][slot][club]) # จำนวนที่ว่างเหลือ

if len(slot_preferences[club]) > remaining_capacity and remaining_capacity > 0:
    print(f"Club {club} is oversubscribed with {len(slot_preferences[club])} students")
    # เข้าสู่ขั้นตอนการจัดการเมื่อชมรมมีคนเกิน
```

**ขั้นตอนที่ 2: เรียงลำดับนักศึกษาตามคะแนน**
```python
# เก็บคะแนนของทุกคนที่สนใจชมรมนี้
candidates = []
for student_id in slot_preferences[club]:
    group = students[student_id]['group']
    represented_groups = club_groups[club] # กลุ่มที่มีตัวแทนแล้ว
    
    # คำนวณคะแนนความยุติธรรม โดยพิจารณากลุ่มที่มีตัวแทนแล้ว
    fairness_score = calculate_fairness_score(
        students[student_id], club, period, club_counts, represented_groups)
    candidates.append((student_id, fairness_score))

# เรียงลำดับตามคะแนน (สูงไปต่ำ)
candidates.sort(key=lambda x: x[1], reverse=True)
```

**ขั้นตอนที่ 3: จัดสรรนักศึกษาที่มีคะแนนสูงสุด**
```python
# เลือกนักศึกษาตามจำนวนที่ว่างเหลือ
selected_students = [c[0] for c in candidates[:remaining_capacity]]

# จัดสรรให้กับชมรม
for student_id in selected_students:
    time_slots[period][slot][club].append(student_id)
    students[student_id]['assignments'][period][slot] = club
    club_groups[club].add(students[student_id]['group']) # อัปเดตกลุ่มที่มีตัวแทนแล้ว
```

**ขั้นตอนที่ 4: จัดสรรนักศึกษาที่ถูกปฏิเสธไปยังตัวเลือกอื่น**
```python
# พยายามจัดสรรคนที่ถูกปฏิเสธไปยังชมรมสำรอง
rejected_students = [c[0] for c in candidates[remaining_capacity:]]

for student_id in rejected_students:
    # ลองจัดสรรไปยังชมรมสำรอง
    backup_prefs = students[student_id]['preferences'][period]['backup']
    assigned = False
    
    for backup_club in backup_prefs:
        if len(time_slots[period][slot][backup_club]) < 20:
            # จัดสรรไปยังชมรมสำรอง
            time_slots[period][slot][backup_club].append(student_id)
            students[student_id]['assignments'][period][slot] = backup_club
            club_groups[backup_club].add(students[student_id]['group'])
            assigned = True
            break
    
    # หากไม่สามารถจัดสรรไปยังชมรมสำรองได้ ลองจัดสรรไปยังชมรมใดๆ ที่ว่าง
    if not assigned:
        available_clubs = [club for club in clubs[period] 
                         if len(time_slots[period][slot][club]) < 20]
        if available_clubs:
            # เลือกชมรมที่มีคนน้อยที่สุด
            available_clubs.sort(key=lambda c: len(time_slots[period][slot][c]))
            chosen_club = available_clubs[0]
            
            time_slots[period][slot][chosen_club].append(student_id)
            students[student_id]['assignments'][period][slot] = chosen_club
            club_groups[chosen_club].add(students[student_id]['group'])
```

#### 3.3 กระบวนการรับประกันตัวแทนกลุ่ม

เมื่อเสร็จสิ้นการจัดสรรนักศึกษาตามความต้องการแล้ว โปรแกรมจะตรวจสอบว่าทุกกลุ่มมีตัวแทนในทุกชมรมหรือไม่:

```python
# ตรวจสอบว่าชมรมใดยังขาดตัวแทนจากกลุ่มใด
for period in ['morning', 'afternoon']:
    for club in clubs[period]:
        missing_groups = set('0123456789') - representation[period][club]
        if not missing_groups:
            continue  # ทุกกลุ่มมีตัวแทนแล้ว
        
        print(f"Club {club} ({period}) is missing students from groups: {missing_groups}")
```

สำหรับกลุ่มที่ยังไม่มีตัวแทน โปรแกรมจะดำเนินการตามลำดับดังนี้:

**1. ค้นหานักศึกษาที่มีช่องว่างในตารางเวลา:**
```python
for student_id in group_students:
    for slot in range(1, 5):
        # หากยังไม่ได้รับการจัดสรรในช่วงเวลานี้
        if slot not in students[student_id]['assignments'][period]:
            # จัดสรรให้เป็นตัวแทน
            time_slots[period][slot][club].append(student_id)
            students[student_id]['assignments'][period][slot] = club
            representation[period][club].add(group)
            assigned = True
            break
```

**2. หากนักศึกษาทุกคนในกลุ่มมีตารางเต็มแล้ว พยายามสลับจากชมรมอื่น:**
```python
for student_id in group_students:
    for slot in range(1, 5):
        # หากมีการจัดสรรในช่วงเวลานี้แล้ว
        if slot in students[student_id]['assignments'][period]:
            current_club = students[student_id]['assignments'][period][slot]
            
            # ตรวจสอบว่าชมรมปัจจุบันมีตัวแทนจากกลุ่มนี้หลายคนหรือไม่
            same_group_in_slot = [s for s in time_slots[period][slot][current_club] 
                                  if students[s]['group'] == group]
            
            if len(same_group_in_slot) > 1:
                # สลับไปยังชมรมที่ต้องการตัวแทน
                time_slots[period][slot][current_club].remove(student_id)
                time_slots[period][slot][club].append(student_id)
                students[student_id]['assignments'][period][slot] = club
                representation[period][club].add(group)
                assigned = True
                break
```

**3. หากยังไม่สามารถจัดสรรได้ ใช้วิธีบังคับสลับ:**
```python
# เลือกช่วงเวลาที่มีนักศึกษาน้อยที่สุด
slot_counts = [(slot, len(time_slots[period][slot][club])) for slot in range(1, 5)]
slot_counts.sort(key=lambda x: x[1])  # เรียงตามจำนวน
target_slot = slot_counts[0][0]  # ช่วงเวลาที่มีคนน้อยที่สุด

for student_id in group_students:
    # สลับนักศึกษาโดยไม่สนใจว่าชมรมปัจจุบันจะมีตัวแทนเหลือหรือไม่
    current_club = students[student_id]['assignments'][period][target_slot]
    
    # ดำเนินการสลับแม้ว่าชมรมจะเกิน 20 คน
    time_slots[period][target_slot][current_club].remove(student_id)
    time_slots[period][target_slot][club].append(student_id)
    students[student_id]['assignments'][period][target_slot] = club
    representation[period][club].add(group)
```

ด้วยกระบวนการ 3 ขั้นตอนนี้ โปรแกรมรับประกันว่าทุกกลุ่มจะมีตัวแทนในทุกชมรมในที่สุด แม้ว่าอาจต้องยอมให้บางชมรมมีนักศึกษาเกิน 20 คนเล็กน้อย

### 4. การสร้างผลลัพธ์และสถิติ

1. **สร้างผลลัพธ์**: จัดเรียงผลลัพธ์ตามกลุ่มของนักศึกษา
2. **วิเคราะห์สถิติ**: ทำการวิเคราะห์และแสดงสถิติเกี่ยวกับ:
   - อัตราความพึงพอใจ (ได้รับจัดสรรตามความต้องการหลัก/รอง)
   - สถิติการกระจายตัวของนักศึกษาในแต่ละชมรม
   - การกระจายตัวของตัวแทนกลุ่มในแต่ละชมรม
3. **บันทึกผลลัพธ์**: บันทึกผลลัพธ์ลงไฟล์ CSV

## คำอธิบายฟังก์ชันหลัก

### ฟังก์ชันการอ่านและการเตรียมข้อมูล

1. **read_data(file_path)**: อ่านข้อมูลจากไฟล์ CSV และแปลงเป็น DataFrame
2. **assign_groups(df)**: แบ่งกลุ่มนักศึกษาตามเลขท้ายรหัสนักศึกษา
3. **get_all_clubs(df)**: ดึงรายชื่อชมรมทั้งหมดและทำความสะอาดข้อมูล
4. **initialize_time_slots(clubs)**: สร้างโครงสร้างข้อมูลสำหรับเก็บการจัดสรร
5. **count_preferences(df)**: นับความนิยมของแต่ละชมรม
6. **create_student_preferences(df)**: สร้างข้อมูลความต้องการของนักศึกษา

### ฟังก์ชันการจัดสรรและการคำนวณ

1. **calculate_fairness_score(student, club, period, club_counts, represented_groups)**: คำนวณคะแนนความยุติธรรม
2. **assign_time_slot(students, time_slots, period, slot, club_counts, clubs)**: จัดสรรนักศึกษาในช่วงเวลาหนึ่ง
3. **ensure_group_representation(students, time_slots, clubs)**: รับประกันว่าทุกกลุ่มมีตัวแทนในทุกชมรม

### ฟังก์ชันการแสดงผลและการวิเคราะห์

1. **calculate_statistics(students, clubs)**: คำนวณสถิติเกี่ยวกับการจัดสรร
2. **calculate_detailed_statistics(students, time_slots, clubs)**: คำนวณสถิติโดยละเอียด
3. **print_statistics(stats, detailed_stats, students, clubs)**: แสดงสถิติและความสมบูรณ์ของการจัดสรร

## การใช้งานโปรแกรม

1. เตรียมไฟล์ CSV ที่มีรูปแบบตามที่กำหนด
2. ปรับแต่งตัวแปร `file_path` ในโปรแกรมให้ชี้ไปยังไฟล์ CSV
3. รันโปรแกรมด้วยคำสั่ง `python club_allocation_improved.py`
4. ผลลัพธ์จะถูกบันทึกในไฟล์ `club_assignment_results_improved.csv`

## ข้อจำกัดและข้อควรระวัง

1. **การจัดสรรที่เกิน 20 คน**: ในบางกรณี ชมรมอาจมีนักศึกษาเกิน 20 คนเล็กน้อย เพื่อให้มีตัวแทนจากทุกกลุ่ม
2. **ความขัดแย้งของเงื่อนไข**: โปรแกรมให้ความสำคัญกับการมีตัวแทนกลุ่มมากกว่าการจำกัดจำนวน 20 คน
3. **ชื่อชมรมซ้ำซ้อน**: โปรแกรมพยายามทำความสะอาดชื่อชมรมที่ซ้ำซ้อน แต่อาจมีข้อผิดพลาดหากรูปแบบแตกต่างมาก

## ตัวชี้วัดความสำเร็จ

1. **อัตราความพึงพอใจสูง**: ส่วนใหญ่ของนักศึกษาได้รับการจัดสรรตามความต้องการหลัก
2. **การกระจายตัวที่ดี**: ทุกกลุ่มมีตัวแทนในทุกชมรม
3. **จำนวนที่สมดุล**: ชมรมส่วนใหญ่มีนักศึกษาไม่เกิน 20 คน

## ผู้พัฒนา

โปรแกรมนี้พัฒนาขึ้นเพื่อจัดสรรชมรมงาน "หาชมรมที่ใช่" โดยใช้การวิเคราะห์ข้อมูลและอัลกอริทึมการจัดสรรที่เป็นธรรม
