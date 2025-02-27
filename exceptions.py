from fastapi import Request, status
from fastapi.responses import JSONResponse


class TaskAPIException(Exception):
    status_code: int
    detail: str

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


async def task_exception_handler(request: Request, exc: TaskAPIException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# Define some common exceptions
class TaskNotFoundException(TaskAPIException):
    def __init__(self, task_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )


class UserNotFoundException(TaskAPIException):
    def __init__(self, user_id: int = None, email: str = None):
        detail = "User not found"
        if user_id:
            detail = f"User with ID {user_id} not found"
        elif email:
            detail = f"User with email {email} not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class InvalidCredentialsException(TaskAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
