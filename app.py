import os
import json
import time
import warnings
import requests
import sqlite3
from datetime import datetime

import pymysql
import google.generativeai as genai
import werkzeug.utils
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_cors import CORS
from groq import Groq
from werkzeug.security import check_password_hash, generate_password_hash

warnings.filterwarnings("ignore", category=FutureWarning)

load_dotenv(override=True)
print(f"DEBUG: PAYMOB_API_KEY loaded: {bool(os.getenv('PAYMOB_API_KEY'))}")

app = Flask(__name__)
app.secret_key = "edyguide-premium-secret"
CORS(app)

# AI Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = None
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("DEBUG: Gemini API configured.")
else:
    print("DEBUG: Gemini API key NOT found.")

if GROQ_API_KEY:
    print("DEBUG: Groq API client initialized.")
else:
    print("DEBUG: Groq API key NOT found.")

def get_db():
    try:
        # Try MySQL (for production/render if configured)
        host = os.getenv("DB_HOST")
        if host:
            return pymysql.connect(
                host=host,
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASS", ""),
                database=os.getenv("DB_NAME", "edyguide1"),
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
    except:
        pass
        
    # Fallback to local SQLite for zero-config demo
    db = sqlite3.connect('eduguide1.db')
    db.row_factory = sqlite3.Row
    # Monkey-patch cursor to match pymysql interface if needed
    return db
 
@app.context_processor
def inject_notifications():
    if 'user_id' in session:
        user_id = session['user_id']
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Map student_id (string) to numeric internal ID
            cursor.execute("SELECT id FROM users WHERE student_code=%s", (user_id,))
            local_user = cursor.fetchone()
            numeric_id = local_user['id'] if local_user else None
            
            if numeric_id:
                cursor.execute("SELECT title, message, created_at FROM notifications WHERE user_id=%s ORDER BY created_at DESC LIMIT 5", (numeric_id,))
                notifs = cursor.fetchall()
                db.close()
                return dict(notifications=notifs)
            db.close()
        except Exception as e:
            print(f"Notification context error: {e}")
    return dict(notifications=[])


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = (request.form.get("identifier") or request.form.get("email") or "").strip()
        password = (request.form.get("password") or "").strip()
        selected_role = request.form.get("role", "student")  # student | instructor | system

        db = get_db()
        cursor = db.cursor()

        # ============================================================
        # ROLE: SYSTEM (system_users table)
        # ============================================================
        if selected_role == "system":
            cursor.execute(
                "SELECT * FROM system_users WHERE email=%s OR username=%s",
                (identifier, identifier)
            )
            sys_user = cursor.fetchone()
            if sys_user and (sys_user['password'] == password or check_password_hash(sys_user['password'], password)):
                session['role'] = 'system'
                session['name'] = sys_user['full_name']
                session['user_id'] = f"sys_{sys_user['id']}"
                db.close()
                return redirect(url_for("system_dashboard"))
            db.close()
            flash("Invalid system credentials.", "danger")
            return render_template("login.html")

        # ============================================================
        # ROLE: INSTRUCTOR (admins table with role='instructor')
        # ============================================================
        if selected_role == "instructor":
            cursor.execute(
                "SELECT * FROM admins WHERE (email=%s OR username=%s) AND (role='instructor' OR role IS NULL)",
                (identifier, identifier)
            )
            instructor = cursor.fetchone()
            if not instructor:
                # Also try FacUsers + Instructors tables
                cursor.execute("SELECT * FROM FacUsers WHERE email=%s OR user_id=%s", (identifier, identifier))
                fac_user = cursor.fetchone()
                if fac_user and (fac_user['password'] == password or check_password_hash(fac_user['password'], password)):
                    cursor.execute("SELECT * FROM Instructors WHERE instructor_id=%s OR email=%s", (fac_user['user_id'], identifier))
                    instructor_row = cursor.fetchone()
                    if instructor_row:
                        session['role'] = 'instructor'
                        session['name'] = f"{instructor_row['first_name']} {instructor_row['last_name']}"
                        session['admin_name'] = session['name']
                        session['user_id'] = fac_user['user_id']
                        db.close()
                        return redirect(url_for("admin_dashboard"))
                db.close()
                flash("Instructor account not found.", "danger")
                return render_template("login.html")

            if instructor and (instructor['password'] == password or check_password_hash(instructor['password'], password)):
                session['role'] = 'instructor'
                session['name'] = instructor['full_name']
                session['admin_name'] = instructor['full_name']
                session['user_id'] = f"ins_{instructor['id']}"
                db.close()
                return redirect(url_for("admin_dashboard"))
            db.close()
            flash("Invalid instructor credentials.", "danger")
            return render_template("login.html")

        # ============================================================
        # ROLE: STUDENT (users table or FacUsers+Students)
        # ============================================================
        # Try local users table first
        cursor.execute(
            "SELECT * FROM users WHERE email=%s OR student_code=%s",
            (identifier, identifier)
        )
        local_user = cursor.fetchone()
        if local_user and (local_user['password'] == password or check_password_hash(local_user['password'], password)):
            session['role'] = 'student'
            session['name'] = local_user['full_name']
            session['user_id'] = local_user['student_code']
            session['profile_pic'] = local_user.get('profile_pic', '')
            db.close()
            return redirect(url_for("dashboard"))

        # Try FacUsers + Students
        cursor.execute("SELECT * FROM FacUsers WHERE email=%s OR user_id=%s", (identifier, identifier))
        fac_user = cursor.fetchone()
        if fac_user and (fac_user['password'] == password or check_password_hash(fac_user['password'], password)):
            cursor.execute("SELECT * FROM Students WHERE student_id=%s", (fac_user['user_id'],))
            student = cursor.fetchone()
            if student:
                session['role'] = 'student'
                session['name'] = f"{student['first_name']} {student['last_name']}"
                session['user_id'] = fac_user['user_id']
                db.close()
                return redirect(url_for("dashboard"))

        db.close()
        flash("Invalid email or password.", "danger")

    return render_template("login.html")





@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session: return redirect(url_for("login"))
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    # Map student_id (string) to numeric internal ID from users table
    cursor.execute("SELECT id FROM users WHERE student_code=%s", (user_id,))
    local_user = cursor.fetchone()
    numeric_id = local_user['id'] if local_user else None
    
    # Profile
    cursor.execute("SELECT * FROM vw_StudentProfile WHERE student_id=%s", (user_id,))
    user = cursor.fetchone()
    if user:
        user['student_code'] = user['student_id']
        user['faculty'] = user['department']
        user['level'] = user['year_level']
    
    # Schedules
    cursor.execute("SELECT * FROM schedules WHERE user_id=%s", (numeric_id,))
    schedules = cursor.fetchall()
    
    # Exams
    cursor.execute("SELECT * FROM exams WHERE user_id=%s", (numeric_id,))
    exams = cursor.fetchall()
    
    # Payment
    cursor.execute("SELECT * FROM payments WHERE user_id=%s ORDER BY id DESC LIMIT 1", (numeric_id,))
    payment = cursor.fetchone()
    
    # Reminder
    cursor.execute("SELECT * FROM reminders WHERE user_id=%s LIMIT 1", (numeric_id,))
    reminder = cursor.fetchone()
    
    db.close()
    return render_template("dashboard.html", user=user, schedules=schedules, exams=exams, payment=payment, reminder=reminder)


GEMINI_MODEL_NAME = "gemini-1.5-flash"

def ask_gemini(prompt: str) -> str:
    try:
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = model.generate_content(prompt)
        if hasattr(response, "text") and response.text:
            return response.text.strip()
        return "No response from AI."
    except Exception as e:
        error_text = str(e).lower()
        if "429" in error_text or "quota" in error_text or "limit" in error_text:
            return "__QUOTA__"
        print(f"Gemini API Error: {e}")
        return "__ERROR__"

# Global Cache
UNIVERSITY_INFO_CACHE = None

def build_context(cursor, user_id) -> str:
    global UNIVERSITY_INFO_CACHE
    
    # Mapping
    cursor.execute("SELECT id FROM users WHERE student_code=%s", (user_id,))
    l_u = cursor.fetchone()
    n_id = l_u['id'] if l_u else None

    cursor.execute("SELECT * FROM vw_StudentProfile WHERE student_id=%s", (user_id,))
    user = cursor.fetchone() or {}
    
    cursor.execute("SELECT * FROM schedules WHERE user_id=%s ORDER BY id ASC LIMIT 6", (n_id,))
    schedules = cursor.fetchall()
    
    cursor.execute("SELECT * FROM exams WHERE user_id=%s ORDER BY exam_date ASC LIMIT 6", (n_id,))
    exams = cursor.fetchall()
    
    cursor.execute("SELECT *, amount_egp as amount, payment_method as payment_type FROM vw_PaymentSummary WHERE student_id=%s ORDER BY payment_id DESC LIMIT 3", (user_id,))
    payments = cursor.fetchall()

    # Student Requests
    cursor.execute("SELECT title, message, status, created_at FROM student_requests WHERE user_id=%s ORDER BY created_at DESC LIMIT 3", (n_id,))
    reqs = cursor.fetchall()
    
    # Notifications
    cursor.execute("SELECT title, message, created_at FROM notifications WHERE user_id=%s ORDER BY created_at DESC LIMIT 3", (n_id,))
    notifs = cursor.fetchall()

    # Personal Notes
    cursor.execute("SELECT title, content, category FROM student_notes WHERE user_id=%s ORDER BY created_at DESC LIMIT 5", (n_id,))
    notes = cursor.fetchall()

    # Get University Knowledge Base (Cached)
    if UNIVERSITY_INFO_CACHE is None:
        cursor.execute("SELECT category, answer FROM university_info")
        u_rows = cursor.fetchall()
        UNIVERSITY_INFO_CACHE = "\n".join([f"[{r['category']}]: {r['answer']}" for r in u_rows])
    
    u_info_text = UNIVERSITY_INFO_CACHE
    
    return f"""You are EDYGUIDE AI — a smart, friendly, and extremely helpful AI assistant for Egyptian university students. You talk like a close friend: warm, authentic, and direct.

GUIDELINES:
1. Always refer to yourself as EDYGUIDE AI.
2. Be conversational and friendly. If the student chats casually, chat back warmly in Egyptian Arabic or English as appropriate.
3. Provide concise but complete answers. Don't be too brief if the question needs detail.
4. For schedules/exams: summarize the most important upcoming items first.
5. Match the student's language and tone (Arabic/English/Mix).
6. Sound human and supportive — like a mentor or a close friend.

STUDENT DATA (use ONLY when directly relevant):
- Name: {user.get('full_name', 'Student')}
- GPA: {user.get('gpa', 'N/A')} | Dept: {user.get('department', 'N/A')} | Year: {user.get('year_level', 'N/A')}
- Schedule: {schedules if schedules else 'None'}
- Exams: {exams if exams else 'None'}
- Payments: {payments if payments else 'None'}
- Latest Notes: {notes if notes else 'None'}
- Notifications: {notifs if notifs else 'None'}

UNIVERSITY INFO:
{u_info_text}

Date: {datetime.now().strftime('%A, %d %B %Y')}""".strip()

ARABIC_HINTS = ["ا", "ب", "ت", "ث", "ج", "ح", "خ", "د", "ذ", "ر", "ز", "س", "ش", "ص", "ض", "ط", "ظ", "ع", "غ", "ف", "ق", "ك", "ل", "م", "ن", "ه", "و", "ي", "ة"]

def is_arabic_text(text: str) -> bool:
    return any(ch in text for ch in ARABIC_HINTS)

STOP_WORDS = {"how", "are", "you", "the", "a", "an", "is", "it", "to", "in", "of", "and", "or", "for", "with", "on", "at", "by", "from"}

def get_university_answer(cursor, message: str):
    try:
        cursor.execute("SELECT category, keywords, answer FROM university_info")
        rows = cursor.fetchall()
        msg_words = set(message.lower().strip().split())
        best_answer = None
        best_score = 0
        for row in rows:
            keywords = set((row.get("keywords") or "").lower().split())
            # Intersection of message words and keywords, excluding stop words
            matches = (msg_words & keywords) - STOP_WORDS
            score = len(matches)
            if score > best_score:
                best_score = score
                best_answer = row["answer"]
        if best_score >= 1:
            return best_answer
    except:
        pass
    return None

@app.route("/schedule")
def schedule_page():
    if 'user_id' not in session: return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE student_code=%s", (session['user_id'],))
    nid = cursor.fetchone()['id']
    cursor.execute("SELECT * FROM schedules WHERE user_id=%s", (nid,))
    schedules = cursor.fetchall()
    db.close()
    return render_template("schedule.html", schedules=schedules)

@app.route("/exams")
def exams_page():
    if 'user_id' not in session: return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE student_code=%s", (session['user_id'],))
    nid = cursor.fetchone()['id']
    cursor.execute("SELECT * FROM exams WHERE user_id=%s", (nid,))
    exams = cursor.fetchall()
    db.close()
    return render_template("exams.html", exams=exams)

@app.route("/payments")
def payments_page():
    if 'user_id' not in session: return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    
    # Map student_code to numeric ID
    cursor.execute("SELECT id FROM users WHERE student_code=%s", (session['user_id'],))
    local_user = cursor.fetchone()
    nid = local_user['id'] if local_user else None
    
    if nid:
        cursor.execute("SELECT * FROM payments WHERE user_id=%s ORDER BY id DESC", (nid,))
        payments = cursor.fetchall()
    else:
        payments = []
        
    db.close()
    return render_template("payments.html", payments=payments)

@app.route("/chat")
def chat_page():
    if 'user_id' not in session: return redirect(url_for("login"))
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    # Map student_code to numeric ID
    cursor.execute("SELECT id, full_name, email FROM users WHERE student_code=%s", (user_id,))
    local_user = cursor.fetchone()
    
    cursor.execute("SELECT * FROM vw_StudentProfile WHERE student_id=%s", (user_id,))
    user_profile = cursor.fetchone()
    db.close()
    
    user_data = {}
    if local_user:
        user_data['id'] = local_user['id']
        user_data['full_name'] = local_user['full_name']
    elif user_profile:
        user_data['full_name'] = f"{user_profile.get('first_name','')} {user_profile.get('last_name','')}".strip()
        user_data['id'] = 0 # Fallback
    else:
        user_data['full_name'] = "Student"
        user_data['id'] = 0
        
    return render_template("chat.html", user=user_data)

@app.route("/chat/history", methods=["GET"])
def get_chat():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE student_code=%s", (user_id,))
        l_u = cursor.fetchone()
        n_id = l_u['id'] if l_u else None
        if n_id:
            cursor.execute("SELECT sender, message, created_at FROM chatbot_messages WHERE user_id = %s ORDER BY created_at ASC, id ASC", (n_id,))
            chat = cursor.fetchall()
        else:
            chat = []
    except:
        chat = []
    db.close()
    return jsonify(chat)

@app.route("/chat/clear", methods=["POST"])
def clear_chat():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE student_code=%s", (user_id,))
        l_u = cursor.fetchone()
        n_id = l_u['id'] if l_u else None
        if n_id:
            cursor.execute("DELETE FROM chatbot_messages WHERE user_id=%s", (n_id,))
            db.commit()
    except Exception as e:
        print("Clear chat error:", e)
    db.close()
    return jsonify({"status": "cleared"})

@app.route("/chat/send", methods=["POST"])
def send_message():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    user_id = session['user_id']
    msg = request.json.get("message", "").strip()
    if not msg: return jsonify({"error": "Empty message."})
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE student_code=%s", (user_id,))
    l_u = cursor.fetchone()
    n_id = l_u['id'] if l_u else None
    
    msg_lower = msg.lower()
    
    # Step 1: ALWAYS use LLM for the smartest experience
    context = ""
    try: context = build_context(cursor, user_id)
    except Exception as e: print("Context Error:", e)
    
    # Step 2: Fetch Recent Chat History
    cursor.execute("SELECT sender, message FROM chatbot_messages WHERE user_id=%s ORDER BY created_at DESC LIMIT 12", (n_id,))
    history_rows = list(cursor.fetchall())
    history_rows.reverse()  # Oldest first

    # Build proper message list for Groq (system + history + current user message)
    messages_for_groq = [{"role": "system", "content": context}]
    for h in history_rows:
        role = "user" if h['sender'] == 'student' else "assistant"
        messages_for_groq.append({"role": role, "content": h['message']})
    messages_for_groq.append({"role": "user", "content": msg})

    bot_reply = None
    if groq_client:
        try:
            completion = groq_client.chat.completions.create(
                messages=messages_for_groq,
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=400,
            )
            bot_reply = completion.choices[0].message.content
        except Exception as e:
            print("Groq Error:", e)

    if not bot_reply and GEMINI_API_KEY:
        # Gemini fallback: flat prompt
        flat = context + "\n\nCONVERSATION:\n"
        for h in history_rows:
            role_label = "Student" if h['sender'] == 'student' else "Assistant"
            flat += f"{role_label}: {h['message']}\n"
        flat += f"Student: {msg}\nAssistant:"
        gemini_reply = ask_gemini(flat)
        if gemini_reply == "__QUOTA__":
            bot_reply = "الذكاء الاصطناعي مشغول حالياً، جرب تاني بعد شوية."
        elif gemini_reply == "__ERROR__":
            bot_reply = "حدث خطأ ما."
        else:
            bot_reply = gemini_reply
            
    if not bot_reply:
        bot_reply = "عذراً، مش قادر أجاوبك دلوقتي."
        
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS chatbot_messages (id INT AUTO_INCREMENT PRIMARY KEY, user_id INT, sender VARCHAR(20), message TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("INSERT INTO chatbot_messages (user_id, sender, message) VALUES (%s, %s, %s)", (n_id, "student", msg))
        cursor.execute("INSERT INTO chatbot_messages (user_id, sender, message) VALUES (%s, %s, %s)", (n_id, "bot", bot_reply))
    except Exception as e:
        print("Error saving message:", e)
        
    db.close()
    return jsonify({"bot_reply": bot_reply})

@app.route("/gpa")
def gpa_page():
    if 'user_id' not in session: return redirect(url_for("login"))
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    # User Profile
    cursor.execute("SELECT * FROM vw_StudentProfile WHERE student_id=%s", (user_id,))
    user = cursor.fetchone()
    if user:
        user['student_code'] = user['student_id']
        user['faculty'] = user['department']
    
    # Map string user_id to numeric internal ID
    cursor.execute("SELECT id FROM users WHERE student_code=%s", (user_id,))
    local_user = cursor.fetchone()
    nid = local_user['id'] if local_user else None
    
    # Grades grouping
    if nid:
        cursor.execute("SELECT * FROM student_grades WHERE user_id=%s ORDER BY academic_year DESC, semester ASC", (nid,))
        all_grades = cursor.fetchall()
    else:
        all_grades = []
    db.close()
    
    years = {}
    for g in all_grades:
        y = g['academic_year']
        s = g['semester']
        
        # Format year label properly (avoid "Academic Year Year 1")
        year_label = y if "Year" in str(y) else f"Academic Year {y}"
        
        if y not in years:
            years[y] = {
                "label": year_label, 
                "semesters": {},
                "total_points": 0,
                "total_credits": 0,
                "year_gpa": 0.0
            }
            
        if s not in years[y]["semesters"]:
            years[y]["semesters"][s] = {
                "courses": [],
                "total_points": 0,
                "total_credits": 0,
                "semester_gpa": 0.0
            }
            
        # Add course to semester
        years[y]["semesters"][s]["courses"].append(g)
        
        # GPA Calculation: points = course points, credits = credit hours
        # Usually GPA = sum(points * credits) / sum(credits)
        # Wait, if `points` is already the quality points for the course (grade points * credits) or just the grade points?
        # Usually `points` in the DB is grade points (e.g., 4.0 for A). So quality points = points * credit_hours
        try:
            pts = float(g['points'])
            creds = int(g['credit_hours'])
            quality_points = pts * creds
            
            years[y]["semesters"][s]["total_points"] += quality_points
            years[y]["semesters"][s]["total_credits"] += creds
            
            years[y]["total_points"] += quality_points
            years[y]["total_credits"] += creds
        except:
            pass
            
    # Calculate final GPAs
    for y in years:
        if years[y]["total_credits"] > 0:
            years[y]["year_gpa"] = round(years[y]["total_points"] / years[y]["total_credits"], 2)
        for s in years[y]["semesters"]:
            if years[y]["semesters"][s]["total_credits"] > 0:
                years[y]["semesters"][s]["semester_gpa"] = round(years[y]["semesters"][s]["total_points"] / years[y]["semesters"][s]["total_credits"], 2)
        
    return render_template("gpa.html", user=user, years=years)

@app.route("/career")
def career_page(): return render_template("career.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))





@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/contact_send", methods=["POST"])
def contact_send():
    full_name = request.form.get("full_name")
    email = request.form.get("email")
    msg = request.form.get("message")
    
    db = get_db()
    cursor = db.cursor()
    # Ensure table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(255),
            email VARCHAR(255),
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("INSERT INTO contact_messages (full_name, email, message) VALUES (%s, %s, %s)", (full_name, email, msg))
    db.close()
    
    flash("Your message has been sent successfully!", "success")
    return redirect(url_for("contact"))


@app.route("/admin_my_students")
def admin_my_students():
    if session.get('role') != 'instructor': return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    real_id = session.get('real_instructor_id', 1)
    cursor.execute("""
        SELECT u.full_name as student_name, u.email, sg.course_code as course_id, sg.course_name, sg.grade
        FROM student_grades sg
        JOIN users u ON sg.user_id = u.id
        JOIN courses c ON sg.course_code = c.course_id
        WHERE c.instructor_id = %s
    """, (real_id,))
    students = cursor.fetchall()
    db.close()
    return render_template("admin_my_students.html", students=students)

@app.route("/admin_grades", methods=["GET", "POST"])
def admin_grades():
    if session.get('role') != 'instructor': return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    
    if request.method == "POST":
        grade_id = request.form.get("grade_id")
        grade_letter = request.form.get("grade")
        points = request.form.get("points")
        cursor.execute("UPDATE student_grades SET grade=%s, points=%s WHERE id=%s", (grade_letter, points, grade_id))
        db.commit()
        flash("Grade updated successfully!", "success")
        
    real_id = session.get('real_instructor_id', 1)
    cursor.execute("""
        SELECT sg.*, u.full_name as student_name 
        FROM student_grades sg
        JOIN users u ON sg.user_id = u.id
        JOIN courses c ON sg.course_code = c.course_id
        WHERE c.instructor_id = %s
    """, (real_id,))
    grades = cursor.fetchall()
    db.close()
    return render_template("admin_grades.html", grades=grades)

@app.route("/admin_requests", methods=["GET", "POST"])
def admin_requests():
    if session.get('role') != 'instructor': return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    
    if request.method == "POST":
        req_id = request.form.get("request_id")
        status = request.form.get("status")
        cursor.execute("UPDATE student_requests SET status=%s WHERE id=%s", (status, req_id))
        db.commit()
        flash("Request status updated!", "success")
        
    real_id = session.get('real_instructor_id', 1)
    cursor.execute("""
        SELECT sr.*, u.full_name as student_name, u.email 
        FROM student_requests sr
        JOIN users u ON sr.user_id = u.id
        WHERE (sr.instructor_id = %s OR sr.instructor_id IS NULL)
        ORDER BY sr.created_at DESC
    """, (real_id,))
    reqs = cursor.fetchall()
    db.close()
    return render_template("admin_requests.html", requests=reqs)



@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if 'user_id' not in session: return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    
    if request.method == "POST":
        email = request.form.get("email")
        phone = request.form.get("phone")
        address = request.form.get("address")
        
        cursor.execute("UPDATE Students SET email=%s, phone=%s, address=%s WHERE student_id=%s", (email, phone, address, session['user_id']))
        
        profile_pic = request.files.get("profile_pic")
        if profile_pic and profile_pic.filename:
            filename = werkzeug.utils.secure_filename(profile_pic.filename)
            filename = f"user_{session['user_id']}_{int(time.time())}_{filename}"
            # Ensure uploads dir exists
            uploads_dir = os.path.join(app.static_folder, "uploads")
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
            upload_path = os.path.join(uploads_dir, filename)
            profile_pic.save(upload_path)
            cursor.execute("UPDATE users SET profile_pic=%s WHERE student_code=%s", (filename, session['user_id']))
            session['profile_pic'] = filename
            
        db.commit()
        db.close()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile_page"))
        
    cursor.execute("""
        SELECT s.*, u.profile_pic 
        FROM Students s
        LEFT JOIN users u ON s.student_id = u.student_code
        WHERE s.student_id=%s
    """, (session['user_id'],))
    user = cursor.fetchone()
    db.close()
    return render_template("edit_profile.html", user=user)

@app.route("/schedule_details/<course_id>")
def schedule_details(course_id):
    if 'user_id' not in session: return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT c.*, CONCAT(i.title, ' ', i.first_name, ' ', i.last_name) as instructor_name 
        FROM Courses c 
        JOIN Instructors i ON c.instructor_id = i.instructor_id 
        WHERE c.course_id=%s
    """, (course_id,))
    course = cursor.fetchone()
    db.close()
    if not course: return redirect(url_for("schedule_page"))
    return render_template("schedule_details.html", course=course)

@app.route("/set_language/<lang>")
def set_language(lang):
    session['lang'] = lang
    return redirect(request.args.get('next', url_for('landing')))


@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get('role') not in ['instructor', 'system']: return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    
    # 1. Resolve actual instructor_id
    user_val = str(session.get('user_id', ''))
    instructor_email = None
    real_instructor_id = None
    
    if user_val.startswith("ins_"):
        admin_id = user_val.split("_")[1]
        cursor.execute("SELECT email FROM admins WHERE id=%s", (admin_id,))
        a = cursor.fetchone()
        if a: instructor_email = a['email']
    else:
        cursor.execute("SELECT email FROM Instructors WHERE instructor_id=%s", (user_val,))
        i = cursor.fetchone()
        if i: 
            instructor_email = i['email']
            real_instructor_id = user_val
            
    if instructor_email and not real_instructor_id:
        cursor.execute("SELECT instructor_id FROM Instructors WHERE email=%s", (instructor_email,))
        i = cursor.fetchone()
        if i: real_instructor_id = i['instructor_id']
        
    if not real_instructor_id:
        real_instructor_id = 1 # Fallback for demo
        
    session['real_instructor_id'] = real_instructor_id

    # 2. Get my courses
    cursor.execute("SELECT course_id, name, credit_hours, semester FROM courses WHERE instructor_id=%s", (real_instructor_id,))
    my_courses = cursor.fetchall()
    
    # 3. Get students enrolled
    course_ids = [c['course_id'] for c in my_courses]
    total_students = 0
    my_students = []
    if course_ids:
        format_strings = ','.join(['%s'] * len(course_ids))
        cursor.execute(f"SELECT COUNT(DISTINCT user_id) as count FROM student_grades WHERE course_code IN ({format_strings})", tuple(course_ids))
        total_students = cursor.fetchone()['count']
        
        cursor.execute(f"""
            SELECT DISTINCT u.full_name, sg.course_code, sg.grade, u.email
            FROM student_grades sg 
            JOIN users u ON sg.user_id = u.id 
            WHERE sg.course_code IN ({format_strings})
            LIMIT 8
        """, tuple(course_ids))
        my_students = cursor.fetchall()

    # 4. Get requests (pending count + recent list)
    cursor.execute("SELECT COUNT(*) as count FROM student_requests WHERE instructor_id=%s AND (status='Pending' OR doctor_reply IS NULL)", (real_instructor_id,))
    pending_requests_count = cursor.fetchone()['count']

    cursor.execute("""
        SELECT sr.*, u.full_name as student_name 
        FROM student_requests sr
        JOIN users u ON sr.user_id = u.id
        WHERE sr.instructor_id=%s 
        ORDER BY sr.created_at DESC LIMIT 5
    """, (real_instructor_id,))
    my_requests = cursor.fetchall()
    
    # 5. Get uploaded library materials
    cursor.execute("SELECT * FROM marketplace_products WHERE instructor_id=%s ORDER BY id DESC LIMIT 4", (real_instructor_id,))
    my_materials = cursor.fetchall()
    
    db.close()
    
    return render_template("admin_dashboard.html", 
        courses=my_courses,
        total_students=total_students,
        my_students=my_students,
        pending_requests_count=pending_requests_count,
        my_requests=my_requests,
        my_materials=my_materials
    )


@app.route("/admin/reply_request", methods=["POST"])
def admin_reply_request():
    if session.get('role') != 'instructor':
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    req_id = request.json.get('request_id')
    reply_text = request.json.get('reply_text')
    if not req_id or not reply_text:
        return jsonify({"success": False, "error": "Missing data"}), 400
        
    db = get_db()
    cursor = db.cursor()
    real_instructor_id = session.get('real_instructor_id', 1)
    cursor.execute("SELECT id FROM student_requests WHERE id=%s AND (instructor_id=%s OR instructor_id IS NULL)", (req_id, real_instructor_id))
    if not cursor.fetchone():
        db.close()
        return jsonify({"success": False, "error": "Request not found"}), 404
        
    cursor.execute("UPDATE student_requests SET doctor_reply=%s, status='Replied' WHERE id=%s", (reply_text, req_id))
    db.commit()
    db.close()
    return jsonify({"success": True})

@app.route("/system_dashboard")
def system_dashboard():
    if session.get('role') != 'system': return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    # System-wide stats
    cursor.execute("SELECT COUNT(*) as c FROM users")
    res = cursor.fetchone()
    st_count = res['c'] if res else 0
    
    cursor.execute("SELECT COUNT(*) as c FROM admins WHERE role='instructor'")
    res = cursor.fetchone()
    ins_count = res['c'] if res else 0
    
    cursor.execute("SELECT COUNT(*) as c FROM courses")
    res = cursor.fetchone()
    cr_count = res['c'] if res else 0
    
    cursor.execute("SELECT AVG(gpa) as avg_gpa FROM users WHERE gpa > 0")
    res = cursor.fetchone()
    avg_gpa = res['avg_gpa'] if res and res['avg_gpa'] else 0

    # Department distribution
    cursor.execute("SELECT faculty, COUNT(*) as c FROM users WHERE faculty IS NOT NULL AND faculty != '' GROUP BY faculty")
    depts = cursor.fetchall()
    dept_labels = [d['faculty'] for d in depts]
    dept_counts = [d['c'] for d in depts]

    # Top Students
    cursor.execute("""
        SELECT full_name, student_code, gpa 
        FROM users 
        WHERE gpa IS NOT NULL AND gpa > 0 
        ORDER BY gpa DESC 
        LIMIT 5
    """)
    top_students = cursor.fetchall()
    db.close()
    
    return render_template("system_dashboard.html",
        st_count=st_count,
        ins_count=ins_count,
        cr_count=cr_count,
        avg_gpa=round(avg_gpa, 2),
        dept_labels=dept_labels,
        dept_counts=dept_counts,
        top_students=top_students
    )

@app.route("/system/interviews")
def manage_interviews():
    if session.get('role') != 'system': return redirect(url_for("login"))
    return render_template("admin_interviews.html", is_ar=(session.get('lang')=='ar'))


@app.route("/system_students")
def system_students():
    if session.get('role') != 'system': return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users ORDER BY id DESC")
    students = cursor.fetchall()
    db.close()
    return render_template("system_students.html", students=students)

@app.route("/system_faculty")
def system_faculty():
    if session.get('role') != 'system': return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM admins WHERE role='instructor' ORDER BY id DESC")
    faculty = cursor.fetchall()
    db.close()
    return render_template("system_faculty.html", faculty=faculty)

@app.route("/system_departments")
def system_departments():
    if session.get('role') != 'system': return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT faculty as name, COUNT(*) as student_count FROM users WHERE faculty IS NOT NULL AND faculty != '' GROUP BY faculty")
    depts = cursor.fetchall()
    db.close()
    return render_template("system_departments.html", depts=depts)

@app.route("/system_database")
def system_database():
    if session.get('role') != 'system': return redirect(url_for("login"))
    return render_template("system_database.html")

@app.route("/system_courses")
def system_courses():
    if session.get('role') != 'system': return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM courses ORDER BY course_id")
    courses = cursor.fetchall()
    db.close()
    return render_template("system_courses.html", courses=courses)



@app.route("/admin/integrations", methods=["GET", "POST"])
def admin_integrations():
    if session.get('role') != 'instructor': return redirect(url_for("login"))
    
    env_file = os.path.join(os.getcwd(), '.env')
    
    if request.method == "POST":
        new_keys = {
            "GROQ_API_KEY": request.form.get("GROQ_API_KEY"),
            "GEMINI_API_KEY": request.form.get("GEMINI_API_KEY"),
            "PAYMOB_API_KEY": request.form.get("PAYMOB_API_KEY"),
            "PAYMOB_INTEGRATION_ID_CARD": request.form.get("PAYMOB_INTEGRATION_ID_CARD"),
            "PAYMOB_INTEGRATION_ID_FAWRY": request.form.get("PAYMOB_INTEGRATION_ID_FAWRY"),
        }
        
        # Simple update logic for .env
        lines = []
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                lines = f.readlines()
                
        with open(env_file, 'w') as f:
            written_keys = set()
            for line in lines:
                if '=' in line:
                    key = line.split('=')[0].strip()
                    if key in new_keys:
                        f.write(f"{key}={new_keys[key]}\n")
                        written_keys.add(key)
                    else:
                        f.write(line)
                else:
                    f.write(line)
            # Add any that weren't in the file
            for key, val in new_keys.items():
                if key not in written_keys:
                    f.write(f"{key}={val}\n")
        
        flash("Integration settings updated successfully!", "success")
        return redirect(url_for("admin_integrations"))

    # Read keys for display
    keys = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line:
                    parts = line.strip().split('=', 1)
                    if len(parts) == 2:
                        keys[parts[0]] = parts[1]
                    
    return render_template("admin_integrations.html", keys=keys)



@app.route("/notifications")
def notifications_page():
    if 'user_id' not in session: return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    # Numeric ID mapping
    cursor.execute("SELECT id FROM users WHERE student_code=%s", (session['user_id'],))
    nid = cursor.fetchone()['id']
    cursor.execute("SELECT * FROM notifications WHERE user_id=%s ORDER BY created_at DESC", (nid,))
    notifs = cursor.fetchall()
    db.close()
    return render_template("notifications.html", notifications=notifs)

@app.route("/notifications/count")
def notifications_count():
    if 'user_id' not in session: return jsonify({"count": 0})
    user_id = session['user_id']
    role = session.get('role')
    
    db = get_db()
    cursor = db.cursor()
    try:
        if role == 'student':
            cursor.execute("SELECT id FROM users WHERE student_code=%s", (user_id,))
            user_row = cursor.fetchone()
            n_id = user_row['id'] if user_row else None
            if n_id:
                cursor.execute("SELECT COUNT(*) as c FROM notifications WHERE user_id=%s AND is_read=0", (n_id,))
                cnt = cursor.fetchone()
                return jsonify({"count": cnt['c'] if cnt else 0})
    except Exception as e:
        pass
    finally:
        db.close()
    return jsonify({"count": 0})

@app.route("/payments/confirm", methods=["POST"])
def payments_confirm():
    if 'user_id' not in session: return jsonify({"success": False})
    data = request.json
    pid = data.get("payment_id")
    method = data.get("method", "Card")
    
    db = get_db()
    cursor = db.cursor()
    # Update the specific payment record to 'paid'
    cursor.execute("UPDATE payments SET payment_status='paid', payment_date=CURDATE(), payment_method=%s WHERE id=%s", (method, pid))
    
    # Also update the official FacPayments table to keep profile/dashboard in sync
    user_code = session.get('user_id')
    if user_code:
        cursor.execute("UPDATE FacPayments SET status='Paid', payment_date=CURDATE(), payment_method=%s WHERE student_id=%s ORDER BY payment_id DESC LIMIT 1", (method, user_code))
    
    db.commit()
    db.close()
    return jsonify({"success": True})

@app.route("/receipt/<int:payment_id>")
def receipt(payment_id):
    if 'user_id' not in session: return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    # Use the 'payments' table which matches the IDs on the payments page
    cursor.execute("SELECT * FROM payments WHERE id=%s", (payment_id,))
    payment = cursor.fetchone()
    db.close()
    if not payment: return redirect(url_for("payments_page"))
    return render_template("receipt.html", payment=payment)

@app.route("/marketplace")
def marketplace_page():
    if 'user_id' not in session: return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT mp.*, CONCAT(i.first_name, ' ', i.last_name) as doctor_name 
        FROM marketplace_products mp
        LEFT JOIN Instructors i ON mp.instructor_id = i.instructor_id
        ORDER BY mp.created_at DESC
    """)
    products = cursor.fetchall()
    db.close()
    return render_template("marketplace.html", products=products)

@app.route("/marketplace/<int:product_id>")
def marketplace_details(product_id):
    if 'user_id' not in session: return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT mp.*, CONCAT(i.first_name, ' ', i.last_name) as doctor_name 
        FROM marketplace_products mp
        LEFT JOIN Instructors i ON mp.instructor_id = i.instructor_id
        WHERE mp.id=%s
    """, (product_id,))
    product = cursor.fetchone()
    db.close()
    if not product: return redirect(url_for("marketplace_page"))
    return render_template("marketplace_details.html", product=product)

@app.route("/new_request", methods=["GET", "POST"])
def new_request_page():
    if 'user_id' not in session: return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    
    if request.method == "POST":
        instructor_id = request.form.get("instructor_id")
        msg = request.form.get("message")
        
        # Map string user_id to numeric internal ID
        cursor.execute("SELECT id FROM users WHERE student_code=%s", (session['user_id'],))
        user_record = cursor.fetchone()
        nid = user_record['id'] if user_record else session['user_id']
        
        # Insert with dummy title since user requested to replace type with doctor selection
        cursor.execute("INSERT INTO student_requests (user_id, instructor_id, title, message, status) VALUES (%s, %s, %s, %s, 'Pending')", 
                       (nid, instructor_id, "Direct Message", msg))
        db.commit()
        db.close()
        flash("Request submitted successfully!", "success")
        return redirect(url_for("my_requests_page"))
        
    cursor.execute("SELECT instructor_id as id, CONCAT(first_name, ' ', last_name) as full_name FROM Instructors")
    instructors = cursor.fetchall()
    db.close()
    return render_template("new_request.html", instructors=instructors)


@app.route("/my_requests")
def my_requests_page():
    if 'user_id' not in session: return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    # Map string user_id to numeric internal ID
    cursor.execute("SELECT id FROM users WHERE student_code=%s", (session['user_id'],))
    nid = cursor.fetchone()['id']
    
    cursor.execute("""
        SELECT sr.*, CONCAT(i.first_name, ' ', i.last_name) as doctor_name 
        FROM student_requests sr 
        LEFT JOIN Instructors i ON sr.instructor_id = i.instructor_id 
        WHERE sr.user_id=%s ORDER BY sr.created_at DESC
    """, (nid,))
    reqs = cursor.fetchall()
    db.close()
    return render_template("my_requests.html", requests=reqs)


@app.route("/my_notes", methods=["GET", "POST"])
def my_notes():
    if 'user_id' not in session: return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    
    # Map student_code to internal ID
    cursor.execute("SELECT id FROM users WHERE student_code=%s", (session['user_id'],))
    user_record = cursor.fetchone()
    
    if not user_record:
        # Fallback: maybe session['user_id'] IS already the internal ID (integer)
        nid = session['user_id']
    else:
        nid = user_record['id']

    if request.method == "POST":
        title = request.form.get("title", "New Note")
        content = request.form.get("content", "")
        category = request.form.get("category", "General")
        cursor.execute("INSERT INTO student_notes (user_id, title, content, category) VALUES (%s, %s, %s, %s)", (nid, title, content, category))
        db.commit()
        db.close()
        flash("Note saved!", "success")
        return redirect(url_for("my_notes"))

    cursor.execute("SELECT * FROM student_notes WHERE user_id=%s ORDER BY created_at DESC", (nid,))
    notes = cursor.fetchall()
    db.close()
    return render_template("my_notes.html", notes=notes)

@app.route("/delete_note/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    if 'user_id' not in session: return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM student_notes WHERE id=%s", (note_id,))
    db.commit()
    db.close()
    flash("Note deleted!", "success")
    return redirect(url_for("my_notes"))

@app.route("/edit_note/<int:note_id>", methods=["POST"])
def edit_note(note_id):
    if 'user_id' not in session: return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    title = request.form.get("title")
    content = request.form.get("content")
    category = request.form.get("category", "General")
    cursor.execute("UPDATE student_notes SET title=%s, content=%s, category=%s WHERE id=%s", (title, content, category, note_id))
    db.commit()
    db.close()
    flash("Note updated!", "success")
    return redirect(url_for("my_notes"))

@app.route("/profile")
def profile_page():
    if 'user_id' not in session: return redirect(url_for("login"))
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    # Profile
    cursor.execute("""
        SELECT v.*, u.profile_pic 
        FROM vw_StudentProfile v
        LEFT JOIN users u ON v.student_id = u.student_code
        WHERE v.student_id=%s
    """, (user_id,))
    user = cursor.fetchone()
    if user:
        user['student_code'] = user['student_id']
        user['faculty'] = user['department']
        user['level'] = user['year_level']
    
    # Map student_code to numeric ID
    cursor.execute("SELECT id FROM users WHERE student_code=%s", (user_id,))
    local_user_for_pay = cursor.fetchone()
    nid_for_pay = local_user_for_pay['id'] if local_user_for_pay else None
    
    # Latest Payment (Using the transactional 'payments' table for consistency)
    if nid_for_pay:
        cursor.execute("SELECT *, amount as amount_egp, payment_type as type_name, payment_status as status_name FROM payments WHERE user_id=%s ORDER BY id DESC LIMIT 1", (nid_for_pay,))
        latest_payment = cursor.fetchone()
        if latest_payment:
            latest_payment['payment_type'] = latest_payment['type_name']
            latest_payment['amount'] = latest_payment['amount']
            latest_payment['payment_status'] = latest_payment['status_name']
    else:
        latest_payment = None
    
    # Counts
    cursor.execute("SELECT id FROM users WHERE student_code=%s", (user_id,))
    res = cursor.fetchone()
    if res:
        nid = res['id']
        
        cursor.execute("SELECT COUNT(*) as total_subjects FROM schedules WHERE user_id=%s", (nid,))
        subject_count = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as total_exams FROM exams WHERE user_id=%s", (nid,))
        exam_count = cursor.fetchone()
    else:
        subject_count = {'total_subjects': 0}
        exam_count = {'total_exams': 0}
    
    cursor.execute("SELECT COUNT(*) as total_requests FROM student_requests WHERE user_id=%s", (user_id,))
    req_count = cursor.fetchone()
    
    db.close()
    return render_template("profile.html", user=user, subject_count=subject_count, exam_count=exam_count, req_count=req_count, latest_payment=latest_payment)

@app.route("/cv_optimizer")
def cv_optimizer_page():
    if 'user_id' not in session: return redirect(url_for("login"))
    return render_template("cv_optimizer.html")

@app.route("/career_matching")
def career_matching_page():
    if 'user_id' not in session: return redirect(url_for("login"))
    return render_template("career_matching.html")

@app.route("/mock_interview")
def mock_interview_page():
    if 'user_id' not in session: return redirect(url_for("login"))
    return render_template("mock_interview.html")

@app.route("/registration")
def registration_page():
    if 'user_id' not in session: return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    # Map student_code to numeric ID
    cursor.execute("SELECT id FROM users WHERE student_code=%s", (session['user_id'],))
    u_row = cursor.fetchone()
    nid = u_row['id'] if u_row else None
    
    if nid:
        cursor.execute("SELECT * FROM schedules WHERE user_id=%s", (nid,))
        regs = cursor.fetchall()
    else:
        regs = []
    db.close()
    return render_template("registration.html", registrations=regs)

@app.route("/admin_add_product", methods=["GET", "POST"])
def admin_add_product():
    if session.get('role') != 'instructor': return redirect(url_for("login"))
    if request.method == "POST":
        title = request.form.get("title")
        cat = request.form.get("category")
        price = request.form.get("price") or 0
        summary = request.form.get("summary")
        real_id = session.get('real_instructor_id', 1)
        
        pdf_filename = None
        img_filename = None
        
        import os
        from werkzeug.utils import secure_filename
        import time
        
        uploads_dir = os.path.join(app.static_folder, "uploads")
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
            
        if 'pdf_file' in request.files:
            pdf = request.files['pdf_file']
            if pdf.filename:
                pdf_filename = f"pdf_{int(time.time())}_{secure_filename(pdf.filename)}"
                pdf.save(os.path.join(uploads_dir, pdf_filename))
                
        if 'image' in request.files:
            img = request.files['image']
            if img.filename:
                img_filename = f"img_{int(time.time())}_{secure_filename(img.filename)}"
                img.save(os.path.join(uploads_dir, img_filename))

        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO marketplace_products (title, category, price, summary, instructor_id, pdf_file, image) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                       (title, cat, price, summary, real_id, pdf_filename, img_filename))
        db.commit()
        db.close()
        flash("Product added to library successfully!", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_add_product.html")

# AI SERVICES ENDPOINTS
@app.route("/cv/analyze-pdf", methods=["POST"])
def cv_analyze():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"})
    
    f = request.files.get("cv_file")
    if not f:
        return jsonify({"success": False, "error": "No file uploaded"})
    
    # Extract text from PDF using PyPDF2
    try:
        import PyPDF2
        import io
        
        pdf_bytes = f.read()
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        
        full_text = ""
        for page in reader.pages:
            try:
                full_text += page.extract_text() or ""
            except:
                pass
        
        full_text_lower = full_text.lower()
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Could not read PDF: {str(e)}"})
    
    if not full_text.strip():
        return jsonify({"success": False, "error": "Could not extract text from this PDF. Make sure it is not a scanned image."})
    
    # Comprehensive skills database
    ALL_SKILLS = {
        # Programming
        "Python": ["python"],
        "Java": ["java"],
        "JavaScript": ["javascript", "js"],
        "C++": ["c++", "cpp"],
        "C#": ["c#", "csharp"],
        "PHP": ["php"],
        "Swift": ["swift"],
        "Kotlin": ["kotlin"],
        "TypeScript": ["typescript"],
        "Go": ["golang", " go "],
        "R": [" r programming", "r studio", "rstudio"],
        "MATLAB": ["matlab"],
        "SQL": ["sql", "mysql", "postgresql", "sqlite", "oracle sql"],
        "NoSQL": ["nosql", "mongodb", "cassandra", "dynamodb"],
        
        # Web / Frameworks
        "HTML/CSS": ["html", "css"],
        "React": ["react", "reactjs"],
        "Angular": ["angular"],
        "Vue.js": ["vue", "vuejs"],
        "Node.js": ["node.js", "nodejs"],
        "Flask": ["flask"],
        "Django": ["django"],
        "Spring Boot": ["spring boot", "springboot"],
        "Bootstrap": ["bootstrap"],
        
        # Data & AI
        "Machine Learning": ["machine learning", "ml model", "scikit-learn", "sklearn"],
        "Deep Learning": ["deep learning", "neural network", "tensorflow", "keras", "pytorch"],
        "Data Analysis": ["data analysis", "data analytics", "pandas", "numpy"],
        "Data Visualization": ["data visualization", "matplotlib", "tableau", "power bi", "powerbi"],
        "NLP": ["nlp", "natural language processing"],
        "Computer Vision": ["computer vision", "opencv", "image recognition"],
        "Statistics": ["statistics", "statistical analysis", "spss"],
        
        # Cloud & DevOps
        "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda"],
        "Azure": ["azure", "microsoft azure"],
        "GCP": ["gcp", "google cloud", "google cloud platform"],
        "Docker": ["docker", "dockerfile", "containerization"],
        "Kubernetes": ["kubernetes", "k8s"],
        "CI/CD": ["ci/cd", "jenkins", "github actions", "gitlab ci"],
        "Linux": ["linux", "ubuntu", "bash", "shell scripting"],
        "Git": ["git", "github", "gitlab", "version control"],
        
        # Business & Finance
        "Accounting": ["accounting", "bookkeeping", "ledger", "محاسبة"],
        "Financial Analysis": ["financial analysis", "financial modeling", "تحليل مالي"],
        "Financial Auditing": ["auditing", "audit", "مراجعة"],
        "Microsoft Excel": ["excel", "microsoft excel", "spreadsheet", "pivot table"],
        "Microsoft Word": ["microsoft word", "word processing"],
        "Microsoft PowerPoint": ["powerpoint", "presentation"],
        "ERP Systems": ["erp", "sap", "oracle erp", "odoo"],
        "QuickBooks": ["quickbooks"],
        "Taxation": ["taxation", "tax", "ضرائب"],
        "Budgeting": ["budgeting", "budget", "ميزانية"],
        
        # Soft Skills & General
        "Communication": ["communication", "interpersonal", "تواصل", "تواصل فعّال"],
        "Teamwork": ["teamwork", "team player", "collaboration", "عمل فريق"],
        "Leadership": ["leadership", "team lead", "leading", "قيادة"],
        "Problem Solving": ["problem solving", "problem-solving", "حل مشكلات"],
        "Time Management": ["time management", "إدارة وقت"],
        "Project Management": ["project management", "pmp", "agile", "scrum", "kanban"],
        "Critical Thinking": ["critical thinking", "analytical thinking"],
        "Research": ["research", "بحث علمي"],
        "Customer Service": ["customer service", "خدمة عملاء"],
        "Marketing": ["marketing", "digital marketing", "seo", "social media marketing", "تسويق"],
        "Sales": ["sales", "مبيعات", "business development"],
        "Negotiation": ["negotiation", "تفاوض"],
        "Arabic": ["arabic", "العربية"],
        "English": ["english", "الإنجليزية", "toefl", "ielts"],
        "French": ["french", "الفرنسية"],
        "Photoshop": ["photoshop", "adobe photoshop"],
        "UI/UX": ["ui/ux", "user interface", "ux design", "figma", "adobe xd"],
        "AutoCAD": ["autocad"],
        "Network": ["networking", "cisco", "ccna", "network administration"],
        "Cybersecurity": ["cybersecurity", "cyber security", "information security", "penetration testing"],
    }
    
    found_skills = []
    missing_skills = []
    
    for skill_name, keywords in ALL_SKILLS.items():
        detected = any(kw in full_text_lower for kw in keywords)
        if detected:
            found_skills.append(skill_name)
        else:
            missing_skills.append(skill_name)
    
    # Calculate score based on found skills ratio (weighted, max 95)
    total_skills = len(ALL_SKILLS)
    found_count = len(found_skills)
    
    # Base score
    raw_score = (found_count / total_skills) * 100
    
    # Bonus: longer CV content = more detail (up to 5 pts)
    length_bonus = min(5, len(full_text) / 500)
    
    score = min(95, int(raw_score + length_bonus))
    score = max(10, score)  # minimum 10 so it's not insulting
    
    return jsonify({
        "success": True,
        "score": score,
        "file_name": f.filename,
        "found_skills": found_skills,
        "missing_skills": missing_skills[:12],  # top 12 recommendations
        "total_words": len(full_text.split())
    })

@app.route("/interview/start")
def interview_start():
    if 'user_id' not in session: return jsonify([])
    field = request.args.get("field", "General")
    
    # Generate opening question using AI
    if groq_client:
        try:
            system_prompt = f"""You are a professional hiring manager conducting a job interview for a {field} position at a top company.
Start with a warm, professional greeting and then ask your FIRST interview question.
Keep it concise (2-3 sentences max). Be friendly but professional.
Do NOT say you are an AI. Act as a real human interviewer named 'Alex'.
Respond in the same language the candidate will likely use based on the role."""
            
            completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Start the interview."}
                ],
                model="llama-3.3-70b-versatile",
                max_tokens=200,
            )
            opening = completion.choices[0].message.content
            return jsonify({"success": True, "opening": opening})
        except Exception as e:
            print("Groq Interview Start Error:", e)
    
    # Fallback
    return jsonify({"success": True, "opening": "Hello! I'm Alex, your interviewer today for the interview. Let's start — could you please tell me a bit about yourself and your background?"})


@app.route("/interview/reply", methods=["POST"])
def interview_reply():
    if 'user_id' not in session: return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    data = request.json
    field = data.get("field", "General")
    history = data.get("history", [])
    user_answer = data.get("answer", "")
    question_num = data.get("question_num", 0)
    total_questions = data.get("total_questions", 10)
    
    system_prompt = f"""You are 'Alex', an expert hiring manager for {field} roles at EDUGUIDE.
    YOUR GOAL: Conduct a professional, realistic interview.
    
    YOUR BEHAVIOR RULES:
    1. You are a REAL human interviewer - never reveal you are an AI.
    2. Evaluate the candidate's answer briefly (1 sentence).
    3. Then ask your NEXT interview question naturally.
    4. Keep responses SHORT (3-4 sentences max).
    5. Ask progressively deeper technical questions.
    """

    messages = [{"role": "system", "content": system_prompt}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_answer})
    
    is_final = (question_num >= total_questions)
    score = 0
    feedback = ""
    
    if is_final:
        # Calculate substance
        total_user_chars = sum(len(m['content']) for m in history if m['role'] == 'user')
        is_low_effort = (total_user_chars < 150)

        if is_low_effort:
            score = 15
            feedback = "Extremely low effort. Please provide more detailed answers next time."
        else:
            summary_prompt = f"As a professional evaluator for {field}, score this interview 0-100 and give feedback. Format strictly as SCORE: [num] FEEDBACK: [text]. HISTORY: {history}"
            try:
                res_text = ask_gemini(summary_prompt)
                if "SCORE:" in res_text:
                    parts = res_text.split("FEEDBACK:")
                    score_str = parts[0].replace("SCORE:", "").strip()
                    score = int(''.join(filter(str.isdigit, score_str)) or 0)
                    feedback = parts[1].strip() if len(parts) > 1 else "Good job."
                else:
                    score = 40
                    feedback = res_text
            except:
                score = 35
                feedback = "Interview completed. Quality was below standards."

        # SAVE TO DB
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT id FROM users WHERE student_code=%s", (session['user_id'],))
            u_row = cursor.fetchone()
            if u_row:
                user_id = u_row['id']
                # Robust history check
                safe_history = history if isinstance(history, list) else []
                cursor.execute("""
                    INSERT INTO mock_interview_sessions (user_id, field, score, feedback, chat_history) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, field, score, feedback, json.dumps(safe_history + [{"role": "user", "content": user_answer}])))
                db.commit()
            db.close()
            print(f"DEBUG: Interview successfully saved to MySQL for user {session.get('user_id')}")
        except Exception as e:
            print(f"CRITICAL DB SAVE ERROR: {e}")

    # AI MODELS TO TRY IN ORDER
    models_to_try = [
        {"provider": "groq", "model": "llama-3.3-70b-versatile"},
        {"provider": "groq", "model": "llama-3.1-8b-instant"},
        {"provider": "gemini", "model": "gemini-1.5-flash-latest"}
    ]
    
    reply = None
    for attempt in models_to_try:
        try:
            if attempt["provider"] == "groq" and groq_client:
                completion = groq_client.chat.completions.create(
                    messages=messages,
                    model=attempt["model"],
                    max_tokens=300,
                )
                reply = completion.choices[0].message.content
                if reply: break
            elif attempt["provider"] == "gemini" and GEMINI_API_KEY:
                history_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                prompt = f"Respond as Alex for {field}. INTERVIEW HISTORY: {history_text}"
                reply = ask_gemini(prompt)
                if reply and reply not in ["__QUOTA__", "__ERROR__"]:
                    break
        except: continue

    if reply:
        return jsonify({"success": True, "reply": reply, "is_final": is_final, "score": score, "feedback": feedback})
    return jsonify({"success": False, "error": "AI busy."})

