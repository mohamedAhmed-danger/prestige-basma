# seed.py
from app import create_app
from app.services.auth_service import create_user

app = create_app()

with app.app_context():
    create_user(name="admin", password="123456", role="admin")
    create_user(name="emp1`", password="123456", role="employee")
    print("تم إنشاء اليوزرز بنجاح")