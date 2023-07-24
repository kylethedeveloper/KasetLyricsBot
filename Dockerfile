FROM python:alpine

# Environment variables
ENV TG_SESSION_NAME='kasetlyricsbot' \
    TG_API_ID='' \
    TG_API_HASH='' \
    TG_BOT_TOKEN=''

# Copy required files
COPY entrypoint.sh /entrypoint.sh
COPY *.py /app/
COPY requirements.txt /app/requirements.txt

# Set working directory
WORKDIR /app

# Run necessary commands
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN chmod +x /entrypoint.sh

# Run the bot
ENTRYPOINT ["/entrypoint.sh"]
