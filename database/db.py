import json
import os

# Базовый путь к папке data
# На Amvera это будет /data, локально - data
DATA_DIR = "/data" if "AMVERA" in os.environ else "data"

# Путь к конкретному файлу
DATA_FILE_PATH = os.path.join(DATA_DIR, "data.json")
SETTINGS_FILE_PATH = os.path.join(DATA_DIR, "settings.json")


# Запись и чтение в JSON
def save_to_file(file_name, dictionary):
    try:
        with open(file_name, 'w', encoding='utf8') as f:
            json_data = json.dumps(dictionary)
            f.write(json_data)
    except Exception as e:
        print("Ошибка, при сохранении файла:", e)

def read_from_file(file_name, dictionary):
    try:
        with open(file_name, 'r', encoding='utf8') as f:
            json_input = f.read()
            info = json.loads(json_input)
            print(dictionary)
            for key, item in info.items():
                dictionary[int(key)] = item
            print(dictionary)
    except Exception as e:
        print("Произошла ошибка, при считывании файла:", e)