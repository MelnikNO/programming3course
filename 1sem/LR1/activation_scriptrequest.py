# В URLFinder и будет срабатывать функция url_hook, которая и будет перехватывать ситуацию, в которой загрузка модуля
# должна идти по URL-адресу

from importlib.abc import PathEntryFinder
from importlib.util import spec_from_loader
import re
import sys
# from urllib.request import urlopen
import requests



def url_hook(some_str):
    if not some_str.startswith(("http", "https")):
        raise ImportError
    # with urlopen(some_str) as page:  # requests.get()
    #     data = page.read().decode("utf-8")
    try:
        response = requests.get(some_str)
        data = response.text
        filenames = re.findall("[a-zA-Z_][a-zA-Z0-9_]*.py", data)
        modnames = {name[:-3] for name in filenames}
        directories = re.findall(r'<a href="([a-zA-Z_][a-zA-Z0-9_]*)/">', data)
        for directory in directories:
            try:
                init_url = f"{some_str.rstrip('/')}/{directory}/__init__.py"
                init_response = requests.get(init_url)
                if init_response.status_code == 200:
                    modnames.add(directory)
            except:
                continue
        return URLFinder(some_str, modnames)

    except requests.exceptions.RequestException as e:
        print(f"Ошибка: Не удалось подключиться к {some_str}")
        print(f"Причина: {e}")
        raise ImportError(f"Хост недоступен: {some_str}")


class URLLoader:
    def create_module(self, target):
        return None

    def exec_module(self, module):
        # with urlopen(module.__spec__.origin) as page:
        #     source = page.read()
        try:
            response = requests.get(module.__spec__.origin)
            source = response.text
            code = compile(source, module.__spec__.origin, mode="exec")
            exec(code, module.__dict__)

        except requests.exceptions.RequestException as e:
            raise ImportError(f"Не удалось загрузить модуль {module.__spec__.origin}: {e}")


class URLFinder(PathEntryFinder):
    def __init__(self, url, available):
        self.url = url.rstrip('/')
        self.available = available

    def find_spec(self, name, target=None):
        if name in self.available:
            package_check_url = f"{self.url}/{name}/"
            try:
                response = requests.get(package_check_url)
                if response.status_code == 200:
                    origin = f"{self.url}/{name}/__init__.py"
                    loader = URLLoader()
                    return spec_from_loader(name, loader, origin=origin, is_package=True)
            except:
                pass

            origin = f"{self.url}/{name}.py"
            loader = URLLoader()
            return spec_from_loader(name, loader, origin=origin, is_package=False)

        return None


sys.path_hooks.append(url_hook)
print("Доступные path_hooks:", [h.__name__ if hasattr(h, '__name__') else str(h) for h in sys.path_hooks])