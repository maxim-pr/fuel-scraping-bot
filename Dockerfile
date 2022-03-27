FROM python:3.9

WORKDIR /opt/fuel_scraping_bot/
COPY bot/ bot/
COPY scrapers/ scrapers/

COPY requirements.txt .
RUN pip install -r requirements.txt

CMD ["python", "-m", "bot"]