-- ============================================================
-- MIGRAÇÃO: PARCEIRO DE ESTUDOS (dupla) → GRUPOS DE ESTUDOS
-- Execute este script no SQL Editor do Supabase (Dashboard).
-- Pode ser executado quantas vezes quiser (é idempotente).
-- ============================================================

-- 1. Tabela de grupos
CREATE TABLE IF NOT EXISTS grupos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    codigo_convite TEXT UNIQUE NOT NULL,
    criador_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Tabela de membros do grupo
CREATE TABLE IF NOT EXISTS membros_grupo (
    id BIGSERIAL PRIMARY KEY,
    grupo_id UUID NOT NULL REFERENCES grupos(id) ON DELETE CASCADE,
    user_id UUID NOT NULL UNIQUE,
    joined_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_membros_grupo_grupo_id ON membros_grupo(grupo_id);

-- 3. Migração automática de duplas existentes (parceiro_id) → grupos de 2
DO $$
DECLARE
    p RECORD;
    novo_grupo_id UUID;
    novo_codigo TEXT;
BEGIN
    FOR p IN
        SELECT * FROM perfis_usuario
        WHERE parceiro_id IS NOT NULL
    LOOP
        -- Re-checa se o usuário já está em algum grupo. A verificação é feita
        -- AQUI (dentro do loop) e não no SELECT, porque o cursor do FOR usa um
        -- snapshot "antigo" que não enxerga os membros inseridos durante o loop,
        -- o que causaria erro de chave duplicada em vínculos mútuos.
        IF EXISTS (SELECT 1 FROM membros_grupo WHERE user_id = p.user_id) THEN
            CONTINUE;
        END IF;

        -- Gera um código único no formato GR-XXXXXX
        LOOP
            novo_codigo := 'GR-' || upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 6));
            EXIT WHEN NOT EXISTS (SELECT 1 FROM grupos WHERE codigo_convite = novo_codigo);
        END LOOP;

        INSERT INTO grupos (codigo_convite, criador_id)
        VALUES (novo_codigo, p.user_id)
        RETURNING id INTO novo_grupo_id;

        -- Usuário atual vira membro (e criador/admin) do grupo
        INSERT INTO membros_grupo (grupo_id, user_id)
        VALUES (novo_grupo_id, p.user_id)
        ON CONFLICT (user_id) DO NOTHING;

        -- Se o parceiro apontar de volta (vínculo mútuo), entra no mesmo grupo.
        -- Caso contrário, o vínculo fica pendente: o parceiro entra pelo código.
        IF EXISTS (SELECT 1 FROM perfis_usuario WHERE user_id = p.parceiro_id AND parceiro_id = p.user_id) THEN
            INSERT INTO membros_grupo (grupo_id, user_id)
            VALUES (novo_grupo_id, p.parceiro_id)
            ON CONFLICT (user_id) DO NOTHING;
        END IF;
    END LOOP;
END $$;

-- 4. (Opcional) Políticas de RLS, caso seu projeto tenha RLS habilitado.
--    Se o projeto atual NÃO usa RLS (padrão destas tabelas), pode ignorar.
--
-- ALTER TABLE grupos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE membros_grupo ENABLE ROW LEVEL SECURITY;
--
-- CREATE POLICY grupos_select ON grupos FOR SELECT USING (true);
-- CREATE POLICY grupos_insert ON grupos FOR INSERT WITH CHECK (true);
-- CREATE POLICY grupos_update ON grupos FOR UPDATE USING (true);
--
-- CREATE POLICY membros_select ON membros_grupo FOR SELECT USING (true);
-- CREATE POLICY membros_insert ON membros_grupo FOR INSERT WITH CHECK (true);
-- CREATE POLICY membros_delete ON membros_grupo FOR DELETE USING (true);

-- 5. (Opcional) Depois de validar a migração, pode limpar a coluna antiga:
-- ALTER TABLE perfis_usuario DROP COLUMN parceiro_id;
