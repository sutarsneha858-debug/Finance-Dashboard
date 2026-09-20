
from flask import Flask, render_template, request, jsonify
import sqlite3, csv, io, re
from datetime import datetime, timedelta
from collections import defaultdict
from statistics import mean

app = Flask(__name__)
DB = "finpilot.db"

CATEGORIES = {
    "Food & Dining": ["swiggy", "zomato", "restaurant", "cafe", "coffee", "food", "dominos", "pizza"],
    "Shopping": ["amazon", "flipkart", "myntra", "shopping", "mall", "store"],
    "Transport": ["uber", "ola", "metro", "fuel", "petrol", "rapido", "transport"],
    "Bills & Utilities": ["electricity", "water", "internet", "wifi", "mobile", "recharge", "utility"],
    "Subscriptions": ["netflix", "spotify", "prime", "hotstar", "subscription", "adobe", "canva"],
    "Healthcare": ["pharmacy", "hospital", "doctor", "medical", "health"],
    "Education": ["course", "udemy", "college", "books", "education"],
    "Salary": ["salary", "payroll", "income", "credited"],
    "Housing": ["rent", "housing", "maintenance"],
    "Entertainment": ["movie", "cinema", "game", "entertainment"],
    "Travel": ["hotel", "flight", "airbnb", "travel"],
}

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        type TEXT NOT NULL,
        category TEXT NOT NULL,
        source TEXT DEFAULT 'manual'
    );
    CREATE TABLE IF NOT EXISTS budgets(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT UNIQUE NOT NULL,
        amount REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS goals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        target REAL NOT NULL,
        saved REAL NOT NULL DEFAULT 0,
        deadline TEXT
    );
    """)
    conn.commit()
    conn.close()

def categorize(description, tx_type="expense"):
    d = description.lower()
    if tx_type == "income":
        return "Salary" if any(x in d for x in ["salary","payroll","income"]) else "Other Income"
    for cat, words in CATEGORIES.items():
        if any(w in d for w in words):
            return cat
    return "Other"

def seed_demo():
    conn = get_db()
    if conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] > 0:
        return
    rows = [
        ("2026-09-01","Salary credited",65000,"income","Salary"),
        ("2026-09-02","House Rent",16000,"expense","Housing"),
        ("2026-09-03","Netflix Subscription",649,"expense","Subscriptions"),
        ("2026-09-04","Spotify Subscription",119,"expense","Subscriptions"),
        ("2026-09-05","Grocery Store",2850,"expense","Food & Dining"),
        ("2026-09-06","Uber",480,"expense","Transport"),
        ("2026-09-07","Amazon Shopping",3290,"expense","Shopping"),
        ("2026-09-09","Electricity Bill",1850,"expense","Bills & Utilities"),
        ("2026-09-10","Restaurant Dinner",1450,"expense","Food & Dining"),
        ("2026-09-11","Mobile Recharge",799,"expense","Bills & Utilities"),
        ("2026-09-12","Udemy Course",899,"expense","Education"),
        ("2026-09-13","Ola",340,"expense","Transport"),
        ("2026-09-14","Pharmacy",720,"expense","Healthcare"),
        ("2026-09-15","Netflix Subscription",649,"expense","Subscriptions"),
        ("2026-09-16","Amazon Shopping",2190,"expense","Shopping"),
        ("2026-09-17","Electricity Bill",1700,"expense","Bills & Utilities"),
        ("2026-08-01","Salary credited",65000,"income","Salary"),
        ("2026-08-02","House Rent",16000,"expense","Housing"),
        ("2026-08-04","Netflix Subscription",649,"expense","Subscriptions"),
        ("2026-08-05","Grocery Store",2100,"expense","Food & Dining"),
        ("2026-08-08","Amazon Shopping",1100,"expense","Shopping"),
        ("2026-08-10","Electricity Bill",1400,"expense","Bills & Utilities"),
        ("2026-08-12","Uber",320,"expense","Transport"),
        ("2026-08-15","Restaurant Dinner",850,"expense","Food & Dining"),
    ]
    conn.executemany("INSERT INTO transactions(date,description,amount,type,category) VALUES(?,?,?,?,?)", rows)
    conn.executemany("INSERT OR IGNORE INTO budgets(category,amount) VALUES(?,?)", [
        ("Food & Dining",6000),("Shopping",5000),("Transport",3000),
        ("Bills & Utilities",5000),("Subscriptions",1500),("Entertainment",2500),
        ("Education",3000),("Healthcare",2500),("Housing",18000)
    ])
    conn.execute("INSERT INTO goals(name,target,saved,deadline) VALUES(?,?,?,?)",
                 ("Emergency Fund",100000,30000,"2027-03-31"))
    conn.commit()
    conn.close()

def transactions(month=None):
    conn = get_db()
    if month:
        rows = conn.execute("SELECT * FROM transactions WHERE substr(date,1,7)=? ORDER BY date DESC", (month,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM transactions ORDER BY date DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def analytics(month="2026-09"):
    tx = transactions(month)
    income = sum(x["amount"] for x in tx if x["type"]=="income")
    expenses = sum(x["amount"] for x in tx if x["type"]=="expense")
    by_cat = defaultdict(float)
    for x in tx:
        if x["type"]=="expense":
            by_cat[x["category"]] += x["amount"]

    conn = get_db()
    budgets = {r["category"]: r["amount"] for r in conn.execute("SELECT * FROM budgets")}
    goals = [dict(r) for r in conn.execute("SELECT * FROM goals").fetchall()]
    conn.close()

    budget_status = []
    for cat, budget in budgets.items():
        spent = by_cat.get(cat, 0)
        budget_status.append({
            "category": cat, "budget": budget, "spent": round(spent,2),
            "remaining": round(budget-spent,2),
            "percent": round((spent/budget*100),1) if budget else 0
        })

    prev = month_before(month)
    prev_tx = transactions(prev)
    prev_by = defaultdict(float)
    for x in prev_tx:
        if x["type"]=="expense": prev_by[x["category"]] += x["amount"]
    changes = []
    for cat in set(by_cat)|set(prev_by):
        cur, old = by_cat.get(cat,0), prev_by.get(cat,0)
        changes.append({"category":cat,"current":round(cur,2),"previous":round(old,2),
                        "change":round(cur-old,2),
                        "percent":round((cur-old)/old*100,1) if old else None})
    changes.sort(key=lambda x: x["change"], reverse=True)

    return {
        "month": month, "income": round(income,2), "expenses": round(expenses,2),
        "savings": round(income-expenses,2),
        "savings_rate": round((income-expenses)/income*100,1) if income else 0,
        "categories": [{"category":k,"amount":round(v,2)} for k,v in sorted(by_cat.items(), key=lambda x:x[1], reverse=True)],
        "budgets": budget_status, "changes": changes,
        "goals": goals, "transactions": tx
    }

def month_before(month):
    y,m = map(int, month.split("-"))
    if m == 1: y,m = y-1,12
    else: m -= 1
    return f"{y:04d}-{m:02d}"

def recurring():
    alltx = transactions()
    groups = defaultdict(list)
    for x in alltx:
        if x["type"] == "expense":
            key = re.sub(r"[^a-z0-9 ]","",x["description"].lower()).strip()
            key = re.sub(r"\s+"," ",key)
            groups[key].append(x)
    result=[]
    for desc, items in groups.items():
        if len(items) >= 2:
            amounts=[i["amount"] for i in items]
            result.append({
                "description": items[0]["description"],
                "category": items[0]["category"],
                "average": round(mean(amounts),2),
                "occurrences": len(items),
                "last_date": max(i["date"] for i in items)
            })
    # Also surface subscription-like singletons
    for x in alltx:
        if x["category"]=="Subscriptions" and not any(r["description"]==x["description"] for r in result):
            result.append({"description":x["description"],"category":x["category"],
                           "average":x["amount"],"occurrences":1,"last_date":x["date"]})
    return sorted(result,key=lambda x:x["average"],reverse=True)

def unusual(month):
    tx = [x for x in transactions(month) if x["type"]=="expense"]
    vals=[x["amount"] for x in tx]
    if not vals: return []
    avg=mean(vals)
    # Simple explainable anomaly rule: transaction > 2x average or > category typical by a large amount.
    return [x for x in tx if x["amount"] > max(avg*2, 3000)]

def insights(data):
    out=[]
    if data["savings_rate"] < 10 and data["income"]:
        out.append("Your current savings rate is below 10% this month.")
    if data["categories"]:
        top=data["categories"][0]
        out.append(f"{top['category']} is your largest expense category at ₹{top['amount']:,.0f}.")
    for b in data["budgets"]:
        if b["percent"] >= 100:
            out.append(f"{b['category']} has exceeded its budget by ₹{abs(b['remaining']):,.0f}.")
        elif b["percent"] >= 80:
            out.append(f"{b['category']} has used {b['percent']:.0f}% of its budget.")
    if data["changes"]:
        c=data["changes"][0]
        if c["change"]>0:
            out.append(f"{c['category']} increased by ₹{c['change']:,.0f} compared with last month.")
    if not out:
        out.append("Your spending is currently within the tracked budget limits.")
    return out

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/dashboard")
def dashboard():
    month=request.args.get("month","2026-09")
    d=analytics(month)
    d["recurring"]=recurring()
    d["unusual"]=unusual(month)
    d["insights"]=insights(d)
    return jsonify(d)

@app.route("/api/transactions")
def api_transactions():
    return jsonify(transactions(request.args.get("month")))

@app.route("/api/upload", methods=["POST"])
def upload():
    f=request.files.get("file")
    if not f: return jsonify({"error":"No file uploaded"}),400
    try:
        content=f.read().decode("utf-8-sig")
        reader=csv.DictReader(io.StringIO(content))
        required={"date","description","amount"}
        if not required.issubset(set(reader.fieldnames or [])):
            return jsonify({"error":"CSV must contain date, description and amount columns."}),400
        conn=get_db(); count=0
        for row in reader:
            typ=(row.get("type") or "expense").strip().lower()
            if typ not in ("income","expense"): typ="expense"
            amount=float(str(row["amount"]).replace(",","").replace("₹","").strip())
            cat=(row.get("category") or "").strip() or categorize(row["description"],typ)
            conn.execute("INSERT INTO transactions(date,description,amount,type,category,source) VALUES(?,?,?,?,?,?)",
                         (row["date"],row["description"],amount,typ,cat,"upload"))
            count+=1
        conn.commit(); conn.close()
        return jsonify({"message":f"{count} transactions imported successfully."})
    except Exception as e:
        return jsonify({"error":f"Could not import file: {e}"}),400

@app.route("/api/budgets", methods=["POST"])
def save_budget():
    data=request.json
    conn=get_db()
    conn.execute("INSERT INTO budgets(category,amount) VALUES(?,?) ON CONFLICT(category) DO UPDATE SET amount=excluded.amount",
                 (data["category"],float(data["amount"])))
    conn.commit(); conn.close()
    return jsonify({"message":"Budget saved."})

@app.route("/api/goals", methods=["POST"])
def save_goal():
    data=request.json
    conn=get_db()
    conn.execute("INSERT INTO goals(name,target,saved,deadline) VALUES(?,?,?,?)",
                 (data["name"],float(data["target"]),float(data.get("saved",0)),data.get("deadline")))
    conn.commit(); conn.close()
    return jsonify({"message":"Goal created."})

@app.route("/api/ask", methods=["POST"])
def ask():
    q=request.json.get("question","").lower().strip()
    d=analytics("2026-09")
    if not q: return jsonify({"answer":"Ask me about spending, subscriptions, budgets, goals, or month-to-month changes."})
    if "most" in q or "highest" in q or "where" in q and "spend" in q:
        if d["categories"]:
            c=d["categories"][0]
            return jsonify({"answer":f"You spent the most on {c['category']}: ₹{c['amount']:,.2f} this month."})
    if "subscription" in q:
        r=recurring()
        subs=[x for x in r if x["category"]=="Subscriptions"]
        total=sum(x["average"] for x in subs)
        return jsonify({"answer":f"I found {len(subs)} subscription-related payment(s), averaging about ₹{total:,.2f} across the detected items.",
                        "items":subs})
    if "increase" in q or "compared" in q or "last month" in q:
        inc=[x for x in d["changes"] if x["change"]>0][:3]
        if inc:
            return jsonify({"answer":"The largest increases are: "+", ".join(f"{x['category']} (+₹{x['change']:,.0f})" for x in inc)+".",
                            "items":inc})
        return jsonify({"answer":"No category has increased compared with the previous month in the current dataset."})
    if "budget" in q or "committed" in q:
        total=sum(x["budget"] for x in d["budgets"]); spent=sum(x["spent"] for x in d["budgets"])
        return jsonify({"answer":f"₹{spent:,.0f} of ₹{total:,.0f} across your tracked category budgets has been used ({spent/total*100:.1f}%)." if total else "No budgets are configured yet."})
    if "goal" in q or "save" in q:
        gs=d["goals"]
        if gs:
            g=gs[0]; remain=max(g["target"]-g["saved"],0)
            return jsonify({"answer":f"Your {g['name']} is {g['saved']/g['target']*100:.1f}% funded. ₹{remain:,.0f} remains to reach the target."})
    return jsonify({"answer":"I can answer questions about your top spending category, subscriptions, month-over-month changes, budget usage, and savings goals. Try: “Where did I spend the most this month?”"})

@app.route("/api/reset", methods=["POST"])
def reset():
    conn=get_db()
    conn.execute("DELETE FROM transactions"); conn.execute("DELETE FROM budgets"); conn.execute("DELETE FROM goals")
    conn.commit(); conn.close(); seed_demo()
    return jsonify({"message":"Demo data restored."})

init_db()
seed_demo()

if __name__=="__main__":
    app.run(debug=True)
