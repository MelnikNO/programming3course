# Лабораторная работа 1. Реализация удаленного импорта
## Задание
Разместите представленный ниже код локально на компьютере и реализуйте механизм удаленного импорта. 
Продемонстрируйте в виде скринкаста или в текстовом отчете с несколькими скриншотами работу удаленного импорта.

По шагам: 
1. Создайте файл ```myremotemodule.py```, который будет импортироваться, разместите его в каталоге, который далее будет "корнем сервера" (допустим, создайте его в папке ```rootserver```).
2. Разместите в нём следующий код:  
```python
def myfoo():
    author = "" # Здесь обознаться своё имя (авторство модуля)
    print(f"{author}'s module is imported")
```

3. Создайте файл Python с содержимым функций ```url_hook``` и классов ```URLLoader```, ```URLFinder``` из текста конспекта лекции со всеми необходимыми библиотеками (допустим, ```activation_script.py```).
4. Далее, чтобы продемонстрировать работу импорта из удаленного каталога, мы должны запустить сервер http так, чтобы наш желаемый для импорта модуль "лежал" на сервере (например, в корневой директории сервера). Откроем каталог ```rootserver``` с файлом ```myremotemodule.py``` и запустим там сервер:
```sh
python3 -m http.server
```
5. После этого мы запускаем файл, в котором содержится код, размещенный выше (обязательно добавление в ```sys.path_hooks```). 
```sh
python3 -i activation_script.py
```
6. Теперь, если мы попытаемся импортировать файл ```myremotemodule.py```, в котором размещена наша функция ```myfoo``` будет выведен ```ModuleNotFoundError: No module named 'myremotemodule'```, потому что такого модуля пока у нас нет (транслятор про него ничего не знает).
7. Однако, как только мы выполним код:
```python
sys.path.append("http://localhost:8000")
``` 
добавив путь, где располагается модуль, в ```sys.path```, будет срабатывать наш "кастомный" ```URLLoader```.
В ```path_hooks``` будет содержатся наша функция ```url_hook```. 

8. Протестируйте работу удаленного импорта, используя в качестве источника модуля другие "хостинги" (например, repl.it, github pages, beget, sprinthost). 
9. Переписать содержимое функции url_hook, класса URLLoader с помощью модуля ```requests``` (см. комменты).
10. Задание со звездочкой (\*): реализовать обработку исключения в ситуации, когда хост (где лежит модуль) недоступен.
11. Задание про-уровня (\*\*\*): реализовать загрузку **пакета**, разобравшись с аргументами функции spec_from_loader и внутренним устройством импорта пакетов. 

---

## Решение

- Создали файл ```myremotemodule.py``` и разместили код: [myremotemodule.py](https://github.com/MelnikNO/programming3course/blob/main/1sem/LR1/myremotemodule.py)

- Создали файл ```activation_script.py``` с содержимым функций ```url_hook``` и классов ```URLLoader```, ```URLFinder```: [activation_script.py](https://github.com/MelnikNO/programming3course/blob/main/1sem/LR1/activation_script.py)

- Демонастрация удаленной работы импорта (локально)

<img width="1037" height="130" alt="image" src="https://github.com/user-attachments/assets/9c8ef2ca-8741-4167-b6f3-37129059252c" />

<img width="1477" height="361" alt="image" src="https://github.com/user-attachments/assets/5deac449-4680-4836-adf5-b13eaed91103" />

- Демонастрация удаленной работы импорта (хостинг)

Использован Replit. [Борд один для запуска импорта](https://replit.com/@yrmelnikno/programming3curs?v=1) и [брод 2 для показа удаленного импорта](https://replit.com/@yrmelnikno/progra3curssecond?v=1)

Для запуска создали файл main.py и написали программу:

```
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

port = int(os.environ.get("PORT", 5000))
httpd = HTTPServer(('0.0.0.0', port), Handler)
print(f"Server running on port {port}")
httpd.serve_forever()
```

<img width="851" height="534" alt="image" src="https://github.com/user-attachments/assets/ad7af0fd-7e2c-4f4c-bf30-659cd626ab11" />


<img width="1198" height="462" alt="image_2025-09-09_15-22-49" src="https://github.com/user-attachments/assets/34987f0a-abc9-4bf0-8387-82423a710d70" />

- Переписать содержимое функции url_hook, класса URLLoader с помощью модуля ```requests``` (см. комменты).

Задание со звездочкой (\*): реализовать обработку исключения в ситуации, когда хост (где лежит модуль) недоступен.

Задание про-уровня (\*\*\*): реализовать загрузку **пакета**, разобравшись с аргументами функции spec_from_loader и внутренним устройством импорта пакетов. 

Оно представлено в файле [activation_scriptrequest.py](https://github.com/MelnikNO/programming3course/blob/main/1sem/LR1/activation_scriptrequest.py)


9. Переписать содержимое функции url_hook, класса URLLoader с помощью модуля ```requests```

```
response = requests.get(some_str)
data = response.text
```

```
response = requests.get(module.__spec__.origin)
source = response.text
```

10. Задание со звездочкой (\*): реализовать обработку исключения в ситуации, когда хост (где лежит модуль) недоступен

```
    try:
        response = requests.get(some_str)
        data = response.text
        filenames = re.findall("[a-zA-Z_][a-zA-Z0-9_]*.py", data)
        modnames = {name[:-3] for name in filenames}
        return URLFinder(some_str, modnames)

    except requests.exceptions.RequestException as e:
        print(f"Ошибка: Не удалось подключиться к {some_str}")
        print(f"Причина: {e}")
        raise ImportError(f"Хост недоступен: {some_str}")
```

```
        try:
            response = requests.get(module.__spec__.origin)
            source = response.text
            code = compile(source, module.__spec__.origin, mode="exec")
            exec(code, module.__dict__)

        except requests.exceptions.RequestException as e:
            raise ImportError(f"Не удалось загрузить модуль {module.__spec__.origin}: {e}")
```

11. Задание про-уровня (\*\*\*): реализовать загрузку **пакета**, разобравшись с аргументами функции spec_from_loader и внутренним устройством импорта пакетов

```
        directories = re.findall(r'<a href="([a-zA-Z_][a-zA-Z0-9_]*)/">', data)
        for directory in directories:
            try:
                init_url = f"{some_str.rstrip('/')}/{directory}/__init__.py"
                init_response = requests.get(init_url)
                if init_response.status_code == 200:
                    modnames.add(directory)
            except:
                continue
```

```
            package_check_url = f"{self.url}/{name}/"
            try:
                response = requests.get(package_check_url)
                if response.status_code == 200:
                    origin = f"{self.url}/{name}/__init__.py"
                    loader = URLLoader()
                    return spec_from_loader(name, loader, origin=origin, is_package=True)
            except:
                pass
```

* Демонастрация удаленной работы импорта (хостинг)

Аналогично пункту 8

<img width="963" height="652" alt="image_2025-09-09_23-44-48" src="https://github.com/user-attachments/assets/315e7081-62aa-450e-afe5-ffcd2629e685" />


---

### Комментарий

Задание не вызвала особых сложностей, за исключением пункта 11 и демонстрация на других хостингах (replit).
Replit не хотел делать ```import package```, как это было в локлаьной демонстрации, и это получилось реализовать только после пункта 11.
А в пункте 11 надо было достаточно подумать, чтобы реализовать это.