@app.route("/career/match")
def career_match():
    if 'user_id' not in session: return jsonify([])
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM career_jobs LIMIT 3")
    jobs = cursor.fetchall()
    db.close()
    for j in jobs:
        j['score'] = 92
        j['matched_skills'] = ["Accounting", "Excel"]
    return jsonify(jobs)
# PAYMOB INTEGRATION
def get_paymob_auth_token():
    api_key = os.getenv("PAYMOB_API_KEY")
    if not api_key: return None
    api_key = api_key.strip()
    url = "https://accept.paymob.com/api/auth/tokens"
    resp = requests.post(url, json={"api_key": api_key})
    print("AUTH RESP:", resp.text)
    return resp.json().get("token")

def initiate_paymob_order(token, amount_cents, merchant_order_id=None):
    url = "https://accept.paymob.com/api/ecommerce/orders"
    payload = {
        "auth_token": token,
        "delivery_needed": "false",
        "amount_cents": str(amount_cents),
        "currency": "EGP",
        "items": []
    }
    if merchant_order_id:
        payload["merchant_order_id"] = str(merchant_order_id)
    resp = requests.post(url, json=payload)
    print("ORDER RESP:", resp.text)
    return resp.json().get("id")

def get_payment_key(token, order_id, amount_cents, integration_id, user_info):
    url = "https://accept.paymob.com/api/acceptance/payment_keys"
    payload = {
        "auth_token": token,
        "amount_cents": str(amount_cents),
        "expiration": 3600,
        "order_id": str(order_id),
        "billing_data": {
            "apartment": "NA",
            "email": user_info.get('email', 'student@eduguide.com'),
            "floor": "NA",
            "first_name": user_info.get('first_name', 'Student'),
            "street": "NA",
            "building": "NA",
            "phone_number": user_info.get('phone', '01000000000'),
            "shipping_method": "NA",
            "postal_code": "NA",
            "city": "Cairo",
            "country": "EG",
            "last_name": user_info.get('last_name', 'User'),
            "state": "NA"
        },
        "currency": "EGP",
        "integration_id": integration_id
    }
    resp = requests.post(url, json=payload)
    print("KEY RESP:", resp.text)
    return resp.json().get("token")

