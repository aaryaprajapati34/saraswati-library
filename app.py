from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import re
import datetime
import os
from models import db, User, Book
from dotenv import load_dotenv
load_dotenv()
import dj_database_url

# Setup logging (FIXED - added missing parenthesis)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.static_folder = 'static'
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import db from models

db.init_app(app)
CORS(app)
def validate_email(email):
    pattern = r'^[\w\.-]+@gmail\.com$'
    return re.match(pattern, email)

# ==================== PAGE ROUTES ====================

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/add_book')
def add_book_page():
    return render_template('add_book.html')

@app.route('/book')
def book_page():
    return render_template('book.html')

@app.route('/student_profile')
def student_profile_page():
    return render_template('student_profile.html')

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

@app.route('/rules')
def rules_page():
    return render_template('rules.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email').lower()
        member_id = data.get('memberId')
        password = data.get('password')
        
        if not all([name, email, member_id, password]):
            return jsonify({'success': False, 'message': 'All fields required'}), 400
        
        if not validate_email(email):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        from models import User
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        if User.query.filter_by(member_id=member_id).first():
            return jsonify({'success': False, 'message': 'Member ID already registered'}), 400
        
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, member_id=member_id, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Registration successful'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Registration failed'}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request, JSON required'}), 400

        username = data.get('username')
        password = data.get('password')
        
        if not all([username, password]):
            return jsonify({'success': False, 'message': 'All fields required'}), 400

        username = username.lower()
        user = User.query.filter((User.email == username) | (User.member_id == username)).first()
        
        if user and check_password_hash(user.password, password):
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': user.name,
                'email': user.email
            })

        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    except Exception as e:
        print("Login Error:", e)  # Logs real error on Render
        return jsonify({'success': False, 'message': 'Login failed'}), 500

@app.route('/logout', methods=['POST'])
def logout():
    return jsonify({'success': True, 'message': 'Logged out'})

@app.route('/get_profile', methods=['POST'])
def get_profile():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email required'}), 400
        
        from models import User
        
        user = User.query.filter_by(email=email).first()
        if user:
            return jsonify({'success': True, 'name': user.name, 'email': user.email, 'member_id': user.member_id})
        
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to get profile'}), 500

@app.route('/get_issued_books', methods=['POST'])
def get_issued_books():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email required'}), 400
        
        issued_books = Book.query.filter_by(holder=email, status='Issued').all()
        
        return jsonify({'success': True, 'books': [{'id': b.id, 'name': b.name, 'author': b.author, 'issue_date': b.issue_date, 'due_date': b.due_date} for b in issued_books]})    
   
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to get books'}), 500

@app.route('/return_book', methods=['POST'])
def return_book():
    try:
        data = request.get_json()
        book_id = data.get('bookId')
        email = data.get('email')
        
        book = Book.query.get(book_id)
        if book and book.status == 'Issued' and book.holder == email:
            
            # Calculate fine if overdue (₹5 per day)
            fine = 0
            if book.due_date:
                due = datetime.datetime.strptime(book.due_date, '%Y-%m-%d').date()
                today = datetime.date.today()
                if today > due:
                    days_late = (today - due).days
                    fine = days_late * 5
            
            book.status = 'Available'
            book.holder = ''
            book.requested_by = ''
            book.issue_date = ''
            book.due_date = ''
            db.session.commit()
            
            if fine > 0:
                return jsonify({'success': True, 'message': f'Book returned! Fine: ₹{fine}', 'fine': fine})
            else:
                return jsonify({'success': True, 'message': 'Book returned successfully!'})
        
        return jsonify({'success': False, 'message': 'Cannot return book'}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'message': 'Return failed'}), 500

@app.route('/books', methods=['GET'])
def get_books():
    try:
        books = Book.query.all()
        books_list = [{
            'id': b.id,
            'name': b.name,
            'author': b.author,
            'status': b.status,
            'holder': b.holder,
            'requested_by': b.requested_by,
            'issue_date': b.issue_date,
            'due_date': b.due_date
        } for b in books]
        return jsonify(books_list)  # <-- always an array
    except Exception as e:
        print("Fetch Books Error:", e)  # log actual error
        return jsonify([])  # <-- return empty array instead of object

@app.route('/add_book', methods=['POST'])
def add_book():
    try:
        data = request.get_json()
        name = data.get('name')
        author = data.get('author')
        
        if not all([name, author]):
            return jsonify({'success': False, 'message': 'Name and author required'}), 400
        
        new_book = Book(name=name, author=author, status='Available')
        db.session.add(new_book)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Book added successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to add book'}), 500

