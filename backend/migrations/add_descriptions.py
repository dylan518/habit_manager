from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("day_plans", sa.Column("description", sa.String(), nullable=True))


def downgrade():
    op.drop_column("day_plans", "description")
