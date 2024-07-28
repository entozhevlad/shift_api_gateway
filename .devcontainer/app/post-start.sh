#!/bin/sh
apt list --installed

# Конфигурация темы oh-my-zsh
if [ ! -d "~/.oh-my-zsh/custom/themes/powerlevel10k" ] ; then
    git clone --depth 1 https://github.com/romkatv/powerlevel10k.git ~/.oh-my-zsh/custom/themes/powerlevel10k
fi

# Конфигурация kubernetes
if [ "$SYNC_LOCALHOST_KUBECONFIG" = "true" ] && [ -d "/usr/local/share/kube-localhost" ]; then
    mkdir -p $HOME/.kube
    cp -r /usr/local/share/kube-localhost/* $HOME/.kube
    chown -R $(id -u) $HOME/.kube
    sed -i -e "s|/Users/[a-z]\+\(/.kube/.*\)|$HOME\1|gm" $HOME/.kube/config
fi

# Конфигурация poetry
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true
mkdir -p ~/.oh-my-zsh/plugins/poetry
poetry completions zsh > ~/.oh-my-zsh/plugins/poetry/_poetry

poetry install --all-extras --compile --no-root
