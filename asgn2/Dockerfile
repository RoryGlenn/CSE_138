FROM python:3

WORKDIR /usr/src/app

RUN pip install flask requests

COPY . .

CMD [ "python3", "-m", "flask", "run", "--host=0.0.0.0", "-p", "8085" ]

EXPOSE 8085