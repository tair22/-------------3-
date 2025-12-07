import telebot
from logic import DB_Manager
from config import *
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telebot import types
import os

bot = TeleBot(TOKEN)
hideBoard = types.ReplyKeyboardRemove() 

cancel_button = "Отмена 🚫"
def cancel(message):
    """
    Отправляет сообщение пользователю с информацией о доступных командах.
    
    """
    bot.send_message(message.chat.id, "Чтобы посмотреть команды, используй - /info", reply_markup=hideBoard)
  
def no_projects(message):
    """
    Отправляет сообщение пользователю о том, что у него пока нет проектов.
    
    """
    bot.send_message(message.chat.id, 'У тебя пока нет проектов!\nМожешь добавить их с помошью команды /new_project')

def gen_inline_markup(rows):
    """
    Создает инлайн-клавиатуру с кнопками.
 
    """
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for row in rows:
        markup.add(InlineKeyboardButton(row, callback_data=row))
    return markup
def gen_markup(rows):
    """
    Создает клавиатуру с кнопками.
    
    """
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row_width = 1
    for row in rows:
        markup.add(KeyboardButton(row))
    markup.add(KeyboardButton(cancel_button))
    return markup


attributes_of_projects = {'Имя проекта' : ["Введите новое имя проекта", "project_name"],
                          "Описание" : ["Введите новое описание проекта", "description"],
                          "Ссылка" : ["Введите новую ссылку на проект", "url"],
                          "Статус" : ["Выберите новый статус задачи", "status_id"]}

def info_project(message, user_id, project_name):
    """
    Отправляет пользователю информацию о проекте.
    
    """
    try:
        project_info = manager.get_project_info(user_id, project_name)
        if not project_info:
            bot.send_message(message.chat.id, f"Проект с именем '{project_name}' не найден.")
            return
            
        info = project_info[0]
        skills = manager.get_project_skills(project_name)
        if not skills:
            skills = 'Навыки пока не добавлены'
        bot.send_message(message.chat.id, f"""Project name: {info[0]}
Description: {info[1]}
Link: {info[2]}
Status: {info[3]}
Skills: {skills}
""")
        # Проверяем наличие фото у проекта
        project_data = manager.get_projects(user_id)
        project = next((p for p in project_data if p[2] == project_name), None)
        photo_path = project[6] if project and len(project) > 6 else None
        if photo_path and os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo)
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка при получении информации о проекте: {str(e)}")
        print(f"Error in info_project: {e}")

# Хэндлер для команды /start
@bot.message_handler(commands=['start'])
def start_command(message):
    """
    Обработчик команды /start.
    Отправляет приветственное сообщение и информацию о доступных командах.
    
    """
    bot.send_message(message.chat.id, """👋 Привет! Я бот-менеджер проектов 🤖
Помогу тебе сохранить твои проекты и информацию о них! 📁
""")
    info(message)
    
# Хэндлер для команды /info
@bot.message_handler(commands=['info'])
def info(message):
    """
    Обработчик команды /info.
    Отправляет пользователю информацию о доступных командах.
    
    """
    bot.send_message(message.chat.id,
"""
🤖 Вот команды которые могут тебе помочь:
📍 /description - описание проекта
➕ /new_project - добавить новый проект
📋 /projects - список всех проектов
🎯 /skills - добавить навыки к проекту
✏️ /update_projects - обновить информацию о проекте
🗑️ /delete - удалить проект
📸 /add_photo - добавить фото
🤳🏼 /change_photo - изменить фото

Также ты можешь ввести имя проекта и узнать информацию о нем! 📚""")
    

# Хэндлер для команды /new_project
@bot.message_handler(commands=['new_project'])
def addtask_command(message):
    """
    Обработчик команды /new_project.
    Запрашивает у пользователя название проекта.
    
    """
    bot.send_message(message.chat.id, "Введите название проекта:")
    bot.register_next_step_handler(message, name_project)

def name_project(message):
    """
    Обрабатывает ввод названия проекта.
    Запрашивает у пользователя ссылку на проект.

    """
    name = message.text
    user_id = message.from_user.id
    data = [user_id, name]
    bot.send_message(message.chat.id, "Введите ссылку на проект")
    bot.register_next_step_handler(message, link_project, data=data)

