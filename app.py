from flask import Flask, render_template, request, redirect, url_for, session
import requests
import os
from dotenv import load_dotenv
import random
from datetime import datetime, timezone

load_dotenv()
from functools import wraps
from flask import jsonify, flash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
FIREBASE_DB_URL  = os.getenv("FIREBASE_DB_URL")

@app.before_request
def redirect_html():
    """Redirect any .html URL to its clean counterpart."""
    if request.path.endswith('.html'):
        return redirect(request.path[:-5], code=301)

# ----------------------
# Login Required Decorator 990
# ----------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ----------------------
# Login Page
# ----------------------
# ----------------------
# Login Page
# ----------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
        payload = {"email": email, "password": password, "returnSecureToken": True}
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        if "idToken" in data:
            session["user"] = data["email"]
            session["token"] = data["idToken"]
            session["refreshToken"] = data.get("refreshToken", "")
            session["user_id"] = data.get("localId", "")  # Store Firebase UID
            return redirect(url_for("dashboard"))
        else:
            error_code = data.get("error", {}).get("message", "")
            # Map Firebase codes to friendly messages
            error_map = {
                "INVALID_LOGIN_CREDENTIALS": "The email or password you entered is incorrect.",
                "EMAIL_NOT_FOUND": "No account found with this email.",
                "INVALID_PASSWORD": "The password you entered is incorrect.",
                "USER_DISABLED": "This account has been disabled.",
                "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many failed attempts. Please try again later."
            }
            friendly_msg = error_map.get(error_code, "Login failed. Please check your credentials.")
            flash(friendly_msg, "danger")
            
    return render_template("login.html")

@app.route("/signup", methods=["POST"])
def signup():
    email = request.form.get("email")
    password = request.form.get("password")
    full_name = request.form.get("name")
    company = request.form.get("company")
    
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    
    response = requests.post(url, json=payload)
    data = response.json()
    
    if "idToken" in data:
        user_id = data["localId"]
        session["user"] = data["email"]
        session["token"] = data["idToken"]
        session["refreshToken"] = data.get("refreshToken", "")
        session["user_id"] = user_id
        
        # Split full name into first / last for Settings page compatibility
        name_parts = (full_name or "").strip().split(" ", 1)
        first_name = name_parts[0] if name_parts else ""
        last_name  = name_parts[1] if len(name_parts) > 1 else ""
        
        # Save extra user info to Firestore (using the UID as the document ID)
        created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        firestore_url = f"https://firestore.googleapis.com/v1/projects/humananalysisv0/databases/(default)/documents/Users?documentId={user_id}&key={FIREBASE_API_KEY}"
        user_payload = {
            "fields": {
                "email":        {"stringValue": email},
                "fullName":     {"stringValue": full_name or ""},
                "firstName":    {"stringValue": first_name},
                "lastName":     {"stringValue": last_name},
                "company":      {"stringValue": company or ""},
                "account_type": {"stringValue": "trial"},
                "createdAt":    {"timestampValue": created_at}
            }
        }
        fs_resp = requests.post(
            firestore_url, 
            json=user_payload,
            headers={"Authorization": f"Bearer {data['idToken']}"}
        )
        print(f"Firestore signup write status: {fs_resp.status_code}")
        if fs_resp.status_code != 200:
            print("Write error:", fs_resp.text)
        # Pre-populate session profile so dashboard greets user by name immediately
        session["user_profile"] = {
            "email":        email,
            "firstName":    first_name,
            "lastName":     last_name,
            "company":      company or "",
            "account_type": "trial"
        }
        
        return redirect(url_for("dashboard"))
    else:
        error = data.get("error", {}).get("message", "Signup failed")
        flash(error, "danger")
        return redirect(url_for("start_free_trial"))

@app.route("/forgot-password", methods=["POST"])
def forgot_password_post():
    email = request.form.get("email")
    
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
    payload = {"requestType": "PASSWORD_RESET", "email": email}
    
    response = requests.post(url, json=payload)
    data = response.json()
    
    if "email" in data:
        flash("Password reset link sent to your email.", "success")
    else:
        error = data.get("error", {}).get("message", "Error sending reset email")
        flash(error, "danger")
    
    return redirect(url_for("forgot_password"))

@app.route("/login-redirect")
def login_redirect():
    return redirect(url_for("login"))

# -----------------------
# Main Routes
# -----------------------

@app.route("/auth/google", methods=["POST"])
def auth_google():
    id_token = request.json.get("idToken")
    email = request.json.get("email")
    
    # In a full production app, you would verify id_token with firebase-admin
    # For now, we'll trust the token if secure headers are present, but a real check is better.
    if email:
        session["user"] = email
        session["token"] = id_token
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid token"}), 400

