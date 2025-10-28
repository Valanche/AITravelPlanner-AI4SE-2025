# AI Travel Planner: Functional Implementation Design

This document details the implementation design for each functional requirement of the AI Travel Planner, based on the simplified monolithic architecture using Flask and Supabase.

## 1. User Management (FR4)

This is the foundation for saving and managing plans. Authentication logic will be handled by the Flask backend to keep the client-side simple.

-   **Technology:** Flask, `supabase-py`.
-   **Assumption:** Email confirmation has been disabled in the Supabase project settings for simpler registration.
-   **Implementation:**
    1.  **Login/Register Forms:** The `login.html` and `register.html` templates will contain standard HTML forms that `POST` directly to the `/login` and `/register` Flask routes.
    2.  **Backend Registration (`/register` route):**
        -   The route will accept `POST` requests.
        -   It will extract the email and password from the form data.
        -   It will call `supabase.auth.sign_up()` with the user's credentials.
        -   It will show a success message and redirect to the login page.
    3.  **Backend Login (`/login` route):**
        -   The route will accept `POST` requests.
        -   It will extract the email and password from the form data.
        -   It will call `supabase.auth.sign_in_with_password()`.
        -   On successful login, it will store the user's information in the Flask `session` and redirect to the `/my-plans` page.
        -   If there is an error (e.g., wrong password), it will display an error message on the login page.
    4.  **Session Management:** The Flask `session` will be used to track the authenticated user. The `login_required` decorator will protect routes that require a user to be logged in.
    5.  **Logout:** The `/logout` route will simply clear the Flask `session` and redirect to the home page.
## 2. User Input (FR1)

This covers the main user interaction on the home page.

-   **Technology:** HTML forms, JavaScript, Web Speech API.
-   **Implementation:**
    1.  **UI:** The home page (`/`) will feature a large `<textarea>` inside an HTML `<form>`.
    2.  **Text Input:** Users can type their query directly into the textarea.
    3.  **Voice Input:**
        -   A "Start Recording" button will be placed next to the textarea.
        -   A JavaScript event listener on this button will trigger the `Web Speech API` (`SpeechRecognition` object).
        -   The API will capture the user's speech and convert it to text.
        -   The resulting text will be automatically placed into the textarea.
    4.  **Submission:** The form will be submitted via a `POST` request to the `/plan` route.

## 3. AI-Powered Itinerary Generation & Display (FR2)

This is the core feature, now enhanced with a map display.

-   **Technology:** Flask, Google Gemini API, Amap JS API 2.0, Amap Web Service API (for Geocoding).
-   **Implementation:**
    1.  **Flask Route (`/plan`):**
        -   **Prompt Engineering:** The route will instruct the Gemini API to return a `JSON` object. The JSON must contain a structured itinerary with an array of locations, each having a name and a full street address. Example: `{"days": [{"day": 1, "locations": [{"name": "Shinjuku Gyoen", "address": "11 Naitomachi, Shinjuku City, Tokyo"}]}]}`.
        -   **API Call (Gemini):** The backend calls the Gemini API and parses the resulting JSON string.
        -   **Geocoding:** The backend iterates through the locations from the AI's response. For each location, it makes a server-side request to the Amap Geocoding API to convert the address into latitude and longitude coordinates. This enriched data (including coordinates) is then passed to the template.
    2.  **Display Page (`plan_display.html`):
        -   **Note:** An Amap API Key will be required.
        -   **Layout:** The page will use a two-column layout. The left column will be a scrollable list for the itinerary details. The right, larger column will contain the map `div`.
        -   **Amap API Setup:** The Amap JS API script will be included in the HTML `<head>`.
        -   **Client-Side JavaScript:** A script on this page will:
            1.  Read the enriched JSON data passed from Flask.
            2.  Initialize an `AMap.Map` instance in the map container.
            3.  Iterate through the itinerary data and dynamically generate the HTML for the itinerary list in the left sidebar.
            4.  Loop through the locations again, creating an `AMap.Marker` for each and adding it to the map.
            5.  Use the `AMap.Driving` service to calculate and draw the travel route between the points for each day on the map.

## 4. Budget Management (FR3)

This will be integrated into the AI generation and plan display.

-   **Technology:** Gemini API, HTML forms, Flask, Supabase.
-   **Implementation:**
    1.  **AI Budget Analysis:** The prompt sent to the Gemini API will explicitly ask for a budget analysis, which will be part of the generated plan display.
    2.  **Expense Tracking (Simplified):**
        -   On the `plan_display.html` page, a simple form (`<form>`) will allow users to add an expense with a description and amount.
        -   This form will `POST` to a new route, `/plan/<plan_id>/add_expense`.
        -   This Flask route will save the expense to a new `Expenses` table in Supabase, linked to the `plan_id`.
        -   The plan display page will be re-rendered, now showing a list of expenses and the updated remaining budget.
        -   **Note:** Voice input for expense tracking will be considered a future enhancement to maintain simplicity in this initial design.

## 5. Data Synchronization (FR5)

This requirement is met implicitly by the architecture.

-   **Technology:** Supabase.
-   **Implementation:**
    -   Since all user-specific data (user info, saved plans, expenses) is stored in the cloud-hosted Supabase database, the data is naturally synchronized. When a user logs in from any device, the Flask application will fetch the data from Supabase, ensuring a consistent view.