@app.route("/payments/initiate", methods=["POST"])
def initiate_payment():
    if 'user_id' not in session: return jsonify({"success": False, "error": "Unauthorized"})
    
    paymob_api_key = os.getenv("PAYMOB_API_KEY")
    if not paymob_api_key:
        return jsonify({"success": False, "error": "Please add PAYMOB_API_KEY to your .env file"})

    data = request.json
    amount = float(data.get("amount", 0))
    payment_id = data.get("payment_id")
    method = data.get("method") # 'card' or 'fawry'
    
    amount_cents = int(amount * 100)
    import time
    merchant_order_id = f"EDY_{payment_id}_{int(time.time())}"
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM vw_StudentProfile WHERE student_id=%s", (session['user_id'],))
    user = cursor.fetchone() or {}
    db.close()
    
    token = get_paymob_auth_token()
    if not token: return jsonify({"success": False, "error": "Invalid Paymob API Key. Please check your credentials."})
    
    order_id = initiate_paymob_order(token, amount_cents, merchant_order_id)
    if not order_id: return jsonify({"success": False, "error": "Order Creation Failed. Check your connection."})
    
    integration_id = os.getenv("PAYMOB_INTEGRATION_ID_CARD") if method == 'card' else os.getenv("PAYMOB_INTEGRATION_ID_FAWRY")
    
    if not integration_id:
        return jsonify({"success": False, "error": f"Integration ID for {method} is missing in .env"})

    payment_token = get_payment_key(token, order_id, amount_cents, integration_id, user)
    
    if method == 'card':
        iframe_id = "1039430" 
        redirect_url = f"https://accept.paymob.com/api/acceptance/iframes/{iframe_id}?payment_token={payment_token}"
        return jsonify({"success": True, "redirect_url": redirect_url})
    else:
        pay_url = "https://accept.paymob.com/api/acceptance/payments/pay"
        pay_payload = {
            "source": {"identifier": "AGGREGATOR", "subtype": "AGGREGATOR"},
            "payment_token": payment_token
        }
        pay_resp = requests.post(pay_url, json=pay_payload)
        fawry_code = pay_resp.json().get("data", {}).get("bill_reference", "Error")
        return jsonify({"success": True, "payment_token": fawry_code})