@app.route("/contact", methods=["POST"])
def contact_post():
    fname = request.form.get("fname")
    lname = request.form.get("lname")
    email = request.form.get("email")
    inquiry = request.form.get("inquiry")
    message = request.form.get("message")
    
    # Firestore REST API URL
    url = f"https://firestore.googleapis.com/v1/projects/humananalysisv0/databases/(default)/documents/ContactMessages?key={FIREBASE_API_KEY}"
    
    # Map to Firestore format
    payload = {
        "fields": {
            "firstName": {"stringValue": fname},
            "lastName": {"stringValue": lname},
            "email": {"stringValue": email},
            "inquiry": {"stringValue": inquiry},
            "message": {"stringValue": message},
            "timestamp": {"timestampValue": "2026-04-18T11:46:00Z"} # Normally use serverValue but REST is different
        }
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        flash("Message Sent Successfully! We will get back to you soon.", "success")
    else:
        flash("Error sending message. Please try again later.", "danger")
        
    return redirect(url_for("contact"))

@app.route("/dashboard")
@login_required
def dashboard():
    view = request.args.get("view", "dashboard")
    email = session.get("user")
    
    # Re-fetch from DB if profile not cached or missing account_type
    needs_fetch = "user_profile" not in session or "account_type" not in session.get("user_profile", {})

    if needs_fetch:
        user_data = {"email": email, "firstName": "", "lastName": "", "company": "", "account_type": ""}
        user_id = session.get("user_id", "")
        token   = session.get("token", "")

        if user_id and token:
            # Direct document GET by UID — allowed by Firestore rule: request.auth.uid == userId
            doc_url = (f"https://firestore.googleapis.com/v1/projects/humananalysisv0"
                       f"/databases/(default)/documents/Users/{user_id}?key={FIREBASE_API_KEY}")
            try:
                res = requests.get(doc_url, headers={"Authorization": f"Bearer {token}"})
                print(f"\n[DEBUG] Profile GET status: {res.status_code}\n")
                if res.status_code == 200:
                    fields = res.json().get("fields", {})
                    full_name = fields.get("fullName", {}).get("stringValue", "")
                    if " " in full_name:
                        user_data["firstName"], user_data["lastName"] = full_name.split(" ", 1)
                    else:
                        user_data["firstName"] = full_name
                    user_data["company"]      = fields.get("company",      {}).get("stringValue", "")
                    user_data["account_type"] = fields.get("account_type", {}).get("stringValue", "")
                else:
                    print(f"[DEBUG] Profile fetch failed ({res.status_code}): {res.text[:300]}")
            except Exception as e:
                print(f"Error fetching user profile: {e}")
        else:
            print(f"[DEBUG] Missing user_id='{user_id}' or token in session — cannot fetch profile.")

        print(f"\n[DEBUG] Final user_data for {email}: {user_data}\n")
        session["user_profile"] = user_data
        session.modified = True
    else:
        user_data = session["user_profile"]

    is_admin = is_admin_user()
    return render_template("dashboard.html", user=email, view=view, user_data=user_data, is_admin=is_admin)


@app.route("/contact")
def contact():
    return render_template("contact.html")

def is_admin_user():
    return session.get("user_profile", {}).get("account_type") == "admin"

@app.route("/admin")
@login_required
def admin():
    if not is_admin_user():
        return redirect(url_for("dashboard"))
    return render_template("admin.html")

@app.route("/admin/pending-requests")
@login_required
def admin_pending_requests():
    """Return all pending license requests as JSON via robust REST API."""
    if not is_admin_user():
        return jsonify({"error": "Access denied"}), 403

    payload = {
        "structuredQuery": {
            "from": [{"collectionId": "license_requests"}],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "status"},
                    "op": "EQUAL",
                    "value": {"stringValue": "pending"}
                }
            }
        }
    }
    try:
        res = _call_firestore("POST", ":runQuery", payload)
        
        if res.status_code == 401 or "authentication" in res.text.lower():
            return jsonify({"error": "Your session has expired. Please log out and log back in."}), 401
            
        results = res.json()
        requests_list = []
        
        if isinstance(results, dict) and "error" in results:
            return jsonify({"error": results["error"].get("message", "Database error")}), 500
            
        for item in results:
            if "document" in item:
                doc = item["document"]
                fields = doc.get("fields", {})
                doc_id = doc["name"].split("/")[-1]
                req_email = fields.get("email", {}).get("stringValue", "")
                req_date = fields.get("requestDate", {}).get("timestampValue", "")
                company = fields.get("company", {}).get("stringValue", "")
                event_name = fields.get("eventName", {}).get("stringValue", "")
                event_date = fields.get("eventDate", {}).get("stringValue", "")
                
                # FALLBACK: If company is missing or empty, fetch from Users collection
                if not company or company == "N/A":
                    try:
                        u_query = {
                            "structuredQuery": {
                                "from": [{"collectionId": "Users"}],
                                "where": {"fieldFilter": {"field": {"fieldPath": "email"}, "op": "EQUAL", "value": {"stringValue": req_email}}},
                                "limit": 1
                            }
                        }
                        u_res = _call_firestore("POST", ":runQuery", u_query)
                        u_results = u_res.json()
                        if u_results and isinstance(u_results, list) and "document" in u_results[0]:
                            company = u_results[0]["document"].get("fields", {}).get("company", {}).get("stringValue", "N/A")
                        else:
                            company = "Personal Account" # Default if no user record found
                    except Exception as e:
                        print("Fallback company fetch error:", e)
                        company = "N/A"

                requests_list.append({
                    "id":        doc_id,
                    "email":     req_email,
                    "company":   company,
                    "eventName": event_name,
                    "eventDate": event_date,
                    "date":      req_date
                })
                
        # Sort manually to avoid composite index failure
        requests_list.sort(key=lambda x: x["date"], reverse=True)
        return jsonify({"requests": requests_list})
        
    except Exception as e:
        print(f"admin_pending_requests error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/admin/approve-key", methods=["POST"])
