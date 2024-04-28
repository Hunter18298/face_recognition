from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import face_recognition
from datetime import datetime
app = Flask(__name__)

# Configuration for the Flask app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Database models
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_file = db.Column(db.String(100), nullable=False)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)

# Ensure the database and upload folder are created
with app.app_context():
    db.create_all()
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        name = request.form['name']
        image = request.files['image']
        if image:
            filename = datetime.now().strftime("%Y%m%d-%H%M%S") + '_' + image.filename
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            employee = Employee(name=name, image_file=image_path)
            db.session.add(employee)
            db.session.commit()
            return redirect(url_for('index'))
    return render_template('add_employee.html')

@app.route('/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    if request.method == 'POST':
        if 'image' in request.files:
            image = request.files['image']
            filename = datetime.now().strftime("%Y%m%d-%H%M%S") + '.jpg'
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            try:
                unknown_image = face_recognition.load_image_file(image_path)
                unknown_encodings = face_recognition.face_encodings(unknown_image)
                if unknown_encodings:
                    unknown_encoding = unknown_encodings[0]
                    # Logic to compare unknown_encoding with known_encodings
                    # This is simplified; normally you'd iterate over stored encodings
                    return jsonify({'message': 'Attendance marked successfully'})
                else:
                    return jsonify({'error': 'No faces detected'})
            except Exception as e:
                return jsonify({'error': str(e)})
        return jsonify({'error': 'No image provided'})
    else:
        # This serves the page to capture images via webcam
        return render_template('mark_attendance.html')

@app.route('/view_attendance')
def view_attendance():
    # Join Employee and Attendance and select specific columns
    attendance_records = db.session.query(Attendance.date, Employee.name, Employee.image_file).join(Employee).all()
    return render_template('view_attendance.html', records=attendance_records)

@app.route('/edit_employee/<int:employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    if request.method == 'POST':
        employee.name = request.form['name']
        image = request.files['image']
        if image:
            filename = datetime.now().strftime("%Y%m%d-%H%M%S") + '_' + image.filename
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            employee.image_file = image_path
        db.session.commit()
        return redirect(url_for('view_employees'))
    return render_template('edit_employee.html', employee=employee)

@app.route('/view_employees')
def view_employees():
    employees = Employee.query.all()
    return render_template('view_employees.html', employees=employees)

@app.route('/delete_employee/<int:employee_id>', methods=['POST'])
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    return redirect(url_for('view_employees'))


if __name__ == '__main__':
    app.run(debug=True)
