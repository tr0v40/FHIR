from django.db import migrations

SQL_FORWARD = r"""
-- 1) Remova a antiga coluna TEXT (se existir)
ALTER TABLE core_evidenciasclinicas
    DROP COLUMN IF EXISTS condicao_saude;

-- 2) Renomeie a coluna FK antiga para o nome que o Django espera
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='core_evidenciasclinicas' AND column_name='condicao_saude_fk_id'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='core_evidenciasclinicas' AND column_name='condicao_saude_id'
    ) THEN
        ALTER TABLE core_evidenciasclinicas RENAME COLUMN condicao_saude_fk_id TO condicao_saude_id;
    END IF;
END$$;

-- 3) Garanta a constraint de FK (idêntica ao que o Django criaria)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints tc
        WHERE tc.table_name='core_evidenciasclinicas'
          AND tc.constraint_type='FOREIGN KEY'
          AND tc.constraint_name='core_evidenciasclinicas_condicao_saude_id_fk'
    ) THEN
        ALTER TABLE core_evidenciasclinicas
        ADD CONSTRAINT core_evidenciasclinicas_condicao_saude_id_fk
        FOREIGN KEY (condicao_saude_id)
        REFERENCES core_condicaosaude (id)
        ON DELETE SET NULL;
    END IF;
END$$;
"""

SQL_BACKWARD = r"""
-- (Opcional) Remove a FK e renomeia de volta, best-effort
ALTER TABLE core_evidenciasclinicas
    DROP CONSTRAINT IF EXISTS core_evidenciasclinicas_condicao_saude_id_fk;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='core_evidenciasclinicas' AND column_name='condicao_saude_id'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='core_evidenciasclinicas' AND column_name='condicao_saude_fk_id'
    ) THEN
        ALTER TABLE core_evidenciasclinicas RENAME COLUMN condicao_saude_id TO condicao_saude_fk_id;
    END IF;
END$$;
"""

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0062_remove_evidenciasclinicas_condicao_saude_fk_and_more'),
    ]

    operations = [
        migrations.RunSQL(SQL_FORWARD, reverse_sql=SQL_BACKWARD),
    ]


