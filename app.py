from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, User, Department, Subject, Question, Answer, Announcement, Upvote, FacultySubject
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


app = Flask(__name__)
app.secret_key = "supersecretkey"

# Configure MySQL Database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:mysql123@localhost/vit_forum'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Create tables if not exist
with app.app_context():
    db.create_all()

# ------------------ Routes ------------------

# @app.route('/')
# def home():
#     return "Database connected successfully!"

@app.route('/')
def home():
    return render_template("index.html")


# ---------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    departments = Department.query.order_by(Department.name).all()
    subjects = Subject.query.order_by(Subject.name).all()

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        role = request.form['role']
        dept_id = request.form.get('department_id') or None
        subject_id = request.form.get('subject_id') or None

        if not username or not password or not role:
            flash("Please fill all required fields.", "warning")
            return render_template('register.html', departments=departments, subjects=subjects)

        hashed = generate_password_hash(password)
        new_user = User(
            username=username,
            password_hash=hashed,
            role=role,
            department_ID=dept_id,
            reputation_points=0
        )
        try:
            db.session.add(new_user)
            db.session.commit()

            if role == "faculty" and subject_id:
                faculty_subject = FacultySubject(
                    faculty_ID=new_user.user_ID,
                    subject_ID=subject_id
                )
                db.session.add(faculty_subject)
                db.session.commit()

            flash("Registration successful — please login.", "success")
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            flash("Error: username may already exist. " + str(e), "danger")
            return render_template('register.html', departments=departments, subjects=subjects)

    return render_template('register.html', departments=departments, subjects=subjects)

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Logged in successfully.", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash("Invalid username or password.", "danger")
    return render_template('login.html')

# ---------- LOGOUT ----------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for('home'))

# ---------- DASHBOARD ----------
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

