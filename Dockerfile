FROM python:3.9

# Install system dependencies
RUN apt-get update && apt-get install -y \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-latex-recommended \
    texlive-pictures \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*



RUN mkdir -p /app/uploads && chmod -R 777 /app/uploads



WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY .env .
COPY . .




CMD ["python3", "run.py"]
