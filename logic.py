import sqlite3
from config import DATABASE

skills = [ (_,) for _ in (['Python', 'SQL', 'API', 'Telegram'])]
statuses = [ (_,) for _ in (['На этапе проектирования', 'В процессе разработки', 'Разработан. Готов к использованию.', 'Обновлен', 'Завершен. Не поддерживается'])]

class DB_Manager:
    """Класс для управления базой данных проектов."""
    def __init__(self, database):
        """Инициализирует менеджер базы данных.

        """
        self.database = database

    def create_tables(self):
        """Создает таблицы в базе данных, если они еще не существуют."""
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS projects (
                            project_id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            project_name TEXT NOT NULL,
                            description TEXT,
                            url TEXT,
                            status_id INTEGER,
                            photo TEXT,
                            FOREIGN KEY(status_id) REFERENCES status(status_id)
                        )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS skills (
                            skill_id INTEGER PRIMARY KEY,
                            skill_name TEXT
                        )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS project_skills (
                            project_id INTEGER,
                            skill_id INTEGER,
                            FOREIGN KEY(project_id) REFERENCES projects(project_id),
                            FOREIGN KEY(skill_id) REFERENCES skills(skill_id)
                        )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS status (
                            status_id INTEGER PRIMARY KEY,
                            status_name TEXT
                        )''')
            conn.commit()

    print("База данных успешно создана.")
    def __executemany(self, sql, data):
        """Выполняет SQL-запрос с несколькими наборами параметров.

        """
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany(sql, data)
            conn.commit()

    def __select_data(self, sql, data = tuple()):
        """Выполняет SELECT-запрос и возвращает результаты.

        """
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return cur.fetchall()
            

    def default_insert(self):
        """Вставляет стандартные значения навыков и статусов в базу данных."""
        sql = 'INSERT OR IGNORE INTO skills (skill_name) values(?)'
        data = skills
        self.__executemany(sql, data)
        sql = 'INSERT OR IGNORE INTO status (status_name) values(?)'
        data = statuses
        self.__executemany(sql, data)


    def insert_project(self, data):
        """Вставляет новый проект в базу данных.
        """
        sql = 'INSERT OR IGNORE INTO projects (user_id, project_name, url, status_id) values(?, ?, ?, ?)'
        self.__executemany(sql, data)

    def insert_skill(self, user_id, project_name, skill):
        """Добавляет навык к проекту.

        """
        sql = 'SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?'
        project_id = self.__select_data(sql, (project_name, user_id))[0][0]
        skill_id = self.__select_data('SELECT skill_id FROM skills WHERE skill_name = ?', (skill,))[0][0]
        data = [(project_id,skill_id)]
        sql = 'INSERT OR IGNORE INTO project_skills VALUES (?, ?)'
        self.__executemany(sql, data)

  
    def get_statuses(self):
        """Получает все статусы проектов.
        """
        sql='SELECT status_name from status'
        return self.__select_data(sql)
        
    def get_status_id(self, status_name):
        """Получает ID статуса по его названию.

        """
        sql = 'SELECT status_id FROM status WHERE status_name = ?'
        res = self.__select_data(sql, (status_name,))
        if res: return res[0][0]
        else: return None

    def get_projects(self, user_id):
        """Получает все проекты пользователя.

        """
        return self.__select_data(sql='SELECT * FROM projects WHERE user_id = ?', data = (user_id,))

    def get_project_id(self, project_name, user_id):
        """Получает ID проекта по его названию и ID пользователя.
        """
        return self.__select_data(sql='SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?  ', data = (project_name, user_id,))[0][0]

    def get_skills(self):
        """Получает все навыки.
        """
        return self.__select_data(sql='SELECT * FROM skills')
    
    def get_project_skills(self, project_name):
        """Получает навыки проекта.

        """
        res = self.__select_data(sql='''SELECT skill_name FROM projects
JOIN project_skills ON projects.project_id = project_skills.project_id
JOIN skills ON skills.skill_id = project_skills.skill_id
WHERE project_name = ?''', data = (project_name,) )
        return ', '.join([x[0] for x in res])
    
    def get_project_info(self, user_id, project_name):
        """Получает информацию о проекте.
        """
        # First try to get project info with status join
        sql = """
SELECT project_name, description, url, status_name FROM projects
JOIN status ON
status.status_id = projects.status_id
WHERE project_name=? AND user_id=?
"""
        result = self.__select_data(sql=sql, data = (project_name, user_id))
        
        # If no result found, try to get basic project info without status join
        if not result:
            sql = """
SELECT project_name, description, url, NULL as status_name FROM projects
WHERE project_name=? AND user_id=?
"""
            result = self.__select_data(sql=sql, data = (project_name, user_id))
            
        return result
    

    def update_projects(self, param, data):
        """Обновляет параметр проекта.

        """
        self.__executemany(f"UPDATE projects SET {param} = ? WHERE project_name = ? AND user_id = ?", [data]) # data ('atr', 'mew', 'name', 'user_id')

    def update_status(self, project_name, user_id, status_name):
        """Обновляет статус проекта.

        """
        status_id = self.get_status_id(status_name)
        if status_id:
            self.__executemany("UPDATE projects SET status_id = ? WHERE project_name = ? AND user_id = ?", [(status_id, project_name, user_id)])
            return True
        return False
    
    def update_skills(self, project_name, user_id, skills):
        """Обновляет навыки проекта.

        """
        # Удаляем старые навыки проекта
        project_id = self.get_project_id(project_name, user_id)
        self.__executemany("DELETE FROM project_skills WHERE project_id = ?", [(project_id,)])
        
        # Добавляем новые навыки
        for skill_name in skills:
            skill_id = self.__select_data('SELECT skill_id FROM skills WHERE skill_name = ?', (skill_name,))
            if skill_id:
                self.__executemany("INSERT INTO project_skills (project_id, skill_id) VALUES (?, ?)", [(project_id, skill_id[0][0])])
                
    def delete_project(self, user_id, project_id):
        """Удаляет проект.

        """
        # Удаляем связанные навыки проекта
        self.delete_project_skills(project_id)
        
        # Удаляем проект
        sql = "DELETE FROM projects WHERE user_id = ? AND project_id = ? "
        self.__executemany(sql, [(user_id, project_id)])

    def delete_skill(self, project_id, skill_id):
        """Удаляет навык.

        """
        sql = "DELETE FROM skills WHERE skill_id = ? AND project_id = ? "
        self.__executemany(sql, [(skill_id, project_id)])

    def delete_project_skill(self, project_id, skill_id):
        """Удаляет навык проекта.

        """
        sql = """DELETE FROM project_skills  WHERE project_id = ? AND skill_id = ?"""
        self.__executemany(sql, [(project_id, skill_id)])

    def delete_project_skills(self, project_id):
        """Удаляет все навыки проекта.

        """
        sql = """DELETE FROM project_skills
                WHERE project_id = ?"""
        self.__executemany(sql, [(project_id,)])

if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    manager.create_tables()
    manager.default_insert()
