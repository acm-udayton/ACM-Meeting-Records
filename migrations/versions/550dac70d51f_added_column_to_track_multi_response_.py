"""added column to track multi-response questions.

Revision ID: 550dac70d51f
Revises: b1704bf488ee
Create Date: 2026-02-06 13:31:33.468888

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '550dac70d51f'
down_revision = 'b1704bf488ee'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('poll_questions', 
                  sa.Column('allow_multiple_responses', sa.Boolean(), nullable=True))
    op.execute('UPDATE poll_questions SET allow_multiple_responses = FALSE WHERE allow_multiple_responses IS NULL')
    op.alter_column('poll_questions', 'allow_multiple_responses',
                    existing_type=sa.Boolean(),
                    nullable=False)
    
    # Remove the unique constraint on poll_voters to allow multiple votes
    op.drop_constraint('unique_user_question_vote', 'poll_voters', type_='unique')


def downgrade():
    op.create_unique_constraint('unique_user_question_vote', 'poll_voters', ['user_id', 'question_id'])
    op.drop_column('poll_questions', 'allow_multiple_responses')
