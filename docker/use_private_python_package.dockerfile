# syntax=docker/dockerfile:1.4
FROM python:3.12

# Set the working directory in the container
WORKDIR /app

RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

COPY poetry.lock pyproject.toml /app/

RUN git config --global url."ssh://git@github.com/".insteadOf https://github.com/

# github/actions/use_ssh_key.yaml 참고
RUN --mount=type=secret,id=ssh_key \
    poetry config virtualenvs.create false && \
    GIT_SSH_COMMAND="ssh -i /run/secrets/ssh_key -o StrictHostKeyChecking=no" \
    poetry install --no-root --only main --no-interaction --no-ansi

COPY app /app/app

EXPOSE 8000

CMD [ "python", "app/main.py" ]