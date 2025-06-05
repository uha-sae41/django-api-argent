FROM python:latest

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt
RUN pip install gunicorn
RUN pip install whitenoise

WORKDIR /app/apiproject

EXPOSE 8000

CMD ["gunicorn", "apiproject.wsgi:application", "--bind", "0.0.0.0:8000"]