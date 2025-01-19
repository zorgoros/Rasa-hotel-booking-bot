from rasa_sdk import Action
from rasa_sdk.events import SlotSet
from datetime import datetime, timedelta
import dateparser

class ActionValidateInputs(Action):
    def name(self) -> str:
        return "action_validate_inputs"

    def validate_name(self, name: str) -> str:
        """Validate and format the name."""
        if not name:
            return None
        return " ".join(word.capitalize() for word in name.split())

    def parse_date(self, date_text: str) -> str:
        """Parse a date from natural language to a standard format (DD-MM-YYYY)."""
        try:
            parsed_date = dateparser.parse(date_text)
            if parsed_date:
                return parsed_date.strftime("%d-%m-%Y")
        except Exception:
            return None
        return None

    def validate_dates(self, checkin_date: str, checkout_date: str) -> tuple:
        """Validate and format check-in and check-out dates."""
        formatted_checkin = self.parse_date(checkin_date)
        formatted_checkout = self.parse_date(checkout_date)

        if not formatted_checkin or not formatted_checkout:
            return None, None

        checkin_dt = datetime.strptime(formatted_checkin, "%d-%m-%Y")
        checkout_dt = datetime.strptime(formatted_checkout, "%d-%m-%Y")

        if checkin_dt >= checkout_dt:
            return None, None  # Invalid if check-out is not after check-in

        return formatted_checkin, formatted_checkout

    def validate_guests(self, guests_text: str) -> int:
        """Validate and convert guest number from text to integer."""
        try:
            # Extract number from text
            guests_text = guests_text.lower().replace("one", "1").replace("two", "2").replace("three", "3")
            for word in guests_text.split():
                if word.isdigit():
                    guests = int(word)
                    if 1 <= guests <= 20:  # Enforce maximum guests
                        return guests
        except Exception:
            return None
        return None

    def run(self, dispatcher, tracker, domain):
        # Retrieve slots
        name = tracker.get_slot("name")
        checkin_date = tracker.get_slot("checkin_date")
        checkout_date = tracker.get_slot("checkout_date")
        number_of_guests = tracker.get_slot("number_of_guests")

        # Validate name
        formatted_name = self.validate_name(name)
        if not formatted_name:
            dispatcher.utter_message(text="Please provide a valid name.")
            return [SlotSet("name", None)]

        # Validate dates
        formatted_checkin, formatted_checkout = self.validate_dates(checkin_date, checkout_date)
        if not formatted_checkin or not formatted_checkout:
            dispatcher.utter_message(
                text="Please provide valid check-in and check-out dates. Check-out must be after check-in."
            )
            return [SlotSet("checkin_date", None), SlotSet("checkout_date", None)]

        # Validate number of guests
        validated_guests = self.validate_guests(number_of_guests)
        if not validated_guests:
            dispatcher.utter_message(
                text="Please provide a valid number of guests (1-20)."
            )
            return [SlotSet("number_of_guests", None)]

        # Confirm valid data
        dispatcher.utter_message(
            text=(
                f"Thank you! Your booking for {formatted_name} from {formatted_checkin} "
                f"to {formatted_checkout} for {validated_guests} guests is confirmed."
            )
        )
        return [
            SlotSet("name", formatted_name),
            SlotSet("checkin_date", formatted_checkin),
            SlotSet("checkout_date", formatted_checkout),
            SlotSet("number_of_guests", validated_guests),
        ]