# Importing necessary modules and classes for type hinting, date parsing, database operations, and Rasa SDK functionality
from typing import Any, Text, Dict, List, Optional
from datetime import datetime  # For working with dates and times
import dateparser  # For parsing user-provided date text into a standard format
import sqlite3  # For database operations (e.g., storing booking data)
import re  # For regular expression operations (e.g., text processing)
from rasa_sdk import Action, Tracker  # For defining custom actions and tracking conversation state
from rasa_sdk.executor import CollectingDispatcher  # For dispatching responses to the user
from rasa_sdk.events import SlotSet, EventType, FollowupAction, AllSlotsReset   # For managing events and slots in the conversation

# ------------------------------------------------------------------------------
# 1) A helper function to parse user-provided date text to a standard format
#    (e.g., "dd-mm-yyyy"). Using dateparser for flexible date input.
# ------------------------------------------------------------------------------
def parse_date(date_text: str) -> Optional[str]:
    """
    Attempts to parse a user text date (e.g., "25th Jan" or "tomorrow")
    into a standard dd-mm-yyyy format. Returns None if parsing fails.
    """
    if not date_text:
        return None

    parsed = dateparser.parse(date_text)
    if parsed:
        return parsed.strftime("%d-%m-%Y")
    return None


# ------------------------------------------------------------------------------
# 2) ActionValidateInputs
#    This action runs after the form is completed to validate or correct data.
#    Then it saves the data in a (dummy) database.
# ------------------------------------------------------------------------------
class ActionValidateInputs(Action):
    def name(self) -> Text:
        return "action_validate_inputs"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[EventType]:
        """
        1. Get slot values from the tracker.
        2. Optionally validate or parse them (e.g. date format, number of guests).
        3. Save the data to DB (dummy SQLite example here).
        4. If invalid, reset slots or re-prompt. Otherwise confirm to user.
        """

        # ----------------------------------------------------------------------
        # Retrieve slots
        # ----------------------------------------------------------------------
        name_slot = tracker.get_slot("name") or ""
        checkin_slot = tracker.get_slot("checkin_date") or ""
        checkout_slot = tracker.get_slot("checkout_date") or ""
        guests_slot = tracker.get_slot("number_of_guests") or ""

        # ----------------------------------------------------------------------
        # Validate / parse name (simple capitalization)
        # ----------------------------------------------------------------------
        # stricter name rules, will be implemented here.
        if not name_slot.strip():
            dispatcher.utter_message(
                text="Please provide a valid name."
            )
            # Clearing the slot to force the bot to re-ask
            return [SlotSet("name", None), FollowupAction("hotel_booking_form")]

        formatted_name = " ".join(word.capitalize() for word in name_slot.split())

        # ----------------------------------------------------------------------
        # Validate / parse check-in & check-out dates
        # ----------------------------------------------------------------------
        parsed_checkin = parse_date(checkin_slot)
        parsed_checkout = parse_date(checkout_slot)
        if not parsed_checkin or not parsed_checkout:
            dispatcher.utter_message(
                text="Please provide valid check-in and check-out dates."
            )
            return [
                SlotSet("checkin_date", None),
                SlotSet("checkout_date", None),
                FollowupAction("hotel_booking_form"),
            ]

        #  ensure checkin is not in the past
        now = datetime.now()
        if dt_checkin < now:
            dispatcher.utter_message(text="Check-in date cannot be in the past.")
            return [
                SlotSet("checkin_date", None),
                FollowupAction("hotel_booking_form"),
            ]  
        # Convert to Python datetime for comparison if needed
        dt_checkin = datetime.strptime(parsed_checkin, "%d-%m-%Y")
        dt_checkout = datetime.strptime(parsed_checkout, "%d-%m-%Y")
        if dt_checkin >= dt_checkout:
            dispatcher.utter_message(
                text="Check-out date must be after check-in date."
            )
            return [
                SlotSet("checkin_date", None),
                SlotSet("checkout_date", None),
                FollowupAction("hotel_booking_form"),
            ]

        

        # ----------------------------------------------------------------------
        # Validate / parse number_of_guests
        # ----------------------------------------------------------------------
        # e.g. try to extract an integer from guests_slot
        import re
        found_digits = re.findall(r"\d+", guests_slot)
        if not found_digits:
            dispatcher.utter_message(
                text="Please provide a valid number of guests (e.g. '3')."
            )
            return [
                SlotSet("number_of_guests", None),
                FollowupAction("hotel_booking_form"),
            ]

        # We take the first digit we find as the guest number
        guests_count = int(found_digits[0])
        if guests_count < 1 or guests_count > 20:
            dispatcher.utter_message(
                text="Please provide a valid number of guests between 1 and 20."
            )
            return [
                SlotSet("number_of_guests", None),
                FollowupAction("hotel_booking_form"),
            ]

        # ----------------------------------------------------------------------
        # 3) Check availability in a dummy database & "save" the booking
        # ----------------------------------------------------------------------
        #  using local SQLite.can be Adjusted for real database.

        # 3a. Connect to DB (or create if not exist)
        #     In production, will connect to a remote DB or use SQLAlchemy.
        conn = sqlite3.connect("hotel_bookings.db")
        cursor = conn.cursor()

        # 3b. Create a table if not exists
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                checkin_date TEXT,
                checkout_date TEXT,
                guests INTEGER
            )
            """
        )

        # 3c. Here normally check if there's an available room.
        #     We'll assume there's always availability for simplicity.
        #     If not available, we'll do something like:
        # dispatcher.utter_message(text="No rooms available for those dates!")
        # return []

        # 3d. Insert the booking row
        cursor.execute(
            """
            INSERT INTO bookings (name, checkin_date, checkout_date, guests)
            VALUES (?, ?, ?, ?)
            """,
            (formatted_name, parsed_checkin, parsed_checkout, guests_count),
        )
        conn.commit()

        # we retrieve the newly inserted booking ID or other info
        booking_id = cursor.lastrowid

        # Close the DB connection
        conn.close()

        # Convert booking_id to string for the slot
        str_booking_id = str(booking_id)

        # ----------------------------------------------------------------------
        # 4) Return a final "summary" to user or rely on utter_confirm_booking
        #    The rule has "action_validate_inputs" -> "utter_confirm_booking",
        #    which uses the domain's template. We'll just set the final, validated
        #    slots here for the template.
        # ----------------------------------------------------------------------
        # Example: "Your booking for Mikel from 25-01-2023 to 26-01-2023 for 3 guests is confirmed!"
        # The domain's "utter_confirm_booking" uses {name}, {checkin_date}, etc.

        # Store final validated values in the slots so "utter_confirm_booking" sees them
        return [
            SlotSet("name", formatted_name),
            SlotSet("checkin_date", parsed_checkin),
            SlotSet("checkout_date", parsed_checkout),
            SlotSet("number_of_guests", str(guests_count)),
            SlotSet("booking_id", str_booking_id),
        ]
    
class ActionResetSlots(Action):
    """Clears all slots when user says 'reset'."""

    def name(self) -> Text:
        return "action_reset_slots"

    async def run(
        self, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain: Dict[Text, Any]
    ) -> List[EventType]:
        dispatcher.utter_message(text="Resetting all your data. Let's start fresh!")
        # Option 1: Clear all slots:
        return [AllSlotsReset()]
        # Option 2: If prefer to do something else after resetting,
        # we can also return [AllSlotsReset(), FollowupAction("action_listen")] 
        # or a new greeting, etc.

class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[EventType]:
        dispatcher.utter_message(
            text="I’m sorry, I didn’t understand that. Type ‘help’ for instructions or ‘reset’ to start over."
        )
        return []