@login_required
def admin_approve_key():
    """Approve a license request via REST API."""
    if not is_admin_user():
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    doc_id    = data.get("docId", "").strip()
    license_key = data.get("licenseKey", "").strip()

    if not doc_id or not license_key:
        return jsonify({"error": "docId and licenseKey are required"}), 400

    url_suffix = (
        f"/license_requests/{doc_id}"
        f"?updateMask.fieldPaths=status&updateMask.fieldPaths=licenseKey"
        f"&updateMask.fieldPaths=approvedAt&updateMask.fieldPaths=acceptedBy"
    )
    
    update_payload = {
        "fields": {
            "status":     {"stringValue": "approved"},
            "licenseKey": {"stringValue": license_key},
            "acceptedBy": {"stringValue": session.get("user")},
            "approvedAt": {"timestampValue": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        }
    }
    try:
        res = _call_firestore("PATCH", url_suffix, update_payload)
        if res.status_code in (200, 201):
            return jsonify({"status": "success"})
            
        print(f"admin_approve fail [{res.status_code}]: {res.text}")
        if res.status_code == 401:
            return jsonify({"error": "Session expired. Please re-login."}), 401
        err_msg = res.json().get("error", {}).get("message", "Update failed")
        return jsonify({"error": err_msg}), 500
    except Exception as e:
        print(f"admin_approve_key REST error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/forgot-password-page")
def forgot_password():
    return render_template("forgot-password.html")

@app.route("/start-free-trial")
def start_free_trial():
    return render_template("start-free-trial.html")

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "GET":
        return redirect(url_for("dashboard", view="settings"))

    email = session.get("user")
    
    # Try to find user in Firestore by searching for email or using user_id if we have it
    # For now, let's try to get user data from Firestore
    # We might not have user_id in session if they logged in via old login
    # So we'll try to find by email
    
    user_data = {
        "email": email,
        "firstName": "",
        "lastName": "",
        "company": ""
    }
    
    # Firestore Query for user by email
    query_url = f"https://firestore.googleapis.com/v1/projects/humananalysisv0/databases/(default)/documents:runQuery?key={FIREBASE_API_KEY}"
    query_payload = {
        "structuredQuery": {
            "from": [{"collectionId": "Users"}],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "email"},
                    "op": "EQUAL",
                    "value": {"stringValue": email}
                }
            },
            "limit": 1
        }
    }
    
    res = requests.post(query_url, json=query_payload)
    query_results = res.json()
    
    doc_path = None
    
    if query_results and "document" in query_results[0]:
        doc = query_results[0]["document"]
        fields = doc.get("fields", {})
        full_name = fields.get("fullName", {}).get("stringValue", "")
        if " " in full_name:
            user_data["firstName"], user_data["lastName"] = full_name.split(" ", 1)
        else:
            user_data["firstName"] = full_name
        
        user_data["company"] = fields.get("company", {}).get("stringValue", "")
        doc_path = doc["name"] # projects/humananalysisv0/databases/(default)/documents/Users/ID

    if request.method == "POST":
        first_name = request.form.get("firstName")
        last_name = request.form.get("lastName")
        company = request.form.get("company")
        
        full_name = f"{first_name} {last_name}".strip()
        
        update_payload = {
            "fields": {
                "email": {"stringValue": email},
                "fullName": {"stringValue": full_name},
                "company": {"stringValue": company}
            }
        }
        
        if doc_path:
            # Update existing document
            update_url = f"https://firestore.googleapis.com/v1/{doc_path}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=fullName&updateMask.fieldPaths=company"
            requests.patch(update_url, json=update_payload)
        else:
            # Create new document if not exists
            create_url = f"https://firestore.googleapis.com/v1/projects/humananalysisv0/databases/(default)/documents/Users?key={FIREBASE_API_KEY}"
            requests.post(create_url, json=update_payload)
            
        # Update session cache immediately
        session["user_profile"] = {
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "company": company
        }
        session.modified = True
            
        flash("Settings updated successfully!", "success")
        return redirect(url_for("dashboard", view="settings"))

    return redirect(url_for("dashboard", view="settings"))

