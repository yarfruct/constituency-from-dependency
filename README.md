# Модуль построения дерева синтаксических единиц русскоязычного предложения на основе дерева синтаксических связей
Copyright © 2023 Anatoliy Poletaev, Ilya Paramonov, Elena Boychuk. All rights reserved.

## Установка и запуск
Системные требования: Python 3.10, UNIX-подобная ОС.
1. Создайте виртуальное окружение и установите зависимости
   ```bash
   python3 -m virtualenv venv
   source venv/bin/activate
   python3 -m pip install -r requirements.txt
   ```
2. Для проведения анализа в интерактивном режиме запустите `main.py`.
3. Для расчёта метрик качества на наборе предложений из 100 предложений из OpenCorpora (файл sentences/opencorpora-sample.json) с использованием всех доступных анализаторов синтаксических связей запустите `test_algoritm.py`.

## Лицензия
Модуль распространяется по свободной лицензии GNU GPLv3