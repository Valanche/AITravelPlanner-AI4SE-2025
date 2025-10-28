# Project: AI Travel Planner

## Project Overview

This is a monolithic web application for AI-powered travel planning. It is built using Python and the Flask framework. User authentication is handled by Supabase, and the core AI travel planning capabilities are intended to be powered by an external service like the Google Gemini API.

The application allows users to register and log in. Once logged in, they can provide a natural language query for a travel plan (including voice input). The backend processes this query, generates a detailed itinerary, and displays it on a page that includes an interactive map (using Amap) showing the locations and route.

## Building and Running

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up environment variables:**
    -   Copy `.env.example` to a new file named `.env`.
    -   Fill in your Supabase URL and Key in the `.env` file.
    -   **Important:** In your Supabase project settings, disable the "Confirm email" option under `Authentication -> Providers -> Email` to allow for simplified registration.

3.  **Run the application:**
    ```bash
    flask run
    ```

## Project Structure

The project is organized as a standard Flask application:

-   `app.py`: The main Flask application file containing all routes and business logic.
-   `requirements.txt`: A list of all Python dependencies for the project.
-   `.env.example`: A template for the required environment variables (Supabase credentials).
-   `/templates`: Contains all HTML templates used for rendering the web pages.
-   `/static`: Contains static assets. Currently, this is planned for JavaScript files (like for voice input) and CSS.
-   `/docs`: Contains all project documentation, including requirements, design documents, and this file.

## Development Conventions

-   **Authentication:** Authentication is handled on the server-side within the Flask application (`app.py`). The backend communicates with Supabase to sign up and sign in users. Client-side code is not involved in the authentication process.
-   **Simplicity:** The current design prioritizes simplicity and rapid implementation over long-term scalability. It uses a monolithic structure and server-side rendering.