@app.route("/payments/callback")
def payment_callback():
    # Paymob redirects here after payment
    success = request.args.get("success")
    merchant_order_id = request.args.get("merchant_order_id", "")
    
    payment_id = None
    if merchant_order_id.startswith("EDY_"):
        parts = merchant_order_id.split("_")
        if len(parts) >= 2:
            payment_id = parts[1]
            
    if success == "true" and payment_id:
        try:
            db = get_db()
            cursor = db.cursor()
            # Update the payment status in the database
            cursor.execute("UPDATE payments SET payment_status='paid', payment_date=CURDATE() WHERE id=%s", (payment_id,))
            db.commit()
            db.close()
            return render_template("success.html", message="Payment successful! Your fees have been updated.")
        except Exception as e:
            print(f"Callback DB Error: {e}")
            return render_template("success.html", message="Payment detected, but database update failed. Please contact support.")
    
    return render_template("error.html", message="Payment failed or was cancelled.")

# 🔍 SUPER SEARCH API
@app.route("/api/search")
def global_search():
    if 'user_id' not in session: return jsonify([])
    q = request.args.get("q", "").lower().strip()
    if not q: return jsonify([])
    
    db = get_db()
    cursor = db.cursor()
    user_id = session['user_id']
    
    # Map student_code to internal ID
    cursor.execute("SELECT id FROM users WHERE student_code=%s", (user_id,))
    l_u = cursor.fetchone()
    n_id = l_u['id'] if l_u else None
    
    results = []
    
    # Search Notes
    cursor.execute("SELECT id, title, category FROM student_notes WHERE user_id=%s AND (title LIKE %s OR content LIKE %s)", (n_id, f"%{q}%", f"%{q}%"))
    notes = cursor.fetchall()
    for n in notes:
        results.append({"type": "note", "title": n['title'], "cat": n['category'], "url": url_for('my_notes') + f"#note-{n['id']}"})
        
    # Search Subjects/Schedules
    cursor.execute("SELECT DISTINCT subject_name FROM schedules WHERE user_id=%s AND subject_name LIKE %s", (n_id, f"%{q}%"))
    subs = cursor.fetchall()
    for s in subs:
        results.append({"type": "subject", "title": s['subject_name'], "cat": "Schedule", "url": url_for('schedule_page')})

    # Search Exams
    cursor.execute("SELECT DISTINCT subject_name FROM exams WHERE user_id=%s AND subject_name LIKE %s", (n_id, f"%{q}%"))
    exs = cursor.fetchall()
    for e in exs:
        results.append({"type": "exam", "title": e['subject_name'], "cat": "Exam", "url": url_for('exams_page')})
        
    db.close()
    return jsonify(results[:10])

