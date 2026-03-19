from core.database import get_connection, get_cursor


def buscar_usuario_por_username(username):

    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute(
        "SELECT id, nome, username, senha FROM usuarios WHERE username = %s",
        (username,)
    )

    usuario = cursor.fetchone()
    conn.close()

    return usuario


def buscar_usuario_por_google_id(google_id):

    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute(
        "SELECT id, nome, username, email FROM usuarios WHERE google_id = %s",
        (google_id,)
    )

    usuario = cursor.fetchone()
    conn.close()

    return usuario


def buscar_usuario_por_email(email):

    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute(
        "SELECT id, nome, username, email, google_id FROM usuarios WHERE email = %s",
        (email,)
    )

    usuario = cursor.fetchone()
    conn.close()

    return usuario


def buscar_usuario_por_cpf(cpf):

    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute(
        "SELECT id FROM usuarios WHERE cpf = %s",
        (cpf,)
    )

    usuario = cursor.fetchone()
    conn.close()

    return usuario


def criar_usuario(nome, username, senha, dados_completos=None):
    """
    Cria um usuário com dados básicos obrigatórios.
    dados_completos: dict opcional com nome_completo, data_nascimento,
                     cpf, email, celular, cep, logradouro, numero,
                     complemento, bairro, cidade, estado
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    d = dados_completos or {}

    cursor.execute(
        """
        INSERT INTO usuarios (
            nome, username, senha,
            nome_completo, data_nascimento, cpf, email, celular,
            cep, logradouro, numero, complemento, bairro, cidade, estado
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            nome, username, senha,
            d.get("nome_completo"),
            d.get("data_nascimento"),
            d.get("cpf"),
            d.get("email"),
            d.get("celular"),
            d.get("cep"),
            d.get("logradouro"),
            d.get("numero"),
            d.get("complemento"),
            d.get("bairro"),
            d.get("cidade"),
            d.get("estado"),
        )
    )

    row = cursor.fetchone()
    conn.commit()
    conn.close()

    return row["id"]


def criar_usuario_google(nome, username, email, google_id, avatar_url=None):
    """
    Cria um usuário autenticado via Google (sem senha).
    Dados complementares devem ser preenchidos após o primeiro login.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute(
        """
        INSERT INTO usuarios (nome, username, email, google_id, avatar_url)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (nome, username, email, google_id, avatar_url)
    )

    row = cursor.fetchone()
    conn.commit()
    conn.close()

    return row["id"]


def atualizar_dados_usuario(usuario_id, dados):
    """
    Atualiza os dados cadastrais completos do usuário.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute(
        """
        UPDATE usuarios SET
            nome_completo    = %s,
            data_nascimento  = %s,
            cpf              = %s,
            email            = %s,
            celular          = %s,
            cep              = %s,
            logradouro       = %s,
            numero           = %s,
            complemento      = %s,
            bairro           = %s,
            cidade           = %s,
            estado           = %s
        WHERE id = %s
        """,
        (
            dados.get("nome_completo"),
            dados.get("data_nascimento"),
            dados.get("cpf"),
            dados.get("email"),
            dados.get("celular"),
            dados.get("cep"),
            dados.get("logradouro"),
            dados.get("numero"),
            dados.get("complemento"),
            dados.get("bairro"),
            dados.get("cidade"),
            dados.get("estado"),
            usuario_id,
        )
    )

    conn.commit()
    conn.close()


def buscar_dados_completos(usuario_id):
    """
    Retorna todos os dados cadastrais do usuário.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute(
        """
        SELECT nome, username, email, nome_completo, data_nascimento,
               cpf, celular, cep, logradouro, numero, complemento,
               bairro, cidade, estado
        FROM usuarios
        WHERE id = %s
        """,
        (usuario_id,)
    )

    row = cursor.fetchone()
    conn.close()

    return row


def cadastro_completo(usuario_id):
    """
    Verifica se o usuário preencheu todos os campos obrigatórios.
    """
    dados = buscar_dados_completos(usuario_id)
    if not dados:
        return False

    obrigatorios = [
        "nome_completo", "data_nascimento", "cpf",
        "email", "celular", "logradouro", "cidade", "estado"
    ]

    return all(dados.get(campo) for campo in obrigatorios)


def vincular_google_id(usuario_id, google_id, email, avatar_url=None):
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute(
        """
        UPDATE usuarios
        SET google_id = %s, email = %s, avatar_url = %s
        WHERE id = %s
        """,
        (google_id, email, avatar_url, usuario_id)
    )

    conn.commit()
    conn.close()