"""Tests for ticket creation, validation, and the priority engine (F1).

Owner: Engineer A. Run from the repository root:

    python -m unittest discover -s tests -v
"""

import unittest

from campusflow import tickets
from campusflow.errors import ValidationError


class PriorityEngineTests(unittest.TestCase):
    """The four priority rules, in the order the brief specifies."""

    def test_high_urgency_with_ten_or_more_users_is_critical(self):
        # Rule 1. Also the brief's headline acceptance example.
        self.assertEqual(tickets.calculate_priority("high", 12), "critical")

    def test_high_urgency_at_the_boundary_of_ten_is_critical(self):
        # Rule 1 boundary: 10 is "10 or more".
        self.assertEqual(tickets.calculate_priority("high", 10), "critical")

    def test_high_urgency_with_few_users_is_high(self):
        # Rule 2 via urgency alone, users below the rule 1 threshold.
        self.assertEqual(tickets.calculate_priority("high", 2), "high")

    def test_low_urgency_with_ten_users_is_high(self):
        # Rule 2 via user count alone. Guards against a copy-paste error that
        # would make rule 2 test urgency again instead of users.
        self.assertEqual(tickets.calculate_priority("low", 10), "high")

    def test_low_urgency_with_four_users_is_medium(self):
        # Rule 3.
        self.assertEqual(tickets.calculate_priority("low", 4), "medium")

    def test_low_urgency_with_one_user_is_low(self):
        # Rule 4, the fall-through.
        self.assertEqual(tickets.calculate_priority("low", 1), "low")

    def test_urgency_is_case_insensitive(self):
        self.assertEqual(tickets.calculate_priority("HIGH", 12), "critical")


class AffectedUsersValidationTests(unittest.TestCase):
    """affected_users must be a positive whole number."""

    def test_zero_is_rejected(self):
        with self.assertRaises(ValidationError):
            tickets.validate_affected_users(0)

    def test_negative_is_rejected(self):
        with self.assertRaises(ValidationError):
            tickets.validate_affected_users(-3)

    def test_decimal_is_rejected(self):
        with self.assertRaises(ValidationError):
            tickets.validate_affected_users(2.5)

    def test_text_is_rejected(self):
        with self.assertRaises(ValidationError):
            tickets.validate_affected_users("many")

    def test_decimal_written_as_text_is_rejected(self):
        with self.assertRaises(ValidationError):
            tickets.validate_affected_users("2.5")

    def test_numeric_string_is_accepted_and_trimmed(self):
        # The CLI hands us strings, so digits-as-text must be accepted.
        self.assertEqual(tickets.validate_affected_users(" 15 "), 15)

    def test_bool_is_rejected(self):
        # isinstance(True, int) is True in Python, so this needs an explicit
        # guard - otherwise True would silently mean 1 user.
        with self.assertRaises(ValidationError):
            tickets.validate_affected_users(True)


class FieldValidationTests(unittest.TestCase):
    """Title, category and urgency rules."""

    def test_blank_title_is_rejected(self):
        with self.assertRaises(ValidationError):
            tickets.validate_title("   ")

    def test_empty_title_is_rejected(self):
        with self.assertRaises(ValidationError):
            tickets.validate_title("")

    def test_title_is_trimmed(self):
        self.assertEqual(tickets.validate_title("  Wi-Fi down  "), "Wi-Fi down")

    def test_invalid_urgency_is_rejected(self):
        with self.assertRaises(ValidationError):
            tickets.normalize_urgency("urgent")

    def test_urgency_is_normalised_to_lowercase(self):
        self.assertEqual(tickets.normalize_urgency(" Medium "), "medium")

    def test_category_is_case_insensitive(self):
        self.assertEqual(tickets.normalize_category(" network "), "Network")

    def test_unknown_category_is_rejected(self):
        with self.assertRaises(ValidationError):
            tickets.normalize_category("Printing")


class CreateTicketTests(unittest.TestCase):
    """create_ticket wiring: ids, defaults, and all-or-nothing storage."""

    def test_create_fills_every_field(self):
        ticket_list = []
        ticket = tickets.create_ticket(
            ticket_list, "Campus Wi-Fi is down", "Network", "high", 15
        )
        self.assertEqual(ticket["id"], "T001")
        self.assertEqual(ticket["title"], "Campus Wi-Fi is down")
        self.assertEqual(ticket["category"], "Network")
        self.assertEqual(ticket["urgency"], "high")
        self.assertEqual(ticket["affected_users"], 15)
        self.assertEqual(ticket["priority"], "critical")
        self.assertEqual(ticket["status"], "open")
        self.assertIsNone(ticket["assigned_to"])
        self.assertEqual(ticket_list, [ticket])

    def test_ids_are_sequential(self):
        ticket_list = []
        for _ in range(3):
            tickets.create_ticket(ticket_list, "Something broke", "Other", "low", 1)
        self.assertEqual([t["id"] for t in ticket_list], ["T001", "T002", "T003"])

    def test_ids_continue_past_the_highest_existing(self):
        existing = [{"id": "T001"}, {"id": "T007"}]
        self.assertEqual(tickets.next_ticket_id(existing), "T008")

    def test_unrecognised_ids_are_ignored_not_fatal(self):
        existing = [{"id": "T001"}, {"id": "legacy-9"}, {"id": "T002"}]
        self.assertEqual(tickets.next_ticket_id(existing), "T003")

    def test_next_id_on_an_empty_collection_is_t001(self):
        self.assertEqual(tickets.next_ticket_id([]), "T001")

    def test_rejected_ticket_is_not_stored(self):
        # A validation failure mid-create must not leave a partial record.
        ticket_list = []
        with self.assertRaises(ValidationError):
            tickets.create_ticket(ticket_list, "Printer jam", "Hardware", "low", 0)
        self.assertEqual(ticket_list, [])

    def test_rejected_ticket_does_not_burn_an_id(self):
        ticket_list = []
        with self.assertRaises(ValidationError):
            tickets.create_ticket(ticket_list, "Printer jam", "Hardware", "low", 0)
        ticket = tickets.create_ticket(ticket_list, "Printer jam", "Hardware", "low", 1)
        self.assertEqual(ticket["id"], "T001")


if __name__ == "__main__":
    unittest.main()