# 🎙️ ELITE SPEECH-TO-TEXT (GROQ WHISPER)
@app.route("/speech-to-text", methods=["POST"])
def transcribe_speech():
    if not groq_client: 
        return jsonify({"error": "Groq client not configured"}), 500
    
    if 'file' not in request.files: 
        return jsonify({"error": "No audio file"}), 400
    
    audio_file = request.files['file']
    temp_path = "temp_speech.webm"
    audio_file.save(temp_path)
    
    try:
        with open(temp_path, "rb") as f:
            transcription = groq_client.audio.transcriptions.create(
              file=(temp_path, f.read()),
              model="whisper-large-v3",
              response_format="json",
              language="ar", 
              prompt="تحدث الطالب باللهجة المصرية العامية عن مواضيع جامعية مثل: جدول المحاضرات، الامتحانات، النتيجة، المعدل التراكمي (GPA)، المذاكرة، المواد الدراسية، السيرة الذاتية (CV)، والمشاريع. يرجى تحويل الكلام بدقة تامة وبنفس الكلمات المستخدمة.",
              temperature=0.0
            )
        os.remove(temp_path)
        return jsonify({"text": transcription.text})
            
    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        print(f"Transcription Error: {e}")
        return jsonify({"error": str(e)}), 500
# 🏆 ELITE FEATURES (STUDY PLANNER, FEEDBACK, SMART ANALYTICS)

