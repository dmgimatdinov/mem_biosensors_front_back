"""add_reliability_fields

Revision ID: add_reliability_fields
Revises: 
Create Date: 2026-07-12
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_reliability_fields'
down_revision = None
branch_labels = None
depends_on = None


TABLES = [
    'Analytes',
    'BioRecognitionLayers',
    'ImmobilizationLayers',
    'MemristiveLayers',
]


def _add_reliability_columns(table: str) -> None:
    op.add_column(
        table,
        sa.Column(
            'source_type',
            sa.String(length=32),
            nullable=True,
            server_default='expert',
        ),
    )
    op.add_column(table, sa.Column('source_doi', sa.String(length=255), nullable=True))
    op.add_column(table, sa.Column('source_date', sa.Date(), nullable=True))
    op.add_column(
        table,
        sa.Column(
            'reliability_category',
            sa.String(length=16),
            nullable=True,
            server_default='medium',
        ),
    )
    op.add_column(
        table,
        sa.Column(
            'data_completeness',
            sa.Float(),
            nullable=True,
            server_default='1.0',
        ),
    )

    op.create_check_constraint(
        f'ck_{table}_source_type',
        table,
        "source_type IS NULL OR source_type IN ('experimental','manufacturer','expert','literature')",
    )
    op.create_check_constraint(
        f'ck_{table}_reliability_category',
        table,
        "reliability_category IS NULL OR reliability_category IN ('high','medium','low')",
    )
    op.create_check_constraint(
        f'ck_{table}_data_completeness',
        table,
        'data_completeness IS NULL OR (data_completeness >= 0.0 AND data_completeness <= 1.0)',
    )


def upgrade() -> None:
    for table in TABLES:
        _add_reliability_columns(table)
        op.execute(
            sa.text(
                f"""
                UPDATE {table}
                SET reliability_category = 'medium',
                    data_completeness = 0.5
                WHERE source_doi IS NULL
                  AND source_date IS NULL
                  AND (reliability_category IS NULL OR reliability_category = 'medium')
                  AND (data_completeness IS NULL OR data_completeness = 1.0)
                """
            )
        )


def downgrade() -> None:
    for table in TABLES:
        op.drop_constraint(f'ck_{table}_data_completeness', table, type_='check')
        op.drop_constraint(f'ck_{table}_reliability_category', table, type_='check')
        op.drop_constraint(f'ck_{table}_source_type', table, type_='check')

        op.drop_column(table, 'data_completeness')
        op.drop_column(table, 'reliability_category')
        op.drop_column(table, 'source_date')
        op.drop_column(table, 'source_doi')
        op.drop_column(table, 'source_type')
