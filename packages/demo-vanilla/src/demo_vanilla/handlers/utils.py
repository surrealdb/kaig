# def ensure_db_open(func):
#     """Decorator to ensure the db connection is open, and close it after the function is executed"""

#     async def wrapper(*args, **kwargs):
#         if "db" not in kwargs:
#             raise ValueError("db is not in kwargs")
#         await kwargs["db"].ensure_open()
#         return await func(*args, **kwargs)
#         # finally:
#         #     await kwargs["db"].close()

#     return wrapper
