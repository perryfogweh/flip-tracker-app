import os
from datetime import date

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

# -------------------------------------------------
# APP + DATABASE SETUP
# -------------------------------------------------
app = Flask(__name__)

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

    # Contractors
    c1 = Contractor(
        name="Ace Plumbing Co.",
        trade_type="Plumbing",
        phone="555-1234",
        project_id=project.id,
    )
    c2 = Contractor(
        name="Bright Spark Electric",
        trade_type="Electrical",
        phone="555-5678",
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
