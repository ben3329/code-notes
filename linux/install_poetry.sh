curl -sSL https://install.python-poetry.org | python -

if [[ -f ~/.bashrc && -d "$HOME/.local/bin" && -z "$(grep '# set poetry' ~/.bashrc)" ]]; then
  {
    echo '# set poetry'
    echo 'export PATH="$HOME/.local/bin:$PATH"'
  } >> ~/.bashrc
fi

export PATH="$HOME/.local/bin:$PATH"
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true