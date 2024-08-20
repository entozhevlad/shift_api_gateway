# Настройка локального окружения

Для внесения изменений в репозиторий необходимо настроить работу внутри devcontainer-а.

## MacOS / Windows

- Устновить [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Установить [Visual Studio Code](https://code.visualstudio.com/download)
- [Настроить Visual Studio Code и Docker для использования Devcontainers](https://code.visualstudio.com/docs/devcontainers/containers#_getting-started)
- [Настроить Git и SSH для работы в Devcontainer](https://code.visualstudio.com/remote/advancedcontainers/sharing-git-credentials)
- [Установить шрифт Meslo Nerd Font для CLI в терминале](https://github.com/romkatv/powerlevel10k?tab=readme-ov-file#fonts)
- По необходимости установить и настроить kubectl, внутри контейнера будут использованы настройки с хоста
- Склонировать этот репозиторий на рабочую станцию
- Открыть директорию с репозиторием через Visual Studio Code
- Установить [рекомендуемые плагины](.vscode/extensions.json) Visual Studio Code
- Ввести `Ctrl+Shift+P` или `Cmd+Shift+P` и выбрать `Dev Containers: Rebuild and Reopen in Container`

### Миграции в базу данных
Перед началом работы с миграциями, убедитесь, что все микросервисы подняты через docker-compose в сервисе API-Gateway

Работа с миграциями организована за счёт инструмента alembic.

После поднятия контейнеров есть два пути работы с миграциями.

1. Зайти в консоль отдельного контейнера и выполнитель следующие команды

Чтобы создать миграции выполните следующую команду

- alembic revision --autogenerate -m "Init migration"

Чтобы применить миграции выполните следующую команду

- alembic upgrade head

2. Выполните команды через командную строку введя следующие команды docker exec с параметрами

- docker exec -it shift-api-gateway-transactions_service-1 alembic revision --autogenerate -m "Initial migration"
- docker exec -it shift-api-gateway-transactions_service-1 alembic upgrade head
- docker exec -it shift-api-gateway-auth_service-1 alembic revision --autogenerate -m "Initial migration"
- docker exec -it shift-api-gateway-auth_service-1 alembic upgrade head