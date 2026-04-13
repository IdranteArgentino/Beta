"""Gestore per operazioni di modifica e operazioni complesse su progetti."""
from ..database import create_connection
from ..models import StatoProgetto, Progetto, SchedaGiornaliera


class GestoreProgetti:
    """Gestisce modifiche, validazioni e operazioni complesse su progetti."""

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

    def _verifica_duplicati(self, nome_progetto: str) -> None:
        """Verifica se esiste un omonimo e lancia un'eccezione come warning."""
        progetti = self.cercaProgetto(nome_progetto)
        for p in progetti:
            if p.nome_progetto.lower() == nome_progetto.lower():
                raise Exception(f"Attenzione: Esiste già un progetto con il nome '{nome_progetto}'.")

    # ==========================================
    # METODI PUBBLICI UML
    # ==========================================

    def aggiungiProgetto(self, nome_progetto: str, id_cliente: str, indirizzo_cantiere: str, note: str) -> None:
        """Aggiunge un nuovo progetto (alias di creaProgetto senza ritorno)."""
        self.creaProgetto(nome_progetto, int(id_cliente) if id_cliente else 0, indirizzo_cantiere, note)

    def creaProgetto(self, nome_progetto: str, id_cliente: int, indirizzo_cantiere: str, note: str) -> 'Progetto':
        """Crea e restituisce un nuovo progetto. Solleva ValueError se nome vuoto."""
        nome_norm = self._normalizza(nome_progetto)
        if not nome_norm:
            raise ValueError("Il nome del progetto non può essere vuoto")

        indirizzo_norm = self._normalizza(indirizzo_cantiere)

        try:
            self._verifica_duplicati(nome_norm)
        except Exception as w:
            print(w)

        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO progetti (nome_progetto, id_cliente, indirizzo_cantiere, stato, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (nome_norm, int(id_cliente), indirizzo_norm, StatoProgetto.IN_CORSO.value, note)
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return Progetto(new_id, nome_norm, int(id_cliente), indirizzo_norm, note, StatoProgetto.IN_CORSO)

    def cambiaStato(self, id_progetto: int, nuovo_stato: 'StatoProgetto') -> None:
        """Imposta lo stato di un progetto al valore indicato."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("UPDATE progetti SET stato = ? WHERE id = ?", (nuovo_stato.value, id_progetto))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore nel cambio stato progetto: {e}")

    def cambiaStatoProgetto(self, id_progetto: int) -> None:
        """Cambia lo stato di un progetto (toggle tra IN_CORSO e COMPLETATO)."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM progetti WHERE id = ?", (id_progetto,))
            row = cur.fetchone()
            conn.close()
            if not row:
                return
            progetto = Progetto(
                row['id'], row['nome_progetto'], row['id_cliente'],
                row['indirizzo_cantiere'], row['note'], StatoProgetto(row['stato'])
            )
            nuovo_stato = StatoProgetto.COMPLETATO if progetto.stato == StatoProgetto.IN_CORSO else StatoProgetto.IN_CORSO
            self.cambiaStato(id_progetto, nuovo_stato)
        except Exception as e:
            print(f"Errore nel cambio stato progetto: {e}")

    def cercaProgetto(self, termine_ricerca: str) -> list:
        """Cerca progetti attivi/non disattivati per nome, indirizzo cantiere o id."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            query = """
                SELECT * FROM progetti
                WHERE stato != ?
                  AND (nome_progetto LIKE ? OR indirizzo_cantiere LIKE ? OR CAST(id AS TEXT) LIKE ?)
                ORDER BY nome_progetto COLLATE NOCASE ASC
            """
            termine = f"%{(termine_ricerca or '').strip()}%"
            cur.execute(query, (StatoProgetto.DISATTIVO.value, termine, termine, termine))
            rows = cur.fetchall()
            conn.close()

            progetti = []
            for row in rows:

                progetti.append(Progetto(row['id'], row['nome_progetto'], row['id_cliente'],
                                         row['indirizzo_cantiere'], row['note'], StatoProgetto(row['stato'])))
            return progetti
        except Exception as e:
            print(f"Errore nella ricerca progetto: {e}")
            return []

    def costoTotaleProgetto(self, id_progetto: int) -> float:
        """Calcola il costo totale di un progetto."""
        try:
            costo_operai = self._get_costo_operai(id_progetto)
            costo_materiali = self._get_costo_materiali(id_progetto)
            return float(costo_operai + costo_materiali)
        except Exception as e:
            print(f"Errore nel calcolo costo totale: {e}")
            return 0.0

    def dettaglioProgetto(self, id_progetto: int) -> dict:
        """Restituisce i dettagli completi di un progetto."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM progetti WHERE id = ?", (id_progetto,))
            row = cur.fetchone()
            if not row:
                conn.close()
                return {}

            p = Progetto(
                row['id'], row['nome_progetto'], row['id_cliente'],
                row['indirizzo_cantiere'], row['note'], StatoProgetto(row['stato'])
            )

            # Recupera il cliente
            cliente = None
            cur.execute("SELECT * FROM clienti WHERE id = ?", (p.id_cliente,))
            cr = cur.fetchone()
            if cr:
                cliente = {'id': cr['id'], 'ragione_sociale': cr['ragione_sociale']}

            conn.close()

            costo_totale = self.costoTotaleProgetto(id_progetto)
            ore_totali = self._get_totale_ore(id_progetto)
            schede = self.schedeGiornaliereProgetto(id_progetto)

            return {
                "id": p.id,
                "nome_progetto": p.nome_progetto,
                "id_cliente": p.id_cliente,
                "indirizzo_cantiere": p.indirizzo_cantiere,
                "stato": p.stato.value,
                "note": p.note,
                "costo_totale": costo_totale,
                "ore_totali": ore_totali,
                # Chiavi attese dai test
                "progetto": p,
                "cliente": cliente,
                "costoTot": costo_totale,
                "schede": schede,
            }
        except Exception as e:
            print(f"Errore nel recupero dettaglio progetto: {e}")
            return {}

    def modificaProgetto(self, id_progetto: int, nome_progetto: str = None, 
                         id_cliente: int = None, indirizzo_cantiere: str = None, 
                         note: str = None, stato: 'StatoProgetto' = None) -> None:
        """Modifica i dati di un progetto."""
        try:
            if not self._verificaProgettoModificabile(id_progetto):
                return

            conn = self._get_conn()
            cur = conn.cursor()
            updates = []
            params = []

            if nome_progetto is not None:
                updates.append("nome_progetto = ?")
                params.append(self._normalizza(nome_progetto))
            if id_cliente is not None:
                updates.append("id_cliente = ?")
                params.append(id_cliente)
            if indirizzo_cantiere is not None:
                updates.append("indirizzo_cantiere = ?")
                params.append(indirizzo_cantiere)
            if note is not None:
                updates.append("note = ?")
                params.append(note)
            if stato is not None:
                updates.append("stato = ?")
                params.append(stato.value)

            if updates:
                query = f"UPDATE progetti SET {', '.join(updates)} WHERE id = ?"
                params.append(id_progetto)
                cur.execute(query, params)
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore nella modifica progetto: {e}")

    def eliminaProgetto(self, id_progetto: int) -> str:
        """Elimina un progetto: soft delete se ha schede associate, hard delete altrimenti."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()

            cur.execute("SELECT id FROM progetti WHERE id = ?", (id_progetto,))
            if not cur.fetchone():
                conn.close()
                return "not_found"

            if self._ha_schede_associate(cur, id_progetto):
                cur.execute("UPDATE progetti SET stato = ? WHERE id = ?", (StatoProgetto.DISATTIVO.value, id_progetto))
                conn.commit()
                conn.close()
                return "soft_deleted"

            cur.execute("DELETE FROM progetti WHERE id = ?", (id_progetto,))
            conn.commit()
            conn.close()
            return "hard_deleted"
        except Exception as e:
            print(f"Errore nell'eliminazione progetto: {e}")
            return "error"

    def listaProgetto(self) -> list:
        """Restituisce la lista di tutti i progetti non disattivati."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM progetti WHERE stato != ? ORDER BY nome_progetto COLLATE NOCASE ASC",
                (StatoProgetto.DISATTIVO.value,),
            )
            rows = cur.fetchall()
            conn.close()
            return [
                Progetto(
                    row['id'], row['nome_progetto'], row['id_cliente'],
                    row['indirizzo_cantiere'], row['note'], StatoProgetto(row['stato'])
                )
                for row in rows
            ]
        except Exception as e:
            print(f"Errore nel recupero lista progetti: {e}")
            return []

    def listaProgetti(self) -> list:
        """Alias compatibile con le viste web."""
        return self.listaProgetto()

    def schedeGiornaliereProgetto(self, id_progetto: int = None) -> list:
        """Ottiene le schede giornaliere associate al progetto, ordinate per id decrescente (più recenti per inserimento prima)."""
        try:
            if id_progetto is None:
                return []

            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM schede_giornaliere WHERE id_progetto = ? ORDER BY id DESC", (id_progetto,))
            rows = cur.fetchall()
            conn.close()

            return [SchedaGiornaliera(row['id'], row['data'], row['descrizione'], row['id_progetto']) for row in rows]
        except Exception as e:
            print(f"Errore nel recupero schede giornaliere: {e}")
            return []

    # ==========================================
    # METODI PRIVATI
    # ==========================================

    def _get_totale_ore(self, id_progetto: int) -> float:
        """Ottiene le ore totali lavorate su un progetto."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT SUM(ore_lavorate) as tot_ore
                FROM voci_operai v
                JOIN schede_giornaliere s ON v.id_scheda = s.id
                WHERE s.id_progetto = ?
            """, (id_progetto,))
            r = cur.fetchone()
            conn.close()
            return r['tot_ore'] or 0.0
        except Exception as e:
            print(f"Errore nel calcolo ore totali: {e}")
            return 0.0

    def _get_costo_operai(self, id_progetto: int) -> float:
        """Ottiene il costo totale della manodopera su un progetto."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT SUM(ore_lavorate * costo_orario_snapshot) as tot_costo
                FROM voci_operai v
                JOIN schede_giornaliere s ON v.id_scheda = s.id
                WHERE s.id_progetto = ?
            """, (id_progetto,))
            r = cur.fetchone()
            conn.close()
            return r['tot_costo'] or 0.0
        except Exception as e:
            print(f"Errore nel calcolo costo operai: {e}")
            return 0.0

    def _get_costo_materiali(self, id_progetto: int) -> float:
        """Ottiene il costo totale dei materiali su un progetto."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT SUM(quantita * prezzo_unitario_snapshot) as tot_costo
                FROM voci_materiali v
                JOIN schede_giornaliere s ON v.id_scheda = s.id
                WHERE s.id_progetto = ?
            """, (id_progetto,))
            r = cur.fetchone()
            conn.close()
            return r['tot_costo'] or 0.0
        except Exception as e:
            print(f"Errore nel calcolo costo materiali: {e}")
            return 0.0

    def _verificaProgettoModificabile(self, id_progetto: int) -> bool:
        """Un progetto e' modificabile se esiste e non e' COMPLETATO."""
        progetto = self._trova_progetto(id_progetto)
        return bool(progetto and progetto.isModificabile())

    def _trova_progetto(self, id_progetto: int) -> 'Progetto | None':
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM progetti WHERE id = ?", (id_progetto,))
            row = cur.fetchone()
            conn.close()
            if not row:
                return None
            return Progetto(
                row['id'],
                row['nome_progetto'],
                row['id_cliente'],
                row['indirizzo_cantiere'],
                row['note'],
                StatoProgetto(row['stato']),
            )
        except Exception:
            return None

    def _ha_schede_associate(self, cur, id_progetto: int) -> bool:
        cur.execute("SELECT 1 FROM schede_giornaliere WHERE id_progetto = ? LIMIT 1", (id_progetto,))
        return cur.fetchone() is not None

