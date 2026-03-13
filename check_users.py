from models import db, User, Book
from app import app

def check_users():
    """Check total users and list all users"""
    with app.app_context():
        user_count = User.query.count()
        print("=" * 50)
        print("📊 USER STATISTICS")
        print("=" * 50)
        print(f"Total Users: {user_count}")
        
        # Show all users
        users = User.query.all()
        print("\n📋 User List:")
        print("-" * 50)
        for user in users:
            print(f"- {user.name} ({user.email}) - {user.member_id} - Role: {user.role}")
        print("=" * 50)

def check_books():
    """Check total books and list all books"""
    with app.app_context():
        book_count = Book.query.count()
        print("\n📚 BOOK STATISTICS")
        print("=" * 50)
        print(f"Total Books: {book_count}")
        
        # Show books by status
        available = Book.query.filter_by(status='Available').count()
        issued = Book.query.filter_by(status='Issued').count()
        requested = Book.query.filter_by(status='Requested').count()
        
        print(f"  - Available: {available}")
        print(f"  - Issued: {issued}")
        print(f"  - Requested: {requested}")
        print("=" * 50)

def check_all():
    """Check both users and books"""
    check_users()
    check_books()

if __name__ == "__main__":
    print("\n🎓 SARASWATI LIBRARY SYSTEM - DATABASE CHECKER")
    print("=" * 50)
    
    # Ask user what to check
    print("\nWhat would you like to check?")
    print("1. Users only")
    print("2. Books only")
    print("3. Both Users and Books")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    if choice == "1":
        check_users()
    elif choice == "2":
        check_books()
    elif choice == "3":
        check_all()
    else:
        print("Invalid choice! Showing all data...")
        check_all()
    
    print("\n✅ Check complete!")