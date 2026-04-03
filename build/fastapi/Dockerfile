FROM tiangolo/uvicorn-gunicorn:python3.11

LABEL maintainer="Sebastian Ramirez <tiangolo@gmail.com>"

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && update-ca-certificates \
 && rm -rf /var/lib/apt/lists/*

#COPY ../../volume/fastapi-app/app /app

#CMD ["python" , "setup_db.py" ]

WORKDIR /app/source

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8686" , "--reload" , "--root-path" , "/" ]
