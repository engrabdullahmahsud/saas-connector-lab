"""Add user id to agent tasks

Revision ID: 017d0c9aa2f4
Revises: 713ae90bc26f
Create Date: 2026-08-15 21:42:09.144632

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '017d0c9aa2f4'
down_revision: Union[str, Sequence[str], None] = '713ae90bc26f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Add the column as nullable first so existing rows can be populated.
    op.add_column(
        'agent_tasks',
        sa.Column('user_id', sa.Integer(), nullable=True)
    )

    # Assign existing agent tasks to an existing user.
    op.execute(
        sa.text(
            "UPDATE agent_tasks SET user_id = 7 WHERE user_id IS NULL"
        )
    )

    # Now that all existing rows have a user_id, make it required.
    op.alter_column(
        'agent_tasks',
        'user_id',
        existing_type=sa.Integer(),
        nullable=False
    )

    # Add the foreign key constraint.
    op.create_foreign_key(
        'fk_agent_tasks_user_id_users',
        'agent_tasks',
        'users',
        ['user_id'],
        ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        'fk_agent_tasks_user_id_users',
        'agent_tasks',
        type_='foreignkey'
    )
    op.drop_column('agent_tasks', 'user_id')