# ---------- ASK A QUESTION ----------
@app.route('/ask_question', methods=['GET', 'POST'])
@login_required
def ask_question():
    if current_user.role != 'student':
        flash("Only students can ask questions.", "danger")
        return redirect(url_for('dashboard'))

    subjects = Subject.query.filter_by(department_ID=current_user.department_ID).all()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        subject_id = request.form['subject_id']

        new_q = Question(
            student_ID=current_user.user_ID,
            subject_ID=subject_id,
            title=title,
            description=description
        )
        db.session.add(new_q)
        db.session.commit()
        flash("Question submitted successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('ask_question.html', subjects=subjects)


# ---------- FACULTY: VIEW & ANSWER QUESTIONS ----------
# @app.route('/faculty/questions', methods=['GET', 'POST'])
# @login_required
# def faculty_questions():
#     if current_user.role != 'faculty':
#         flash("Access denied! Faculty only.", "danger")
#         return redirect(url_for('dashboard'))

#     subject_ids = [fs.subject_ID for fs in FacultySubject.query.filter_by(faculty_ID=current_user.user_ID).all()]
#     questions = Question.query.filter(Question.subject_ID.in_(subject_ids)).all()

#     if request.method == 'POST':
#         question_id = int(request.form['question_id'])
#         answer_text = request.form['answer_text']

#         new_answer = Answer(
#             question_ID=question_id,
#             faculty_ID=current_user.user_ID,
#             content=answer_text
#         )
#         db.session.add(new_answer)

#         q = Question.query.get(question_id)
#         q.is_answered = True
#         db.session.commit()

#         flash("Answer submitted successfully ✅", "success")
#         return redirect(url_for('faculty_questions'))

#     return render_template('faculty_questions.html', questions=questions)

@app.route('/faculty/questions', methods=['GET', 'POST'])
@login_required
def faculty_questions():
    if current_user.role != 'faculty':
        flash("Access denied! Faculty only.", "danger")
        return redirect(url_for('dashboard'))

    # Faculty’s department
    department = Department.query.get(current_user.department_ID)

    # Subjects assigned to this faculty
    faculty_subjects = FacultySubject.query.filter_by(faculty_ID=current_user.user_ID).all()
    subjects = [Subject.query.get(fs.subject_ID) for fs in faculty_subjects]

    # Questions only from subjects this faculty teaches
    subject_ids = [s.subject_ID for s in subjects]
    questions = Question.query.filter(Question.subject_ID.in_(subject_ids)).all()
    # questions = Question.query.join(Subject).filter(Question.subject_ID.in_(subject_ids)).all()

    # Handle answering a question
    if request.method == 'POST':
        question_id = int(request.form['question_id'])
        answer_text = request.form['answer_text']

        new_answer = Answer(
            question_ID=question_id,
            faculty_ID=current_user.user_ID,
            content=answer_text
        )
        db.session.add(new_answer)

        q = Question.query.get(question_id)
        q.is_answered = True
        db.session.commit()

        flash("Answer submitted successfully ✅", "success")
        return redirect(url_for('faculty_questions'))

    return render_template(
        'faculty_questions.html',
        questions=questions,
        department=department,
        subjects=subjects
    )


# ---------- STUDENT: VIEW ONLY THEIR OWN QUESTIONS ----------
@app.route('/my_questions')
@login_required
def my_questions():
    if current_user.role != 'student':
        flash("Access denied! Students only.", "danger")
        return redirect(url_for('dashboard'))

    questions = Question.query.filter_by(student_ID=current_user.user_ID).order_by(Question.created_at.desc()).all()
    return render_template('my_questions.html', questions=questions)


# ---------- STUDENT: VIEW ALL QUESTIONS ----------
@app.route('/all_questions')
@login_required
def all_questions():
    if current_user.role != 'student':
        flash("Access denied! Students only.", "danger")
        return redirect(url_for('dashboard'))

    questions = Question.query.order_by(Question.created_at.desc()).all()
    return render_template('all_questions.html', questions=questions)

# ----------------- Faculty Dashboard -----------------
@app.route('/faculty/dashboard')
@login_required
def faculty_dashboard():
    if current_user.role != 'faculty':
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard'))

    subject_ids = [fs.subject_ID for fs in FacultySubject.query.filter_by(faculty_ID=current_user.user_ID).all()]
    questions = Question.query.filter(Question.subject_ID.in_(subject_ids)).all()
    return render_template("faculty_dashboard.html", questions=questions)




#------------------- Faculty Answer Route----------------------------
@app.route('/answer/<int:question_id>', methods=['POST'])
@login_required
def answer_question(question_id):
    if current_user.role != "faculty":
        flash("Only faculty can answer questions!", "danger")
        return redirect(url_for("dashboard"))

    content = request.form["content"].strip()
    if not content:
        flash("Answer cannot be empty.", "warning")
        return redirect(url_for("dashboard"))

    new_answer = Answer(
        content=content,
        question_ID=question_id,
        faculty_ID=current_user.user_ID,
        created_at=datetime.now()
    )
    db.session.add(new_answer)
    db.session.commit()

    flash("Answer submitted successfully!", "success")
    return redirect(url_for("dashboard"))


# ----------------upvote route---------------
@app.route('/upvote/<int:answer_id>', methods=['POST'])
def upvote(answer_id):
    if 'user_id' not in session:  
        return redirect(url_for('login'))

    answer = Answer.query.get_or_404(answer_id)
    user_id = session['user_id']

    # Check if already voted
    existing_vote = Vote.query.filter_by(user_ID=user_id, answer_ID=answer_id).first()
    if existing_vote:
        if existing_vote.vote_type != 'upvote':
            existing_vote.vote_type = 'upvote'
    else:
        new_vote = Vote(user_ID=user_id, answer_ID=answer_id, vote_type='upvote')
        db.session.add(new_vote)

    db.session.commit()
    return redirect(request.referrer)


@app.route('/downvote/<int:answer_id>', methods=['POST'])
def downvote(answer_id):
    if 'user_id' not in session:  
        return redirect(url_for('login'))

    answer = Answer.query.get_or_404(answer_id)
    user_id = session['user_id']

    # Check if already voted
    existing_vote = Vote.query.filter_by(user_ID=user_id, answer_ID=answer_id).first()
    if existing_vote:
        if existing_vote.vote_type != 'downvote':
            existing_vote.vote_type = 'downvote'
    else:
        new_vote = Vote(user_ID=user_id, answer_ID=answer_id, vote_type='downvote')
        db.session.add(new_vote)

    db.session.commit()
    return redirect(request.referrer)



# ----------------- Run App -----------------
if __name__ == "__main__":
    app.run(debug=True)
