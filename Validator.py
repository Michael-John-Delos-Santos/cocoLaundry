def validate_password_complexity(password):
    length_check = len(password) >= 8
    upper_check = any(char.isupper() for char in password)
    lower_check = any(char.islower() for char in password)
    special_check = any(char in "!@#$%^&*(),.?\":{}|<>" for char in password)
    digit_check = any(char.isdigit() for char in password)

    if not (length_check and upper_check and lower_check and special_check and digit_check):
        return "Password must be at least 8 characters long and contain: uppercase, lowercase, numerical, and a special character."
    
    return None