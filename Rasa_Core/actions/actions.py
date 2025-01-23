# Importing necessary modules and classes for type hinting, date parsing, database operations, and Rasa SDK functionality
from typing import Any, Text, Dict, List, Optional
from datetime import datetime  # For working with dates and times
import dateparser  # For parsing user-provided date text into a standard format
import sqlite3  # For database operations (e.g., storing booking data)
import re  # For regular expression operations (e.g., text processing)
from rasa_sdk import Action, Tracker  # For defining custom actions and tracking conversation state
from rasa_sdk.executor import CollectingDispatcher  # For dispatching responses to the user
from rasa_sdk.events import SlotSet, EventType, FollowupAction, AllSlotsReset   # For managing events and slots in the conversation
import logging # For logging messages to the console

logger = logging.getLogger(__name__) # For logging messages to the console


# ------------------------------------------------------------------------------
# 1) A helper function to parse user-provided date text to a standard format
#    (e.g., "dd-mm-yyyy"). Using dateparser for flexible date input.
# ------------------------------------------------------------------------------
def parse_date_basic(date_text: str) -> Optional[datetime]:
    """
    A simple dateparser-based function that returns a Python datetime
    if parse is successful, or None if it fails.
    This does NOT do any fancy future-year logic. We rely on other logic
    to interpret it relative to check-in, etc.
    """
    if not date_text:
        return None
    parsed = dateparser.parse(date_text)
    return parsed

def parse_checkout_relative(checkout_text: str, dt_checkin: datetime) -> Optional[datetime]:
    """
    Parses the user’s checkout text. If the text includes a year explicitly,
    dateparser will handle that. If not, dateparser might place it in the
    current year. If that ends up before dt_checkin, we try bumping to the
    same year as check-in or the next year. 
    """
    if not checkout_text:
        return None

    # parse with dateparser ignoring year (if user didn't specify)
    dt_checkout = dateparser.parse(checkout_text)
    if not dt_checkout:
        return None  # unparseable

    # If the parsed checkout is already >= checkin, great – no changes
    if dt_checkout >= dt_checkin:
        return dt_checkout

    # If dt_checkout < dt_checkin, maybe the user omitted the year.
    # We do one or two attempts:
    #  1) set checkout's year to checkin's year
    #  2) if that is still < checkin, increment one more year
    #
    # NOTE: This is a guess. If user typed "Jan 12" but check-in is "Jan 15, 2026",
    # we try "Jan 12, 2026" => that is still < checkin => so we do "Jan 12, 2027".

    # Step 1: create a dt with the same month/day, but the checkin's year
    dt_checkout_same_year = dt_checkout.replace(year=dt_checkin.year)
    if dt_checkout_same_year >= dt_checkin:
        return dt_checkout_same_year

    # Step 2: If it is still < checkin, add 1 year
    dt_checkout_next_year = dt_checkout_same_year.replace(year=dt_checkin.year + 1)
    # Now we assume that is the final guess
    return dt_checkout_next_year

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
        1. Retrieve slots from the form: name, checkin_date, checkout_date, number_of_guests
        2. Validate each:
            - name: not empty
            - checkin_date: not in the past
            - checkout_date: strictly after checkin_date
            - number_of_guests: integer, 1..20
        3. If invalid, re-prompt the user by clearing the relevant slot(s).
        4. If valid, store row in DB, return booking_id -> slot, so "utter_confirm_booking" can show it.
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
        # Parse checkin
        dt_checkin = parse_date_basic(checkin_slot)
        if not dt_checkin:
            dispatcher.utter_message(
                text="Please provide a valid check-in date (e.g. '25 January 2025')."
            )
            return [
                SlotSet("checkin_date", None),
                FollowupAction("hotel_booking_form")
            ]

        # If checkin in the past, re-prompt
        now = datetime.now()
        if dt_checkin < now:
            dispatcher.utter_message(
                text=(
                    "Your check-in date is in the past!\n"
                    "If you meant next year, please specify the year.\n"
                    "Please re-enter your check-in date."
                )
            )
            return [
                SlotSet("checkin_date", None),
                FollowupAction("hotel_booking_form")
            ]

        # Parse checkout in a "relative" manner
        dt_checkout = parse_checkout_relative(checkout_slot, dt_checkin)
        if not dt_checkout:
            dispatcher.utter_message(
                text="Please provide a valid check-out date (e.g. '26 January 2025')."
            )
            return [
                SlotSet("checkout_date", None),
                FollowupAction("hotel_booking_form")
            ]

        # Now if the final dt_checkout is STILL <= dt_checkin, fail
        if dt_checkout <= dt_checkin:
            dispatcher.utter_message(
                text=(
                    "Check-out date must be after your check-in date.\n"
                    "If you meant a date next year, please specify that explicitly.\n"
                    "Please re-enter your check-out date."
                )
            )
            return [
                SlotSet("checkout_date", None),
                FollowupAction("hotel_booking_form")
            ]

        # At this point, we have validated checkin in the future, checkout > checkin
        # Format them as dd-mm-yyyy strings
        parsed_checkin_str = dt_checkin.strftime("%d-%m-%Y")
        parsed_checkout_str = dt_checkout.strftime("%d-%m-%Y")

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
        conn = sqlite3.connect("database/hotel_bookings.db")
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
            (
                formatted_name,
                parsed_checkin_str,  # dd-mm-yyyy
                parsed_checkout_str, # dd-mm-yyyy
                guests_count
            ),
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
            SlotSet("checkin_date", parsed_checkin_str),
            SlotSet("checkout_date", parsed_checkout_str),
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
        logger.info("ActionResetSlots triggered")
        # Option 1: Clear all slots:
        return [AllSlotsReset()]
        # Option 2: If prefer to do something else after resetting,
        # we can also return [AllSlotsReset(), FollowupAction("action_listen")] 
        # or a new greeting, etc.

class ActionDefaultFallback(Action):
    """Called when the user’s input is not recognized by Rasa’s NLU"""

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