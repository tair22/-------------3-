from logic import DB_Manager
from config import DATABASE

manager = DB_Manager(DATABASE)
manager.insert_project([('2', 'telega', '\/\/\/\]', 'нету', '9')])