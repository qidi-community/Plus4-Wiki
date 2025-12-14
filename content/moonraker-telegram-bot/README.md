# Moonraker Telegram Bot

Alternative remote control solution for printer.
Support video recording, upload gcode (include archived) and more.

[moonraker-telegram-bot GitHub](https://github.com/nlef/moonraker-telegram-bot)

## Installation changes for +4

> [!INFO]
> In this doc will use git version from [Commit 96a7fb9](https://github.com/nlef/moonraker-telegram-bot/commit/96a7fb91d2f27153f4424032c1e758074dabb9aa).


1. Complete step 1 from [original install instructions](https://github.com/nlef/moonraker-telegram-bot/wiki/Installation)
2. Need fresh python. Using from [ShakeTune For Qidi](https://github.com/stew675/ShakeTune_For_Qidi)
    ```shell
    cd ~
    wget https://github.com/stew675/ShakeTune_For_Qidi/releases/download/v1.0.0/python-3-12-3.tgz
    tar xvzf python-3-12-3.tgz
    ```
3. Clone moonraker-telegram-bot
    ```shell
    cd ~
    git clone https://github.com/nlef/moonraker-telegram-bot.git
    ```
    > [!INFO]
    > install.sh from moonraker-telegram-bot written to run from path ~/moonraker-telegram-bot. If you use specific version from releases - keep it in mind.
4. Edit ~/moonraker-telegram-bot/scripts/install.sh:
    1) Find row:
        ```shell
        virtualenv -p /usr/bin/python3 --system-site-packages "${MOONRAKER_BOT_ENV}
        ```
    2) Replace with:
        ```shell
        ~/python-3.12.3/bin/python3.12 -m venv "${MOONRAKER_BOT_ENV}"
        ```
5. Edit Armbian repo (stock repo outdated):
    ```shell
    sudo cp /etc/apt/sources.list /etc/apt/sources.list.back
    echo "deb http://archive.debian.org/debian buster main contrib non-free
    deb http://archive.debian.org/debian buster-updates main contrib non-free
    deb http://archive.debian.org/debian buster-backports main contrib non-free
    deb http://archive.debian.org/debian-security buster/updates main" | sudo tee /etc/apt/sources.list
    sudo apt update
    ```
6. Prepare service drop-in for lower cpu priority (will not interfere with the klipper when recording video):
    ```shell
    sudo mkdir -p /etc/systemd/system/moonraker-telegram-bot.service.d/
    echo -e "[Service]\nCPUWeight=10" | sudo tee /etc/systemd/system/moonraker-telegram-bot.service.d/override.conf
    ```
7. Install:
    ```shell
    cd moonraker-telegram-bot
    ./scripts/install.sh
    ```
8. Complete [original install instructions](https://github.com/nlef/moonraker-telegram-bot/wiki/Installation) from step 3