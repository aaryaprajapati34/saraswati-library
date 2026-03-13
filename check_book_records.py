from models import db, User, Book
from app import app

def check_book_records():
    """Check which user has taken which book"""
    with app.app_context():
        # Get all issued books
        issued_books = Book.query.filter_by(status='Issued').all()
        
        if not issued_books:
            print("\n📚 No books are currently issued!")
            return
        
        print("\n" + "=" * 80)
        print("📚 BOOK ISSUE RECORDS")
        print("=" * 80)
        print(f"{'User Name':<20} | {'User Email':<25} | {'Book Name':<30} | {'Issue Date':<12} | {'Due Date':<12}")
        print("-" * 80)
        
        for book in issued_books:
            # Get user who has the book
            user = User.query.filter_by(email=book.holder).first()
            
            user_name = user.name if user else "Unknown"
            user_email = user.email if user else "Unknown"
            book_name = book.name
            issue_date = book.issue_date if book.issue_date else "N/A"
            due_date = book.due_date if book.due_date else "N/A"
            
            print(f"{user_name:<20} | {user_email:<25} | {book_name:<30} | {issue_date:<12} | {due_date:<12}")
        
        print("=" * 80)
        print(f"\nTotal Issued Books: {len(issued_books)}")
        print("=" * 80)

def check_user_books(email):
    """Check all books taken by a specific user"""
    with app.app_context():
        # Get user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            print(f"\n❌ User not found: {email}")
            return
        
        # Get all issued books for this user
        issued_books = Book.query.filter_by(holder=email, status='Issued').all()
        
        print(f"\n📚 Books taken by {user.name} ({email}):")
        print("-" * 80)
        
        if not issued_books:
            print("No books currently issued!")
        else:
            print(f"{'Book Name':<30} | {'Author':<25} | {'Issue Date':<12} | {'Due Date':<12}")
            print("-" * 80)
            
            for book in issued_books:
                print(f"{book.name:<30} | {book.author:<25} | {book.issue_date if book.issue_date else 'N/A':<12} | {book.due_date if book.due_date else 'N/A':<12}")
        
        print("-" * 80)
        print(f"Total Books Issued: {len(issued_books)}")

def check_all_users_books():
    """Check all users and their issued books"""
    with app.app_context():
        users = User.query.all()
        
        print("\n" + "=" * 80)
        print("📚 ALL USERS AND THEIR BOOKS")
        print("=" * 80)
        
        for user in users:
            issued_books = Book.query.filter_by(holder=user.email, status='Issued').all()
            
            print(f"\n👤 {user.name} ({user.email})")
            print(f"   Member ID: {user.member_id}")
            print(f"   Books Issued: {len(issued_books)}")
            
            if issued_books:
                for book in issued_books:
                    print(f"   - {book.name} (Due: {book.due_date if book.due_date else 'N/A'})")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    print("\n🎓 SARASWATI LIBRARY - BOOK RECORD CHECKER")
    print("=" * 50)
    
    print("\nWhat would you like to check?")
    print("1. All issued books (User → Book mapping)")
    print("2. Books taken by specific user (by email)")
    print("3. All users and their books")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1/2/3/4): ").strip()
    
    if choice == "1":
        check_book_records()
    elif choice == "2":
        email = input("Enter user email: ").strip()
        check_user_books(email)
    elif choice == "3":
        check_all_users_books()
    elif choice == "4":
        print("Exiting...")
    else:
        print("Invalid choice!")