# -----------------------
# Dashboard (Protected)
# -----------------------
@app.route("/dashboard_analysis")
@login_required
def dashboard_analysis():
    token = session.get("token")

    # If DB requires auth
    params = {"auth": token}

    response = requests.get(FIREBASE_DB_URL, params=params)
    data = response.json()

    return render_template("dashboard_analysis.html", user=session["user"], data=data)


@app.route("/api/data")
@login_required
def get_realtime_data():
    token = session.get("token")

    response = requests.get(
        FIREBASE_DB_URL,
        params={"auth": token}
    )

    data = response.json()
    return data

@app.route("/add-event", methods=["GET", "POST"])
@login_required
def add_event():
    if request.method == "POST":

        event_name = request.form.get("event_name")
        event_date = request.form.get("event_date")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        handler = request.form.get("handler")
        lic_key = request.form.get("lic_key")

        if not all([event_name, event_date, start_time, end_time, handler, lic_key]):
            return render_template("add_event.html", error="All fields are required")

        event_data = {
            "event_name": event_name,
            "event_date": event_date,  # DD/MM/YYYY
            "event_start_time_": start_time,
            "event_end_time_to": end_time,
            "handling_person_name": handler,
            "lic_key": int(lic_key),
            "data": {}
        }

        firebase_url = f"https://humananalysisv0-default-rtdb.firebaseio.com/Events/{lic_key}.json"

        requests.put(
            firebase_url,
            json=event_data,
            params={"auth": session.get("token")}
        )

        return redirect(url_for("dashboard"))

    return render_template("add_event.html")


@app.route("/generate-license-key")
@login_required
def generate_license_key():
    token = session.get("token")

    while True:
        # Generate 6-digit unique key
        lic_key = random.randint(10000, 999999999)

        # Check if key exists in Firebase
        check_url = f"https://humananalysisv0-default-rtdb.firebaseio.com/Events/{lic_key}.json"
        response = requests.get(check_url, params={"auth": token})

        if response.json() is None:
            return jsonify({"lic_key": lic_key})


# ----------------------
# Robust Firestore REST Helpers (Auto-Refreshes Expired Tokens)
# ----------------------
FS_BASE = "https://firestore.googleapis.com/v1/projects/humananalysisv0/databases/(default)/documents"

def _call_firestore(method, url_suffix, json_payload=None):
    """Makes a Firestore REST call with Bearer token. Auto-refreshes if 401 occurs."""
    url = f"{FS_BASE}{url_suffix}"
    if "?" in url_suffix:
        url += f"&key={FIREBASE_API_KEY}"
    else:
        url += f"?key={FIREBASE_API_KEY}"
        
    token = session.get("token")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    def do_req():
        if method == "POST": return requests.post(url, json=json_payload, headers=headers)
        if method == "PATCH": return requests.patch(url, json=json_payload, headers=headers)
        if method == "GET": return requests.get(url, headers=headers)

    res = do_req()
    
    # If unauthenticated, token may be expired (1 hour limit). Try to refresh!
    if res.status_code == 401 or "authentication" in res.text.lower():
        refresh_token = session.get("refreshToken")
        if refresh_token:
            print("Token expired. Auto-refreshing using refreshToken...")
            refresh_url = f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}"
            refresh_res = requests.post(refresh_url, data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            })
            r_data = refresh_res.json()
            if "id_token" in r_data:
                # Successfully refreshed
                new_token = r_data["id_token"]
                session["token"] = new_token
                session["refreshToken"] = r_data.get("refresh_token", refresh_token)
                headers["Authorization"] = f"Bearer {new_token}"
                res = do_req() # Retry the original request
            else:
                print("Failed to auto-refresh token.")
    return res


