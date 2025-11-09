# AI Travel Planner

This project is an AI-based travel planner application built with Flask and Supabase.

## Quick Start

### Local Development

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up environment variables:**
    -   Copy `.env.example` to a new file named `.env`.
    -   Fill in your Supabase URL/Key and Baidu AI credentials (APP_ID, API_KEY, SECRET_KEY) in the `.env` file.
    -   In your Supabase project settings, disable the "Confirm email" option under Authentication -> Providers -> Email.

3.  **Run the application:**
    ```bash
    flask run
    ```

### Docker

1.  **Create and configure .env file**

    If you don't have a .env file, copy it from .env.example:

    ```bash
    cp .env.example .env
    ```

    Then, edit the .env file to fill in your API keys.

2.  **Build the Docker image**

    In the project root directory, run the following command to build the Docker image:

    ```bash
    docker build -t ai-travel-planner .
    ```

3.  **Run the Docker container**

    After the build is complete, use the following command to run your application:

    ```bash
    docker run -p 5000:5000 --env-file .env ai-travel-planner
    ```

    This will:
    *   `-p 5000:5000`: Map port 5000 on your local machine to port 5000 in the container.
    *   `--env-file .env`: Load all variables from the .env file into the container as environment variables.
    *   `ai-travel-planner`: The name you specified for the image during the build.

    You can now access your application by visiting http://localhost:5000 in your browser.

## Documentation

For detailed project documentation, including requirements, design, and functional specifications, please see the files in the `/docs` directory.