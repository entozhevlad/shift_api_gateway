# Base Devcontainers

Репозиторий с рабочим окружением, необходимым для работы над ШИФТ 2024.

От приложения ожидается использование [8080 порта](./.devcontainer/docker-compose.yml#L12) внутри контейнера.
На локальном хосте приложение будет доступно на [28080 порту](./.devcontainer/docker-compose.yml#L12).

## Внесение изменений внутри Devcontainer

Перед использованием devcontainer-ов необходимо установить:
- Для Windows: рекомендуется использовать [WSL](https://virgo.ftc.ru/pages/viewpage.action?pageId=1084887269)
- Docker Desktop для MacOS/Windows или просто docker для Linux
- Visual Studio Code c плагинами
  - `ms-vscode-remote.remote-containers`
  - `ms-azuretools.vscode-docker`
- Git
- OpenSSH с SSH Agent
- OpenSSL
- [Шрифты для powerlevel10k](https://github.com/romkatv/powerlevel10k?tab=readme-ov-file#fonts)

Если какие-то из дальнейших пунктов у вас уже выполнены, смело пропускайте шаг.

После установки необходимого ПО:
- Сгенерируйте SSH ключ и добавьте его в свой MosHub аккаунт
- Настройте `user.name` и `user.email` для Git
- [Настройте SSH Agent c вашим ключом](https://code.visualstudio.com/remote/advancedcontainers/sharing-git-credentials)
- Склонируйте текущий репозиторий в локальную директорию, если еще не сделали этого

Для настройки kubernetes (потребуется во второй половине курса):
- Сгенерируйте ключи для kubectl и положите их в папку `~/.kube`
- Настройте kubectl на использование ключей из папки `~/.kube`

После настройки локального окружения:
- Откройте директорию в Visual Studio Code
- Нажмите `Ctrl+Shift+P` или `Cmd+Shift+P`
- Введите `Dev Containers:`
- Выберите из предложенных вариантов пункт `Dev Containers: Rebuild and Reopen in Container`
- Дождитесь открытия проекта внутри окружения в Devcontainer


### Окружение доступное после старта Devcontainer
- Преднастроенная конфигурация для запуска линтера

  Доступ из командной панели:
  - Нажмите `Ctrl+Shift+P` или `Cmd+Shift+P`
  - Выберете `Tasks: Run Task`
  - Выберете `Flake8` или `ISort`

- Преднастроенная конфигурация для запуска тестов

  Смотрите по кнопке `Testing` в левой панели Visual Studio Code.

- Преднастроенная конфигурация для запуска сервиса

  Смотрите по кнопке `Run and Debug` в левой панели Visual Studio Code.
- `Zsh` с Oh-My-Zsh в качестве shell по-умолчанию
- базовые консольные инструменты вроде `git`, `curl` и прочие
- `kubectl` и `helm` для работы с kubernetes
- `python` версии 3.12 с `poetry` для управления зависимостями и виртуальным окружением
- настроен доступ до `docker` на хосте