@app.route("/study/planner")
def study_planner():
    if 'user_id' not in session: return redirect(url_for("login"))
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    # Map student_code to numeric ID
    cursor.execute("SELECT id FROM users WHERE student_code=%s", (user_id,))
    l_u = cursor.fetchone()
    n_id = l_u['id'] if l_u else None
    
    cursor.execute("SELECT * FROM student_tasks WHERE user_id=%s ORDER BY deadline ASC", (n_id,))
    tasks = cursor.fetchall()
    db.close()
    return render_template("study_planner.html", tasks=tasks)

@app.route("/api/study/add-task", methods=["POST"])
def add_task():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE student_code=%s", (session['user_id'],))
    n_id = cursor.fetchone()['id']
    cursor.execute("INSERT INTO student_tasks (user_id, title, deadline, priority) VALUES (%s, %s, %s, %s)", 
                   (n_id, data['title'], data['deadline'], data['priority']))
    db.commit()
    db.close()
    return jsonify({"success": True})

@app.route("/instructor/feedback")
def instructor_feedback():
    if 'user_id' not in session: return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT *, CONCAT(title, ' ', first_name, ' ', last_name) as full_name FROM instructors")
    instructors = cursor.fetchall()
    
    cursor.execute("""
        SELECT r.*, CONCAT(i.title, ' ', i.first_name, ' ', i.last_name) as instructor_name 
        FROM instructor_ratings r 
        JOIN instructors i ON r.instructor_id = i.instructor_id 
        ORDER BY r.created_at DESC LIMIT 10
    """)
    recent_ratings = cursor.fetchall()
    db.close()
    return render_template("instructor_feedback.html", instructors=instructors, recent_ratings=recent_ratings)

