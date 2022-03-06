FROM python:3.9
WORKDIR /chess-server
COPY ./.env.json .
COPY ./server.py .
COPY ./Dockerfile .
COPY ./README.md .
# RUN pip install -r requirements.txt
ENTRYPOINT ["python", "./server.py"]