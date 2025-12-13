import os
from datetime import date

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)
from flask_sqlalchemy import SQLAlchemy

# -------------------------------------------------
# APP + DATABASE SETUP
# -------------------------------------------------
app = Flask(__name__)
app.secret_key = "dev-secret-key-change-me"  # for sessions & flash messages (demo only)

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "fliptracker.db")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# -------------------------------------------------
# DATABASE MODELS
# -------------------------------------------------
class Project(db.Model):
    __tablename__ = "project"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200))
    status = db.Column(db.String(50))          # e.g. "In Progress", "Completed"
    progress_percent = db.Column(db.Integer)   # 0–100

    # relationships
    tasks = db.relationship("Task", backref="project", lazy=True)
    budget = db.relationship("Budget", uselist=False, backref="project")
    expenses = db.relationship("Expense", backref="project", lazy=True)
    inspections = db.relationship("Inspection", backref="project", lazy=True)
    reports = db.relationship("StatusReport", backref="project", lazy=True)
    contractors = db.relationship("Contractor", backref="project", lazy=True)


class Contractor(db.Model):
    __tablename__ = "contractor"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    trade_type = db.Column(db.String(80))   # e.g. "Plumbing", "Electrical"
    phone = db.Column(db.String(40))

    # simple login fields (demo only – no hashing)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(120))

    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)


class Task(db.Model):
    __tablename__ = "task"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(40))      # "Not Started", "In Progress", "Done"
    due_date = db.Column(db.Date)

    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)


class Budget(db.Model):
    __tablename__ = "budget"

    id = db.Column(db.Integer, primary_key=True)
    total_budget = db.Column(db.Float, nullable=False)

    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)


class Expense(db.Model):
    __tablename__ = "expense"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(80))   # "Labor", "Materials", etc.
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))

    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)


class Inspection(db.Model):
    __tablename__ = "inspection"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(80))       # "Electrical", "Framing", "Final", etc.
    status = db.Column(db.String(40))     # "Requested", "Scheduled", "Passed", "Failed"
    date = db.Column(db.Date)

    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)


class StatusReport(db.Model):
    __tablename__ = "status_report"

    id = db.Column(db.Integer, primary_key=True)
    report_date = db.Column(db.Date, default=date.today)
    progress_summary = db.Column(db.String(300))
    cost_summary = db.Column(db.String(300))
    timeline_summary = db.Column(db.String(300))

    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)


# -------------------------------------------------
# DEMO DATA
# -------------------------------------------------
def create_demo_data():
    """Create one demo project with some data if DB is empty."""
    if Project.query.first():
        return  # already have data

    project = Project(
        name="Elm Street Flip",
        address="123 Elm Street",
        status="In Progress",
        progress_percent=45,
    )

    db.session.add(project)
    db.session.flush()  # so project.id is available

    # Budget
    budget = Budget(total_budget=150000, project_id=project.id)
    db.session.add(budget)

    # Contractors (with login)
    c1 = Contractor(
        name="Ace Plumbing Co.",
        trade_type="Plumbing",
        phone="555-1234",
        username="aceplumb",
        password="password123",  # demo only
        project_id=project.id,
    )
    c2 = Contractor(
        name="Bright Spark Electric",
        trade_type="Electrical",
        phone="555-5678",
        username="sparky",
        password="password123",  # demo only
        project_id=project.id,
    )
    db.session.add_all([c1, c2])

    # Tasks
    t1 = Task(
        title="Demo old kitchen",
        status="Completed",
        due_date=date(2025, 1, 10),
        project_id=project.id,
    )
    t2 = Task(
        title="Rough plumbing",
        status="In Progress",
        due_date=date(2025, 1, 25),
        project_id=project.id,
    )
    t3 = Task(
        title="Electrical rough-in",
        status="Not Started",
        due_date=date(2025, 2, 5),
        project_id=project.id,
    )
    db.session.add_all([t1, t2, t3])

    # Expenses
    e1 = Expense(
        category="Materials",
        amount=3500,
        description="Lumber + drywall",
        project_id=project.id,
    )
    e2 = Expense(
        category="Labor",
        amount=2000,
        description="Demo crew",
        project_id=project.id,
    )
    db.session.add_all([e1, e2])

    # Inspections
    i1 = Inspection(
        type="Framing",
        status="Scheduled",
        date=date(2025, 1, 30),
        project_id=project.id,
    )
    i2 = Inspection(
        type="Electrical",
        status="Requested",
        date=None,
        project_id=project.id,
    )
    db.session.add_all([i1, i2])

    # Status report
    r1 = StatusReport(
        project_id=project.id,
        progress_summary="Demo complete, framing underway.",
        cost_summary="Spent $5,500 out of $150,000 budget.",
        timeline_summary="On track, inspections scheduled for end of month.",
    )
    db.session.add(r1)

    db.session.commit()


