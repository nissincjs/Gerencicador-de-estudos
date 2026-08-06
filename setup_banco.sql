-- ============================================================
-- SETUP COMPLETO DO BANCO - CICLO DE ESTUDOS ESTRATÉGICO
-- Execute este script no SQL Editor do Supabase (Dashboard).
--
-- Funciona em banco NOVO (cria todas as tabelas e políticas)
-- e em banco EXISTENTE (migra duplas antigas e limpa o legado).
-- É idempotente: pode ser executado quantas vezes quiser.
-- ============================================================

-- 1. Perfis de usuários (autenticação e convites)
CREATE TABLE IF NOT EXISTS perfis_usuario (
    user_id UUID PRIMARY KEY,
    email TEXT NOT NULL,
    codigo_convite TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Dados de estudo de cada usuário (sincronização local + nuvem)
CREATE TABLE IF NOT EXISTS ciclos_usuario (
    user_id UUID PRIMARY KEY,
    dados JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Grupos de estudos (criador = admin)
CREATE TABLE IF NOT EXISTS grupos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    codigo_convite TEXT UNIQUE NOT NULL,
    criador_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Membros do grupo
CREATE TABLE IF NOT EXISTS membros_grupo (
    id BIGSERIAL PRIMARY KEY,
    grupo_id UUID NOT NULL REFERENCES grupos(id) ON DELETE CASCADE,
    user_id UUID NOT NULL UNIQUE,
    joined_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_membros_grupo_grupo_id ON membros_grupo(grupo_id);

-- 5. RLS: habilita e cria políticas permissivas para o app.
--    (Replica o mesmo nível de acesso que o app sempre teve.)
ALTER TABLE perfis_usuario ENABLE ROW LEVEL SECURITY;
ALTER TABLE ciclos_usuario ENABLE ROW LEVEL SECURITY;
ALTER TABLE grupos ENABLE ROW LEVEL SECURITY;
ALTER TABLE membros_grupo ENABLE ROW LEVEL SECURITY;

-- 5.1 perfis_usuario
DROP POLICY IF EXISTS perfis_select ON perfis_usuario;
DROP POLICY IF EXISTS perfis_insert ON perfis_usuario;
DROP POLICY IF EXISTS perfis_update ON perfis_usuario;
DROP POLICY IF EXISTS perfis_delete ON perfis_usuario;

CREATE POLICY perfis_select ON perfis_usuario FOR SELECT USING (true);
CREATE POLICY perfis_insert ON perfis_usuario FOR INSERT WITH CHECK (true);
CREATE POLICY perfis_update ON perfis_usuario FOR UPDATE USING (true);
CREATE POLICY perfis_delete ON perfis_usuario FOR DELETE USING (true);

-- 5.2 ciclos_usuario
-- Remove eventuais políticas antigas que o app de dupla criava
DROP POLICY IF EXISTS "Permitir leitura ao proprietário ou parceiro" ON ciclos_usuario;
DROP POLICY IF EXISTS "Permitir leitura ao proprietário e membros do grupo" ON ciclos_usuario;

DROP POLICY IF EXISTS ciclos_select ON ciclos_usuario;
DROP POLICY IF EXISTS ciclos_insert ON ciclos_usuario;
DROP POLICY IF EXISTS ciclos_update ON ciclos_usuario;
DROP POLICY IF EXISTS ciclos_delete ON ciclos_usuario;

CREATE POLICY ciclos_select ON ciclos_usuario FOR SELECT USING (true);
CREATE POLICY ciclos_insert ON ciclos_usuario FOR INSERT WITH CHECK (true);
CREATE POLICY ciclos_update ON ciclos_usuario FOR UPDATE USING (true);
CREATE POLICY ciclos_delete ON ciclos_usuario FOR DELETE USING (true);

-- 5.3 grupos
DROP POLICY IF EXISTS grupos_select ON grupos;
DROP POLICY IF EXISTS grupos_insert ON grupos;
DROP POLICY IF EXISTS grupos_update ON grupos;
DROP POLICY IF EXISTS grupos_delete ON grupos;

CREATE POLICY grupos_select ON grupos FOR SELECT USING (true);
CREATE POLICY grupos_insert ON grupos FOR INSERT WITH CHECK (true);
CREATE POLICY grupos_update ON grupos FOR UPDATE USING (true);
CREATE POLICY grupos_delete ON grupos FOR DELETE USING (true);

-- 5.4 membros_grupo
DROP POLICY IF EXISTS membros_select ON membros_grupo;
DROP POLICY IF EXISTS membros_insert ON membros_grupo;
DROP POLICY IF EXISTS membros_update ON membros_grupo;
DROP POLICY IF EXISTS membros_delete ON membros_grupo;

CREATE POLICY membros_select ON membros_grupo FOR SELECT USING (true);
CREATE POLICY membros_insert ON membros_grupo FOR INSERT WITH CHECK (true);
CREATE POLICY membros_update ON membros_grupo FOR UPDATE USING (true);
CREATE POLICY membros_delete ON membros_grupo FOR DELETE USING (true);

-- 6. Migração automática de duplas antigas (parceiro_id) → grupos de 2.
--    Só roda se a coluna parceiro_id ainda existir (banco antigo).
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

-- 7. Remove a coluna antiga (se ainda existir)
ALTER TABLE perfis_usuario DROP COLUMN IF EXISTS parceiro_id;

-- 8. Verificação: deve retornar 0 linhas (nenhuma política referenciando parceiro_id)
SELECT p.polname, p.polrelid::regclass
FROM pg_policy p
WHERE (pg_get_expr(p.polqual, p.polrelid) LIKE '%parceiro_id%'
       OR pg_get_expr(p.polwithcheck, p.polrelid) LIKE '%parceiro_id%');
