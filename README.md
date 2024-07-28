# Face Verification Service

API-Gateway сервис проекта

## Установка

1. Клонируйте репозиторий:
    ```sh
    git clone <repository_url>
    cd <repository_directory>
    ```

2. Откройте проект в VS Code с Dev Containers:
    - Установите [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) расширение для VS Code.
    - Откройте командную палитру (Ctrl+Shift+P) и выберите "Remote-Containers: Open Folder in Container...".

3. Poetry автоматически установит все зависимости после создания контейнера.

## Использование

Запустите главный файл проекта:
```sh
uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload



## Code Linting

Проект использует `wemake-python-styleguide` в качестве линтера. Чтобы запустить линтер, следуйте следующим шагам:

1. Установить зависимости проекта:

    ```bash
    poetry install
    ```

2. Зарустите линтер для папки app:

    ```bash
    poetry run flake8 --jobs=1 src/app
    ```

Можно редактировать конфигурационный файл линтера `.flake8` в корне проекта.