# -------------------------------------------------
# DB INIT (compatible with Flask 3)
# -------------------------------------------------
@app.before_request
def init_db():
    if not hasattr(app, "db_initialized"):
        db.create_all()
        create_demo_data()
        app.db_initialized = True


# -------------------------------------------------
# ROUTES / VIEWS
# -------------------------------------------------
@app.route("/")
def dashboard():
    """Main dashboard showing all projects."""
    projects = Project.query.all()
    return render_template("dashboard.html", projects=projects)


@app.route("/project/<int:project_id>")
def project_detail(project_id):
    """Detail view for a single project, used by the dashboard links."""
    project = Project.query.get_or_404(project_id)

    # Calculate total expenses
    total_expenses = sum(e.amount for e in project.expenses)
    total_budget = project.budget.total_budget if project.budget else 0
    remaining_budget = total_budget - total_expenses

    # Data for budget vs spending chart
    chart_labels = ["Total Budget", "Total Spent"]
    chart_data = [total_budget, total_expenses]

    return render_template(
        "project_detail.html",
        project=project,
        total_expenses=total_expenses,
        remaining_budget=remaining_budget,
        chart_labels=chart_labels,
        chart_data=chart_data,
    )


# ---------- New Project Form ----------
@app.route("/project/new", methods=["GET", "POST"])
def new_project():
    if request.method == "POST":
        name = request.form.get("name")
        address = request.form.get("address")
        status = request.form.get("status") or "Planned"
        total_budget = float(request.form.get("total_budget") or 0)

        if not name:
            flash("Project name is required.", "danger")
            return redirect(url_for("new_project"))

        project = Project(
            name=name,
            address=address,
            status=status,
            progress_percent=0,
        )
        db.session.add(project)
        db.session.flush()

        budget = Budget(total_budget=total_budget, project_id=project.id)
        db.session.add(budget)

        db.session.commit()
        flash("New project created!", "success")
        return redirect(url_for("dashboard"))

    return render_template("new_project.html")


# ---------- Add Expense Form ----------
@app.route("/project/<int:project_id>/expenses/new", methods=["GET", "POST"])
def new_expense(project_id):
    project = Project.query.get_or_404(project_id)

    if request.method == "POST":
        category = request.form.get("category")
        amount_raw = request.form.get("amount") or "0"
        description = request.form.get("description")

        try:
            amount = float(amount_raw)
        except ValueError:
            flash("Amount must be a number.", "danger")
            return redirect(url_for("new_expense", project_id=project_id))

        expense = Expense(
            category=category,
            amount=amount,
            description=description,
            project_id=project.id,
        )
        db.session.add(expense)
        db.session.commit()
        flash("Expense added!", "success")
        return redirect(url_for("project_detail", project_id=project.id))

    return render_template("new_expense.html", project=project)


# ---------- Contractor Login ----------
@app.route("/contractor/login", methods=["GET", "POST"])
def contractor_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        contractor = Contractor.query.filter_by(username=username, password=password).first()
        if contractor:
            session["contractor_id"] = contractor.id
            flash(f"Welcome, {contractor.name}!", "success")
            return redirect(url_for("contractor_dashboard"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("contractor_login.html")


@app.route("/contractor/dashboard")
def contractor_dashboard():
    contractor_id = session.get("contractor_id")
    if not contractor_id:
        flash("Please log in as a contractor.", "warning")
        return redirect(url_for("contractor_login"))

    contractor = Contractor.query.get_or_404(contractor_id)
    # show the contractor's project and tasks
    project = contractor.project
    tasks = Task.query.filter_by(project_id=project.id).all()

    return render_template(
        "contractor_dashboard.html",
        contractor=contractor,
        project=project,
        tasks=tasks,
    )


@app.route("/contractor/logout")
def contractor_logout():
    session.pop("contractor_id", None)
    flash("Logged out.", "info")
    return redirect(url_for("contractor_login"))


if __name__ == "__main__":
    app.run(debug=True)
