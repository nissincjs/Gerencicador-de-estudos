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
--    Só roda se a coluna parceiro_id ainda existir (pode já ter sido removida).
DO $$
DECLARE
    p RECORD;
    novo_grupo_id UUID;
    novo_codigo TEXT;
    tem_coluna_parceiro BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'perfis_usuario'
          AND column_name = 'parceiro_id'
    ) INTO tem_coluna_parceiro;

    IF tem_coluna_parceiro THEN
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
    END IF;
END $$;

-- 4. Garante acesso do app às tabelas de grupos via RLS.
--    Habilita RLS (caso ainda esteja desligado) e cria políticas permissivas,
--    replicando o mesmo nível de acesso das demais tabelas do app.
ALTER TABLE grupos ENABLE ROW LEVEL SECURITY;
ALTER TABLE membros_grupo ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS grupos_select ON grupos;
DROP POLICY IF EXISTS grupos_insert ON grupos;
DROP POLICY IF EXISTS grupos_update ON grupos;
DROP POLICY IF EXISTS grupos_delete ON grupos;

DROP POLICY IF EXISTS membros_select ON membros_grupo;
DROP POLICY IF EXISTS membros_insert ON membros_grupo;
DROP POLICY IF EXISTS membros_update ON membros_grupo;
DROP POLICY IF EXISTS membros_delete ON membros_grupo;

CREATE POLICY grupos_select ON grupos FOR SELECT USING (true);
CREATE POLICY grupos_insert ON grupos FOR INSERT WITH CHECK (true);
CREATE POLICY grupos_update ON grupos FOR UPDATE USING (true);
CREATE POLICY grupos_delete ON grupos FOR DELETE USING (true);

CREATE POLICY membros_select ON membros_grupo FOR SELECT USING (true);
CREATE POLICY membros_insert ON membros_grupo FOR INSERT WITH CHECK (true);
CREATE POLICY membros_update ON membros_grupo FOR UPDATE USING (true);
CREATE POLICY membros_delete ON membros_grupo FOR DELETE USING (true);

-- 5. Remove a coluna antiga parceiro_id.
--    A política de RLS "Permitir leitura ao proprietário ou parceiro" depende
--    dessa coluna, então ela é recriada antes usando o modelo de grupos.
--    A nova política permite a leitura ao proprietário e a todos os membros
--    do mesmo grupo de estudos.

-- 5.1 Remove a política antiga (que dependia da coluna parceiro_id)
DROP POLICY IF EXISTS "Permitir leitura ao proprietário ou parceiro" ON ciclos_usuario;

-- 5.2 Recria a política de leitura baseada no grupo de estudos
DROP POLICY IF EXISTS "Permitir leitura ao proprietário e membros do grupo" ON ciclos_usuario;
CREATE POLICY "Permitir leitura ao proprietário e membros do grupo"
ON ciclos_usuario
FOR SELECT
USING (
    ciclos_usuario.user_id = auth.uid()
    OR EXISTS (
        SELECT 1
        FROM membros_grupo mg_meu
        JOIN membros_grupo mg_alvo ON mg_alvo.grupo_id = mg_meu.grupo_id
        WHERE mg_meu.user_id = auth.uid()
          AND mg_alvo.user_id = ciclos_usuario.user_id
    )
);

-- 5.3 Remove a coluna antiga (se ainda existir)
ALTER TABLE perfis_usuario DROP COLUMN IF EXISTS parceiro_id;

-- 5.4 Verificação: deve retornar 0 linhas (nenhuma política referenciando parceiro_id)
SELECT p.polname, p.polrelid::regclass
FROM pg_policy p
WHERE (pg_get_expr(p.polqual, p.polrelid) LIKE '%parceiro_id%'
       OR pg_get_expr(p.polwithcheck, p.polrelid) LIKE '%parceiro_id%');

-- Se a etapa 5.3 ainda falhar com outro objeto dependente, descubra qual com a
-- consulta acima e remova/recrie a política correspondente antes de rodar de novo.
