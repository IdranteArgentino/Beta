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

    def aggiungiOperaio(self, nome: str, cognome: str, costo_orario_base: float,
                        alias: str = "", note: str = "") -> dict:
        """Aggiunge un nuovo operaio. Restituisce {'operaio': Operaio, 'warning': str}. Solleva ValueError se costo invalido."""
        warning = ""
        try:
            nome_norm = self._normalizza(nome)
            cognome_norm = self._normalizza(cognome)

            if not self._validoCostoOrario(float(costo_orario_base)):
                raise ValueError(f"Costo orario non valido: {costo_orario_base}")

            try:
                self._verifica_duplicati(nome_norm, cognome_norm)
            except Exception as w:
                warning = str(w)
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
            new_id = cur.lastrowid
            conn.close()
            operaio = Operaio(new_id, nome_norm, cognome_norm, alias,
                              float(costo_orario_base), StatoEntita.ATTIVO, note)
            return {"operaio": operaio, "warning": warning}
        except ValueError:
            raise
        except Exception as e:
            print(f"Errore nell'aggiunta operaio: {e}")
            return {"operaio": None, "warning": warning}

    def cercaOperaio(self, termine_ricerca: str) -> list:
        """Cerca operai attivi per id, nome, cognome, nome completo o alias."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            query = """
                SELECT * FROM operai
                WHERE stato = ?
                  AND (
                        nome LIKE ?
                     OR cognome LIKE ?
                     OR alias LIKE ?
                     OR (nome || ' ' || cognome) LIKE ?
                     OR CAST(id AS TEXT) LIKE ?
                  )
                ORDER BY cognome COLLATE NOCASE ASC, nome COLLATE NOCASE ASC
            """
            termine = f"%{(termine_ricerca or '').strip()}%"
            cur.execute(query, (StatoEntita.ATTIVO.value, termine, termine, termine, termine, termine))
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
        """Restituisce la lista di tutti gli operai attivi."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM operai WHERE stato = ? ORDER BY cognome COLLATE NOCASE ASC, nome COLLATE NOCASE ASC",
                (StatoEntita.ATTIVO.value,),
            )
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
            storico_voci = self.storicoVociOperaio(id_operaio)

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
                'ore_per_progetto': ore_per_progetto,
                'storico_voci': storico_voci,
            }
        except Exception as e:
            print(f"Errore nel recupero dettaglio operaio: {e}")
            return {}

    def modificaOperaio(self, id_operaio: int, updates: dict = None, nome: str = None,
                        cognome: str = None, alias: str = None, costo_orario_base: float = None,
                        note: str = None, stato: StatoEntita = None) -> None:
        """Modifica i dati di un operaio. Accetta dict come secondo parametro o kwargs."""
        try:
            if updates and isinstance(updates, dict):
                nome = updates.get("nome", nome)
                cognome = updates.get("cognome", cognome)
                alias = updates.get("alias", alias)
                costo_orario_base = updates.get("costo_orario_base", costo_orario_base)
                note = updates.get("note", note)
                if "stato" in updates:
                    stato = StatoEntita(updates["stato"]) if isinstance(updates["stato"], str) else updates["stato"]

            conn = self._get_conn()
            cur = conn.cursor()
            update_parts = []
            params = []

            if nome is not None:
                update_parts.append("nome = ?")
                params.append(self._normalizza(nome))
            if cognome is not None:
                update_parts.append("cognome = ?")
                params.append(self._normalizza(cognome))
            if alias is not None:
                update_parts.append("alias = ?")
                params.append(alias)
            if costo_orario_base is not None:
                if not self._validoCostoOrario(float(costo_orario_base)):
                    print("Costo orario non valido per la modifica")
                else:
                    update_parts.append("costo_orario_base = ?")
                    params.append(float(costo_orario_base))
            if note is not None:
                update_parts.append("note = ?")
                params.append(note)
            if stato is not None:
                update_parts.append("stato = ?")
                params.append(stato.value)

            if update_parts:
                query = f"UPDATE operai SET {', '.join(update_parts)} WHERE id = ?"
                params.append(id_operaio)
                cur.execute(query, params)
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore nella modifica operaio: {e}")

    def eliminaOperaio(self, id_operaio: int) -> str:
        """Elimina un operaio: soft delete se ha voci associate, hard delete altrimenti."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()

            cur.execute("SELECT id FROM operai WHERE id = ?", (id_operaio,))
            if not cur.fetchone():
                conn.close()
                return "not_found"

            if self._ha_voci_operai_associate(cur, id_operaio):
                cur.execute("UPDATE operai SET stato = ? WHERE id = ?", (StatoEntita.DISATTIVATO.value, id_operaio))
                conn.commit()
                conn.close()
                return "soft_deleted"

            cur.execute("DELETE FROM operai WHERE id = ?", (id_operaio,))
            conn.commit()
            conn.close()
            return "hard_deleted"
        except Exception as e:
            print(f"Errore nell'eliminazione operaio: {e}")
            return "error"

    def storicoOreOperaio(self, id_operaio: int) -> list:
        """Ottiene lo storico delle schede giornaliere di un operaio (ordinate per data desc, id desc)."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT s.*
                FROM schede_giornaliere s
                JOIN voci_operai v ON s.id = v.id_scheda
                WHERE v.id_operaio = ?
                ORDER BY s.data DESC, s.id DESC
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

    def storicoVociOperaio(self, id_operaio: int) -> list:
        """Storico voci con dati arricchiti (data, ore, costo, nome progetto, id scheda) ordinati per data desc."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT s.id as scheda_id, s.data, s.descrizione, s.id_progetto,
                       p.nome_progetto,
                       v.ore_lavorate, v.costo_orario_snapshot
                FROM voci_operai v
                JOIN schede_giornaliere s ON v.id_scheda = s.id
                LEFT JOIN progetti p ON s.id_progetto = p.id
                WHERE v.id_operaio = ?
                ORDER BY s.data DESC, s.id DESC
            """, (id_operaio,))
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    'id_scheda': row['scheda_id'],
                    'data': row['data'],
                    'descrizione': row['descrizione'],
                    'id_progetto': row['id_progetto'],
                    'nome_progetto': row['nome_progetto'] or f"Progetto #{row['id_progetto']}",
                    'ore_lavorate': row['ore_lavorate'],
                    'costo_orario_snapshot': row['costo_orario_snapshot'],
                    'costo_totale': row['ore_lavorate'] * row['costo_orario_snapshot'],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Errore nel recupero storico voci operaio: {e}")
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

    def _ha_voci_operai_associate(self, cur, id_operaio: int) -> bool:
        """Verifica se un operaio e' presente in almeno una voce operaio."""
        cur.execute("SELECT 1 FROM voci_operai WHERE id_operaio = ? LIMIT 1", (id_operaio,))
        return cur.fetchone() is not None
