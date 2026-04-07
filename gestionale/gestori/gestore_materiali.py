"""Gestore per operazioni di modifica e operazioni complesse su materiali."""
from ..database import create_connection
from ..models import (StatoEntita, Materiale)


class GestoreMateriali:
    """Gestisce modifiche, validazioni e operazioni complesse su materiali."""

    def __init__(self, azienda):
        self.azienda = azienda
        self.db_path = azienda.db_path

    def _normalizza(self, testo: str) -> str:
        """Normalizza una stringa (trim e capitalize)."""
        if not testo:
            return ""
        return " ".join(word.capitalize() for word in testo.strip().split())

    def _verifica_duplicati(self, descrizione: str) -> None:
        """Verifica se esiste e lancia un'eccezione bloccante per i materiali."""
        materiali = self.cercaMateriale(descrizione)
        for m in materiali:
            if m.descrizione.lower() == descrizione.lower():
                raise ValueError("Blocco: Esiste già un materiale con questa descrizione.")

    # ==========================================
    # METODI PUBBLICI
    # ==========================================

    def aggiungiMateriale(self, descrizione: str, unita_misura: str, prezzo_unitario: int,
                          note: str, unitaDiMisura : str) -> None:
        """Aggiunge un nuovo materiale al catalogo."""
        try:
            desc_norm = self._normalizza(descrizione)

            try:
                self._verifica_duplicati(desc_norm)
            except ValueError as e:
                print(e)
                return  # Blocca l'inserimento

            if not self._validaPrezzo(float(prezzo_unitario)):
                print("Prezzo non valido")
                return

            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO materiali (descrizione, unita_misura, prezzo_unitario_base, stato, note)
                VALUES (?, ?, ?, ?, ?)
                """,
                (desc_norm, unita_misura, float(prezzo_unitario), StatoEntita.ATTIVO.value, note)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore nell'aggiunta materiale: {e}")

    def cercaMateriale(self, termine_ricerca: str) -> list:
        """Cerca materiali per descrizione o id."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            query = """
                SELECT * FROM materiali 
                WHERE descrizione LIKE ? OR CAST(id AS TEXT) LIKE ?
                ORDER BY descrizione COLLATE NOCASE ASC
            """
            termine = f"%{(termine_ricerca or '').strip()}%"
            cur.execute(query, (termine, termine))
            rows = cur.fetchall()
            conn.close()

            materiali = []
            for row in rows:
                materiali.append(Materiale(row['id'], row['descrizione'], row['unita_misura'],
                                          row['prezzo_unitario_base'], StatoEntita(row['stato']),
                                          row['note']))
            return materiali
        except Exception as e:
            print(f"Errore nella ricerca materiale: {e}")
            return []

    def listaMateriali(self) -> list:
        """Restituisce la lista di tutti i materiali."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM materiali ORDER BY descrizione COLLATE NOCASE ASC")
            rows = cur.fetchall()
            conn.close()
            return [
                Materiale(
                    row['id'], row['descrizione'], row['unita_misura'],
                    row['prezzo_unitario_base'], StatoEntita(row['stato']), row['note']
                )
                for row in rows
            ]
        except Exception as e:
            print(f"Errore nel recupero lista materiali: {e}")
            return []

    def dettaglioMateriale(self, id_materiale: int) -> dict:
        """Restituisce i dettagli completi di un materiale."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM materiali WHERE id = ?", (id_materiale,))
            row = cur.fetchone()
            conn.close()
            if not row:
                return {}

            materiale = Materiale(
                row['id'], row['descrizione'], row['unita_misura'],
                row['prezzo_unitario_base'], StatoEntita(row['stato']), row['note']
            )
            if not materiale:
                return {}

            storico = self._get_storico_utilizzo(id_materiale)
            utilizzo_per_progetto = self._get_utilizzo_per_progetto(id_materiale)

            return {
                'id': materiale.id,
                'descrizione': materiale.descrizione,
                'unita_misura': materiale.unita_misura,
                'prezzo_unitario_base': materiale.prezzo_unitario_base,
                'stato': materiale.stato.value,
                'note': materiale.note,
                'quantita_totale': storico['quantita_totale'],
                'costo_totale': storico['costo_totale'],
                'numero_schede': storico['numero_schede'],
                'utilizzo_per_progetto': utilizzo_per_progetto
            }
        except Exception as e:
            print(f"Errore nel recupero dettaglio materiale: {e}")
            return {}

    def modificaMateriale(self, id_materiale: int, descrizione: str = None, 
                          unita_misura: str = None, prezzo_unitario_base: float = None, 
                          note: str = None, stato: StatoEntita = None) -> None:
        """Modifica i dati di un materiale."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            updates = []
            params = []

            if descrizione is not None:
                updates.append("descrizione = ?")
                params.append(self._normalizza(descrizione))
            if unita_misura is not None:
                updates.append("unita_misura = ?")
                params.append(unita_misura)
            if prezzo_unitario_base is not None:
                if not self._validaPrezzo(float(prezzo_unitario_base)):
                    print("Prezzo non valido per la modifica")
                else:
                    updates.append("prezzo_unitario_base = ?")
                    params.append(float(prezzo_unitario_base))
            if note is not None:
                updates.append("note = ?")
                params.append(note)
            if stato is not None:
                updates.append("stato = ?")
                params.append(stato.value)

            if updates:
                query = f"UPDATE materiali SET {', '.join(updates)} WHERE id = ?"
                params.append(id_materiale)
                cur.execute(query, params)
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore nella modifica materiale: {e}")

    def eliminaMateriale(self, id_materiale: int) -> None:
        """Elimina un materiale."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM materiali WHERE id = ?", (id_materiale,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore nell'eliminazione materiale: {e}")

    # ==========================================
    # METODI PRIVATI
    # ==========================================

    def _validaPrezzo(self, prezzo: float) -> bool:
        """Valida il prezzo (deve essere positivo)."""
        try:
            return isinstance(prezzo, (int, float)) and prezzo > 0
        except Exception as e:
            print(f"Errore nella validazione prezzo: {e}")
            return False

    def _get_conn(self):
        return create_connection(self.db_path)

    def _get_storico_utilizzo(self, id_materiale: int) -> dict:
        """Ottiene lo storico di utilizzo di un materiale."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    SUM(quantita) as tot_quantita,
                    SUM(quantita * prezzo_unitario_snapshot) as tot_costo,
                    COUNT(DISTINCT id_scheda) as num_schede
                FROM voci_materiali
                WHERE id_materiale = ?
            """, (id_materiale,))
            r = cur.fetchone()
            conn.close()
            return {
                "quantita_totale": r['tot_quantita'] or 0.0,
                "costo_totale": r['tot_costo'] or 0.0,
                "numero_schede": r['num_schede'] or 0
            }
        except Exception as e:
            print(f"Errore nel recupero storico utilizzo: {e}")
            return {"quantita_totale": 0.0, "costo_totale": 0.0, "numero_schede": 0}

    def _get_utilizzo_per_progetto(self, id_materiale: int) -> dict:
        """Ottiene l'utilizzo di un materiale per ogni progetto."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    p.id,
                    p.nome_progetto,
                    SUM(v.quantita) as quantita,
                    SUM(v.quantita * v.prezzo_unitario_snapshot) as costo
                FROM voci_materiali v
                JOIN schede_giornaliere s ON v.id_scheda = s.id
                JOIN progetti p ON s.id_progetto = p.id
                WHERE v.id_materiale = ?
                GROUP BY p.id, p.nome_progetto
                ORDER BY p.nome_progetto
            """, (id_materiale,))
            rows = cur.fetchall()
            conn.close()
            return {row['id']: {
                'nome': row['nome_progetto'],
                'quantita': row['quantita'] or 0.0,
                'costo': row['costo'] or 0.0
            } for row in rows}
        except Exception as e:
            print(f"Errore nel recupero utilizzo per progetto: {e}")
            return {}

