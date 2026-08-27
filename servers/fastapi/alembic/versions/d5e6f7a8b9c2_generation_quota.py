"""generation quota: таблица generation_usage и колонка user.generation_limit.

Revision ID: d5e6f7a8b9c2
Revises: e4c7a9b2d6f1
Create Date: 2026-08-27

Квоты на генерацию (P4): generation_usage хранит по строке на запуск
генерации (скользящее окно 24ч), user.generation_limit — персональное
переопределение лимита (NULL = дефолт из GENERATION_QUOTA_PER_DAY).

Идемпотентно: на старых тестовых/базовых снапшотах таблицы user может
не быть — тогда пропускаем добавление колонки.
"""

import sqlalchemy as sa

from alembic import op

revision = "d5e6f7a8b9c2"
down_revision = "e4c7a9b2d6f1"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "generation_usage" not in tables:
        op.create_table(
            "generation_usage",
            sa.Column("id", sa.CHAR(36), primary_key=True),
            sa.Column(
                "owner_id",
                sa.CHAR(36),
                sa.ForeignKey("user.id", ondelete="CASCADE"),
                nullable=True,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_generation_usage_owner_id",
            "generation_usage",
            ["owner_id"],
        )

    if "user" in tables:
        user_columns = {column["name"] for column in inspector.get_columns("user")}
        if "generation_limit" not in user_columns:
            op.add_column("user", sa.Column("generation_limit", sa.Integer(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "user" in tables:
        user_columns = {column["name"] for column in inspector.get_columns("user")}
        if "generation_limit" in user_columns:
            op.drop_column("user", "generation_limit")
    if "generation_usage" in tables:
        op.drop_index("ix_generation_usage_owner_id", table_name="generation_usage")
        op.drop_table("generation_usage")
