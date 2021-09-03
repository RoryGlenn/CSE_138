FROM python:3

WORKDIR /usr/src/app

RUN pip install flask 

COPY . .

CMD [ "python3", "-m", "flask", "run", "--host=0.0.0.0", "-p", "8085" ]

EXPOSE 8085

# docker build -t cse138_assignment1 .
# docker run -p 8085:8085 cse138_assignment1

# show all the running docker executables
#   docker ps