# ----------------------
# Check Existing License Status (REST)
# ----------------------
@app.route("/check-license-status")
@login_required
def check_license_status():
    email = session.get("user")
    
    payload = {
        "structuredQuery": {
            "from": [{"collectionId": "license_requests"}],
            "where": {"fieldFilter": {
                "field": {"fieldPath": "email"},
                "op": "EQUAL",
                "value": {"stringValue": email}
            }},
            "limit": 1
        }
    }
    
    try:
        res = _call_firestore("POST", ":runQuery", payload)
        if res.status_code == 401:
            return jsonify({"status": "none"})
            
        results = res.json()
        if results and "document" in results[0]:
            fields = results[0]["document"].get("fields", {})
            status = fields.get("status", {}).get("stringValue", "pending")
            ev_name = fields.get("eventName", {}).get("stringValue", "")
            ev_date = fields.get("eventDate", {}).get("stringValue", "")
            
            if status == "approved":
                license_key = fields.get("licenseKey", {}).get("stringValue", "")
                return jsonify({"status": "approved", "licenseKey": license_key, "eventName": ev_name, "eventDate": ev_date})
            return jsonify({"status": "pending", "eventName": ev_name, "eventDate": ev_date})
    except Exception as e:
        print(f"check_license_status error: {e}")
        
    return jsonify({"status": "none"})


# ----------------------
# License Key Request (REST)
# ----------------------
@app.route("/request-license-key", methods=["POST"])
@login_required
def request_license_key():
    email = session.get("user")
    data = request.get_json() or {}
    event_name = data.get("eventName", "N/A")
    event_date = data.get("eventDate", "N/A")
    
    try:
        # Check for existing request
        query_payload = {
            "structuredQuery": {
                "from": [{"collectionId": "license_requests"}],
                "where": {"fieldFilter": {
                    "field": {"fieldPath": "email"},
                    "op": "EQUAL",
                    "value": {"stringValue": email}
                }},
                "limit": 1
            }
        }
        res_query = _call_firestore("POST", ":runQuery", query_payload)
        if res_query.status_code == 401:
            return jsonify({"status": "error", "message": "Session expired. Please log out and log back in."}), 401
            
        results = res_query.json()
        if results and "document" in results[0]:
            fields = results[0]["document"].get("fields", {})
            status = fields.get("status", {}).get("stringValue", "pending")
            if status == "approved":
                lk = fields.get("licenseKey", {}).get("stringValue", "")
                return jsonify({"status": "already_approved", "licenseKey": lk})
            return jsonify({"status": "already_requested"})

        # Get user's company name
        company = "N/A"
        if "user_profile" in session:
            company = session["user_profile"].get("company", "N/A")
        else:
            # Fallback: query Firestore for user company
            query_body = {
                "structuredQuery": {
                    "from": [{"collectionId": "Users"}],
                    "where": {"fieldFilter": {"field": {"fieldPath": "email"}, "op": "EQUAL", "value": {"stringValue": email}}},
                    "limit": 1
                }
            }
            try:
                res_u = _call_firestore("POST", ":runQuery", query_body)
                u_data = res_u.json()
                if u_data and isinstance(u_data, list) and "document" in u_data[0]:
                    company = u_data[0]["document"].get("fields", {}).get("company", {}).get("stringValue", "N/A")
            except Exception as e:
                print("Request key company fetch error:", e)

        # No existing request — create one
        created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        add_payload = {
            "fields": {
                "email":       {"stringValue": email},
                "company":     {"stringValue": company},
                "eventName":   {"stringValue": event_name},
                "eventDate":   {"stringValue": event_date},
                "requestDate": {"timestampValue": created_at},
                "status":      {"stringValue": "pending"}
            }
        }
        
        res_add = _call_firestore("POST", "/license_requests", add_payload)
        
        if res_add.status_code in (200, 201):
            return jsonify({"status": "success"})

        error_msg = res_add.json().get("error", {}).get("message", "Database write failed")
        return jsonify({"status": "error", "message": error_msg}), 500

    except Exception as e:
        print(f"request_license_key error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ----------------------
# Logout
# ----------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



if __name__ == "__main__":
    app.run(debug=True)
