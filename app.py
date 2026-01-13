from flask import Flask, render_template, request, send_from_directory, session, send_file
import json
import qrcode
import os
from werkzeug.utils import secure_filename
import pandas as pd
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
app.secret_key = "zeal10_secret_key_2025"

# ---------------- CONFIG ----------------
DB_FILE = "database.json"
QR_DIR = "static/qr"
UPLOAD_DIR = "uploads/payments"

os.makedirs(QR_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# ---------------- EVENTS & PRICES ----------------
EVENT_PRICES = {
    "Business Idea Pitching Contest (Case Cracker)": 100,
    "Caselet Solving Competition": 100,
    "Paper / Balloon Tower Making (Paper Peaks)": 100,
    "Corporate Collage (Bizmosaic)": 100,
    "Sales Pitching Contest (DealQuest)": 100,
    "Turbo AI Challenge": 100,
    "INNO Quest": 100,
    "Robo Race": 100,
    "CODING": 100,
    "Clip Clash – REEL": 100,
    "Quiz Competition": 100,
    "Poster Making (Tech Theme)": 100,
    "Rangoli Competition": 100,
    "Cook without Fire": 100,
    "Ad-Mad Show": 100,
    "Eco-Fashion / Recycled Clothing Show": 100,
    "T-Shirt Painting": 100,
    "Eco-Voice Debate / GreenSpeak Debate": 100,
    "Face Painting Competition": 100,
    # Category-based events
    "Dance Competition - Solo": 100,
    "Dance Competition - Duet": 200,
    "Dance Competition - Group": 300,
    "Fashion Show Competition - Solo": 100,
    "Fashion Show Competition - Duet": 200,
    "Fashion Show Competition - Group": 300,
}

# ---------------- JSON DATABASE FUNCTIONS ----------------
def init_db():
    """Initialize JSON database file if it doesn't exist"""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({"registrations": [], "last_id": 0}, f, indent=2)
        print("JSON database initialized successfully!")
    else:
        print("JSON database already exists!")

def read_db():
    """Read data from JSON database"""
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"registrations": [], "last_id": 0}

