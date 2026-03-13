from models import db, User
from app import app

def delete_user_by_email(email):
    """Delete user by email"""
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            print(f"✅ User deleted: {user.name} ({user.email})")
        else:
            print("❌ User not found!")

def delete_user_by_id(user_id):
    """Delete user by ID"""
    with app.app_context():
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            print(f"✅ User deleted: {user.name} ({user.email})")
        else:
            print("❌ User not found!")

if __name__ == "__main__":
    print("\n🗑️ SARASWATI LIBRARY - DELETE USER TOOL")
    print("=" * 50)
    
    print("\nWhat would you like to do?")
    print("1. Delete user by email")
    print("2. Delete user by ID")
    print("3. Show all users first")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    if choice == "1":
        email = input("Enter user email: ").strip()
        delete_user_by_email(email)
    elif choice == "2":
        user_id = input("Enter user ID: ").strip()
        delete_user_by_id(int(user_id))
    elif choice == "3":
        with app.app_context():
            users = User.query.all()
            print("\n📋 Current Users:")
            for user in users:
                print(f"- ID: {user.id} | {user.name} | {user.email}")
    else:
        print("Invalid choice!")