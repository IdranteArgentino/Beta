import sqlite3
import os
from werkzeug.security import generate_password_hash

def create_connection(db_file="data/gestionale.db"):
    """Crea una connessione al database SQLite."""
    # Assicura che la directory esista
    os.makedirs(os.path.dirname(db_file), exist_ok=True)
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = 1") # Forza le FK
    # Permette l'accesso alle colonne come dict
    conn.row_factory = sqlite3.Row 
    return conn

def inizializza_db(db_file="data/gestionale.db"):
    """Crea tutte le tabelle se non esistono e inserisce l'Admin di default."""
    conn = create_connection(db_file)
    cursor = conn.cursor()

    # Tabella Utenti
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS utenti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        nome TEXT NOT NULL,
        cognome TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        stato TEXT NOT NULL,
        ruolo TEXT NOT NULL
    )
    """)

    # Tabella Clienti
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clienti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ragione_sociale TEXT NOT NULL,
        nome TEXT,
        cognome TEXT,
        indirizzo TEXT,
        telefono TEXT,
        note TEXT,
        stato TEXT NOT NULL
    )
    """)

    # Migration: aggiungi colonne nome e cognome se non esistono
    try:
        cursor.execute("ALTER TABLE clienti ADD COLUMN nome TEXT")
    except:
        pass  # Colonna già esiste
    try:
        cursor.execute("ALTER TABLE clienti ADD COLUMN cognome TEXT")
    except:
        pass  # Colonna già esiste

    # Tabella Operai
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operai (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cognome TEXT NOT NULL,
        alias TEXT,
        costo_orario_base REAL NOT NULL,
        stato TEXT NOT NULL,
        note TEXT
    )
    """)

    # Tabella Materiali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materiali (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descrizione TEXT UNIQUE NOT NULL,
        unita_misura TEXT NOT NULL,
        prezzo_unitario_base REAL NOT NULL,
        stato TEXT NOT NULL,
        note TEXT
    )
    """)

    # Tabella Progetti
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS progetti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_progetto TEXT NOT NULL,
        id_cliente INTEGER NOT NULL,
        indirizzo_cantiere TEXT,
        stato TEXT NOT NULL,
        note TEXT,
        FOREIGN KEY (id_cliente) REFERENCES clienti (id)
    )
    """)

    # Tabella Schede Giornaliere
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schede_giornaliere (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        descrizione TEXT,
        id_progetto INTEGER NOT NULL,
        FOREIGN KEY (id_progetto) REFERENCES progetti (id)
    )
    """)

    # Tabella Voce Operai (Associazione M:N con Snapshot Costo)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS voci_operai (
        id_scheda INTEGER NOT NULL,
        id_operaio INTEGER NOT NULL,
        ore_lavorate REAL NOT NULL,
        costo_orario_snapshot REAL NOT NULL,
        PRIMARY KEY (id_scheda, id_operaio),
        FOREIGN KEY (id_scheda) REFERENCES schede_giornaliere (id) ON DELETE CASCADE,
        FOREIGN KEY (id_operaio) REFERENCES operai (id)
    )
    """)

    # Tabella Voce Materiali (Associazione M:N con Snapshot Prezzo)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS voci_materiali (
        id_scheda INTEGER NOT NULL,
        id_materiale INTEGER NOT NULL,
        quantita REAL NOT NULL,
        prezzo_unitario_snapshot REAL NOT NULL,
        PRIMARY KEY (id_scheda, id_materiale),
        FOREIGN KEY (id_scheda) REFERENCES schede_giornaliere (id) ON DELETE CASCADE,
        FOREIGN KEY (id_materiale) REFERENCES materiali (id)
    )
    """)

    # Tabella Allegati
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS allegati (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_scheda INTEGER NOT NULL,
        path TEXT NOT NULL,
        FOREIGN KEY (id_scheda) REFERENCES schede_giornaliere (id) ON DELETE CASCADE
    )
    """)

    # ===== CREAZIONE INDICI PER PERFORMANCE =====
    
    # Indici su Clienti
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clienti_ragione_sociale ON clienti(ragione_sociale COLLATE NOCASE)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clienti_nome ON clienti(nome COLLATE NOCASE)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clienti_cognome ON clienti(cognome COLLATE NOCASE)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clienti_stato ON clienti(stato)")
    
    # Indici su Operai
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_operai_nome ON operai(nome COLLATE NOCASE)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_operai_cognome ON operai(cognome COLLATE NOCASE)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_operai_alias ON operai(alias COLLATE NOCASE)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_operai_stato ON operai(stato)")
    
    # Indici su Materiali
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_materiali_descrizione ON materiali(descrizione COLLATE NOCASE)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_materiali_stato ON materiali(stato)")
    
    # Indici su Progetti
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_progetti_nome ON progetti(nome_progetto COLLATE NOCASE)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_progetti_cliente ON progetti(id_cliente)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_progetti_stato ON progetti(stato)")
    
    # Indici su Schede Giornaliere
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_schede_data ON schede_giornaliere(data)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_schede_progetto ON schede_giornaliere(id_progetto)")
    
    # Indici su Utenti
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_utenti_username ON utenti(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_utenti_ruolo ON utenti(ruolo)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_utenti_stato ON utenti(stato)")
    
    # Indici su Voci Operai e Materiali
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_voci_operai_scheda ON voci_operai(id_scheda)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_voci_materiali_scheda ON voci_materiali(id_scheda)")

    # Admin di default
    cursor.execute("SELECT id FROM utenti WHERE username = ?", ('admin',))
    res = cursor.fetchone()
    pwd_hash = generate_password_hash("admin")
    if res is None:
        cursor.execute("""
            INSERT INTO utenti (username, nome, cognome, password_hash, stato, ruolo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('admin', 'Amministratore', 'Sistema', pwd_hash, 'ATTIVO', 'ADMIN'))
    else:
        cursor.execute("""
            UPDATE utenti
            SET nome = ?, cognome = ?, password_hash = ?, stato = ?, ruolo = ?
            WHERE username = ?
        """, ('Amministratore', 'Sistema', pwd_hash, 'ATTIVO', 'ADMIN', 'admin'))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    inizializza_db()
    print("Database inizializzato correttamente.")
