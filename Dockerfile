FROM python:3.9-alpine

WORKDIR /tmp
RUN pip install pipenv
COPY ./Pipfile* ./
RUN pipenv install --system --deploy

RUN apk update && apk upgrade && apk add curl
RUN curl -LO https://github.com/kovetskiy/mark/releases/download/6.5.1/mark_6.5.1_Linux_x86_64.tar.gz && \
    tar -xvzf mark_6.5.1_Linux_x86_64.tar.gz && \
    chmod +x mark && \
    mv mark /usr/local/bin/mark

WORKDIR /action
COPY ./src .

ENTRYPOINT [ "python", "/action/main.py" ]