@app.route('/request_book', methods=['POST'])
def request_book():
    try:
        data = request.get_json()
        book_id = data.get('bookId')
        requested_by = data.get('requestedBy')
        
        book = Book.query.get(book_id)
        if book and book.status == 'Available':
            book.status = 'Requested'
            book.requested_by = requested_by
            db.session.commit()
            return jsonify({'success': True, 'message': 'Book requested'})
        
        return jsonify({'success': False, 'message': 'Book not available'}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'message': 'Request failed'}), 500

@app.route('/issue_book', methods=['POST'])
def issue_book():
    try:
        data = request.get_json()
        book_id = data.get('bookId')
        
        book = Book.query.get(book_id)
        if book and book.status == 'Requested':
            book.status = 'Issued'
            book.holder = book.requested_by
            book.issue_date = datetime.date.today().strftime('%Y-%m-%d')
            
            # Calculate due date (7 days from now)
            due = datetime.date.today() + datetime.timedelta(days=7)
            book.due_date = due.strftime('%Y-%m-%d')
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Book issued', 'due_date': book.due_date})
        
        return jsonify({'success': False, 'message': 'Cannot issue book'}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'message': 'Issue failed'}), 500
@app.route('/admin_return_book', methods=['POST'])
def admin_return_book():
    try:
        data = request.get_json()
        book_id = data.get('bookId')
        
        book = Book.query.get(book_id)
        if book and book.status == 'Issued':
            # Calculate fine if overdue (₹5 per day)
            fine = 0
            if book.due_date:
                due = datetime.datetime.strptime(book.due_date, '%Y-%m-%d').date()
                today = datetime.date.today()
                if today > due:
                    days_late = (today - due).days
                    fine = days_late * 5
            
            book.status = 'Available'
            book.holder = ''
            book.requested_by = ''
            book.issue_date = ''
            book.due_date = ''
            db.session.commit()
            
            if fine > 0:
                return jsonify({'success': True, 'message': f'Book returned! Fine: ₹{fine}'})
            else:
                return jsonify({'success': True, 'message': 'Book returned'})
        
        return jsonify({'success': False, 'message': 'Cannot return book'}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'message': 'Return failed'}), 500
@app.route('/delete_book', methods=['POST'])
def delete_book():
    try:
        data = request.get_json()
        book_id = data.get('bookId')
        
        book = Book.query.get(book_id)
        if book:
            db.session.delete(book)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Book deleted'})
        
        return jsonify({'success': False, 'message': 'Book not found'}), 404
    
    except Exception as e:
        return jsonify({'success': False, 'message': 'Delete failed'}), 500

