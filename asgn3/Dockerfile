FROM python:3

WORKDIR /usr/src/app

RUN pip install flask requests

COPY . .

CMD [ "python3", "app.py" ]

EXPOSE 8085
