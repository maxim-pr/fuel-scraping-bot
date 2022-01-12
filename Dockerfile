FROM python:3.9

WORKDIR /opt/fuel_parser_bot
COPY bot/ bot/
COPY parsers/ parsers/

COPY requirements.txt .
RUN pip install -r requirements.txt

CMD ["python", "-m", "bot"]