

class TestFactory:

    @staticmethod
    def user_factory(first_name=None, last_name=None, email=None, password=None, username=None):
        return {
            "first_name": first_name or "test",
            "last_name": last_name or "test",
            "username": username or "test",
            "email": email or "test@example.com",
            "password": password or "test1212"
        }


    @staticmethod
    def author_factory():
        return {
            "first_name": "John",
            "last_name": "Doe",
            "biography": "Good Author"
        }


    @staticmethod
    def book_factory():
        return {
            "title": "Introduction to Django with Python",
            "author_id": 1,
            "isbn": "0387-5678-456",
            "genre": "dev",
            "available_copies": 5
        }