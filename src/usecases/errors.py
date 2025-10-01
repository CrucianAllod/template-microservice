class NotFoundDatabaseError(Exception):
    def __init__(self, message: str = "Requested item not found in the database"):
        super().__init__(message)

class AuthenticationError(Exception):
    def __init__(self, message: str = "Invalid username or password."):
        super().__init__(message)

class UserAlreadyExistsError(Exception):
    def __init__(self, message: str = "User already exists."):
        super().__init__(message)