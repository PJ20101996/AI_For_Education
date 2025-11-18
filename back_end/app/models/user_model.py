def create_user(email, name, password):
    return {
        "email": email,
        "name": name,
        "password": password,
        "uploads": [],
        "summaries": []
    }
