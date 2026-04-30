from app.config.settings import settings

def check_settings():
    print(f"EMAIL_USER: {'Set' if settings.EMAIL_USER else 'NOT SET'}")
    print(f"EMAIL_PASS: {'Set' if settings.EMAIL_PASS else 'NOT SET'}")
    print(f"EMAIL_RECEIVER: {'Set' if settings.EMAIL_RECEIVER else 'NOT SET'}")
    
    if settings.EMAIL_USER:
        print(f"User value (first 3 chars): {settings.EMAIL_USER[:3]}...")

if __name__ == "__main__":
    check_settings()
