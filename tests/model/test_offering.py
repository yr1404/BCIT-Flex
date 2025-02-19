"""Tests for the offering model."""
import datetime

import pytest
from sqlalchemy.exc import DataError
from sqlalchemy.orm import Session

from bcitflex.model import Meeting, Offering
from tests import dbtest


class TestOffering:
    """Test properties of the Offering class."""

    def test_init(self, new_offering: Offering) -> None:
        """Test the constructor."""
        assert new_offering.crn == "67890"
        assert new_offering.instructor == "John Doe"
        assert new_offering.price == 123.45
        assert new_offering.duration == "1 week"
        assert new_offering.status == "Open"
        assert new_offering.course_id == 1
        assert new_offering.available is True

    def test_next_meeting_id(self, new_offering: Offering) -> None:
        """Test that the next meeting id is correct."""
        assert new_offering.next_meeting_id() == 1

    def test_next_meeting_id_with_meetings(
        self, new_offering: Offering, new_meeting: Meeting
    ) -> None:
        """Test that the next meeting id is correct."""
        new_meeting.offering = new_offering
        assert new_offering.next_meeting_id() == 2

    def test_next_meeting_id_raises_error(
        self, new_offering: Offering, new_meeting: Meeting
    ) -> None:
        """Test that the next meeting id raises an error."""
        new_offering.meetings.append(new_meeting)
        with pytest.raises(ValueError):
            new_offering.next_meeting_id()


@dbtest
class TestOfferingDB:
    """Test the Offering class with a database session."""

    def test_add_offering(self, new_offering: Offering, session: Session) -> None:
        """Test adding an offering to the db."""
        session.add(new_offering)
        session.commit()
        assert session.get(Offering, "67890") == new_offering
        assert session.get(Offering, "67890").course.course_id == 1

    def test_update_offering(self, session: Session) -> None:
        """Test updating an offering in the db."""
        offering = session.get(Offering, "12345")
        offering.instructor = "Jane Doe"
        session.commit()
        assert session.get(Offering, "12345").instructor == "Jane Doe"

    def test_invalid_crn(self, offering: Offering, session: Session) -> None:
        """Test that adding an offering with an invalid value raises an exception."""
        offering.crn = "abcdef"
        with pytest.raises(DataError):
            try:
                session.add(offering)
                session.commit()
            except DataError as e:
                session.rollback()
                raise e


@dbtest
class TestPrimaryMeeting:
    """Test the primary meeting and attributes of the offering class."""

    def test_get_primary_meeting(self, session: Session) -> None:
        """Test offering from database includes primary meeting."""
        offering = session.get(Offering, "12345")
        assert offering.primary_meeting.meeting_id == 1

    def test_simple_properties(self, session: Session) -> None:
        """Test access attributes of primary meeting through offering."""
        offering = session.get(Offering, "12345")
        assert offering.start_time == datetime.time(18)
        assert offering.end_time == datetime.time(21)
        assert offering.campus == "Online"

    def test_aggregate_properties(self, session: Session) -> None:
        """Test properties that query against all related meetings."""

        # add new meeting to db
        new_meeting = Meeting(
            meeting_id=2,
            crn="12345",
            days=["Thu", "Fri"],
            start_date=datetime.date(2023, 8, 1),
            end_date=datetime.date(2023, 12, 1),
        )
        session.add(new_meeting)
        session.commit()

        # get offering
        offering = session.get(Offering, "12345")
        assert offering.start_date == datetime.date(2023, 8, 1)
        assert offering.end_date == datetime.date(2023, 12, 1)
        assert offering.days == ["Wed", "Thu", "Fri"]
