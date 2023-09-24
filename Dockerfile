FROM openjdk:11

WORKDIR /app
COPY templates /app/templates
COPY requirements.txt app.py db.py constants.py init_db.py run.sh .
RUN chmod +x run.sh
RUN apt update && apt install -y python3-pip
RUN pip3 install -r requirements.txt

ENTRYPOINT ["bash"]
CMD ["run.sh"]