def link_project(message, data):
    """
    Обрабатывает ввод ссылки на проект.
    Запрашивает у пользователя текущий статус проекта.
    
    """
    data.append(message.text)
    statuses = [x[0] for x in manager.get_statuses()]
    bot.send_message(message.chat.id, "Введите текущий статус проекта", reply_markup=gen_markup(statuses))
    bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)

def callback_project(message, data, statuses):
    """
    Обрабатывает выбор статуса проекта.
    Сохраняет проект в базе данных.
    
    """
    status = message.text
    if message.text == cancel_button:
        cancel(message)
        return
    if status not in statuses:
        bot.send_message(message.chat.id, "Ты выбрал статус не из списка, попробуй еще раз!)", reply_markup=gen_markup(statuses))
        bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)
        return
    status_id = manager.get_status_id(status)
    data.append(status_id)
    manager.insert_project([tuple(data)])
    bot.send_message(message.chat.id, "Проект сохранен")

# Хэндлер для добавления фото при создании проекта
@bot.message_handler(commands=['add_photo'])
def add_photo_handler(message):
    """
    Обработчик команды /add_photo.
    Запрашивает у пользователя фото для проекта.
    
    """
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, 'Выбери проект для которого нужно добавить фото', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, request_photo, projects=projects)
    else:
        no_projects(message)


# Хэндлер для команды /skills
@bot.message_handler(commands=['skills'])
def skill_handler(message):
    """
    Обработчик команды /skills.
    Отправляет пользователю список проектов для выбора навыка.

    """
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, 'Выбери проект для которого нужно выбрать навык', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        no_projects(message)


def skill_project(message, projects):
    """
    Обрабатывает выбор проекта для добавления навыка.
    Отправляет пользователю список навыков для выбора.
    
    """
    project_name = message.text
    if message.text == cancel_button:
        cancel(message)
        return
        
    if project_name not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй еще раз!) Выбери проект для которого нужно выбрать навык', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        skills = [x[1] for x in manager.get_skills()]
        bot.send_message(message.chat.id, 'Выбери навык', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)

def set_skill(message, project_name, skills):
    """
    Обрабатывает выбор навыка для проекта.
    Сохраняет навык в базе данных.
    
    """
    skill = message.text
    user_id = message.from_user.id
    if message.text == cancel_button:
        cancel(message)
        return
        
    if skill not in skills:
        bot.send_message(message.chat.id, 'Видимо, ты выбрал навык. не из спика, попробуй еще раз!) Выбери навык', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)
        return
    manager.insert_skill(user_id, project_name, skill )
    bot.send_message(message.chat.id, f'Навык {skill} добавлен проекту {project_name}')


def request_photo(message, projects):
    """
    Обрабатывает выбор проекта и запрашивает фото.
    
    """
    project_name = message.text
    if message.text == cancel_button:
        cancel(message)
        return
        
    if project_name not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй еще раз!) Выбери проект для которого нужно добавить фото', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, request_photo, projects=projects)
    else:
        bot.send_message(message.chat.id, 'Пришли фото для проекта:')
        bot.register_next_step_handler(message, handle_photo, project_name=project_name)

def handle_photo(message, project_name):
    """
    Обрабатывает полученное фото и сохраняет его.
    
    """
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, 'Это не фото. Пожалуйста, пришли фото.')
        bot.register_next_step_handler(message, handle_photo, project_name=project_name)
        return
    
    file_id = message.photo[-1].file_id
    
    # Сохраняем фото локально
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    photo_path = f"photos/{project_name}.jpg"
    
    # Создаем папку photos если её нет
    if not os.path.exists("photos"):
        os.makedirs("photos")
        
    with open(photo_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    
    # Сохраняем путь к фото в БД
    user_id = message.from_user.id
    data = (photo_path, project_name, user_id)
    manager.update_projects("photo", data)
    bot.send_message(message.chat.id, f'Фото добавлено проекту {project_name}')


# Хэндлер для команды /projects
@bot.message_handler(commands=['projects'])
def get_projects(message):
    """
    Обработчик команды /projects.
    Отправляет пользователю список всех проектов.
    
    """
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"Project name:{x[2]} \nLink:{x[4]}\n" for x in projects])
        bot.send_message(message.chat.id, text, reply_markup=gen_inline_markup([x[2] for x in projects]))
    else:
        no_projects(message)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """
    Обработчик callback-запросов.
    Отправляет пользователю информацию о проекте.
    
    """
    project_name = call.data
    info_project(call.message, call.from_user.id, project_name)


