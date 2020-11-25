FROM python:3.6.4
RUN apt-get update


RUN pip install --upgrade pip
RUN pip install spacy==2.3.2
RUN python -m spacy download en_core_web_sm


WORKDIR /ticket-prioritz
COPY . /ticket-prioritz


RUN pip install -r requirements.txt


EXPOSE 5000

CMD ["python", "./app.py"]
