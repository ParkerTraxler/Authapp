FROM ubuntu

RUN apt update && apt install -y \
python3-pip python3-venv pkg-config libmariadb-dev build-essential


WORKDIR /app

COPY requirements.txt ./

RUN python3 -m venv /venv
RUN /venv/bin/pip install --upgrade pip
RUN /venv/bin/pip install -r requirements.txt


ENV PATH="/venv/bin:$PATH"

COPY . .

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
