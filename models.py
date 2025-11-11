from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ---------------------------
# 1. User Table
# ---------------------------

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    user_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('student', 'faculty', 'admin'), nullable=False)
    department_ID = db.Column(db.Integer, db.ForeignKey('department.department_ID'), nullable=True)
    reputation_points = db.Column(db.Integer, default=0)

    # Relationships
    questions = db.relationship('Question', backref='user', lazy=True)
    answers = db.relationship('Answer', backref='user', lazy=True)
    faculty_subjects = db.relationship('FacultySubject', backref='faculty', lazy=True)

    def get_id(self):
        return str(self.user_ID)


# ---------------------------
# 2. Department Table
# ---------------------------
class Department(db.Model):
    __tablename__ = 'department'

    department_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    subjects = db.relationship('Subject', backref='department', lazy=True)
    users = db.relationship('User', backref='department', lazy=True)

# ---------------------------
# 3. Subject Table
# ---------------------------
class Subject(db.Model):
    __tablename__ = 'subject'

    subject_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    department_ID = db.Column(db.Integer, db.ForeignKey('department.department_ID'), nullable=False)

    questions = db.relationship('Question', backref='subject', lazy=True)
    faculty_subjects = db.relationship('FacultySubject', backref='subject', lazy=True)

# ---------------------------
# 4. Question Table
# ---------------------------
class Question(db.Model):
    __tablename__ = 'question'


    # subject = db.relationship('Subject', backref='questions')
    
    
    question_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Keys
    student_ID = db.Column(db.Integer, db.ForeignKey('user.user_ID'), nullable=False)
    subject_ID = db.Column(db.Integer, db.ForeignKey('subject.subject_ID'), nullable=False)

    is_answered = db.Column(db.Boolean, default=False)

    # Relationships
    answers = db.relationship('Answer', backref='question', lazy=True)




# ---------------------------
# 5. Answer Table
# ---------------------------
class Answer(db.Model):
    __tablename__ = 'answer'

    answer_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question_ID = db.Column(db.Integer, db.ForeignKey('question.question_ID'), nullable=False)
    faculty_ID = db.Column(db.Integer, db.ForeignKey('user.user_ID'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class Vote(db.Model):
    __tablename__ = 'vote'
    vote_ID = db.Column(db.Integer, primary_key=True)
    user_ID = db.Column(db.Integer, db.ForeignKey('user.user_ID'), nullable=False)
    answer_ID = db.Column(db.Integer, db.ForeignKey('answer.answer_ID'), nullable=False)
    vote_type = db.Column(db.String(10), nullable=False)  # 'upvote' or 'downvote'

# ---------------------------
# 6. Announcement Table
# ---------------------------
class Announcement(db.Model):
    __tablename__ = 'announcement'

    announcement_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    faculty_ID = db.Column(db.Integer, db.ForeignKey('user.user_ID'), nullable=False)
    department_ID = db.Column(db.Integer, db.ForeignKey('department.department_ID'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships for easier template access
    faculty = db.relationship('User', backref='announcements', foreign_keys=[faculty_ID])
    department = db.relationship('Department', backref='announcements', foreign_keys=[department_ID])

# ---------------------------
# 7. Upvote Table
# ---------------------------
class Upvote(db.Model):
    __tablename__ = 'upvote'

    upvote_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    answer_ID = db.Column(db.Integer, db.ForeignKey('answer.answer_ID'), nullable=False) 
    user_ID = db.Column(db.Integer, db.ForeignKey('user.user_ID'), nullable=False)

# ---------------------------
# 8. Faculty_Subject Table
# ---------------------------
class FacultySubject(db.Model):
    __tablename__ = 'faculty_subject'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    faculty_ID = db.Column(db.Integer, db.ForeignKey('user.user_ID'), nullable=False)
    subject_ID = db.Column(db.Integer, db.ForeignKey('subject.subject_ID'), nullable=False)