# Хэндлер для команды /delete
@bot.message_handler(commands=['delete'])
def delete_handler(message):
    """
    Обработчик команды /delete.
    Отправляет пользователю список проектов для удаления.
   
    """
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"Project name:{x[2]} \nLink:{x[4]}\n" for x in projects])
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, text, reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
    else:
        no_projects(message)

def delete_project(message, projects):
    """
    Обрабатывает выбор проекта для удаления.
    Удаляет проект из базы данных.
    """
    project = message.text
    user_id = message.from_user.id

    if message.text == cancel_button:
        cancel(message)
        return
    if project not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй выбрать еще раз!', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
        return
    project_id = manager.get_project_id(project, user_id)
    manager.delete_project(user_id, project_id)
    bot.send_message(message.chat.id, f'Проект {project} удален!')


# Хэндлер для команды /update_projects
@bot.message_handler(commands=['update_projects'])
def update_project(message):
    """
    Обработчик команды /update_projects.
    Отправляет пользователю список проектов для обновления.

    """
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, "Выбери проект, который хочешь изменить", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects )
    else:
        no_projects(message)

def update_project_step_2(message, projects):
    """
    Обрабатывает выбор проекта для обновления.
    Отправляет пользователю список атрибутов проекта для выбора.
    
    """
    project_name = message.text
    if message.text == cancel_button:
        cancel(message)
        return
    if project_name not in projects:
        bot.send_message(message.chat.id, "Что-то пошло не так!) Выбери проект, который хочешь изменить еще раз:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects )
        return
    bot.send_message(message.chat.id, "Выбери, что требуется изменить в проекте", reply_markup=gen_markup(attributes_of_projects.keys()))
    bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)

def update_project_step_3(message, project_name):
    """
    Обрабатывает выбор атрибута проекта для обновления.
    Отправляет пользователю сообщение с просьбой ввести новое значение атрибута.
    
    """
    attribute = message.text
    reply_markup = None
    if message.text == cancel_button:
        cancel(message)
        return
    if attribute not in attributes_of_projects.keys():
        bot.send_message(message.chat.id, "Кажется, ты ошибся, попробуй еще раз!)", reply_markup=gen_markup(attributes_of_projects.keys()))
        bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)
        return
    elif attribute == "Статус":
        rows = manager.get_statuses()
        reply_markup=gen_markup([x[0] for x in rows])
    bot.send_message(message.chat.id, attributes_of_projects[attribute][0], reply_markup = reply_markup)
    bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attributes_of_projects[attribute][1])

def update_project_step_4(message, project_name, attribute):
    """
    Обрабатывает ввод нового значения атрибута проекта.
    Обновляет атрибут проекта в базе данных.
    
    """
    update_info = message.text
    if attribute== "status_id":
        rows = manager.get_statuses()
        if update_info in [x[0] for x in rows]:
            update_info = manager.get_status_id(update_info)
        elif update_info == cancel_button:
            cancel(message)
        else:
            bot.send_message(message.chat.id, "Был выбран неверный статус, попробуй еще раз!)", reply_markup=gen_markup([x[0] for x in rows]))
            bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attribute)
            return
    user_id = message.from_user.id
    data = (update_info, project_name, user_id)
    manager.update_projects(attribute, data)
    bot.send_message(message.chat.id, "Готово! Обновления внесены!)")
# Обработчик для изменения фото проекта
@bot.message_handler(commands=['change_photo'])
def change_photo_handler(message):
    """
    Обработчик команды /change_photo.
    Отправляет пользователю список проектов для изменения фото.
    
    """
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, 'Выбери проект для которого нужно изменить фото', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, request_new_photo, projects=projects)
    else:
        no_projects(message)

