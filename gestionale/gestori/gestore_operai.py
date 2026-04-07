"""Gestore per operazioni di modifica e operazioni complesse su operai."""
from ..database import create_connection
from ..models import StatoEntita, Operaio, SchedaGiornaliera


class GestoreOperai:
    """Gestisce modifiche, validazioni e operazioni complesse su operai."""
    
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

    def _verifica_duplicati(self, nome: str, cognome: str) -> None:
        """Verifica se esiste un omonimo e lancia un'eccezione come warning."""
        operai = self.cercaOperaio(nome)
        for o in operai:
            if o.nome.lower() == nome.lower() and o.cognome.lower() == cognome.lower():
                raise Exception(f"Attenzione: Rilevato omonimo per l'operaio {nome} {cognome}.")

    # ==========================================
    # METODI PUBBLICI
    # ==========================================

    def aggiungiOperaio(self, nome: str, cognome: str, alias: str,
                        note: str, costo_orario_base: int) -> None:
        """Aggiunge un nuovo operaio."""
        try:
            nome_norm = self._normalizza(nome)
            cognome_norm = self._normalizza(cognome)

            if not self._validoCostoOrario(float(costo_orario_base)):
                print("Costo orario non valido")
                return

            try:
                self._verifica_duplicati(nome_norm, cognome_norm)
            except Exception as w:
                print(w)


            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO operai (nome, cognome, alias, costo_orario_base, stato, note)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (nome_norm, cognome_norm, alias, float(costo_orario_base), StatoEntita.ATTIVO.value, note)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore nell'aggiunta operaio: {e}")

    def cercaOperaio(self, termine_ricerca: str) -> list:
        """Cerca operai per id, nome, cognome, nome completo o alias."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            query = """
                SELECT * FROM operai 
                WHERE nome LIKE ?
                   OR cognome LIKE ?
                   OR alias LIKE ?
                   OR (nome || ' ' || cognome) LIKE ?
                   OR CAST(id AS TEXT) LIKE ?
                ORDER BY cognome COLLATE NOCASE ASC, nome COLLATE NOCASE ASC
            """
            termine = f"%{(termine_ricerca or '').strip()}%"
            cur.execute(query, (termine, termine, termine, termine, termine))
            rows = cur.fetchall()
            conn.close()

            operai = []
            for row in rows:

                operai.append(Operaio(row['id'], row['nome'], row['cognome'], row['alias'],
                                     row['costo_orario_base'], StatoEntita(row['stato']), row['note']))
            return operai
        except Exception as e:
            print(f"Errore nella ricerca operaio: {e}")
            return []

    def listaOperai(self) -> list:
        """Restituisce la lista di tutti gli operai."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM operai ORDER BY cognome COLLATE NOCASE ASC, nome COLLATE NOCASE ASC")
            rows = cur.fetchall()
            conn.close()
            return [
                Operaio(
                    row['id'], row['nome'], row['cognome'], row['alias'],
                    row['costo_orario_base'], StatoEntita(row['stato']), row['note']
                )
                for row in rows
            ]
        except Exception as e:
            print(f"Errore nel recupero lista operai: {e}")
            return []

    def dettaglioOperaio(self, id_operaio: int) -> dict:
        """Restituisce i dettagli completi di un operaio."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM operai WHERE id = ?", (id_operaio,))
            row = cur.fetchone()
            conn.close()
            if not row:
                return {}

            operaio = Operaio(
                row['id'], row['nome'], row['cognome'], row['alias'],
                row['costo_orario_base'], StatoEntita(row['stato']), row['note']
            )
            if not operaio:
                return {}

            storico = self._get_storico_ore(id_operaio)
            ore_per_progetto = self._get_ore_per_progetto(id_operaio)

            return {
                'id': operaio.id,
                'nome': operaio.nome,
                'cognome': operaio.cognome,
                'alias': operaio.alias,
                'costo_orario_base': operaio.costo_orario_base,
                'stato': operaio.stato.value,
                'note': operaio.note,
                'ore_totali': storico['ore_totali'],
                'ricavo_totale': storico['ricavo_totale'],
                'numero_schede': storico['numero_schede'],
                'ore_per_progetto': ore_per_progetto
            }
        except Exception as e:
            print(f"Errore nel recupero dettaglio operaio: {e}")
            return {}

    def modificaOperaio(self, id_operaio: int, nome: str = None, cognome: str = None, 
                        alias: str = None, costo_orario_base: float = None, 
                        note: str = None, stato: StatoEntita = None) -> None:
        """Modifica i dati di un operaio."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            updates = []
            params = []

            if nome is not None:
                updates.append("nome = ?")
                params.append(self._normalizza(nome))
            if cognome is not None:
                updates.append("cognome = ?")
                params.append(self._normalizza(cognome))
            if alias is not None:
                updates.append("alias = ?")
                params.append(alias)
            if costo_orario_base is not None:
                if not self._validoCostoOrario(float(costo_orario_base)):
                    print("Costo orario non valido per la modifica")
                else:
                    updates.append("costo_orario_base = ?")
                    params.append(float(costo_orario_base))
            if note is not None:
                updates.append("note = ?")
                params.append(note)
            if stato is not None:
                updates.append("stato = ?")
                params.append(stato.value)

            if updates:
                query = f"UPDATE operai SET {', '.join(updates)} WHERE id = ?"
                params.append(id_operaio)
                cur.execute(query, params)
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore nella modifica operaio: {e}")

    def eliminaOperaio(self, id_operaio: int) -> None:
        """Elimina un operaio."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM operai WHERE id = ?", (id_operaio,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore nell'eliminazione operaio: {e}")

    def storicoOreOperaio(self, id_operaio: int) -> list:
        """Ottiene lo storico delle schede giornaliere di un operaio."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT s.*
                FROM schede_giornaliere s
                JOIN voci_operai v ON s.id = v.id_scheda
                WHERE v.id_operaio = ?
                ORDER BY s.data DESC
            """, (id_operaio,))
            rows = cur.fetchall()
            conn.close()

            schede = []
            for row in rows:

                scheda = SchedaGiornaliera(row['id'], row['data'], row['descrizione'], row['id_progetto'])
                schede.append(scheda)
            return schede
        except Exception as e:
            print(f"Errore nel recupero storico ore: {e}")
            return []

    def totaleOrePerPeriodoTempo(self, id_operaio: int) -> int:
        """Calcola il totale ore (es. mese corrente) per l'operaio."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()

            query = """
                SELECT SUM(ore_lavorate) as tot_ore
                FROM voci_operai v
                JOIN schede_giornaliere s ON v.id_scheda = s.id
                WHERE v.id_operaio = ? 
                AND strftime('%Y-%m', s.data) = strftime('%Y-%m', 'now')
            """
            cur.execute(query, (id_operaio,))
            r = cur.fetchone()
            conn.close()
            return int(r['tot_ore'] or 0)
        except Exception as e:
            print(f"Errore nel calcolo ore per periodo: {e}")
            return 0

    # ==========================================
    # METODI PRIVATI
    # ==========================================

    def _validoCostoOrario(self, costo: float) -> bool:
        """Valida il costo orario (deve essere positivo)."""
        try:
            return isinstance(costo, (int, float)) and costo > 0
        except Exception as e:
            print(f"Errore nella validazione costo orario: {e}")
            return False

    def _get_storico_ore(self, id_operaio: int) -> dict:
        """Ottiene lo storico ore e ricavi di un operaio."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    SUM(ore_lavorate) as tot_ore, 
                    SUM(ore_lavorate * costo_orario_snapshot) as tot_ricavo,
                    COUNT(DISTINCT id_scheda) as num_schede
                FROM voci_operai 
                WHERE id_operaio = ?
            """, (id_operaio,))
            r = cur.fetchone()
            conn.close()
            return {
                "ore_totali": r['tot_ore'] or 0.0,
                "ricavo_totale": r['tot_ricavo'] or 0.0,
                "numero_schede": r['num_schede'] or 0
            }
        except Exception as e:
            print(f"Errore nel recupero storico ore: {e}")
            return {"ore_totali": 0.0, "ricavo_totale": 0.0, "numero_schede": 0}
    
    def _get_ore_per_progetto(self, id_operaio: int) -> dict:
        """Ottiene le ore lavorate per ogni progetto da un operaio."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    p.id,
                    p.nome_progetto,
                    SUM(v.ore_lavorate) as ore,
                    SUM(v.ore_lavorate * v.costo_orario_snapshot) as ricavo
                FROM voci_operai v
                JOIN schede_giornaliere s ON v.id_scheda = s.id
                JOIN progetti p ON s.id_progetto = p.id
                WHERE v.id_operaio = ?
                GROUP BY p.id, p.nome_progetto
                ORDER BY p.nome_progetto
            """, (id_operaio,))
            rows = cur.fetchall()
            conn.close()
            return {row['id']: {
                'nome': row['nome_progetto'],
                'ore': row['ore'] or 0.0,
                'ricavo': row['ricavo'] or 0.0
            } for row in rows}
        except Exception as e:
            print(f"Errore nel recupero ore per progetto: {e}")
            return {}


