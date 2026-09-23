def validate_username(name):
    if not name or not name.strip():
        raise ValueError('اسم المستخدم مطلوب')
    return name.strip()


def validate_password(password):
    if not password or len(password) < 6:
        raise ValueError('كلمة المرور لازم تكون 6 حروف على الأقل')
    return password