from flask import Flask, render_template, request, jsonify, redirect, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import certifi

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- MONGODB ----------------
MONGO_URI = os.getenv("MONGO_URI")   # 🔐 put your MongoDB URI

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
    tls=True,
    tlsCAFile=certifi.where()
)
db = client["chatbot_db"]

faq_collection = db["faq"]
unknown_collection = db["unknown_queries"]   # ✅ correct name

# ---------------- HELPERS ----------------
def clean(text):
    return text.lower().strip().replace("?", "")

def get_answer(user_input):
    user_input = clean(user_input)

    stop_words = {"what","is","the","are","me","tell","about","please"}
    user_words = set(user_input.split()) - stop_words

    rows = list(faq_collection.find())

    best_match = None
    max_score = 0

    for r in rows:
        db_words = set(clean(r["question"]).split())
        score = len(user_words & db_words)

        if score > max_score and score >= 1:
            max_score = score
            best_match = r["answer"]

    return best_match


def store_unknown(q):
    q = clean(q)

    unknown_collection.update_one(
        {"question": q},
        {"$setOnInsert": {"question": q}},
        upsert=True
    )

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    msg = request.json.get("message", "").strip()

    if not msg:
        return jsonify({"reply": "Please enter a question"})

    reply = get_answer(msg)

    if not reply:
        store_unknown(msg)
        reply = "I don't know this yet. Admin will update soon."

    return jsonify({"reply": reply})


# ---------------- ADMIN ----------------
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/dashboard")
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    faq = list(faq_collection.find())
    unknown = list(unknown_collection.find().sort("_id", -1))  # latest first

    return render_template("admin.html", faq=faq, unknown=unknown)


# ---------------- ADD FAQ ----------------
@app.route("/add", methods=["POST"])
def add():
    if not session.get("admin"):
        return redirect("/admin")

    q = clean(request.form["question"])
    a = request.form["answer"]

    faq_collection.update_one(
        {"question": q},
        {"$set": {"answer": a}},
        upsert=True
    )

    # remove from unknown
    unknown_collection.delete_one({"question": q})

    return redirect("/dashboard")


# ---------------- UPDATE FAQ ----------------
@app.route("/update_faq/<id>", methods=["POST"])
def update_faq(id):
    if not session.get("admin"):
        return redirect("/admin")

    new_answer = request.form["answer"]

    faq_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"answer": new_answer}}
    )

    return redirect("/dashboard")


# ---------------- DELETE FAQ ----------------
@app.route("/delete_faq/<id>")
def delete_faq(id):
    if not session.get("admin"):
        return redirect("/admin")

    faq_collection.delete_one({"_id": ObjectId(id)})

    return redirect("/dashboard")


# ---------------- DELETE UNKNOWN ----------------
@app.route("/delete/<id>")
def delete(id):
    if not session.get("admin"):
        return redirect("/admin")

    unknown_collection.delete_one({"_id": ObjectId(id)})

    return redirect("/dashboard")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
