"""Gestore per operazioni di modifica e operazioni complesse su utenti."""
from ..database import create_connection
from ..models import Utente, StatoEntita, RuoloUtente
from werkzeug.security import generate_password_hash, check_password_hash


class GestoreUtenti:
    """Gestisce modifiche, validazioni e operazioni complesse su utenti."""

    def __init__(self, azienda):
        self.azienda = azienda
        self.db_path = azienda.db_path

    def _get_conn(self):
        return create_connection(self.db_path)

    def _normalizza(self, testo: str) -> str:
        """Normalizza una stringa (trim e capitalize)."""
        if not testo:
            return ""
        return " ".join(word.capitalize() for word in testo.strip().split())

    def _trova_utente(self, username: str):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM utenti WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return Utente(
            row['id'], row['username'], row['nome'], row['cognome'],
            row['password_hash'], StatoEntita(row['stato']), RuoloUtente(row['ruolo'])
        )

    # ==========================================
    # METODI PUBBLICI
    # ==========================================

    def login(self, username: str, password: str) -> Utente:
        """Autentica un utente con username e password. Solleva ValueError su fallimento."""
        utente = self._trova_utente(username)
        if not utente:
            raise ValueError(f"Utente '{username}' non trovato")
        if not self._verificaPassword(password, utente.password):
            raise ValueError("Password non corretta")
        if utente.stato != StatoEntita.ATTIVO:
            raise ValueError("Utente disattivato")
        return utente

    def aggiungiUtente(self, username: str, nome: str, cognome: str,
                       ruolo: RuoloUtente, utente_creatore: Utente) -> Utente:
        """Aggiunge un nuovo utente al sistema (richiede admin) e restituisce l'utente creato."""
        if getattr(utente_creatore, 'ruolo', None) != RuoloUtente.ADMIN:
            raise PermissionError("Permesso negato: solo amministratori possono aggiungere utenti")

        username_clean = (username or "").strip()
        nome_norm = self._normalizza(nome)
        cognome_norm = self._normalizza(cognome)

        if not username_clean:
            raise ValueError("Username obbligatorio")
        if not nome_norm or not cognome_norm:
            raise ValueError("Nome e cognome sono obbligatori")

        ruolo_finale = ruolo if isinstance(ruolo, RuoloUtente) else RuoloUtente.STAFF

        # Password iniziale coerente con il reset forzato.
        password_iniziale = "cambiami123"
        password_hash = self._hashPassword(password_iniziale)

        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM utenti WHERE username = ?", (username_clean,))
            if cur.fetchone():
                raise ValueError(f"Username '{username_clean}' gia' esistente")

            cur.execute(
                """
                INSERT INTO utenti (username, nome, cognome, password_hash, stato, ruolo)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    username_clean,
                    nome_norm,
                    cognome_norm,
                    password_hash,
                    StatoEntita.ATTIVO.value,
                    ruolo_finale.value,
                ),
            )
            conn.commit()
            new_id = cur.lastrowid
            return Utente(new_id, username_clean, nome_norm, cognome_norm, password_hash, StatoEntita.ATTIVO, ruolo_finale)
        finally:
            conn.close()

    def cambiaPasswordUtente(self, utente: Utente, password_vecchia: str,
                             password_nuova: str, password_conferma: str) -> tuple[bool, str]:
        """Cambia la password di un utente dopo verifica della vecchia password."""
        try:
            if not utente:
                return False, "Utente non valido."

            if not self._verificaPassword(password_vecchia or "", utente.password):
                return False, "Password attuale non corretta."

            if password_nuova != password_conferma:
                return False, "Le password non coincidono."

            if not self._validaPassword(password_nuova or ""):
                return False, "Nuova password non valida (minimo 6 caratteri e almeno 1 numero)."

            password_hash = self._hashPassword(password_nuova)
            self.modificaUtente(utente.username, password_hash=password_hash)
            return True, "Password aggiornata correttamente."
        except Exception as e:
            print(f"Errore nel cambio password: {e}")
            return False, "Errore durante l'aggiornamento password."

    def modificaPassword(self, utente: Utente, password_vecchia: str,
                         password_nuova: str, password_conferma: str) -> None:
        """Alias di cambiaPasswordUtente per compatibilità test."""
        self.cambiaPasswordUtente(utente, password_vecchia, password_nuova, password_conferma)

    def resetForzatoPassword(self, username: str, utente_admin: Utente = None) -> None:
        """Reset forzato della password (admin) oppure reset senza controlli."""
        try:
            if utente_admin is not None and getattr(utente_admin, 'ruolo', None) != RuoloUtente.ADMIN:
                print("Permesso negato: solo amministratori possono fare il reset")
                return

            password_hash = self._hashPassword("cambiami123")
            self.modificaUtente(username, password_hash=password_hash)
        except Exception as e:
            print(f"Errore nel reset password: {e}")

    def cercaUtente(self, termine_ricerca: str, utente_richiedente: Utente) -> list:
        """Cerca utenti attivi per username, nome o cognome."""
        try:
            if getattr(utente_richiedente, 'ruolo', None) != RuoloUtente.ADMIN:
                print("Permesso negato: solo amministratori")
                return []

            conn = self._get_conn()
            cur = conn.cursor()
            query = """
                SELECT * FROM utenti
                WHERE stato = ? AND (username LIKE ? OR nome LIKE ? OR cognome LIKE ?)
            """
            termine = f"%{termine_ricerca}%"
            cur.execute(query, (StatoEntita.ATTIVO.value, termine, termine, termine))
            rows = cur.fetchall()
            conn.close()

            utenti = []
            for row in rows:
                ruolo = RuoloUtente(row['ruolo'])
                stato = StatoEntita(row['stato'])

                utenti.append(Utente(row['id'], row['username'], row['nome'], row['cognome'], row['password_hash'], stato, ruolo))
            return utenti
        except Exception as e:
            print(f"Errore nella ricerca utente: {e}")
            return []

    def listaUtenti(self, utente_richiedente: Utente = None) -> list:
        """Restituisce la lista di tutti gli utenti attivi (solo admin se utente_richiedente specificato)."""
        try:
            if utente_richiedente is not None and getattr(utente_richiedente, 'ruolo', None) != RuoloUtente.ADMIN:
                print("Permesso negato: solo amministratori")
                return []
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM utenti WHERE stato = ?", (StatoEntita.ATTIVO.value,))
            rows = cur.fetchall()
            conn.close()
            return [
                Utente(
                    row['id'], row['username'], row['nome'], row['cognome'],
                    row['password_hash'], StatoEntita(row['stato']), RuoloUtente(row['ruolo'])
                )
                for row in rows
            ]
        except Exception as e:
            print(f"Errore nel recupero lista utenti: {e}")
            return []

    def dettaglioUtente(self, id_utente: int) -> dict:
        """Restituisce i dettagli di un utente."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM utenti WHERE id = ?", (id_utente,))
            row = cur.fetchone()
            conn.close()
            if not row:
                return {}

            return {
                'id': row['id'],
                'username': row['username'],
                'nome': row['nome'],
                'cognome': row['cognome'],
                'stato': row['stato'],
                'ruolo': row['ruolo']
            }
        except Exception as e:
            print(f"Errore nel recupero dettaglio utente: {e}")
            return {}

    def revocaUtente(self, username: str, utente_admin: Utente) -> None:
        """Revoca un utente (lo disattiva). Solleva PermissionError se non admin, ValueError se self-revoke."""
        if getattr(utente_admin, 'ruolo', None) != RuoloUtente.ADMIN:
            raise PermissionError("Permesso negato: solo amministratori possono revocare utenti")
        if getattr(utente_admin, 'username', None) == username:
            raise ValueError("Non è possibile revocare se stessi")
        self.modificaUtente(username, stato=StatoEntita.DISATTIVATO)

    def riattivaUtente(self, username: str, utente_admin: Utente) -> None:
        """Riattiva un utente. Solleva PermissionError se non admin."""
        if getattr(utente_admin, 'ruolo', None) != RuoloUtente.ADMIN:
            raise PermissionError("Permesso negato: solo amministratori possono riattivare utenti")
        self.modificaUtente(username, stato=StatoEntita.ATTIVO)

    def eliminaUtente(self, username: str, utente_corrente: Utente) -> str:
        """Elimina definitivamente un utente dal sistema (solo admin, no self-delete)."""
        if getattr(utente_corrente, 'ruolo', None) != RuoloUtente.ADMIN:
            raise PermissionError("Permesso negato: solo amministratori possono eliminare utenti")
        if getattr(utente_corrente, 'username', None) == username:
            raise ValueError("Non e' possibile eliminare il proprio account")

        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id FROM utenti WHERE username = ?", (username,))
            if not cur.fetchone():
                conn.close()
                return "not_found"

            cur.execute("DELETE FROM utenti WHERE username = ?", (username,))
            conn.commit()
            conn.close()
            return "hard_deleted"
        except Exception as e:
            print(f"Errore nell'eliminazione utente: {e}")
            return "error"

    def modificaUtente(self, username: str, nome: str = None, cognome: str = None,
                 password_hash: str = None, stato: StatoEntita = None,
                 ruolo: RuoloUtente = None, nuovo_username: str = None,
                 utente_richiedente: Utente = None) -> None:
        """Modifica i dati di un utente."""
        try:
            if utente_richiedente and getattr(utente_richiedente, 'username', None) == username:
                # Un utente non può auto-degradarsi né disattivarsi.
                ruolo = None
                stato = None
                nuovo_username = None

            conn = self._get_conn()
            cur = conn.cursor()
            updates = []
            params = []

            if nome is not None:
                updates.append("nome = ?")
                params.append(nome)
            if cognome is not None:
                updates.append("cognome = ?")
                params.append(cognome)
            if password_hash is not None:
                updates.append("password_hash = ?")
                params.append(password_hash)
            if stato is not None:
                updates.append("stato = ?")
                params.append(stato.value)
            if ruolo is not None:
                updates.append("ruolo = ?")
                params.append(ruolo.value)
            if nuovo_username is not None:
                updates.append("username = ?")
                params.append(nuovo_username)

            if not updates:
                conn.close()
                return

            params.append(username)
            query = f"UPDATE utenti SET {', '.join(updates)} WHERE username = ?"
            cur.execute(query, params)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore nella modifica utente: {e}")

    # ==========================================
    # METODI PRIVATI
    # ==========================================

    def _hashPassword(self, password: str) -> str:
        """Genera l'hash sicuro della password usando werkzeug (pbkdf2)."""
        return generate_password_hash(password)

    def _verificaPassword(self, password: str, password_hash: str) -> bool:
        """Verifica se la password corrisponde all'hash.
        Supporta sia hash werkzeug (pbkdf2) che hash SHA256 legacy (migrazione trasparente)."""
        try:
            # Prova prima con werkzeug (hash moderno)
            if check_password_hash(password_hash, password):
                return True
            # Fallback: hash SHA256 legacy (64 caratteri hex)
            if len(password_hash) == 64:
                import hashlib
                return hashlib.sha256(password.encode()).hexdigest() == password_hash
            return False
        except Exception:
            return False

    def _validaPassword(self, password: str) -> bool:
        """Valida la password (lunghezza minima, caratteri speciali, ecc)."""
        try:
            # Minimo 6 caratteri
            if len(password) < 6:
                return False
            # Deve contenere almeno un numero
            if not any(c.isdigit() for c in password):
                return False
            return True
        except Exception as e:
            print(f"Errore nella validazione password: {e}")
            return False
