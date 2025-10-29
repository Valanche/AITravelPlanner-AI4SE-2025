# AI Travel Planner: Simplified Design Document

## 1. Introduction

This document outlines a simplified technical design for the AI Travel Planner, prioritizing rapid development and simplicity over scalability. It is based on the `REQUIREMENTS.md` document and user feedback to use a monolithic architecture and Supabase for authentication.

## 2. System Architecture

A monolithic web application architecture will be used. A single Flask application will handle all aspects of the application, including user interface rendering, business logic, and authentication.

-   **Application:** A single Python Flask application.
-   **Templating:** Server-side rendered HTML using the Jinja2 templating engine.
-   **Authentication & Database:** Supabase will be used for both user authentication and the database (PostgreSQL).
-   **AI Service:** The Flask application will directly call the Google Gemini API to generate travel plans.

![Simplified Architecture Diagram](https://i.imgur.com/9y3CEXt.png)

## 3. Technology Selection

### 3.1 Application Framework

-   **Framework: Flask**
    -   **Reasoning:** Flask is a lightweight and flexible Python web framework, making it ideal for creating a simple, monolithic application quickly. It has a gentle learning curve and does not enforce a rigid structure, which is perfect for this project's goal of simplicity.

### 3.2 Frontend

-   **Templating: Jinja2** (included with Flask)
    -   **Reasoning:** We will use server-side rendering to keep the frontend simple. Jinja2 is the standard templating engine for Flask and is perfectly suited for this.
-   **Styling: Bootstrap**
    -   **Reasoning:** Bootstrap is a popular CSS framework that will allow us to create a clean and responsive user interface with minimal custom CSS.
-   **Speech Recognition: Baidu ASR (Client-side PCM recording)**
    -   **Reasoning:** The application will use Baidu ASR for speech-to-text conversion. Client-side JavaScript will record audio directly in PCM format, which is then sent to the backend for transcription, improving efficiency by avoiding server-side audio format conversion.

### 3.3 Authentication and Database

-   **Service: Supabase**
    -   **Reasoning:** As requested, Supabase will be used for authentication. This offloads the complexity of user management. We will also use Supabase's integrated PostgreSQL database for data storage, which simplifies the architecture by consolidating services. The `supabase-py` library will be used in the Flask application.

### 3.4 AI Engine

-   **Service: Google Gemini API**
    -   **Reasoning:** The core AI functionality will be powered by calls to the Google Gemini API from the Flask backend. This is the most straightforward way to integrate advanced AI capabilities for itinerary generation.

## 4. Preliminary Data Model (in Supabase)

The data will be stored in Supabase's PostgreSQL database. The schema will be kept simple.

-   **TravelPlans**
    -   `plan_id` (Primary Key)
    -   `user_id` (Foreign Key to `auth.users` in Supabase)
    -   `plan_name`
    -   `destination`
    -   `plan_details` (JSONB or Text to store the AI-generated plan)
    -   `created_at`

## 5. Application Flow (Routes)

The Flask application will have the following routes:

-   `/` (Home): The main page where users can input their travel query.
-   `/login`: A page for users to log in via Supabase.
-   `/logout`: Logs the user out.
-   `/plan`: The route that receives the form submission from the home page, calls the Gemini API, and displays the generated plan.
-   `/my-plans`: A page that lists all the saved travel plans for the logged-in user.
