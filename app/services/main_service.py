#!/usr/bin/env python
# app/services/main_service.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz), Thomas Crossman (github.com/crossmant1)
Last Modified: 8/2/2026

File Purpose: Main service for the project.
"""

# Standard library imports.
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Third-party imports.
from sqlalchemy import desc

# Local application imports.
from app.extensions import db
from app.models import (
    Attachments,
    Attendees,
    Meetings,
    Minutes,
    Poll,
    PollFreeResponse,
    PollOption,
    PollQuestion,
    PollVoter,
)
from app.utils import sha_hash

LOGGER = logging.getLogger(__name__)


class MainResultStatus(str, Enum):
    """Granular outcomes for main operations."""

    SUCCESS = "success"
    NO_CHANGES = "no_changes"
    MEETING_NOT_FOUND = "meeting_not_found"
    MEETING_INACTIVE = "meeting_inactive"
    ATTENDEE_EXISTS = "attendee_exists"
    INVALID_MEETING_CODE = "invalid_meeting_code"
    ADMIN_ONLY_RESTRICTED = "admin_only_restricted"
    ACCOUNT_NOT_ACTIVATED = "account_not_activated"
    POLL_NOT_FOUND = "poll_not_found"
    POLL_EXPIRED = "poll_expired"
    IMMUTABLE_RESPONSE = "immutable_response"
    IMMUTABLE_RESPONSES = "immutable_responses"
    SELECTED_OPTION_NOT_FOUND = "selected_option_not_found"
    ONE_SELECTED_OPTION_NOT_FOUND = "one_selected_option_not_found"
    QUESTION_NOT_FOUND = "question_not_found"
    PARTIAL_FAILURE = "partial_failure"
    ERROR = "error"


@dataclass(slots=True)
class MainOperationResult:
    """Outcome for a main blueprint operation."""

    statuses: tuple[MainResultStatus, ...]
    changes_made: bool = False
    meeting: Meetings | None = None
    question_text: str | None = None


@dataclass(slots=True)
class HomeViewData:
    """Data required to render the home page."""

    recent_meetings: list[Meetings]
    featured_meeting: Meetings | None
    polls: list[Poll]
    voted_questions: set[int]
    voted_options: set[int]
    user_frq_responses: dict[int, str]


@dataclass(slots=True)
class EventsListViewData:
    """Data required to render the events list page."""

    meetings: list[Meetings]


@dataclass(slots=True)
class EventViewData:
    """Data required to render a single event page."""

    meeting: Meetings
    attendees: list[Attendees]
    minutes: list[Minutes]
    attachments: list[Attachments]


@dataclass(slots=True)
class PollSubmissionResult:
    """Outcome for a bulk poll response submission."""

    statuses: tuple[MainResultStatus, ...]
    question_results: tuple[MainOperationResult, ...] = ()
    changes_made: bool = False
    successes: int = 0
    failures: int = 0


def get_home_view_data(user_id: int | None, is_admin: bool) -> HomeViewData:
    """Return the meetings, polls, and response state needed by the home page."""
    if is_admin:
        recent_meetings = Meetings.query.order_by(desc(Meetings.id)).limit(4).all()
    else:
        recent_meetings = (
            Meetings.query.filter(Meetings.admin_only != True)
            .order_by(desc(Meetings.id))
            .limit(4)
            .all()
        )

    featured_meeting = recent_meetings.pop(0) if recent_meetings else None
    all_polls = Poll.query.filter(
        Poll.poll_expires.is_(None) | (Poll.poll_expires > datetime.now())
    ).all()

    voted_questions: set[int] = set()
    voted_options: set[int] = set()
    user_frq_responses: dict[int, str] = {}

    if user_id is not None:
        voter_records = PollVoter.query.filter_by(user_id=user_id).all()
        voted_questions = {voter.question_id for voter in voter_records}
        voted_options = {voter.option_id for voter in voter_records}

        frq_records = PollFreeResponse.query.filter_by(user_id=user_id).all()
        user_frq_responses = {
            response.question_id: response.response_text for response in frq_records
        }
        voted_questions.update(user_frq_responses.keys())

    return HomeViewData(
        recent_meetings=recent_meetings,
        featured_meeting=featured_meeting,
        polls=all_polls,
        voted_questions=voted_questions,
        voted_options=voted_options,
        user_frq_responses=user_frq_responses,
    )


def get_events_list_data(is_admin: bool) -> EventsListViewData:
    """Return the meetings visible on the events list page."""
    all_meetings = Meetings.query.order_by(desc(Meetings.id)).all()
    if is_admin:
        return EventsListViewData(meetings=all_meetings)

    return EventsListViewData(
        meetings=[meeting for meeting in all_meetings if meeting.admin_only is not True]
    )


def get_event_view_data(meeting_id: int) -> EventViewData | None:
    """Return the data for an event detail page, if the meeting exists."""
    meeting = db.session.get(Meetings, meeting_id)
    if meeting is None:
        return None

    return EventViewData(
        meeting=meeting,
        attendees=Attendees.query.filter_by(meeting=meeting_id).all(),
        minutes=Minutes.query.filter_by(meeting=meeting_id).all(),
        attachments=Attachments.query.filter_by(meeting=meeting_id).all(),
    )


def meeting_exists(meeting_id: int) -> bool:
    """Return whether a meeting exists."""
    return db.session.get(Meetings, meeting_id) is not None


def check_in_to_meeting(
    meeting_id: int,
    username: str,
    user_role: str,
    user_activated: bool,
    code: str,
) -> MainOperationResult:
    """Check a user into an active meeting when all requirements are met."""
    meeting = db.session.get(Meetings, meeting_id)
    if meeting is None:
        return MainOperationResult(statuses=(MainResultStatus.MEETING_NOT_FOUND,))

    if meeting.state != "active":
        return MainOperationResult(
            statuses=(MainResultStatus.MEETING_INACTIVE,),
            meeting=meeting,
        )

    if Attendees.query.filter_by(meeting=meeting_id, username=username).first() is not None:
        return MainOperationResult(
            statuses=(MainResultStatus.ATTENDEE_EXISTS,),
            meeting=meeting,
        )

    if sha_hash(code) != meeting.code_hash:
        return MainOperationResult(
            statuses=(MainResultStatus.INVALID_MEETING_CODE,),
            meeting=meeting,
        )

    if meeting.admin_only and user_role != "admin":
        return MainOperationResult(
            statuses=(MainResultStatus.ADMIN_ONLY_RESTRICTED,),
            meeting=meeting,
        )

    if user_activated is False:
        return MainOperationResult(
            statuses=(MainResultStatus.ACCOUNT_NOT_ACTIVATED,),
            meeting=meeting,
        )

    attendance = Attendees(username=username, meeting=meeting_id)
    db.session.add(attendance)
    db.session.commit()
    return MainOperationResult(
        statuses=(MainResultStatus.SUCCESS,),
        changes_made=True,
        meeting=meeting,
    )


def handle_frq(user_id: int, question_id: int, response_text: str) -> MainOperationResult:
    """Apply one free-response answer without committing the transaction."""
    question = db.session.get(PollQuestion, question_id)
    if question is None:
        return MainOperationResult(statuses=(MainResultStatus.QUESTION_NOT_FOUND,))

    response_text = response_text.strip()
    if not response_text:
        return MainOperationResult(statuses=(MainResultStatus.SUCCESS,))

    existing_response = PollFreeResponse.query.filter_by(
        user_id=user_id,
        question_id=question_id,
    ).first()

    if existing_response is not None:
        if existing_response.response_text == response_text:
            return MainOperationResult(statuses=(MainResultStatus.SUCCESS,))

        if question.immutable_question:
            return MainOperationResult(
                statuses=(MainResultStatus.IMMUTABLE_RESPONSE,),
                changes_made=True,
                question_text=question.question_text,
            )

        existing_response.response_text = response_text
        existing_response.created_at = db.func.now()
        return MainOperationResult(
            statuses=(MainResultStatus.SUCCESS,),
            changes_made=True,
        )

    new_response = PollFreeResponse(
        user_id=user_id,
        question_id=question_id,
        response_text=response_text,
    )
    db.session.add(new_response)
    return MainOperationResult(
        statuses=(MainResultStatus.SUCCESS,),
        changes_made=True,
    )


def _handle_multiple_response_mcq(
    user_id: int,
    selected_option_ids: list[int],
    question: PollQuestion,
) -> MainOperationResult:
    """Apply one multiple-response answer without committing the transaction."""
    existing_votes = PollVoter.query.filter_by(
        user_id=user_id,
        question_id=question.id,
    ).all()
    existing_option_ids = {vote.option_id for vote in existing_votes}
    new_option_ids = set(selected_option_ids)

    if new_option_ids == existing_option_ids:
        return MainOperationResult(statuses=(MainResultStatus.SUCCESS,))

    if question.immutable_question and existing_votes:
        if not new_option_ids:
            return MainOperationResult(statuses=(MainResultStatus.SUCCESS,))

        return MainOperationResult(
            statuses=(MainResultStatus.IMMUTABLE_RESPONSES,),
            changes_made=True,
            question_text=question.question_text,
        )

    changes_made = False
    for vote in existing_votes:
        if vote.option_id not in new_option_ids:
            option = db.session.get(PollOption, vote.option_id)
            if option is not None and option.votes > 0:
                option.votes -= 1
            db.session.delete(vote)
            changes_made = True

    for option_id in new_option_ids:
        if option_id not in existing_option_ids:
            option = db.session.get(PollOption, option_id)
            if option is None:
                return MainOperationResult(
                    statuses=(MainResultStatus.ONE_SELECTED_OPTION_NOT_FOUND,),
                    changes_made=True,
                )

            option.votes += 1
            new_vote = PollVoter(
                user_id=user_id,
                question_id=question.id,
                option_id=option_id,
            )
            db.session.add(new_vote)
            changes_made = True

    return MainOperationResult(
        statuses=(MainResultStatus.SUCCESS,),
        changes_made=changes_made,
    )


def handle_multiple_response_mcq(
    user_id: int,
    question_id: int,
    selected_option_ids: list[int],
) -> MainOperationResult:
    """Apply one multiple-response answer without committing the transaction."""
    question = db.session.get(PollQuestion, question_id)
    if question is None:
        return MainOperationResult(statuses=(MainResultStatus.QUESTION_NOT_FOUND,))

    return _handle_multiple_response_mcq(user_id, selected_option_ids, question)


def _handle_single_mcq(
    user_id: int,
    selected_option_ids: list[int],
    question: PollQuestion,
) -> MainOperationResult:
    """Apply one single-response answer without committing the transaction."""
    option_id = selected_option_ids[0]
    existing_vote = PollVoter.query.filter_by(
        user_id=user_id,
        question_id=question.id,
    ).first()

    if existing_vote is not None:
        if existing_vote.option_id == option_id:
            return MainOperationResult(statuses=(MainResultStatus.SUCCESS,))

        if question.immutable_question:
            return MainOperationResult(
                statuses=(MainResultStatus.IMMUTABLE_RESPONSE,),
                changes_made=True,
                question_text=question.question_text,
            )

        old_option = db.session.get(PollOption, existing_vote.option_id)
        if old_option is not None and old_option.votes > 0:
            old_option.votes -= 1

        new_option = db.session.get(PollOption, option_id)
        if new_option is not None:
            new_option.votes += 1
            existing_vote.option_id = option_id

        return MainOperationResult(
            statuses=(MainResultStatus.SUCCESS,),
            changes_made=True,
        )

    option = db.session.get(PollOption, option_id)
    if option is None:
        return MainOperationResult(
            statuses=(MainResultStatus.SELECTED_OPTION_NOT_FOUND,),
        )

    option.votes += 1
    new_vote = PollVoter(
        user_id=user_id,
        question_id=question.id,
        option_id=option_id,
    )
    db.session.add(new_vote)
    return MainOperationResult(
        statuses=(MainResultStatus.SUCCESS,),
        changes_made=True,
    )


def handle_single_mcq(
    user_id: int,
    question_id: int,
    selected_option_ids: list[int],
) -> MainOperationResult:
    """Apply one single-response answer without committing the transaction."""
    question = db.session.get(PollQuestion, question_id)
    if question is None:
        return MainOperationResult(statuses=(MainResultStatus.QUESTION_NOT_FOUND,))

    if not selected_option_ids:
        return MainOperationResult(statuses=(MainResultStatus.SUCCESS,))

    return _handle_single_mcq(user_id, selected_option_ids, question)


def handle_mcq(
    user_id: int,
    question_id: int,
    selected_option_ids: list[int],
) -> MainOperationResult:
    """Apply one single- or multiple-response answer without committing the transaction."""
    question = db.session.get(PollQuestion, question_id)
    if question is None:
        return MainOperationResult(statuses=(MainResultStatus.QUESTION_NOT_FOUND,))

    if question.allow_multiple_responses:
        return _handle_multiple_response_mcq(user_id, selected_option_ids, question)

    if selected_option_ids:
        return _handle_single_mcq(user_id, selected_option_ids, question)

    return MainOperationResult(statuses=(MainResultStatus.SUCCESS,))


def submit_poll_responses(
    poll_id: int,
    user_id: int,
    free_responses: dict[int, str],
    selected_options: dict[int, list[str]],
) -> PollSubmissionResult:
    """Apply and commit all responses submitted for a poll."""
    poll = db.session.get(Poll, poll_id)
    if poll is None:
        return PollSubmissionResult(statuses=(MainResultStatus.POLL_NOT_FOUND,))

    if poll.poll_expires and poll.poll_expires <= datetime.now():
        return PollSubmissionResult(statuses=(MainResultStatus.POLL_EXPIRED,))

    question_results: list[MainOperationResult] = []
    changes_made = False
    successes = 0
    failures = 0

    try:
        for question in poll.questions:
            if question.is_free_response:
                result = handle_frq(
                    user_id,
                    question.id,
                    free_responses.get(question.id, ""),
                )
            else:
                selected_option_ids = [
                    int(option_id)
                    for option_id in selected_options.get(question.id, [])
                ]
                result = handle_mcq(user_id, question.id, selected_option_ids)

            question_results.append(result)
            changes_made = changes_made or result.changes_made
            if MainResultStatus.SUCCESS in result.statuses:
                successes += 1
            else:
                failures += 1

        db.session.commit()
    except Exception as error:  # pylint: disable=broad-exception-caught
        db.session.rollback()
        LOGGER.error("Error submitting poll: %s", error)
        return PollSubmissionResult(
            statuses=(MainResultStatus.ERROR,),
            question_results=tuple(question_results),
            changes_made=changes_made,
            successes=successes,
            failures=failures,
        )

    if failures:
        status = MainResultStatus.PARTIAL_FAILURE
    elif changes_made:
        status = MainResultStatus.SUCCESS
    else:
        status = MainResultStatus.NO_CHANGES

    return PollSubmissionResult(
        statuses=(status,),
        question_results=tuple(question_results),
        changes_made=changes_made,
        successes=successes,
        failures=failures,
    )
