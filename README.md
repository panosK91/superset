# Apache Superset Navbar Color Customization

This repository fork includes custom modifications to Apache Superset that add a new feature: a button in the Superset UI that changes the navigation bar's background color to `#455a64` and persists this preference in the database.

## Overview

This customization demonstrates both frontend and backend modifications:

- **Frontend:**
  - A new button labeled **"Change Navbar Color"** is added to the Superset menu.
  - Clicking the button immediately changes the navbar's background color by updating the DOM.
  - The new color preference is sent to a backend API endpoint for persistence.
- **Backend:**
  - A new SQLAlchemy model (`UserPreference`) and database table (`user_preferences`) are added to store the custom navbar color.
  - A new API endpoint (`/api/v1/readpostgres`) is implemented in `api.py` (located at `superset/superset/views/api.py`) to accept POST requests with the navbar color.
  - The endpoint validates the input, saves the preference to the database, and returns a JSON confirmation.

## Frontend Changes

The main frontend changes are in `superset-frontend/src/features/home/Menu.tsx`:

- **New Functionality:**

  - Added the function `changeNavbarColor` that:
    - Changes the navbar's background color by targeting the element with `id="main-menu"`.
    - Sends a POST request to the backend endpoint (`/api/v1/readpostgres`) with the new color.
  - A new button is rendered below the existing right-hand menu. Clicking this button triggers the color change function.

- **User Experience:**

  - The color change is applied immediately for instant feedback.
  - The persisted preference ensures that the change can be restored or logged for future enhancements.

## Backend Changes

The backend changes are in `superset/superset/views/api.py`:

- **New Model:**

  - A new SQLAlchemy model, `UserPreference`, is defined to store the navbar color preference. The table includes:
    - `id`: Primary key.
    - `navbar_color`: A string field (7 characters) for the hex color code.
    - `created_at`: A timestamp of when the record was created.

- **New API Endpoint:**

  - A new method `save_navbar_color` is added to the existing `Api` class.
  - The endpoint is available at `/api/v1/readpostgres` and accepts POST requests with a JSON payload (e.g., `{"navbarColor": "#455a64"}`).
  - It validates the payload, persists the new color into the `user_preferences` table, and returns a success message.

- **Error Handling & Logging:**

  - The endpoint uses existing Superset decorators (`@handle_api_exception`, `@has_access_api`, etc.) to ensure proper error handling, logging, and security.

## Database Migration

To integrate the new table into your Superset database, a migration must be created and applied:

1. **Generate a Migration:**
   ```bash
   superset db migrate -m "Add user_preferences table for navbar color preference"
   ```
2. **Apply the Migration:**
   ```bash
   superset db upgrade
   ```

This ensures the `user_preferences` table is created with the correct schema.


## Approach Summary

- **Minimal Changes:**  Only the necessary files (`Menu.tsx` and `api.py`) were modified to add the new feature.

- **Immediate UI Feedback:**  The frontend directly manipulates the DOM for instant visual feedback, while the backend persists the change.

- **Seamless Integration:**  The new API endpoint leverages Superset’s existing backend architecture and decorators for security and error handling.

- **Scalable & Extensible:**  With the color preference now stored in the database, future enhancements can include restoring user preferences on login or providing more customizable UI options.