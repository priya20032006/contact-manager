from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = "contact-manager-secret-key"

DATABASE = "contacts.db"


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            address TEXT,
            company TEXT,
            category TEXT DEFAULT 'Other',
            notes TEXT,
            is_favorite INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------- HOME ----------------

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "danger")
            return redirect(url_for("register"))

        conn = get_db()

        existing_user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_user:
            conn.close()
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        conn.execute("""
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
        """, (name, email, hashed_password))

        conn.commit()
        conn.close()

        flash("Registration successful. Please login.", "success")

        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            flash("Login successful.", "success")

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("login"))


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    contacts = conn.execute("""
        SELECT *
        FROM contacts
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user_id"],)).fetchall()

    total = conn.execute("""
        SELECT COUNT(*) AS count
        FROM contacts
        WHERE user_id = ?
    """, (session["user_id"],)).fetchone()["count"]

    favorites = conn.execute("""
        SELECT COUNT(*) AS count
        FROM contacts
        WHERE user_id = ?
        AND is_favorite = 1
    """, (session["user_id"],)).fetchone()["count"]

    conn.close()

    return render_template(
        "dashboard.html",
        contacts=contacts,
        total=total,
        favorites=favorites
    )


# ---------------- ADD CONTACT ----------------

@app.route("/contact/add", methods=["GET", "POST"])
def add_contact():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        address = request.form["address"].strip()
        company = request.form["company"].strip()
        category = request.form["category"]
        notes = request.form["notes"].strip()

        if not name:
            flash("Contact name is required.", "danger")
            return redirect(url_for("add_contact"))

        conn = get_db()

        conn.execute("""
            INSERT INTO contacts
            (
                user_id,
                name,
                email,
                phone,
                address,
                company,
                category,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            name,
            email,
            phone,
            address,
            company,
            category,
            notes
        ))

        conn.commit()
        conn.close()

        flash("Contact added successfully.", "success")

        return redirect(url_for("dashboard"))

    return render_template("add_contact.html")


# ---------------- EDIT CONTACT ----------------

@app.route("/contact/edit/<int:contact_id>", methods=["GET", "POST"])
def edit_contact(contact_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    contact = conn.execute("""
        SELECT *
        FROM contacts
        WHERE id = ?
        AND user_id = ?
    """, (
        contact_id,
        session["user_id"]
    )).fetchone()

    if not contact:
        conn.close()
        flash("Contact not found.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        address = request.form["address"].strip()
        company = request.form["company"].strip()
        category = request.form["category"]
        notes = request.form["notes"].strip()

        conn.execute("""
            UPDATE contacts

            SET
                name = ?,
                email = ?,
                phone = ?,
                address = ?,
                company = ?,
                category = ?,
                notes = ?

            WHERE id = ?
            AND user_id = ?
        """, (
            name,
            email,
            phone,
            address,
            company,
            category,
            notes,
            contact_id,
            session["user_id"]
        ))

        conn.commit()
        conn.close()

        flash("Contact updated successfully.", "success")

        return redirect(url_for("dashboard"))

    conn.close()

    return render_template(
        "edit_contact.html",
        contact=contact
    )


# ---------------- DELETE CONTACT ----------------

@app.route("/contact/delete/<int:contact_id>")
def delete_contact(contact_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute("""
        DELETE FROM contacts
        WHERE id = ?
        AND user_id = ?
    """, (
        contact_id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    flash("Contact deleted successfully.", "success")

    return redirect(url_for("dashboard"))


# ---------------- FAVORITE ----------------

@app.route("/contact/favorite/<int:contact_id>")
def favorite_contact(contact_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    contact = conn.execute("""
        SELECT is_favorite
        FROM contacts
        WHERE id = ?
        AND user_id = ?
    """, (
        contact_id,
        session["user_id"]
    )).fetchone()

    if contact:

        new_status = 0 if contact["is_favorite"] else 1

        conn.execute("""
            UPDATE contacts
            SET is_favorite = ?
            WHERE id = ?
            AND user_id = ?
        """, (
            new_status,
            contact_id,
            session["user_id"]
        ))

        conn.commit()

    conn.close()

    return redirect(url_for("dashboard"))


# ---------------- PROFILE ----------------

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (session["user_id"],)).fetchone()

    if request.method == "POST":

        name = request.form["name"].strip()

        if name:

            conn.execute("""
                UPDATE users
                SET name = ?
                WHERE id = ?
            """, (
                name,
                session["user_id"]
            ))

            conn.commit()

            session["user_name"] = name

            flash("Profile updated successfully.", "success")

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )


# ---------------- SEARCH ----------------

@app.route("/search")
def search():

    if "user_id" not in session:
        return redirect(url_for("login"))

    query = request.args.get("q", "").strip()

    conn = get_db()

    contacts = conn.execute("""
        SELECT *
        FROM contacts

        WHERE user_id = ?

        AND (
            name LIKE ?
            OR email LIKE ?
            OR phone LIKE ?
            OR company LIKE ?
        )

        ORDER BY id DESC
    """, (
        session["user_id"],
        f"%{query}%",
        f"%{query}%",
        f"%{query}%",
        f"%{query}%"
    )).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        contacts=contacts,
        total=len(contacts),
        favorites=0,
        search_query=query
    )


# ---------------- START ----------------

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )
