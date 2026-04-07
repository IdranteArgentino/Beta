"""Gestore per operazioni di modifica e operazioni complesse su clienti."""
from ..database import create_connection
from ..models import StatoEntita, Cliente


class GestoreClienti:
    """Gestisce modifiche, validazioni e operazioni complesse su clienti."""

    def __init__(self, azienda):
        self.azienda = azienda
        self.db_path = azienda.db_path

    def _normalizza(self, testo: str) -> str:
        """Normalizza una stringa (trim e capitalize)."""
        if not testo:
            return ""
        return " ".join(word.capitalize() for word in testo.strip().split())

    def _get_conn(self):
        return create_connection(self.db_path)

    def _verifica_duplicati(self, ragione_sociale: str) -> None:
        """Verifica se esiste un omonimo e lancia un'eccezione (warning)."""
        clienti = self.cercaCliente(ragione_sociale)
        if clienti:
            raise Exception("Attenzione: Rilevato possibile omonimo o duplicato per il cliente.")

    # ==========================================
    # METODI PUBBLICI
    # ==========================================

    def aggiungiCliente(self, ragione_sociale: str, indirizzo: str = "", telefono: str = "",
                        note: str = "", nome: str = "", cognome: str = "") -> dict:
        """Aggiunge un nuovo cliente. Restituisce {'cliente': Cliente, 'warning': str}."""
        warning = ""
        try:
            ragione_sociale_norm = self._normalizza(ragione_sociale)
            nome_norm = self._normalizza(nome)
            cognome_norm = self._normalizza(cognome)
            indirizzo_norm = self._normalizza(indirizzo)

            try:
                self._verifica_duplicati(ragione_sociale_norm)
            except Exception as w:
                warning = str(w)
                print(w)

            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO clienti (ragione_sociale, nome, cognome, indirizzo, telefono, note, stato)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (ragione_sociale_norm, nome_norm, cognome_norm, indirizzo_norm, telefono, note, StatoEntita.ATTIVO.value)
            )
            conn.commit()
            new_id = cur.lastrowid
            conn.close()
            cliente = Cliente(new_id, ragione_sociale_norm, nome_norm, cognome_norm,
                              indirizzo_norm, telefono, note, StatoEntita.ATTIVO)
            return {"cliente": cliente, "warning": warning}
        except Exception as e:
            print(f"Errore nell'aggiunta cliente: {e}")
            return {"cliente": None, "warning": warning}

    def cercaCliente(self, termine_ricerca: str):
        """Cerca clienti per ragione sociale o id."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            termine = (termine_ricerca or "").strip()
            like_term = f"%{termine}%"
            query = """
                SELECT * FROM clienti
                WHERE ragione_sociale LIKE ? OR CAST(id AS TEXT) LIKE ? OR nome LIKE ? OR cognome LIKE ?
                ORDER BY ragione_sociale COLLATE NOCASE ASC
            """
            cur.execute(query, (like_term, like_term, like_term, like_term))
            rows = cur.fetchall()
            conn.close()
            return [
                Cliente(
                    row['id'], row['ragione_sociale'], row['nome'] or '', row['cognome'] or '', row['indirizzo'],
                    row['telefono'], row['note'], StatoEntita(row['stato'])
                )
                for row in rows
            ]
        except Exception as e:
            print(f"Errore nella ricerca cliente: {e}")
            return []

    def listaClienti(self) -> list:
        """Restituisce la lista di tutti i clienti."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM clienti ORDER BY ragione_sociale COLLATE NOCASE ASC")
            rows = cur.fetchall()
            conn.close()
            return [
                Cliente(
                    row['id'], row['ragione_sociale'], row['nome'] or '', row['cognome'] or '', row['indirizzo'],
                    row['telefono'], row['note'], StatoEntita(row['stato'])
                )
                for row in rows
            ]
        except Exception as e:
            print(f"Errore nel recupero lista clienti: {e}")
            return []

    def dettaglioCliente(self, id_cliente: int) -> dict:
        """Restituisce i dettagli completi di un cliente."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM clienti WHERE id = ?", (id_cliente,))
            row = cur.fetchone()
            if not row:
                conn.close()
                return {}

            cliente = Cliente(
                row['id'], row['ragione_sociale'], row['nome'] or '', row['cognome'] or '', row['indirizzo'],
                row['telefono'], row['note'], StatoEntita(row['stato'])
            )
            if not cliente:
                return {}

            cur.execute("SELECT id, nome_progetto FROM progetti WHERE id_cliente = ?", (id_cliente,))
            progetti_rows = cur.fetchall()
            conn.close()
            progetti = [{'id': p['id'], 'nome': p['nome_progetto']} for p in progetti_rows]

            return {
                'id': cliente.id,
                'ragione_sociale': cliente.ragione_sociale,
                'nome': cliente.nome,
                'cognome': cliente.cognome,
                'indirizzo': cliente.indirizzo,
                'telefono': cliente.telefono,
                'note': cliente.note,
                'stato': cliente.stato.value,
                'numero_progetti': len(progetti),
                'progetti': progetti
            }
        except Exception as e:
            print(f"Errore nel recupero dettaglio cliente: {e}")
            return {}

    def modificaCliente(self, id_cliente: int, updates: dict = None, ragione_sociale: str = None,
                        nome: str = None, cognome: str = None, indirizzo: str = None,
                        telefono: str = None, note: str = None, stato: StatoEntita = None) -> None:
        """Modifica i dati di un cliente. Accetta dict come secondo parametro o kwargs."""
        try:
            if updates and isinstance(updates, dict):
                ragione_sociale = updates.get("ragione_sociale", ragione_sociale)
                nome = updates.get("nome", nome)
                cognome = updates.get("cognome", cognome)
                indirizzo = updates.get("indirizzo", indirizzo)
                telefono = updates.get("telefono", telefono)
                note = updates.get("note", note)
                if "stato" in updates:
                    stato = StatoEntita(updates["stato"]) if isinstance(updates["stato"], str) else updates["stato"]

            conn = self._get_conn()
            cur = conn.cursor()
            update_parts = []
            params = []

            if ragione_sociale is not None:
                update_parts.append("ragione_sociale = ?")
                params.append(ragione_sociale)
            if nome is not None:
                update_parts.append("nome = ?")
                params.append(nome)
            if cognome is not None:
                update_parts.append("cognome = ?")
                params.append(cognome)
            if indirizzo is not None:
                update_parts.append("indirizzo = ?")
                params.append(indirizzo)
            if telefono is not None:
                update_parts.append("telefono = ?")
                params.append(telefono)
            if note is not None:
                update_parts.append("note = ?")
                params.append(note)
            if stato is not None:
                update_parts.append("stato = ?")
                params.append(stato.value)

            if update_parts:
                query = f"UPDATE clienti SET {', '.join(update_parts)} WHERE id = ?"
                params.append(id_cliente)
                cur.execute(query, params)
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore nella modifica cliente: {e}")

    def eliminaCliente(self, id_cliente: int) -> None:
        """Elimina un cliente."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM clienti WHERE id = ?", (id_cliente,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore nell'eliminazione cliente: {e}")