def request_new_photo(message, projects):
    """
    Обрабатывает выбор проекта и запрашивает новое фото.
    
    """
    project_name = message.text
    if message.text == cancel_button:
        cancel(message)
        return
        
    if project_name not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй еще раз!) Выбери проект для которого нужно изменить фото', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, request_new_photo, projects=projects)
    else:
        bot.send_message(message.chat.id, 'Пришли новое фото для проекта:')
        bot.register_next_step_handler(message, handle_new_photo, project_name=project_name)

def handle_new_photo(message, project_name):
    """
    Обрабатывает полученное новое фото и сохраняет его.
    
    """
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, 'Это не фото. Пожалуйста, пришли фото.')
        bot.register_next_step_handler(message, handle_new_photo, project_name=project_name)
        return
    
    file_id = message.photo[-1].file_id
    
    # Сохраняем фото локально
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    photo_path = f"photos/{project_name}.jpg"
    
    # Создаем папку photos если её нет
    if not os.path.exists("photos"):
        os.makedirs("photos")
        
    with open(photo_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    
    # Сохраняем путь к фото в БД
    user_id = message.from_user.id
    data = (photo_path, project_name, user_id)
    manager.update_projects("photo", data)
    bot.send_message(message.chat.id, f'Фото проекта {project_name} успешно изменено')


# Хэндлер для получения описания проекта
@bot.message_handler(commands=['description'])
def description_handler(message):
    """
    Обработчик команды /description.
    Отправляет пользователю список проектов для добавления описания.
    
    """
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, 'Выбери проект для которого нужно добавить описание', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, description_project, projects=projects)
    else:
        no_projects(message)

def description_project(message, projects):
    """
    Обрабатывает выбор проекта для добавления описания.
    Запрашивает у пользователя описание проекта.

    """
    project_name = message.text
    if message.text == cancel_button:
        cancel(message)
        return
        
    if project_name not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй еще раз!) Выбери проект для которого нужно добавить описание', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, description_project, projects=projects)
    else:
        bot.send_message(message.chat.id, 'Введите описание проекта:')
        bot.register_next_step_handler(message, set_description, project_name=project_name)

def set_description(message, project_name):
    """
    Обрабатывает ввод описания проекта.
    Обновляет описание проекта в базе данных.
    
    """
    description = message.text
    user_id = message.from_user.id
    if message.text == cancel_button:
        cancel(message)
        return
        
    data = (description, project_name, user_id)
    manager.update_projects("description", data)
    bot.send_message(message.chat.id, f'Описание добавлено проекту {project_name}')


# Хэндлер для получения фото проекта
@bot.message_handler(content_types=['photo'])
def photo_handler(message):
    """
    Обработчик получения фото от пользователя.
    Отправляет пользователю список проектов для добавления фото.
    
    """
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, 'Выбери проект для которого нужно добавить фото', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, photo_project, message.photo[-1].file_id, projects=projects)
    else:
        no_projects(message)

def photo_project(message, file_id, projects):
    """
    Обрабатывает выбор проекта для добавления фото.
    Сохраняет фото локально и путь к нему в базе данных.
    
    """
    project_name = message.text
    if message.text == cancel_button:
        cancel(message)
        return
        
    if project_name not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй еще раз!) Выбери проект для которого нужно добавить фото', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, photo_project, file_id, projects=projects)
    else:
        # Сохраняем фото локально
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        photo_path = f"photos/{project_name}.jpg"
        
        # Создаем папку photos если её нет
        if not os.path.exists("photos"):
            os.makedirs("photos")
            
        with open(photo_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # Сохраняем путь к фото в БД
        user_id = message.from_user.id
        data = (photo_path, project_name, user_id)
        manager.update_projects("photo", data)
        bot.send_message(message.chat.id, f'Фото добавлено проекту {project_name}')


# Обработчик текстовых сообщений
@bot.message_handler(content_types = telebot.util.content_type_media)
def text_handler(message):
    """
    Обработчик текстовых сообщений.
    Отправляет пользователю информацию о проекте, если введено имя проекта.
    
    """
    user_id = message.from_user.id
    projects =[ x[2] for x in manager.get_projects(user_id)]
    project = message.text
    if project in projects:
        info_project(message, user_id, project)
        return
    bot.reply_to(message, "Тебе нужна помощь?")
    info(message)

    
if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    bot.infinity_polling()
