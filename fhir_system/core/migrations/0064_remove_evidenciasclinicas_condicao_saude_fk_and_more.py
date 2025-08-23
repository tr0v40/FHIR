from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0063_fix_condicao_saude_columns'),
    ]

    operations = [

        # 1) Garante a coluna NO BANCO em DetalhesTratamentoResumo (idempotente)
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    """
                    ALTER TABLE core_detalhestratamentoresumo
                    ADD COLUMN IF NOT EXISTS condicao_saude_id bigint;
                    """,
                    reverse_sql="""
                    -- Não derruba coluna no reverse para não quebrar outros ambientes
                    """
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='detalhestratamentoresumo',
                    name='condicao_saude',
                    field=models.ForeignKey(
                        blank=True, null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='detalhes_tratamento',
                        to='core.condicaosaude'
                    ),
                ),
            ],
        ),

        # 2) Garante a coluna NO BANCO em EvidenciasClinicas (idempotente)
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='core_evidenciasclinicas' AND column_name='condicao_saude'
              ) THEN
                ALTER TABLE core_evidenciasclinicas ADD COLUMN condicao_saude integer NULL;
              END IF;
            END $$;
            """,
            reverse_sql="""
            -- Não remove no reverse
            """
        ),

        # 3) Agora sim: altera o campo para FK com SET_NULL
        migrations.AlterField(
            model_name='evidenciasclinicas',
            name='condicao_saude',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='evidencias',
                to='core.condicaosaude'
            ),
        ),
    ]