# Seed initial books (NEW FUNCTION ADDED)
def seed_books():
    if Book.query.count() > 0:
        return
    
    books_list = [
    # First 100 Unique Books
    ("Python Programming", "Guido van Rossum"),
    ("Clean Code", "Robert C. Martin"),
    ("Deep Work", "Cal Newport"),
    ("Introduction to Algorithms", "Thomas H. Cormen"),
    ("The Pragmatic Programmer", "Andrew Hunt"),
    ("Design Patterns", "Erich Gamma"),
    ("The C Programming Language", "Dennis Ritchie"),
    ("Operating System Concepts", "Peter Galvin"),
    ("Computer Networking", "James Kurose"),
    ("Database System Concepts", "Abraham Silberschatz"),
    ("Artificial Intelligence", "Stuart Russell"),
    ("Machine Learning", "Tom Mitchell"),
    ("Data Structures and Algorithms", "Narasimha Karumanchi"),
    ("Discrete Mathematics", "Kenneth Rosen"),
    ("Linear Algebra", "Gilbert Strang"),
    ("Calculus", "James Stewart"),
    ("Software Engineering", "Roger Pressman"),
    ("Computer Architecture", "John Hennessy"),
    ("Compiler Design", "Alfred Aho"),
    ("Theory of Computation", "Michael Sipser"),
    ("Java: The Complete Reference", "Herbert Schildt"),
    ("Python Crash Course", "Eric Matthes"),
    ("Core Java", "Cay Horstmann"),
    ("Head First Design Patterns", "Eric Freeman"),
    ("Cracking the Coding Interview", "Gayle McDowell"),
    ("Grokking Algorithms", "Aditya Bhargava"),
    ("The Algorithm Design Manual", "Steven Skiena"),
    ("Algorithm Design", "Jon Kleinberg"),
    ("Programming Pearls", "Jon Bentley"),
    ("Code Complete", "Steve McConnell"),
    ("Refactoring", "Martin Fowler"),
    ("Clean Architecture", "Robert C. Martin"),
    ("The Mythical Man-Month", "Fred Brooks"),
    ("Computer Systems", "Randal E. Bryant"),
    ("Distributed Systems", "Andrew Tanenbaum"),
    ("Computer Graphics", "Donald Hearn"),
    ("Object Oriented Programming", "E. Balagurusamy"),
    ("Web Technologies", "Jeffrey Jackson"),
    ("Database Management", "Raghu Ramakrishnan"),
    ("Data Mining", "Jiawei Han"),
    ("Big Data Analytics", "Radha Shankarmani"),
    ("Cloud Computing", "Barrie Sosinsky"),
    ("Internet of Things", "Arshdeep Bahga"),
    ("Cyber Security", "James Graham"),
    ("Network Security", "William Stallings"),
    ("Cryptography", "William Stallings"),
    ("Digital Electronics", "Morris Mano"),
    ("Microprocessors", "Ramesh Gaonkar"),
    ("Embedded Systems", "Raj Kamal"),
    ("VLSI Design", "Debaprasad Das"),
    ("Digital Signal Processing", "John Proakis"),
    ("Signals and Systems", "Alan Oppenheim"),
    ("Control Systems", "I.J. Nagrath"),
    ("Robotics", "Saeed Niku"),
    ("Artificial Neural Networks", "Simon Haykin"),
    ("Deep Learning", "Ian Goodfellow"),
    ("Natural Language Processing", "Christopher Manning"),
    ("Computer Vision", "David Forsyth"),
    ("Reinforcement Learning", "Richard Sutton"),
    ("Data Science", "John D. Kelleher"),
    ("Python for Data Analysis", "Wes McKinney"),
    ("Machine Learning Yearning", "Andrew Ng"),
    ("Hands-On Machine Learning", "Aurelien Geron"),
    ("Statistics", "David Freedman"),
    ("Statistical Inference", "George Casella"),
    ("Numerical Methods", "S.S. Sastry"),
    ("Differential Equations", "Shepley Ross"),
    ("Number Theory", "G.H. Hardy"),
    ("Abstract Algebra", "I.N. Herstein"),
    ("Topology", "James Munkres"),
    ("Complex Analysis", "Tristan Needham"),
    ("Engineering Mathematics", "Erwin Kreyszig"),
    ("Graph Theory", "Robin J. Wilson"),
    ("Combinatorics", "Ronald Graham"),
    ("Real Analysis", "Robert G. Bartle"),
    ("JavaScript: The Good Parts", "Douglas Crockford"),
    ("Eloquent JavaScript", "Marijn Haverbeke"),
    ("Learning Python", "Mark Lutz"),
    ("Fluent Python", "Luciano Ramalho"),
    ("Python Cookbook", "David Beazley"),
    ("Effective Python", "Brett Slatkin"),
    ("C++ Primer", "Stanley Lippman"),
    ("Effective C++", "Scott Meyers"),
    ("Modern C++", "Bjarne Stoustrup"),
    ("C# in Depth", "Jon Skeet"),
    ("Go Programming Language", "Alan A. A. Donovan"),
    ("Rust in Action", "Tim McNamara"),
    ("Scala Programming", "Martin Odersky"),
    ("Kotlin in Action", "Dmitry Jemerov"),
    ("Swift Programming", "Apple Inc."),
    ("Ruby Programming", "Yukihiro Matsumoto"),
    ("PHP Programming", "Rasmus Lerdorf"),
    ("R Programming", "John Chambers"),
    ("MATLAB Programming", "MathWorks"),
    ("Julia Programming", "Jeff Bezanson"),
    ("Lua Programming", "Roberto Ierusalimschy"),
    ("Perl Programming", "Larry Wall"),
    ("Assembly Language", "Kip Irvine"),
    ("Fortran Programming", "John Backus"),
    ("Haskell Programming", "Miran Lipovaca"),
    ("Erlang Programming", "Francesco Cesarini"),
    ("Clojure Programming", "Chas Emerick"),
    ("F# Programming", "Don Syme"),
    ("Objective-C Programming", "Aaron Hillegass"),
    ("Visual Basic", "Matthew MacDonald"),
    ("Delphi Programming", "Marco Cantu"),
    ("Shell Scripting", "Richard Blum"),
    ("PowerShell Scripting", "Don Jones"),
    ("Terraform", "James Turnbull"),
    ("Ansible", "Lorin Hochstein"),
    ("Docker", "Adrian Mouat"),
    ("Kubernetes", "Kelsey Hightower"),
    ("Jenkins", "John Ferguson Smart"),
    ("Git", "Scott Chacon"),
    ("Maven", "Sonatype Company"),
    ("Gradle", "Hans Dockter"),
    ("Node.js", "Ryan Dahl"),
    ("Express.js", "Eran Hammer"),
    ("React", "Facebook"),
    ("Angular", "Google"),
    ("Vue.js", "Evan You"),
    ("Django", "Mozilla"),
    ("Flask", "Armin Ronacher"),
    ("Spring Framework", "Pivotal"),
    ("Hibernate", "Red Hat"),
    ("MySQL", "Oracle"),
    ("PostgreSQL", "PostgreSQL Global"),
    ("MongoDB", "MongoDB Inc"),
    ("Redis", "Salvatore Sanfilippo"),
    ("Elasticsearch", "Elastic"),
    ("Kafka", "Apache"),
    ("Spark", "Apache"),
    ("Hadoop", "Apache"),
    ("TensorFlow", "Google"),
    ("PyTorch", "Facebook"),
    ("Keras", "Francois Chollet"),
    ("Scikit-learn", "Scikit-learn"),
    ("Pandas", "Wes McKinney"),
    ("NumPy", "Travis Oliphant"),
    ("Matplotlib", "John Hunter"),
    ("Seaborn", "Michael Waskom"),
    ("Plotly", "Plotly"),
    ("Bokeh", "Continuum Analytics"),
    ("OpenCV", "Intel"),
    ("Unity", "Unity Technologies"),
    ("Unreal Engine", "Epic Games"),
    ("Godot", "Godot Engine"),
    ("Blender", "Blender Foundation"),
    ("Adobe Photoshop", "Adobe"),
    ("Adobe Illustrator", "Adobe"),
    ("Figma", "Figma Inc"),
    ("Sketch", "Bohemian Coding"),
    ("InVision", "InVision Labs"),
    ("Axure", "Axure"),
    ("Thermodynamics", "P.K. Nag"),
    ("Fluid Mechanics", "R.K. Rajput"),
    ("Strength of Materials", "R.K. Bansal"),
    ("Machine Design", "V.B. Bhandari"),
    ("Theory of Machines", "S.S. Sastry"),
    ("Internal Combustion Engines", "V. Ganesan"),
    ("Automobile Engineering", "Kirpal Singh"),
    ("Refrigeration and Air Conditioning", "C.P. Arora"),
    ("Power Electronics", "P.S. Bimbhra"),
    ("Analog Electronics", "J.B. Gupta"),
    ("Circuit Theory", "A. Chakrabarti"),
    ("Electromagnetic Fields", "Sadiku"),
    ("High Voltage Engineering", "M.S. Naidu"),
    ("Power System Analysis", "Hadi Saadat"),
    ("Electrical Machines", "P.S. Bimbhra"),
    ("Control Systems Engineering", "Nise Norman"),
    ("Microwave Engineering", "David Pozar"),
    ("Radar Engineering", "Merrill Skolnik"),
    ("Antennas and Propagation", "John Kraus"),
    ("Communication Systems", "Simon Haykin"),
    ("Wireless Communications", "Theodore Rappaport"),
    ("Digital Communication", "John Proakis"),
    ("Optical Fiber Communication", "Gerd Keiser"),
    ("Computer Organization", "Carl Hamacher"),
    ("Microprocessor 8086", "N. Senthil Kumar"),
    ("Microcontroller 8051", "Mazidi Muhammad"),
    ("Real-Time Systems", "Jane W. S. Liu"),
    ("Mechatronics", "W. Bolton"),
    ("Sensors and Actuators", "Clarence Silva"),
    ("Industrial Instrumentation", "D. Patranabis"),
    ("Engineering Drawing", "N.D. Bhatt"),
    ("Engineering Mechanics", "R.K. Jain"),
    ("Surveying", "B.C. Punmia"),
    ("Concrete Technology", "M.S. Shetty"),
    ("Steel Structures", "S.K. Duggal"),
    ("Soil Mechanics", "K.R. Arora"),
    ("Foundation Engineering", "B.J. Kasmalkar"),
    ("Hydrology", "K. Subramanya"),
    ("Environmental Engineering", "S.K. Garg"),
    ("Transportation Engineering", "Khanna and Justo"),
    ("Highway Engineering", "Khanna S.K."),
    ("Railway Engineering", "Satish Chandra"),
    ("Bridge Engineering", "S.P. Bindra"),
    ("Geotechnical Engineering", "Gopal Ranjan"),
    ("Structural Analysis", "C.S. Reddy"),
    ("Earthquake Engineering", "Chopra Anil"),
    ("Building Construction", "S.C. Rangwala"),
    ("Water Resources Engineering", "Linsley Ray"),
    ("Wastewater Engineering", "Metcalf & Eddy"),
    ("Airport Engineering", "Khanna S.K."),
    ("Tunnel Engineering", "S.C. Saxena"),
    ("Finite Element Analysis", "Logan"),
    ("Hydraulic Machines", "K. Subramanya"),
    ("IC Engines", "M.L. Mathur"),
    ("Gas Turbines", "V. Ganesan"),
    ("Heat Transfer", "Incropera Frank"),
    ("Mass Transfer", "Treybal Robert"),
    ("Machine Drawing", "K.L. Narayana"),
    ("Manufacturing Technology", "P.N. Rao"),
    ("Industrial Engineering", "O.P. Khanna"),
    ("Production Management", "J.R. Tony"),
    ("Quality Control", "Montgomery Douglas"),
    ("Operations Research", "J. K. Sharma"),
    ("Work System Design", "O.B. Gabriel"),
    ("Industrial Management", "M. Mahajan"),
    ("Production Planning", "R. K. Jain"),
    ("Material Management", "A. K. Datta"),
    ("Supply Chain Management", "Sunil Chopra"),
    ("Logistics Management", "Donald Bowersox"),
    ("Project Management", "Harold Kerzner"),
    ("Risk Management", "PMI"),
    ("Construction Planning", "J. K. Dey"),
    ("Building Design", "S.M. K. Jain"),
    ("Structural Design", "S. K. Saxena"),
    ("Concepts of Physics", "H.C. Verma"),
    ("Fundamentals of Physics", "Halliday & Resnick"),
    ("University Physics", "Young Freedman"),
    ("Modern Physics", "Serway Jewett"),
    ("Classical Mechanics", "John R. Taylor"),
    ("Classical Electrodynamics", "Jackson John D."),
    ("Quantum Mechanics", "David J. Griffiths"),
    ("Statistical Mechanics", "Pathria R.K."),
    ("Thermodynamics", "Zemansky M.W."),
    ("Optics", "Hecht Eugene"),
    ("Solid State Physics", "Kittel Charles"),
    ("Nuclear Physics", "Krane Kenneth"),
    ("Astrophysics", "Carroll Bradley"),
    ("A Brief History of Time", "Stephen Hawking"),
    ("Cosmos", "Carl Sagan"),
    ("The Elegant Universe", "Brian Greene"),
    ("Relativity", "Einstein Albert"),
    ("Optoelectronics", "J. Wilson"),
    ("Semiconductor Physics", "Kittel Charles"),
    ("Laser Physics", "Svelto Orazio"),
    ("Nanotechnology", "M. Ratner"),
    ("Quantum Computing", "Nielsen Michael"),
    ("Information Theory", "Thomas Cover"),
    ("Thomas Calculus", "Thomas G.B."),
    ("Advanced Calculus", "Patrick Fitzpatrick"),
    ("Vector Calculus", "Jerrold Marsden"),
    ("Algebra", "Michael Artin"),
    ("College Algebra", "Sullivan Michael"),
    ("Trigonometry", "Lial Margaret"),
    ("Precalculus", "Sullivan Michael"),
    ("Mathematics for Engineers", "Stroud K.A."),
    ("Higher Engineering Mathematics", "B.S. Grewal"),
    ("Basic Mathematics", "Serge Lang"),
    ("History of Mathematics", "Carl Boyer"),
    ("Computational Methods", "T. K. V. Raghavan"),
    ("Probability Theory", "V. K. Rohatgi"),
    ("Mathematical Modeling", "Frank R. Giordano"),
    ("Game Theory", "John von Neumann"),
    ("Laplace Transforms", "Murray Spiegel"),
    ("Fourier Series", "Georgi Tolstov"),
    ("Partial Differential Equations", "Tyn Myint"),
    ("Tensor Calculus", "Dirk J. Struik"),
    ("Chaos", "James Gleick"),
    ("Fractals", "Benoit Mandelbrot"),
    ("Mathematical Biology", "John D. Murray"),
    ("Financial Mathematics", "John Hull"),
    ("Matrix Analysis", "Horn Roger"),
    ("Vector Spaces", "Serge Lang"),
    ("Measure Theory", "Halmos Paul"),
    ("Functional Analysis", "Walter Rudin"),
    ("Complex Variables", "Murray Spiegel"),
    ("Integral Equations", "M. A. P. S. Rao"),
    ("Green's Functions", "G. F. Carrier"),
    ("Special Functions", "Rainville E.D."),
    ("Harmonic Analysis", "Stein E.M."),
    ("Wavelet Theory", "Daubechies Ingrid"),
    ("Differential Geometry", "Andrew Pressley"),
    ("Mathematical Statistics", "John Freund"),
    ("Time Series Analysis", "Box Jenkins"),
    ("Regression Analysis", "Douglas Montgomery"),
    ("Experimental Design", "Montgomery Douglas"),
    ("Linear Programming", "Vanderbei Robert"),
    ("Integer Programming", "Laurence Wolsey"),
    ("Nonlinear Programming", "Bazaraa M.S."),
    ("Dynamic Programming", "Richard Bellman"),
    ("Stochastic Processes", "Sheldon Ross"),
    ("Queueing Theory", "Gross Donald"),
    ("Inventory Control", "Silver Edward"),
    ("Forecasting", "Makridakis Spyros"),
    ("1984", "George Orwell"),
    ("Animal Farm", "George Orwell"),
    ("To Kill a Mockingbird", "Harper Lee"),
    ("The Great Gatsby", "F. Scott Fitzgerald"),
    ("Brave New World", "Aldous Huxley"),
    ("Fahrenheit 451", "Ray Bradbury"),
    ("The Catcher in the Rye", "J.D. Salinger"),
    ("Lord of the Flies", "William Golding"),
    ("The Alchemist", "Paulo Coelho"),
    ("The Prophet", "Kahlil Gibran"),
    ("One Hundred Years of Solitude", "Gabriel Garcia Marquez"),
    ("The God of Small Things", "Arundhati Roy"),
    ("Midnight's Children", "Salman Rushdie"),
    ("The Kite Runner", "Khaled Hosseini"),
    ("A Thousand Splendid Suns", "Khaled Hosseini"),
    ("Invisible Man", "Ralph Ellison"),
    ("The Color Purple", "Alice Walker"),
    ("Beloved", "Toni Morrison"),
    ("And Then There Were None", "Agatha Christie"),
    ("Murder on the Orient Express", "Agatha Christie"),
    ("The Hound of the Baskervilles", "Arthur Conan Doyle"),
    ("The Adventures of Sherlock Holmes", "Arthur Conan Doyle"),
    ("Pride and Prejudice", "Jane Austen"),
    ("Emma", "Jane Austen"),
    ("Wuthering Heights", "Emily Bronte"),
    ("Jane Eyre", "Charlotte Bronte"),
    ("Gone with the Wind", "Margaret Mitchell"),
    ("Rebecca", "Daphne du Maurier"),
    ("The Count of Monte Cristo", "Alexandre Dumas"),
    ("The Three Musketeers", "Alexandre Dumas"),
    ("Les Miserables", "Victor Hugo"),
    ("The Picture of Dorian Gray", "Oscar Wilde"),
    ("Frankenstein", "Mary Shelley"),
    ("Dracula", "Bram Stoker"),
    ("Treasure Island", "Robert Louis Stevenson"),
    ("The Old Man and the Sea", "Ernest Hemingway"),
    ("A Farewell to Arms", "Ernest Hemingway"),
    ("The Sun Also Rises", "Ernest Hemingway"),
    ("The Grapes of Wrath", "John Steinbeck"),
    ("Of Mice and Men", "John Steinbeck"),
    ("East of Eden", "John Steinbeck"),
    ("To the Lighthouse", "Virginia Woolf"),
    ("Mrs Dalloway", "Virginia Woolf"),
    ("The Blue Umbrella", "Ruskin Bond"),
    ("Great Expectations", "Charles Dickens"),
    ("Oliver Twist", "Charles Dickens"),
    ("Hard Times", "Charles Dickens"),
    ("A Tale of Two Cities", "Charles Dickens"),
    ("Anna Karenina", "Leo Tolstoy"),
    ("War and Peace", "Leo Tolstoy"),
    ("The Brothers Karamazov", "Fyodor Dostoevsky"),
    ("Crime and Punishment", "Fyodor Dostoevsky"),
    ("The Idiot", "Fyodor Dostoevsky"),
    ("The Master and Margarita", "Mikhail Bulgakov"),
    ("Dead Souls", "Nikolai Gogol"),
    ("Heart of Darkness", "Joseph Conrad"),
    ("The Secret Garden", "Frances Hodgson Burnett"),
    ("Alice's Adventures in Wonderland", "Lewis Carroll"),
    ("Winnie the Pooh", "A.A. Milne"),
    ("The Wind in the Willows", "Kenneth Grahame"),
    ("Peter Pan", "J.M. Barrie"),
    ("The Jungle Book", "Rudyard Kipling"),
    ("Kim", "Rudyard Kipling"),
    ("Gulliver's Travels", "Jonathan Swift"),
    ("Robinson Crusoe", "Daniel Defoe"),
    ("The Call of the Wild", "Jack London"),
    ("White Fang", "Jack London"),
    ("The Time Machine", "H.G. Wells"),
    ("The War of the Worlds", "H.G. Wells"),
    ("The Adventures of Tom Sawyer", "Mark Twain"),
    ("The Adventures of Huckleberry Finn", "Mark Twain"),
    ("Around the World in 80 Days", "Jules Verne"),
    ("Journey to the Center of the Earth", "Jules Verne"),
    ("Twenty Thousand Leagues Under the Sea", "Jules Verne"),
    ("Moby Dick", "Herman Melville"),
    ("The Scarlet Letter", "Nathaniel Hawthorne"),
    ("The House of the Spirits", "Isabel Allende"),
    ("The Bell Jar", "Sylvia Plath"),
    ("The Handmaid's Tale", "Margaret Atwood"),
    ("Never Let Me Go", "Kazuo Ishiguro"),
    ("The Remains of the Day", "Kazuo Ishiguro"),
    ("Norwegian Wood", "Haruki Murakami"),
    ("Kafka on the Shore", "Haruki Murakami"),
    ("1Q84", "Haruki Murakami"),
    ("The Unbearable Lightness of Being", "Milan Kundera"),
    ("The Trial", "Franz Kafka"),
    ("The Metamorphosis", "Franz Kafka"),
    ("Demian", "Hermann Hesse"),
    ("Siddhartha", "Hermann Hesse"),
    ("Steppenwolf", "Hermann Hesse"),
    ("The Glass Castle", "Jeannette Walls"),
    ("Atonement", "Ian McEwan"),
    ("Life of Pi", "Yann Martel"),
    ("The Hitchhiker's Guide to the Galaxy", "Douglas Adams"),
    ("Good Omens", "Neil Gaiman"),
    ("American Gods", "Neil Gaiman"),
    ("The Sandman", "Neil Gaiman"),
    ("The Fault in Our Stars", "John Green"),
    ("Looking for Alaska", "John Green"),
    ("Paper Towns", "John Green"),
    ("The Perks of Being a Wallflower", "Stephen Chbosky"),
    ("The Book Thief", "Markus Zusak"),
    ("The Boy in the Striped Pyjamas", "John Boyne"),
    ("The Girl with the Dragon Tattoo", "Stieg Larsson"),
    ("The Girl Who Played with Fire", "Stieg Larsson"),
    ("The Girl Who Kicked the Hornets' Nest", "Stieg Larsson"),
    ("Gone Girl", "Gillian Flynn"),
    ("Sharp Objects", "Gillian Flynn"),
    ("Dark Places", "Gillian Flynn"),
    ("The Girl on the Train", "Paula Hawkins"),
    ("Behind Closed Doors", "B.A. Paris"),
    ("The Couple Next Door", "Shari Lapena"),
    ("Then She Was Gone", "Lisa Jewell"),
    ("I Am Watching You", "Teresa Driscoll"),
    ("The Woman in the Window", "A.J. Finn"),
    ("The Silent Patient", "Alex Michaelides"),
    ("The Maidens", "Alex Michaelides"),
    ("The Subtle Art of Not Giving a F*ck", "Mark Manson"),
    ("Think and Grow Rich", "Napoleon Hill"),
    ("The 7 Habits of Highly Effective People", "Stephen Covey"),
    ("How to Win Friends and Influence People", "Dale Carnegie"),
    ("The Power of Positive Thinking", "Norman Vincent Peale"),
    ("Zero to One", "Peter Thiel"),
    ("The Lean Startup", "Eric Ries"),
    ("Start with Why", "Simon Sinek"),
    ("Good to Great", "Jim Collins"),
    ("The Hard Thing About Hard Things", "Ben Horowitz"),
    ("The 4-Hour Workweek", "Tim Ferriss"),
    ("Rework", "Jason Fried"),
    ("The Innovator's Dilemma", "Clayton Christensen"),
    ("Blue Ocean Strategy", "W. Chan Kim"),
    ("Contagious", "Jonah Berger"),
    ("Influence", "Robert Cialdini"),
    ("Rich Dad Poor Dad", "Robert Kiyosaki"),
    ("The Intelligent Investor", "Benjamin Graham"),
    ("The Richest Man in Babylon", "George Clason"),
    ("Moneyball", "Michael Lewis"),
    ("The Black Swan", "Nassim Taleb"),
    ("Thinking, Fast and Slow", "Daniel Kahneman"),
    ("The Signal and the Noise", "Nate Silver"),
    ("Predictably Irrational", "Dan Ariely"),
    ("Freakonomics", "Steven Levitt"),
    ("Nudge", "Richard Thaler"),
    ("The Four Agreements", "Don Miguel Ruiz"),
    ("The Five Love Languages", "Gary Chapman"),
    ("Men Are from Mars, Women Are from Venus", "John Gray"),
    ("Attached", "Amir Levine"),
    ("The Power of Now", "Eckhart Tolle"),
    ("A New Earth", "Eckhart Tolle"),
    ("The Secret", "Rhonda Byrne"),
    ("The Untethered Soul", "Michael A. Singer"),
    ("The Body Keeps the Score", "Bessel van der Kolk"),
    ("Emotional Intelligence", "Daniel Goleman"),
    ("Quiet", "Susan Cain"),
    ("Daring Greatly", "Brene Brown"),
    ("The Happiness Hypothesis", "Jonathan Haidt"),
    ("Flow", "Mihaly Csikszentmihalyi"),
    ("Reasons to Stay Alive", "Matt Haig"),
    ("The Art of Happiness", "Dalai Lama"),
    ("The Road Less Traveled", "M. Scott Peck"),
    ("Man's Search for Meaning", "Viktor Frankl"),
    ("The Last Lecture", "Randy Pausch"),
    ("Meditations", "Marcus Aurelius"),
    ("The Daily Stoic", "Ryan Holiday"),
    ("Ikigai", "Hector Garcia"),
    ("Awaken the Giant Within", "Tony Robbins"),
    ("The 5 AM Club", "Robin Sharma"),
    ("The Monk Who Sold His Ferrari", "Robin Sharma"),
    ("Who Moved My Cheese", "Spencer Johnson"),
    ("The One Minute Manager", "Kenneth Blanchard"),
    ("Drive", "Daniel Pink"),
    ("The Miracle Morning", "Hal Elrod"),
    ("Eat That Frog", "Brian Tracy"),
    ("So Good They Can't Ignore You", "Cal Newport"),
    ("Digital Minimalism", "Cal Newport"),
    ("Ultralearning", "Scott Young"),
    ("The Art of Learning", "Josh Waitzkin"),
    ("Moonwalking with Einstein", "Joshua Foer"),
    ("Make It Stick", "Peter Brown"),
    ("The Learning Brain", "Sarah-Jayne Blakemore"),
    ("Why Don't Students Like School", "Daniel Willingham"),
    ("How Learning Works", "Ambrose"),
    ("The E-Myth", "Michael Gerber"),
    ("Crossing the Chasm", "Geoffrey Moore"),
    ("The Art of War", "Sun Tzu"),
    ("48 Laws of Power", "Robert Greene"),
    ("The Prince", "Machiavelli"),
    ("The Laws of Human Nature", "Robert Greene"),
    ("Mastery", "Robert Greene"),
    ("The 33 Strategies of War", "Robert Greene"),
    ("Shoe Dog", "Phil Knight"),
    ("Steve Jobs", "Walter Isaacson"),
    ("Elon Musk", "Ashlee Vance"),
    ("Becoming", "Michelle Obama"),
    ("Long Walk to Freedom", "Nelson Mandela"),
    ("The Autobiography of Benjamin Franklin", "Benjamin Franklin"),
    ("Einstein", "Walter Isaacson"),
    ("Leadership", "John Maxwell"),
    ("The 21 Irrefutable Laws of Leadership", "John Maxwell"),
    ("Built to Last", "Jim Collins"),
]
    books_list *= 2
    for name, author in books_list:
        new_book = Book(name=name, author=author, status='Available')
        db.session.add(new_book)
    db.session.commit()
    logging.info(f"Added {len(books_list)} books to database")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_books()

    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG") == "True"
    app.run(host='0.0.0.0', port=port, debug=debug_mode)