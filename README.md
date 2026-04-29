Запуск проекта 

uvicorn main:app --reload

зависимости установить из requirements.txt

рекомендуется создать .env по примеру

SECRET_KEY=любойсекретныйключ
DATABASE_URL=postgresql://postgres:пароль@localhost:5432/todo_db

Запуск тестов

Тесты расположены в папке tests/.

1. Запустить тесты и узнать покрытие:

coverage run -m pytest tests/

2. Полуычить отчет о покрытии:

coverage report -m

3. Нагрузочное тестирование:

locust -f tests/locust.py (обязательно запустить проект)

указать количество пользователей и запустить тестирование в http://localhost:8089/

4. Отчет в html:

coverage html

уже создан в htmlcov/index.html