def write_db(data):
    """Write data to JSON database"""
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_registration(registration_data):
    """Add a new registration to the database"""
    db = read_db()
    db["last_id"] += 1
    registration_data["id"] = db["last_id"]
    registration_data["created_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db["registrations"].append(registration_data)
    write_db(db)
    print(f"Registration added successfully with ID: {db['last_id']}")
    print(f"Total registrations: {len(db['registrations'])}")
    return db["last_id"]

def get_all_registrations():
    """Get all registrations sorted by created_at (newest first)"""
    db = read_db()
    registrations = db["registrations"]
    print(f"Retrieved {len(registrations)} registrations from database")
    # Sort by created_at descending (newest first)
    registrations.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return registrations

# Initialize database
init_db()

# ---------------- HELPERS ----------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_events_with_categories(form_data):
    """Parse events and their categories from form data"""
    selected_events = form_data.getlist("events")
    events_list = []
    
    for i, event in enumerate(selected_events):
        # Check if this event has categories
        category_key = f"category_{i}"
        if category_key in form_data:
            category = form_data.get(category_key)
            events_list.append(f"{event} - {category}")
        else:
            events_list.append(event)
    
    print(f"Parsed events: {events_list}")
    return events_list

def calculate_total_from_events(events_list, college):
    """Calculate total amount from events list"""
    total = 0
    for event in events_list:
        price = EVENT_PRICES.get(event, 0)
        if college == "Mangalmay Group of Institutions":
            price = price // 2
        total += price
    print(f"Total calculated: ₹{total} for {len(events_list)} events")
    return total

# ---------------- ROUTES ----------------
@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        step = request.form.get("step")
        print(f"Processing step: {step}")
        
        name = request.form.get("student_name")
        roll = request.form.get("roll_no")
        course = request.form.get("course")
        college = request.form.get("college")
        college_id = request.form.get("college_id", "")
        other_college = request.form.get("other_college", "")
        group_members = request.form.get("group_members", "")
        contact_numbers = request.form.get("contact_numbers")
        
        # Parse events with categories
        events_list = parse_events_with_categories(request.form)

        session['form_data'] = {
            'student_name': name,
            'roll_no': roll,
            'course': course,
            'college': college,
            'college_id': college_id,
            'other_college': other_college,
            'group_members': group_members,
            'contact_numbers': contact_numbers
        }
        session['selected_events'] = events_list

        if step == "qr":
            if not events_list:
                print("No events selected!")
                return render_template("register.html", 
                                     form_data=session.get('form_data', {}),
                                     error="Please select at least one event",
                                     banner_exists=os.path.exists('static/images/zeal_banner.jpeg'))

            total = calculate_total_from_events(events_list, college)

            upi_link = (
                f"upi://pay?"
                f"pa=9871223900@ptaxis&"
                f"pn=ZEAL10&"
                f"am={total}&"
                f"cu=INR"
            )

            qr_file = f"{roll}_qr.png"
            qr_path = os.path.join(QR_DIR, qr_file)
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(upi_link)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(qr_path)
            
            print(f"QR code generated: {qr_file}")

            return render_template(
                "register.html",
                qr=qr_file,
                total=total,
                form_data=session.get('form_data', {}),
                selected_events=session.get('selected_events', []),
                banner_exists=os.path.exists('static/images/zeal_banner.jpeg')
            )

        if step == "final":
            screenshot = request.files.get("payment_screenshot")
            
            if not screenshot or screenshot.filename == '':
                print("No screenshot uploaded!")
                return "Payment screenshot required", 400
                
            if not allowed_file(screenshot.filename):
                print(f"Invalid file format: {screenshot.filename}")
                return "Invalid file format. Please upload PNG, JPG, or JPEG", 400

            screenshot_name = secure_filename(f"{roll}_{screenshot.filename}")
            screenshot_path = os.path.join(UPLOAD_DIR, screenshot_name)
            screenshot.save(screenshot_path)
            print(f"Screenshot saved: {screenshot_name}")

            total = calculate_total_from_events(events_list, college)

            try:
                registration_data = {
                    "student_name": name,
                    "roll_no": roll,
                    "course": course,
                    "college": college,
                    "college_id": college_id,
                    "other_college": other_college,
                    "events": ", ".join(events_list),
                    "group_members": group_members,
                    "contact_numbers": contact_numbers,
                    "total_amount": total,
                    "payment_screenshot": screenshot_name,
                    "payment_status": "Submitted"
                }
                
                reg_id = add_registration(registration_data)
                print(f"Registration completed with ID: {reg_id}")
                
                session.pop('form_data', None)
                session.pop('selected_events', None)
                
                return render_template("register.html", 
                                     success=True,
                                     registration_id=reg_id,
                                     form_data={},
                                     selected_events=[],
                                     banner_exists=os.path.exists('static/images/zeal_banner.jpeg'))
            
            except Exception as e:
                print(f"Database error: {e}")
                import traceback
                traceback.print_exc()
                return f"Registration failed: {str(e)}", 500

    return render_template("register.html", 
                         form_data=session.get('form_data', {}),
                         selected_events=session.get('selected_events', []),
                         banner_exists=os.path.exists('static/images/zeal_banner.jpeg'))

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():
    try:
        data = get_all_registrations()
        print(f"Displaying {len(data)} registrations on admin page")
        
        # Convert created_at strings to datetime objects for template
        for row in data:
            if 'created_at' in row and isinstance(row['created_at'], str):
                try:
                    row['created_at'] = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
                except:
                    row['created_at'] = None
        
        return render_template("admin.html", data=data)
    except Exception as e:
        print(f"Error loading admin page: {e}")
        import traceback
        traceback.print_exc()
        return f"Error loading admin page: {str(e)}", 500

# ---------------- EXPORT TO EXCEL ----------------
@app.route("/admin/export")
def export_excel():
    try:
        data = get_all_registrations()
        print(f"Exporting {len(data)} registrations")

        if not data:
            # Create empty DataFrame with column headers
            df = pd.DataFrame(columns=[
                'id', 'student_name', 'roll_no', 'course', 'college', 
                'college_id', 'other_college', 'events', 'group_members', 
                'contact_numbers', 'total_amount', 'payment_screenshot', 
                'payment_status', 'created_at'
            ])
        else:
            # Create DataFrame
            df = pd.DataFrame(data)
            
            # Reorder columns for better readability
            column_order = [
                'id', 'student_name', 'roll_no', 'course', 'college', 
                'college_id', 'other_college', 'events', 'group_members', 
                'contact_numbers', 'total_amount', 'payment_status',
                'payment_screenshot', 'created_at'
            ]
            
            # Only include columns that exist in the dataframe
            column_order = [col for col in column_order if col in df.columns]
            df = df[column_order]
        
            # Format created_at column
            if 'created_at' in df.columns and not df.empty:
                df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%d-%m-%Y %H:%M:%S')
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Registrations')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Registrations']
            for idx, col in enumerate(df.columns):
                if not df.empty:
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(str(col))
                    ) + 2
                else:
                    max_length = len(str(col)) + 2
                    
                # Excel column letters
                if idx < 26:
                    col_letter = chr(65 + idx)
                else:
                    col_letter = chr(65 + idx // 26 - 1) + chr(65 + idx % 26)
                    
                worksheet.column_dimensions[col_letter].width = min(max_length, 50)
        
        output.seek(0)
        
        filename = f"ZEAL_10_Registrations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        print(f"Excel exported: {filename}")
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        print(f"Error exporting data: {e}")
        import traceback
        traceback.print_exc()
        return f"Error exporting data: {str(e)}", 500

# ---------------- VIEW PAYMENT SCREENSHOT ----------------
@app.route("/uploads/payments/<filename>")
def view_payment(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# ---------------- DEBUG ROUTE ----------------
@app.route("/debug/db")
def debug_db():
    """Debug route to check database contents"""
    try:
        db = read_db()
        return {
            "total_registrations": len(db.get("registrations", [])),
            "last_id": db.get("last_id", 0),
            "database_file_exists": os.path.exists(DB_FILE),
            "database_path": os.path.abspath(DB_FILE),
            "registrations": db.get("registrations", [])
        }
    except Exception as e:
        return {"error": str(e)}, 500

# ---------------- START ----------------
if __name__ == "__main__":
    print(f"Starting ZEAL 10.0 Registration System")
    print(f"Database file: {os.path.abspath(DB_FILE)}")
    print(f"Upload directory: {os.path.abspath(UPLOAD_DIR)}")
    print(f"QR directory: {os.path.abspath(QR_DIR)}")
    app.run(host="0.0.0.0", port=5000, debug=True)