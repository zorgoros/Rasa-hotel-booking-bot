# Hotel Booking Chatbot

This project is a hotel booking chatbot built using the Rasa framework, Python, and SQLite. The chatbot enables users to book hotel rooms interactively, making the process simple and efficient. It demonstrates the integration of a conversational interface with a backend system for handling bookings and database management.

---

## Objective

The chatbot is designed to:
- Collect booking details from users, such as name, check-in and check-out dates, and the number of guests.
- Provide feedback on successful booking with a confirmation message.
- Handle simple queries, including greetings, information collecting, and booking resets.

---

## Features

### Booking Functionality:
- Users can book a room by providing the required details (e.g., name, dates, number of guests).
- Confirmation messages are displayed after a successful booking.

### Custom Forms:
- The bot uses forms to gather mandatory booking information interactively.

### Database Integration:
- The bot interacts with a SQLite database to manage hotels, rooms, guests, and bookings.
- **Database Setup (Auto-Generated)**: The SQLite database `hotel_management.db` will be created automatically on first run. No additional configuration is needed.

### Fallback and Reset:
- Handles fallback scenarios when input is unclear.
- Users can reset the conversation to start fresh.

### Web Interface:
- A basic web UI is provided (`index.html`) for interaction with the bot.

---

## Project Structure

```
HOTEL_BOOKING_CHATBOT/
├── actions/                   # Custom action scripts for Rasa
│   ├── __init__.py            # Python module initialization file
│   └── actions.py             # Custom actions for the chatbot
├── data/                      # Data files for Rasa training
│   ├── nlu.yml                # NLU training data
│   ├── rules.yml              # Rules for conversation flows
│   └── stories.yml            # Stories for chatbot conversation paths
├── database/                  # SQLite database files and related scripts
│   └── hotel_bookings.db      # SQLite database will be created if not exist
├── Docs/                      # Documentation for the project
│   ├── LICENSE                # Project license
│   └── Rasa_Commands_Detailed.pdf  # Detailed Rasa command guide
├── models/                    # Folder to store trained Rasa models
├── .gitignore                 # Git ignore file
├── cleanup_models.sh          # Script to clean up old Rasa models
├── config.yml                 # Rasa configuration file
├── credentials.yml            # Credentials for third-party services (e.g., messaging platforms)
├── domain.yml                 # Domain configuration for intents, slots, and entities
├── endpoints.yml              # Endpoints configuration for Rasa actions
├── index.html                 # Web interface file
└── requirements.txt           # Python dependencies for the project
```

---

## Setup Instructions

### 1. Prerequisites
- Python 3.9 or later
- Rasa (install via `pip install rasa`)
- SQLite (pre-installed with Python)
- Flask (for the optional API)

### 2. Installation

#### Option 1: Using the provided files
1. Download the files or copy them to your system.
2. Navigate to the directory containing the project files.

#### Option 2: Cloning from my GitHub repository
1. Clone the repository:
   ```bash
   git clone https://github.com/zorgoros/Rasa-hotel-booking-bot.git
   cd Rasa-hotel-booking-bot
   ```

### 3. Project Initialization
1. Set up the virtual environment:
   ```bash
   # MacOS/Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Train the Rasa model:
   ```bash
   rasa train
   ```

4. The SQLite database `hotel_management.db` will be created automatically on first run if it does not exist.

---

## How to Use

### Run the Chatbot
1. Start the Rasa action server (for custom actions):
   ```bash
   rasa run actions
   ```

2. Start the Rasa server:
   ```bash
   rasa run --cors "*" --debug
   ```

3. Open the chatbot in Rasa shell:
   ```bash
   rasa shell
   ```

4. (Optional) Run the web UI:
   - Open `index.html` in your browser.
   - Ensure the Rasa REST endpoint is running:
     ```bash
     rasa run --cors "*" --enable-api
     ```

### Interact with the Bot
#### Example Queries:
- “I want to book a room.”
- “My name is John Doe.”
- “Check-in on January 25th, check-out on January 30th.”
- “2 guests”

#### Commands:
- `reset`: Restart the conversation.
- `help`: Show usage instructions.

---

## Testing

1. Verify database entries:
   ```bash
   sqlite3 hotel_management.db
   SELECT * FROM bookings;
   ```

2. Use the web UI for a user-friendly interface or Rasa shell for testing responses.

---

## Requirements

### Functional Requirements:
- Collect and validate user inputs (name, dates, guests).

### Non-functional Requirements:
- Usable within Rasa shell or web interface.
- Modular design for scalability and future enhancements.

---

## Future Enhancements

1. **Add optional features like payment processing and meal preferences**:
   - Implement a payment gateway API such as Stripe or PayPal.
   - Allow users to specify preferences like "with breakfast".

2. **Expand the NLU model**:
   - Train the bot with diverse datasets.
   - Include synonyms and variations of common terms.

3. **Implement multilingual support**:
   - Use translation APIs like Google Translate.

4. **Add dynamic room availability updates**:
   - Integrate real-time APIs for availability checks.

5. **Enhance user experience**:
   - Add typing indicators and booking summaries.

6. **Introduce booking cancellation/modification**:
   - Allow users to update/cancel bookings.

7. **Build analytics tools**:
   - Track user interactions and booking trends.

---

## License

Licensed under the [Apache License 2.0](LICENSE).