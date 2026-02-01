"""FRQ table added

Revision ID: b1704bf488ee
Revises: 9707706692be
Create Date: 2026-02-01 14:09:58.498700

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1704bf488ee'
down_revision = '9707706692be'
branch_labels = None
depends_on = None


def upgrade():
    # Add column as nullable first
    op.add_column('poll_questions', 
                  sa.Column('is_free_response', sa.Boolean(), nullable=True))
    
    # Set default value for existing rows
    op.execute('UPDATE poll_questions SET is_free_response = FALSE WHERE is_free_response IS NULL')
    
    # Now make it non-nullable
    op.alter_column('poll_questions', 'is_free_response',
                    existing_type=sa.Boolean(),
                    nullable=False)
    
    # Add the PollFreeResponse table
    op.create_table('poll_free_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('response_text', sa.Text(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['poll_questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'question_id', name='unique_user_question_response')
    )


def downgrade():
    op.drop_table('poll_free_responses')
    op.drop_column('poll_questions', 'is_free_response')