@app.route("/api/instructor/rate", methods=["POST"])
def rate_instructor():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE student_code=%s", (session['user_id'],))
    n_id = cursor.fetchone()['id']
    cursor.execute("INSERT INTO instructor_ratings (student_id, instructor_id, rating, comment) VALUES (%s, %s, %s, %s)", 
                   (n_id, data['instructor_id'], data['rating'], data['comment']))
    db.commit()
    db.close()
    return jsonify({"success": True})

@app.route("/api/admin/interviews")
def admin_interviews():
    if 'user_id' not in session: return jsonify([])
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT s.id, u.full_name, s.field, s.score, s.feedback, s.chat_history, s.created_at 
        FROM mock_interview_sessions s 
        JOIN users u ON s.user_id = u.id 
        ORDER BY s.created_at DESC LIMIT 50
    """)
    interviews = cursor.fetchall()
    db.close()
    
    # Format date
    for i in interviews:
        if i['created_at']:
            i['date_str'] = i['created_at'].strftime("%Y-%m-%d %H:%M")
    
    return jsonify(interviews)

@app.route("/api/admin/smart-stats")
def admin_smart_stats():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    # Check if admin (optional logic here)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users")
    u_count = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM chatbot_messages")
    chat_count = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM payments")
    pay_count = cursor.fetchone()['count']
    db.close()
    
    prompt = f"As a platform analytics AI, provide a very short (2 lines) encouraging summary of these stats for the admin: Total Users: {u_count}, AI Chats: {chat_count}, Total Payments: {pay_count}. Use a professional, slightly Egyptian tone."
    ai_summary = ask_gemini(prompt)
    
    return jsonify({
        "summary": ai_summary,
        "users": u_count,
        "chats": chat_count,
        "payments": pay_count
    })

if __name__ == "__main__":
    # Use the port assigned by Render, or default to 5001 for local development
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
