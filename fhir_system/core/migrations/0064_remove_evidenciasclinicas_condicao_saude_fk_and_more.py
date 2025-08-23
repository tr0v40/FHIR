from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ("core", "0063_fix_condicao_saude_columns"),
    ]

    operations = [
        # ... seus RunSQL para garantir as colunas condicao_saude_id ...

        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
DO $$
BEGIN
  -- adiciona a FK se ainda não existir
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints tc
    WHERE tc.table_name='core_evidenciasclinicas'
      AND tc.constraint_type='FOREIGN KEY'
      AND tc.constraint_name='core_evidenciasclinicas_condicao_saude_id_fk'
  ) THEN
    ALTER TABLE core_evidenciasclinicas
      ADD CONSTRAINT core_evidenciasclinicas_condicao_saude_id_fk
      FOREIGN KEY (condicao_saude_id)
      REFERENCES core_condicaosaude (id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
END $$;
""",
                    reverse_sql="""
ALTER TABLE core_evidenciasclinicas
DROP CONSTRAINT IF EXISTS core_evidenciasclinicas_condicao_saude_id_fk;
""",
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="evidenciasclinicas",
                    name="condicao_saude",
                    field=models.ForeignKey(
                        to="core.condicaosaude",
                        on_delete=django.db.models.deletion.SET_NULL,
                        null=True,
                        blank=True,
                        related_name="evidencias",
                        db_column="condicao_saude_id",  # <- importante!
                    ),
                ),
            ],
        ),
    ]
