sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
  libncurses5-dev libncursesw5-dev xz-utils tk-dev \
  libffi-dev liblzma-dev git
curl https://pyenv.run | bash

if [[ -f ~/.bashrc && -d "$HOME/.pyenv/bin" && -z "$(grep '# set pyenv' ~/.bashrc)" ]]; then
  {
    echo '# set pyenv'
    echo 'export PYENV_ROOT="$HOME/.pyenv"'
    echo 'export PATH="$PYENV_ROOT/bin:$PATH"'
    echo 'eval "$(pyenv init - bash)"'
  } >> ~/.bashrc
fi

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - bash)"
pyenv install 3.13.8
pyenv global 3.13.8