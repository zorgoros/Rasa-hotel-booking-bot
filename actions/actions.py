from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import dateparser
from datetime import datetime

class ActionProcessInfo(Action):
    def name(self):
        return "action_process_info"

    def run(self, dispatcher, tracker, domain):
        # Extract slot values
        name = tracker.get_slot("name")
        date_input = tracker.get_slot("date")
        guests = tracker.get_slot("number_of_guests")

        # Process and format name
        if name:
            formatted_name = " ".join([word.capitalize() for word in name.strip().split()])
        else:
            dispatcher.utter_message(text="Please provide your name.")
            return [SlotSet("name", None)]

        # Parse and validate date
        parsed_date = dateparser.parse(date_input) if date_input else None
        if parsed_date:
            if parsed_date.date() < datetime.now().date():
                dispatcher.utter_message(text="The date cannot be in the past. Please provide a future date.")
                return [SlotSet("date", None)]
            standardized_date = parsed_date.strftime("%Y-%m-%d")
        else:
            dispatcher.utter_message(
                text="Sorry, I couldn't understand the date. Could you rephrase it in a format like 'next Monday' or '15th January'?"
            )
            return [SlotSet("date", None)]

        # Process and validate guest count
        try:
            guest_count = int(guests) if guests else None
            if guest_count is None or guest_count <= 0:
                dispatcher.utter_message(text="Please provide a valid number of guests.")
                return [SlotSet("number_of_guests", None)]
        except ValueError:
            dispatcher.utter_message(text="The number of guests must be a valid integer.")
            return [SlotSet("number_of_guests", None)]

        # Final confirmation message
        dispatcher.utter_message(
            text=(
                f"Your booking details: Name: {formatted_name}, Date: {standardized_date}, Guests: {guest_count}."
            )
        )
        return [
            SlotSet("name", formatted_name),
            SlotSet("date", standardized_date),
            SlotSet("number_of_guests", str(guest_count))
        ]