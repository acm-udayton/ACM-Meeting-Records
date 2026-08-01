#!/usr/bin/env python
# app/services/polls_service.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 8/1/2026

File Purpose: Polls service for the project.
"""

# Standard library imports.
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Local application imports.
from app.extensions import db
from app.models import Poll, PollOption, PollQuestion, PollVoter


class PollResultStatus(str, Enum):
    """Granular outcomes for poll operations."""

    SUCCESS = "success"
    INVALID_POLL_EXPIRATION = "invalid_poll_expiration"
    POLL_NOT_FOUND = "poll_not_found"


@dataclass(slots=True)
class PollsListViewData:
    """Data required to render the polls management page."""

    polls: list[Poll]
    voted_questions: set[int]


@dataclass(slots=True)
class PollOperationResult:
    """Outcome for poll operations that mutate state."""

    statuses: tuple[PollResultStatus, ...]
    poll: Poll | None = None


def get_polls_list_data(user_id: int | None) -> PollsListViewData:
    """Return the data needed to render the poll management page."""
    all_polls = Poll.query.all()
    voted_questions: set[int] = set()

    if user_id is not None:
        voter_records = PollVoter.query.filter_by(user_id=user_id).all()
        voted_questions = {voter.question_id for voter in voter_records}

    return PollsListViewData(polls=all_polls, voted_questions=voted_questions)


def create_poll(
    title: str,
    poll_expires: datetime | None,
    questions: list[dict[str, object]],
) -> PollOperationResult:
    """Create a new poll and its nested questions/options."""
    if poll_expires is not None and poll_expires <= datetime.now():
        return PollOperationResult(statuses=(PollResultStatus.INVALID_POLL_EXPIRATION,))

    poll = Poll()
    poll.title = title
    poll.poll_expires = poll_expires
    db.session.add(poll)
    db.session.flush()

    for question_data in questions:
        is_frq = bool(question_data.get("is_free_response", False))
        question = PollQuestion()
        question.poll_id = poll.id
        question.question_text = str(question_data["question_text"])
        question.is_free_response = is_frq
        question.allow_multiple_responses = (
            bool(question_data.get("allow_multiple_responses", False))
            if not is_frq
            else False
        )
        question.private_vote = bool(question_data.get("private_vote", False))
        question.immutable_question = bool(question_data.get("immutable_question", False))
        db.session.add(question)
        db.session.flush()

        if not is_frq:
            option_texts = question_data.get("options", [])
            if isinstance(option_texts, list):
                for option_text in option_texts:
                    option = PollOption()
                    option.question_id = question.id
                    option.option_text = str(option_text)
                    db.session.add(option)

    db.session.commit()
    return PollOperationResult(statuses=(PollResultStatus.SUCCESS,), poll=poll)


def delete_poll(poll_id: int) -> PollOperationResult:
    """Delete a poll if it exists."""
    poll = db.session.get(Poll, poll_id)
    if poll is None:
        return PollOperationResult(statuses=(PollResultStatus.POLL_NOT_FOUND,))

    db.session.delete(poll)
    db.session.commit()
    return PollOperationResult(statuses=(PollResultStatus.SUCCESS,), poll=poll)