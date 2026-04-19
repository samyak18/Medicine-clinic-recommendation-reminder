import streamlit as st
import joblib
import pymysql
from datetime import date, datetime, timedelta
from pymysql.cursors import DictCursor
import re
import json
import os

st.set_page_config(
    page_title="Medicine and clinic Recommendation",
    layout="wide"
)

@st.cache_resource(show_spinner=False)
def get_db_connection():
    try:
        return pymysql.connect(
            host="localhost",
            user="root",
            password="SamyakKumar@200418",
            database="drug_recommendation",
            autocommit=True,
            connect_timeout=5,
            cursorclass=DictCursor
        )
    except:
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                city VARCHAR(100),
                query_date DATE,
                user_input TEXT,
                detected_specialization VARCHAR(100),
                recommended_drugs TEXT
            )
            """)

def save_to_history(city, user_input, spec, drugs):
    conn = get_db_connection()
    if conn:
        try:
            conn.ping(reconnect=True)
            with conn.cursor() as cursor:
                cursor.execute("""
                INSERT INTO history (city, query_date, user_input, detected_specialization, recommended_drugs)
                VALUES (%s, %s, %s, %s, %s)
                """, (city, date.today(), user_input, spec, drugs))
        except:
            pass

class MedicineReminder:
    def __init__(self):
        self.reminders_file = "medicine_reminders.json"
        self.load_reminders()
    
    def load_reminders(self):
        if os.path.exists(self.reminders_file):
            with open(self.reminders_file, 'r') as f:
                self.reminders = json.load(f)
        else:
            self.reminders = []
    
    def save_reminders(self):
        with open(self.reminders_file, 'w') as f:
            json.dump(self.reminders, f, indent=2)
    
    def add_reminder(self, medicine_name, dosage_time, dosage_instruction, start_date, duration_days, notes="", alarm_enabled=True):
        reminder = {
            "id": len(self.reminders) + 1,
            "medicine_name": medicine_name,
            "dosage_time": dosage_time,
            "dosage_instruction": dosage_instruction,
            "start_date": start_date,
            "duration_days": duration_days,
            "notes": notes,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "taken_dates": [],
            "alarm_enabled": alarm_enabled,
            "snooze_count": 0
        }
        self.reminders.append(reminder)
        self.save_reminders()
        return reminder
    
    def mark_as_taken(self, reminder_id):
        for reminder in self.reminders:
            if reminder["id"] == reminder_id:
                today = date.today().isoformat()
                if today not in reminder["taken_dates"]:
                    reminder["taken_dates"].append(today)
                    self.save_reminders()
                    return True
        return False
    
    def delete_reminder(self, reminder_id):
        self.reminders = [r for r in self.reminders if r["id"] != reminder_id]
        self.save_reminders()
    
    def get_today_reminders(self):
        today = date.today().isoformat()
        today_reminders = []
        
        for reminder in self.reminders:
            if reminder["status"] == "active":
                start_date = datetime.fromisoformat(reminder["start_date"]).date()
                days_diff = (date.today() - start_date).days
                
                if 0 <= days_diff <= reminder["duration_days"]:
                    is_taken = today in reminder.get("taken_dates", [])
                    today_reminders.append({
                        **reminder,
                        "is_taken": is_taken,
                        "days_remaining": reminder["duration_days"] - days_diff
                    })
        
        return sorted(today_reminders, key=lambda x: x["dosage_time"])
    
    def get_all_reminders(self):
        all_reminders = []
        for reminder in self.reminders:
            if reminder["status"] == "active":
                start_date = datetime.fromisoformat(reminder["start_date"]).date()
                days_diff = (date.today() - start_date).days
                
                if 0 <= days_diff <= reminder["duration_days"]:
                    all_reminders.append(reminder)
        return all_reminders

reminder_system = MedicineReminder()

def get_reminder_schedule(symptom):
    symptom_lower = symptom.lower()
    
    reminder_schedules = {
        "fever": {
            "duration_days": 3,
            "dosage_instruction": "Take 1 tablet every 6 hours",
            "notes": "Take after meals. Drink plenty of water.",
            "reminder_times": ["09:00 AM", "03:00 PM", "09:00 PM"]
        },
        "cold": {
            "duration_days": 5,
            "dosage_instruction": "Take 1 tablet once daily at night",
            "notes": "Get adequate rest. Stay hydrated.",
            "reminder_times": ["09:00 PM"]
        },
        "cough": {
            "duration_days": 5,
            "dosage_instruction": "Take as needed for cough relief",
            "notes": "Avoid cold drinks and cold food.",
            "reminder_times": ["10:00 AM", "06:00 PM", "10:00 PM"]
        },
        "headache": {
            "duration_days": 2,
            "dosage_instruction": "Take 1 tablet when headache occurs",
            "notes": "Maximum 2 tablets in 24 hours.",
            "reminder_times": ["As needed"]
        },
        "pain": {
            "duration_days": 3,
            "dosage_instruction": "Take 1 tablet every 8 hours",
            "notes": "Take with food to avoid stomach upset.",
            "reminder_times": ["08:00 AM", "04:00 PM", "12:00 AM"]
        },
        "acne": {
            "duration_days": 10,
            "dosage_instruction": "Apply thin layer on affected area at night",
            "notes": "Clean face before application.",
            "reminder_times": ["09:00 PM"]
        },
        "rash": {
            "duration_days": 5,
            "dosage_instruction": "Apply to affected area twice daily",
            "notes": "Avoid scratching the area.",
            "reminder_times": ["08:00 AM", "08:00 PM"]
        },
        "vomit": {
            "duration_days": 2,
            "dosage_instruction": "Take 1 tablet before meals",
            "notes": "Stay hydrated with ORS solution.",
            "reminder_times": ["08:00 AM", "01:00 PM", "07:00 PM"]
        },
        "diarrhea": {
            "duration_days": 3,
            "dosage_instruction": "Take after each loose motion",
            "notes": "Drink ORS solution to prevent dehydration.",
            "reminder_times": ["As needed"]
        },
        "allergy": {
            "duration_days": 5,
            "dosage_instruction": "Take 1 tablet once daily",
            "notes": "May cause drowsiness. Avoid driving.",
            "reminder_times": ["09:00 PM"]
        },
        "anxiety": {
            "duration_days": 7,
            "dosage_instruction": "Take 1 capsule once daily",
            "notes": "Practice deep breathing exercises.",
            "reminder_times": ["08:00 AM"]
        }
    }
    
    for symptom_type, schedule in reminder_schedules.items():
        if symptom_type in symptom_lower:
            return schedule
    
    return {
        "duration_days": 3,
        "dosage_instruction": "As prescribed by doctor",
        "notes": "Consult doctor if symptoms persist.",
        "reminder_times": ["09:00 AM"]
    }

def create_auto_reminder(medicine_name, symptom, dosage_info):
    schedule = get_reminder_schedule(symptom)
    
    reminders_created = []
    
    for reminder_time in schedule["reminder_times"]:
        if reminder_time != "As needed":
            reminder = reminder_system.add_reminder(
                medicine_name=medicine_name,
                dosage_time=reminder_time,
                dosage_instruction=schedule["dosage_instruction"],
                start_date=date.today().isoformat(),
                duration_days=schedule["duration_days"],
                notes=f"{schedule['notes']} For: {symptom[:50]}",
                alarm_enabled=True
            )
            reminders_created.append(reminder)
    
    return reminders_created

def is_valid_symptom_input(text):
    if not text or len(text.strip()) < 2:
        return False
    
    symptom_keywords = [
        "fever", "cold", "cough", "headache", "pain", "ache", "sore", "throat",
        "nausea", "vomit", "diarrhea", "stomach", "acne", "pimple", "rash", "skin",
        "itch", "allergy", "anxiety", "stress", "fatigue", "weakness", "dizzy",
        "runny nose", "sneeze", "congestion", "chest", "breath", "muscle",
        "joint", "back pain", "neck pain", "toothache", "ear pain", "eye pain",
        "feverish", "chills", "sweating", "tired", "exhausted", "insomnia",
        "depression", "panic", "worry", "tension", "restless", "irritable",
        "feeling sick", "not well", "unwell", "sick", "flu", "infection",
        "burning", "swelling", "redness", "bloating", "gas", "indigestion",
        "constipation", "loose motion", "stomach ache", "belly pain",
        "body ache", "leg pain", "arm pain", "knee pain", "joint pain",
        "migraine", "sinus", "blocked nose", "watery eyes", "viral",
        "temperature", "high fever", "mild fever", "low grade fever",
        "cramps", "sprain", "strain", "injury", "wound", "cut", "burn"
    ]
    
    text_lower = text.lower()
    
    for keyword in symptom_keywords:
        if keyword in text_lower:
            return True
    
    symptom_patterns = [
        r'i have', r'i feel', r'i am', r'i\'m', r'feeling', r'suffering from',
        r'experiencing', r'getting', r'got', r'had', r'have been', r'has been'
    ]
    
    for pattern in symptom_patterns:
        if re.search(pattern, text_lower):
            return True
    
    return False

def is_random_text(text):
    if len(text) < 2:
        return True
    
    text_lower = text.lower().strip()
    
    obvious_random = [
        "asdf", "qwerty", "zxcv", "asdfgh", "qwertyui", "zxcvbn",
        "test", "testing", "random", "gibberish", "nothing", "none",
        "aaaa", "bbbb", "cccc", "dddd", "eeee", "ffff", "gggg",
        "1111", "2222", "3333", "1234", "5678", "0000"
    ]
    
    if text_lower in obvious_random:
        return True
    
    if len(set(text_lower)) == 1 and len(text_lower) >= 3:
        return True
    
    keyboard_patterns = [
        r'^[a-z]{1,2}$',
    ]
    
    for pattern in keyboard_patterns:
        if re.match(pattern, text_lower) and len(text_lower) <= 2:
            return True
    
    vowels = set('aeiou')
    if len(text_lower) >= 3 and any(v in text_lower for v in vowels):
        return False
    
    if len(text_lower) >= 4:
        return False
    
    return False

def get_symptom_specific_drugs(condition):
    text = condition.lower()
    
    drug_database = {
        "fever": [
            {"name": "Paracetamol 500mg", "type": "Antipyretic", "dosage": "Take 1 tablet every 6 hours", "note": "Not to exceed 4 tablets in 24 hours"},
            {"name": "Ibuprofen 400mg", "type": "NSAID", "dosage": "Take 1 tablet every 8 hours", "note": "Take with food"}
        ],
        "cold": [
            {"name": "Cetirizine 10mg", "type": "Antihistamine", "dosage": "Once daily", "note": "May cause drowsiness"},
            {"name": "Cold & Flu Tablet", "type": "Combination", "dosage": "Every 6 hours", "note": "Relieves multiple symptoms"}
        ],
        "cough": [
            {"name": "Dextromethorphan", "type": "Cough Suppressant", "dosage": "Every 4-6 hours", "note": "For dry cough"},
            {"name": "Guaifenesin", "type": "Expectorant", "dosage": "Every 4 hours", "note": "For wet cough with mucus"}
        ],
        "headache": [
            {"name": "Aspirin 325mg", "type": "Analgesic", "dosage": "Every 4-6 hours", "note": "Take with food"},
            {"name": "Naproxen Sodium", "type": "NSAID", "dosage": "Every 8-12 hours", "note": "For tension headaches"}
        ],
        "pain": [
            {"name": "Diclofenac", "type": "NSAID", "dosage": "Twice daily", "note": "For muscle pain"},
            {"name": "Paracetamol + Tramadol", "type": "Combination", "dosage": "Every 8 hours", "note": "For moderate pain"}
        ],
        "acne": [
            {"name": "Benzoyl Peroxide 2.5%", "type": "Topical", "dosage": "Apply once daily", "note": "Start with lower concentration"},
            {"name": "Clindamycin Gel", "type": "Antibiotic", "dosage": "Apply twice daily", "note": "For bacterial acne"}
        ],
        "rash": [
            {"name": "Hydrocortisone Cream", "type": "Corticosteroid", "dosage": "Apply twice daily", "note": "For itching and inflammation"},
            {"name": "Calamine Lotion", "type": "Soothing", "dosage": "Apply as needed", "note": "For mild rashes"}
        ],
        "vomit": [
            {"name": "Ondansetron 4mg", "type": "Anti-emetic", "dosage": "Every 8 hours", "note": "For nausea and vomiting"}
        ],
        "diarrhea": [
            {"name": "Loperamide", "type": "Anti-diarrheal", "dosage": "After each loose stool", "note": "Max 8 tablets/day"},
            {"name": "ORS Solution", "type": "Rehydration", "dosage": "After each episode", "note": "Prevents dehydration"}
        ],
        "allergy": [
            {"name": "Fexofenadine 120mg", "type": "Antihistamine", "dosage": "Once daily", "note": "Non-drowsy"}
        ],
        "anxiety": [
            {"name": "Ashwagandha", "type": "Adaptogen", "dosage": "Once daily", "note": "Natural stress reliever"}
        ]
    }
    
    all_drugs = []
    matched_symptom = None
    
    for symptom, drugs in drug_database.items():
        if symptom in text:
            all_drugs.extend(drugs)
            matched_symptom = symptom
            break
    
    if not all_drugs:
        return [], None
    
    unique_drugs = []
    drug_names_seen = set()
    for drug in all_drugs:
        if drug["name"] not in drug_names_seen:
            drug_names_seen.add(drug["name"])
            unique_drugs.append(drug)
    
    return unique_drugs[:3], matched_symptom

def predict_top_drugs(condition):
    if is_random_text(condition) or not is_valid_symptom_input(condition):
        return [], None
    
    drug_list, matched_symptom = get_symptom_specific_drugs(condition)
    
    if not drug_list:
        return [], None
    
    return [(drug["name"], drug, 0.95 - (i * 0.1)) for i, drug in enumerate(drug_list)], matched_symptom

@st.cache_data(show_spinner=False)
def get_clinic_data():
    return {
        "Mumbai": {
            "Dermatology": [
                "SkinGlow Mumbai - Colaba | Contact: 022-44444444", 
                "DermaPlus - Andheri | Contact: 022-55555555"
            ],
            "Pediatrics": [
                "KidsCare Mumbai - Santacruz | Contact: 022-40404040", 
                "HappyChild - Powai | Contact: 022-50505050"
            ],
            "Mental Health": [
                "MindCare Mumbai - Dadar | Contact: 022-77777777", 
                "CalmLife - Andheri | Contact: 022-88888888"
            ],
            "General Medicine": [
                "CityCare Mumbai - Borivali | Contact: 022-10101010", 
                "HealthFirst - Thane | Contact: 022-20202020"
            ],
            "Gastroenterology": [
                "StomachCare Mumbai - Andheri | Contact: 022-30303030",
                "DigestWell - Bandra | Contact: 022-31313131"
            ]
        },
        "Bangalore": {
            "Dermatology": [
                "SkinGlow BLR - Koramangala | Contact: 080-44444444", 
                "DermaPlus - Indiranagar | Contact: 080-55555555"
            ],
            "Pediatrics": [
                "KidsCare BLR - Indiranagar | Contact: 080-40404040", 
                "HappyChild - BTM | Contact: 080-50505050"
            ],
            "Mental Health": [
                "MindCare BLR - BTM | Contact: 080-77777777", 
                "CalmLife - JP Nagar | Contact: 080-88888888"
            ],
            "General Medicine": [
                "CityCare BLR - Hebbal | Contact: 080-10101010", 
                "HealthFirst - Marathahalli | Contact: 080-20202020"
            ],
            "Gastroenterology": [
                "StomachCare BLR - Indiranagar | Contact: 080-30303030",
                "DigestWell - Koramangala | Contact: 080-31313131"
            ]
        },
        "Delhi": {
            "Dermatology": [
                "SkinGlow Delhi - GK | Contact: 011-44444444", 
                "DermaPlus - Rajouri | Contact: 011-55555555"
            ],
            "Pediatrics": [
                "KidsCare Delhi - Saket | Contact: 011-40404040", 
                "HappyChild - Rohini | Contact: 011-50505050"
            ],
            "Mental Health": [
                "MindCare Delhi - Lajpat | Contact: 011-77777777", 
                "CalmLife - Rohini | Contact: 011-88888888"
            ],
            "General Medicine": [
                "CityCare Delhi - CP | Contact: 011-10101010", 
                "HealthFirst - Karol Bagh | Contact: 011-20202020"
            ],
            "Gastroenterology": [
                "StomachCare Delhi - Saket | Contact: 011-30303030",
                "DigestWell - Rohini | Contact: 011-31313131"
            ]
        },
        "Chennai": {
            "Dermatology": [
                "SkinGlow Chennai - Adyar | Contact: 044-44444444", 
                "DermaPlus - T Nagar | Contact: 044-55555555"
            ],
            "Pediatrics": [
                "KidsCare Chennai - T Nagar | Contact: 044-40404040", 
                "HappyChild - Velachery | Contact: 044-50505050"
            ],
            "Mental Health": [
                "MindCare Chennai - Egmore | Contact: 044-77777777", 
                "CalmLife - Velachery | Contact: 044-88888888"
            ],
            "General Medicine": [
                "CityCare Chennai - Porur | Contact: 044-10101010", 
                "HealthFirst - OMR | Contact: 044-20202020"
            ],
            "Gastroenterology": [
                "StomachCare Chennai - T Nagar | Contact: 044-30303030",
                "DigestWell - Adyar | Contact: 044-31313131"
            ]
        },
        "Hyderabad": {
            "Dermatology": [
                "SkinGlow Hyd - Jubilee Hills | Contact: 040-44444444", 
                "DermaPlus - Kondapur | Contact: 040-55555555"
            ],
            "Pediatrics": [
                "KidsCare Hyd - Banjara Hills | Contact: 040-40404040", 
                "HappyChild - Kukatpally | Contact: 040-50505050"
            ],
            "Mental Health": [
                "MindCare Hyd - Begumpet | Contact: 040-77777777", 
                "CalmLife - Ameerpet | Contact: 040-88888888"
            ],
            "General Medicine": [
                "CityCare Hyd - Kukatpally | Contact: 040-10101010", 
                "HealthFirst - LB Nagar | Contact: 040-20202020"
            ],
            "Gastroenterology": [
                "StomachCare Hyd - Banjara Hills | Contact: 040-30303030",
                "DigestWell - Jubilee Hills | Contact: 040-31313131"
            ]
        },
        "Pune": {
            "Dermatology": [
                "SkinGlow Pune - FC Road | Contact: 020-44444444", 
                "DermaPlus - Camp | Contact: 020-55555555"
            ],
            "Pediatrics": [
                "KidsCare Pune - Wakad | Contact: 020-40404040", 
                "HappyChild - Katraj | Contact: 020-50505050"
            ],
            "Mental Health": [
                "MindCare Pune - Camp | Contact: 020-77777777", 
                "CalmLife - Hadapsar | Contact: 020-88888888"
            ],
            "General Medicine": [
                "CityCare Pune - Pimpri | Contact: 020-10101010", 
                "HealthFirst - Aundh | Contact: 020-20202020"
            ],
            "Gastroenterology": [
                "StomachCare Pune - Shivajinagar | Contact: 020-30303030",
                "DigestWell - Kothrud | Contact: 020-31313131"
            ]
        },
        "Kolkata": {
            "Dermatology": [
                "SkinGlow Kol - Ballygunge | Contact: 033-44444444", 
                "DermaPlus - Park Street | Contact: 033-55555555"
            ],
            "Pediatrics": [
                "KidsCare Kol - Dumdum | Contact: 033-40404040", 
                "HappyChild - Howrah | Contact: 033-50505050"
            ],
            "Mental Health": [
                "MindCare Kol - Dumdum | Contact: 033-77777777", 
                "CalmLife - Howrah | Contact: 033-88888888"
            ],
            "General Medicine": [
                "CityCare Kol - Salt Lake | Contact: 033-10101010", 
                "HealthFirst - Howrah | Contact: 033-20202020"
            ],
            "Gastroenterology": [
                "StomachCare Kol - Salt Lake | Contact: 033-30303030",
                "DigestWell - Howrah | Contact: 033-31313131"
            ]
        }
    }

def get_specialization(condition):
    cond = condition.lower()
    
    if any(x in cond for x in ["acne", "pimple", "rash", "skin", "itch", "allergy"]):
        return "Dermatology"
    if any(x in cond for x in ["fever", "cold", "cough", "flu", "viral", "temperature", "chills", "sweating"]):
        return "General Medicine"
    if any(x in cond for x in ["headache", "migraine", "pain", "ache", "body ache", "muscle pain", "joint pain"]):
        return "General Medicine"
    if any(x in cond for x in ["vomit", "nausea", "diarrhea", "stomach", "loose motion", "indigestion", "bloating", "gas"]):
        return "Gastroenterology"
    if any(x in cond for x in ["anxiety", "stress", "depress", "mental", "panic", "worry", "tension", "insomnia"]):
        return "Mental Health"
    if any(x in cond for x in ["child", "baby", "pediatric", "kids"]):
        return "Pediatrics"
    
    return "General Medicine"

def display_reminder_status():
    today_reminders = reminder_system.get_today_reminders()
    pending = [r for r in today_reminders if not r.get('is_taken', False)]
    
    if pending:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Today's Reminders")
        for reminder in pending[:3]:
            st.sidebar.markdown(f"**{reminder['medicine_name']}**")
            st.sidebar.markdown(f"  {reminder['dosage_time']}")
        if len(pending) > 3:
            st.sidebar.markdown(f"... and {len(pending)-3} more")

def medicine_reminder_page():
    st.markdown("# Medicine Reminder Dashboard")
    st.markdown("Manage all your automated medicine reminders here.")
    
    st.markdown("---")
    
    st.subheader("Today's Schedule")
    today_reminders = reminder_system.get_today_reminders()
    
    if today_reminders:
        for reminder in today_reminders:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**{reminder['medicine_name']}**")
                    if reminder['notes']:
                        st.caption(reminder['notes'][:50])
                
                with col2:
                    st.markdown(f"**{reminder['dosage_time']}**")
                    st.markdown(f"{reminder['dosage_instruction']}")
                
                with col3:
                    if reminder['is_taken']:
                        st.success("Taken Today")
                    else:
                        st.warning(" Pending")
                    st.caption(f"{reminder['days_remaining']} days remaining")
                
                with col4:
                    if not reminder['is_taken']:
                        if st.button(f"Mark Taken", key=f"take_{reminder['id']}"):
                            if reminder_system.mark_as_taken(reminder['id']):
                                st.success(f"✓ Marked {reminder['medicine_name']} as taken!")
                                st.rerun()
                    
                    if st.button(f"Delete", key=f"delete_{reminder['id']}"):
                        reminder_system.delete_reminder(reminder['id'])
                        st.warning(f"Reminder for {reminder['medicine_name']} deleted!")
                        st.rerun()
                
                st.divider()
    else:
        st.info("No reminders scheduled for today. When you analyze symptoms, reminders will be automatically created!")
    
    st.markdown("---")
    
    st.subheader("All Active Reminders")
    all_reminders = reminder_system.get_all_reminders()
    
    if all_reminders:
        reminders_by_medicine = {}
        for reminder in all_reminders:
            med_name = reminder['medicine_name']
            if med_name not in reminders_by_medicine:
                reminders_by_medicine[med_name] = []
            reminders_by_medicine[med_name].append(reminder)
        
        for medicine, reminders in reminders_by_medicine.items():
            with st.expander(f"{medicine} ({len(reminders)} reminder(s))"):
                for reminder in reminders:
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.write(f"**{reminder['dosage_time']}**")
                        st.write(f"{reminder['dosage_instruction']}")
                    with col2:
                        st.write(f"Started: {reminder['start_date']}")
                        st.write(f"Duration: {reminder['duration_days']} days")
                    with col3:
                        if st.button(f"Delete", key=f"del_all_{reminder['id']}"):
                            reminder_system.delete_reminder(reminder['id'])
                            st.rerun()
                    st.write(f"Note: {reminder['notes']}")
                    st.divider()
    else:
        st.info("No active reminders. Analyze symptoms on the Home page to create automatic reminders!")
    
    st.markdown("---")
    
    with st.expander("About Auto-Reminders"):
        st.markdown("""
        **How Auto-Reminders Work:**
        
        When you enter your symptoms on the Home page or AI Assistant, the system automatically creates reminders based on your condition:
        
        - **Fever** → 3 reminders daily (morning, afternoon, night) for 3 days
        - **Cold** → 1 reminder at night for 5 days
        - **Cough** → 3 reminders daily for 5 days
        - **Headache** → As needed for 2 days
        - **Pain** → 3 reminders daily for 3 days
        - **Acne** → 1 reminder at night for 10 days
        - **Rash** → 2 reminders daily for 5 days
        - **Allergy** → 1 reminder at night for 5 days
        - **Anxiety** → 1 reminder in morning for 7 days
        
        **How to Use:**
        1. Enter your symptoms on the Home page
        2. System recommends medicines and creates reminders
        3. Check this page daily to mark medicines as taken
        4. Reminders will appear in your sidebar
        
        **Note:** Always consult a doctor before taking any medication.
        """)

def main():
    init_db()
    CLINIC_DATA = get_clinic_data()

    if 'city' not in st.session_state:
        st.session_state.city = "Mumbai"

    if 'current_user_msg' not in st.session_state:
        st.session_state.current_user_msg = None
    if 'current_assistant_msg' not in st.session_state:
        st.session_state.current_assistant_msg = None
    if 'auto_reminders_created' not in st.session_state:
        st.session_state.auto_reminders_created = []
    
    st.sidebar.markdown("## Navigation")
    page = st.sidebar.radio("", ["Home", "AI Assistant", "Medicine Reminder", "About", "Contact"])
    st.session_state.city = st.sidebar.selectbox("Select City", list(CLINIC_DATA.keys()))
    
    st.sidebar.markdown("---")
    st.sidebar.info("For medical advice, consult a doctor")
    
    display_reminder_status()

    if page == "Home":
        st.markdown("# Symptom Analysis")
        st.markdown("Enter your symptoms below to get medicine recommendations with automatic reminders.")
        
        condition = st.text_area("Symptoms", height=100, 
                                placeholder="Example: I have fever and headache")
        
        col1, col2 = st.columns([1, 5])
        with col1:
            analyze = st.button("Analyze", type="primary")
        
        if analyze:
            if not condition or not condition.strip():
                st.warning("Please enter your symptoms.")
            else:
                if is_random_text(condition):
                    st.warning("Please enter valid symptoms. I couldn't recognize your input.")
                elif not is_valid_symptom_input(condition):
                    st.warning("Please describe your symptoms clearly. Example: I have fever and headache")
                else:
                    spec = get_specialization(condition)
                    drugs, matched_symptom = predict_top_drugs(condition)
                    
                    if drugs:
                        drug_names = ', '.join([d[0] for d in drugs])
                        save_to_history(st.session_state.city, condition, spec, drug_names)
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Recommended Medicines")
                            for drug_name, drug_info, confidence in drugs:
                                with st.expander(drug_name):
                                    st.write(f"**Type:** {drug_info['type']}")
                                    st.write(f"**Dosage:** {drug_info['dosage']}")
                                    st.write(f"**Note:** {drug_info['note']}")
                                    st.progress(confidence, text=f"Confidence: {int(confidence*100)}%")
                            
                            st.caption("Please consult a doctor before taking any medication")
                        
                        with col2:
                            st.subheader(f"{spec} Specialists in {st.session_state.city}")
                            if spec in CLINIC_DATA[st.session_state.city]:
                                for clinic in CLINIC_DATA[st.session_state.city][spec]:
                                    st.info(clinic)
                            else:
                                for clinic in CLINIC_DATA[st.session_state.city]["General Medicine"]:
                                    st.info(clinic)
                        
                        st.markdown("---")
                        st.subheader("Auto-Created Medicine Reminders")
                        
                        reminders_created = []
                        for drug_name, drug_info, confidence in drugs:
                            reminders = create_auto_reminder(drug_name, condition, drug_info['dosage'])
                            reminders_created.extend(reminders)
                            st.session_state.auto_reminders_created.append({
                                "medicine": drug_name,
                                "symptom": condition[:50]
                            })
                        
                        if reminders_created:
                            st.success(f"{len(reminders_created)} reminder(s) automatically created for your medicines!")
                            
                            for reminder in reminders_created:
                                st.info(f"{reminder['medicine_name']} - {reminder['dosage_time']} - {reminder['dosage_instruction']}")
                            
                            st.caption("Reminders will appear in your sidebar. Visit Medicine Reminder page to manage them.")
                        else:
                            st.info("No reminders created for this symptom.")
                    else:
                        st.info("No matching medicines found. Please consult a doctor for proper diagnosis.")

    elif page == "AI Assistant":
        st.markdown("# AI Health Assistant")
        st.markdown("Describe your symptoms in natural language. I'll recommend medicines and create reminders for you.")
        
        for msg in st.session_state.get('messages', []):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        if prompt := st.chat_input("Describe your symptoms..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            
            if is_random_text(prompt):
                response = "I couldn't understand your input. Please describe your symptoms clearly."
            elif not is_valid_symptom_input(prompt):
                response = "Please describe your symptoms. For example: I have a fever and headache."
            else:
                spec = get_specialization(prompt)
                drugs, matched_symptom = predict_top_drugs(prompt)
                
                if drugs:
                    drug_names = ', '.join([d[0] for d in drugs])
                    save_to_history(st.session_state.city, prompt, spec, drug_names)
                    
                    response = f"**Detected:** {spec}\n\n"
                    response += f"**Recommended Medicines:**\n\n"
                    
                    for drug_name, drug_info, confidence in drugs:
                        response += f"• **{drug_name}**\n"
                        response += f"  - **Type:** {drug_info['type']}\n"
                        response += f"  - **Dosage:** {drug_info['dosage']}\n"
                        response += f"  - **Note:** {drug_info['note']}\n\n"
                    
                    response += f"**{spec} Specialists in {st.session_state.city} (with contact numbers):**\n"
                    if spec in CLINIC_DATA[st.session_state.city]:
                        for clinic in CLINIC_DATA[st.session_state.city][spec]:
                            response += f"• {clinic}\n"
                    else:
                        for clinic in CLINIC_DATA[st.session_state.city]["General Medicine"]:
                            response += f"• {clinic}\n"
                    
                    reminders_created = []
                    for drug_name, drug_info, confidence in drugs:
                        reminders = create_auto_reminder(drug_name, prompt, drug_info['dosage'])
                        reminders_created.extend(reminders)
                    
                    if reminders_created:
                        response += f"\n\n---\n"
                        response += f"## Auto-Created Reminders\n\n"
                        response += f"Based on your symptoms, the following reminders have been automatically created:\n\n"
                        
                        for i, reminder in enumerate(reminders_created, 1):
                            response += f"**Reminder {i}:**\n"
                            response += f"- **Medicine:** {reminder['medicine_name']}\n"
                            response += f"- **Time:** {reminder['dosage_time']}\n"
                            response += f"- **Instruction:** {reminder['dosage_instruction']}\n"
                            response += f"- **Duration:** {reminder['duration_days']} days\n"
                            response += f"- **Note:** {reminder['notes']}\n\n"
                        
                        response += f"---\n"
                        response += f"*Reminders have been saved to your account. You can view and manage them in the **Medicine Reminder** page.*\n\n"
                    
                    response += "\n*Please consult a doctor before taking any medication.*"
                else:
                    response = "No matching medicines found. Please consult a doctor for proper diagnosis."
            
            with st.chat_message("assistant"):
                st.markdown(response)
            
            st.session_state.messages = [{"role": "user", "content": prompt}, {"role": "assistant", "content": response}]
    
    elif page == "Medicine Reminder":
        medicine_reminder_page()
    
    elif page == "About":
        st.markdown("# About")
        
        st.markdown("""
        ### Automated medicine and clinic recommendation system
        
        This system provides medicine recommendations for common symptoms and **automatically creates reminders** for your medications.
        
        **What this system does:**
        - Matches symptoms to common medicines
        - Provides dosage information
        - Recommends nearby clinics with contact numbers by city
        - Automatically creates medicine reminders based on your symptoms
        - Different symptoms get different reminder schedules
        - Dedicated Medicine Reminder page to manage all your reminders
        
        **Auto-Reminder Schedules by Symptom:**
        - **Fever:** 3 reminders daily (morning, afternoon, night) for 3 days
        - **Cold:** 1 reminder at night for 5 days
        - **Cough:** 3 reminders daily for 5 days
        - **Headache:** As needed for 2 days
        - **Pain:** 3 reminders daily for 3 days
        - **Acne:** 1 reminder at night for 10 days
        - **Rash:** 2 reminders daily for 5 days
        - **Allergy:** 1 reminder at night for 5 days
        - **Anxiety:** 1 reminder in morning for 7 days
        
        **Features:**
        - Mark medicines as taken
        - Delete unwanted reminders
        - View all active reminders
        - Sidebar shows today's pending reminders
        - Reminders organized by medicine
        
        **What this system does NOT do:**
        - Does NOT handle medical emergencies
        - Does NOT replace professional medical advice
        - Does NOT respond to random or invalid inputs
        
        **Always consult a doctor before taking any medication.**
        """)
    
    else:  
        st.markdown("# Contact & Emergency Directory")
        
        st.markdown("---")
        
        st.subheader("Emergency Numbers")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Ambulance:** 102")
            st.markdown("**Police:** 100")
            st.markdown("**Fire:** 101")
        with col2:
            st.markdown("**National Emergency:** 112")
            st.markdown("**Women Helpline:** 1091")
            st.markdown("**Child Helpline:** 1098")
        
        st.markdown("---")
        
        st.subheader(f"Hospital Contact Numbers in {st.session_state.city}")
        
        for specialization, clinics in CLINIC_DATA[st.session_state.city].items():
            with st.expander(f"{specialization}"):
                for clinic in clinics:
                    st.write(clinic)
        
        st.markdown("---")
        
        st.subheader("Emergency Services")
        
        with st.container():
            st.markdown("""
            **When to Call an Ambulance (102):**
            - Chest pain or difficulty breathing
            - Unconsciousness or fainting
            - Severe bleeding or head injury
            - Seizures or fitting
            - Sudden severe pain
            - Stroke symptoms (face drooping, arm weakness, speech difficulty)
            - Major trauma or accident
            
            **Information to Provide:**
            - Your exact location (address with landmarks)
            - What happened
            - Condition of the patient (conscious/breathing/bleeding)
            - Any known medical conditions
            - Phone number you're calling from
            """)
        
        st.markdown("---")
        
        st.warning("""
        **Important:** 
        - This system is for informational purposes only
        - Professional medical help is essential for serious conditions
        """)

if __name__ == "__main__":
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    main()