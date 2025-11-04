## Overview

A agent/bot to monitor the crypto market, send alerts when a token is oversold (oportunity) and open/close orders in a perpetuals exchange via commands on telegram bot

Project in development phase...

## How to Run Locally

1.  **Create and activate a virtual environment:**
    ```sh
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install the dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```sh
    python src/main.py
    ```

## How to Run with Docker

1.  **Build the Docker image:**
    ```sh
    docker build -t trading-bot .
    ```

2.  **Run the container in the foreground:**
    This will run the container and stream logs to your terminal. Press `Ctrl+C` to stop. The `--rm` flag automatically removes the container when it exits.
    ```sh
    docker run --rm trading-bot
    ```

3.  **Run the container in the background (detached mode):**
    To run the application continuously, you can start it in detached mode.
    ```sh
    docker run -d --name trading-bot-instance trading-bot
    ```

4.  **View logs for the background container:**
    ```sh
    docker logs -f trading-bot-instance
    ```

5.  **Stop the background container:**
    ```sh
    docker stop trading-bot-instance
    ```
