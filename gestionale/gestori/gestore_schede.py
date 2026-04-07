"""Gestore per operazioni di modifica e operazioni complesse su schede giornaliere."""
import os
from ..database import create_connection
from ..models import StatoEntita, StatoProgetto, SchedaGiornaliera, VoceMateriali, VoceOperai, Allegato


class GestoreSchede:
    """Gestisce modifiche, validazioni e operazioni complesse su schede giornaliere."""

    def __init__(self, azienda):
        self.azienda = azienda
        self.db_path = azienda.db_path

    def _get_conn(self):
        return create_connection(self.db_path)

    # ==========================================
    # METODI PUBBLICI UML
    # ==========================================

    def creaScheda(self, id_progetto: int, data: str, descrizione: str) -> SchedaGiornaliera | None:
        """Crea una nuova scheda giornaliera e restituisce l'oggetto salvato."""
        try:
            if not self._verificaProgettoModificabile(id_progetto):
                return None

            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO schede_giornaliere (data, descrizione, id_progetto) VALUES (?, ?, ?)",
                (data, descrizione, id_progetto),
            )
            conn.commit()
            new_id = cur.lastrowid
            conn.close()
            return SchedaGiornaliera(new_id, data, descrizione, id_progetto)
        except Exception as e:
            print(f"Errore nella creazione scheda: {e}")
            return None

    def aggiungiScheda(self, data: str, descrizione: str, id_progetto: int) -> SchedaGiornaliera | None:
        """Alias compatibile per creare una nuova scheda."""
        return self.creaScheda(id_progetto, data, descrizione)

    def aggiungiAllegato(self, path: str, id_scheda: int = None) -> None:
        """Aggiunge un allegato a una scheda."""
        try:
            if id_scheda is None or not self._verificaSchedaModificabile(id_scheda):
                return
            if not self._verificaEsistenzaFile(path):
                print("File non trovato")
                return


            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("INSERT INTO allegati (id_scheda, path) VALUES (?, ?)", (id_scheda, path))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore nell'aggiunta allegato: {e}")

    def assegnaOreOperaio(self, id_scheda: int, id_operaio: int, ore: float) -> VoceOperai | None:
        """Assegna ore a un operaio nella scheda e restituisce la voce creata."""
        try:
            if not self._verificaSchedaModificabile(id_scheda):
                return None
            if not self._validaOre(ore) or float(ore) <= 0:
                raise ValueError("Ore non valide")

            operaio = self._trova_operaio(id_operaio)
            if not operaio or operaio['stato'] != StatoEntita.ATTIVO.value:
                return None

            voce = VoceOperai(id_scheda, id_operaio, float(ore), float(operaio['costo_orario_base']))
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO voci_operai (id_scheda, id_operaio, ore_lavorate, costo_orario_snapshot)
                VALUES (?, ?, ?, ?)
                """,
                (voce.id_scheda, voce.id_operaio, voce.ore_lavorate, voce.costo_orario_snapshot),
            )
            conn.commit()
            conn.close()
            return voce
        except ValueError:
            raise
        except Exception as e:
            print(f"Errore nell'assegnazione ore operaio: {e}")
            return None

    def aggiungiScheda(self, data: str, descrizione: str, id_progetto: int) -> None:
        """Aggiunge una nuova scheda giornaliera a un progetto."""
        self.creaScheda(id_progetto, data, descrizione)

    def aggiungiVoceMateriale(self, id_scheda: int, id_materiale: int) -> None:
        """Aggiunge una voce materiale alla scheda."""
        try:
            self.scaricaMateriale(id_scheda, id_materiale, 1.0)
        except Exception as e:
            print(f"Errore nell'aggiunta materiale a scheda: {e}")

    def aggiungiVoceOperaio(self, id_scheda: int, id_operaio: int) -> None:
        """Aggiunge una voce operaio alla scheda."""
        try:
            self.assegnaOreOperaio(id_scheda, id_operaio, 1.0)
        except Exception as e:
            print(f"Errore nell'aggiunta operaio a scheda: {e}")

    def scaricaMateriale(self, id_scheda: int, id_materiale: int, quantita: float) -> VoceMateriali | None:
        """Assegna una quantità di materiale a una scheda e restituisce la voce creata."""
        try:
            if not self._verificaSchedaModificabile(id_scheda):
                return None
            if not self._validaQuantita(quantita):
                raise ValueError("Quantità non valida")

            materiale = self._trova_materiale(id_materiale)
            if not materiale or materiale['stato'] != StatoEntita.ATTIVO.value:
                return None

            voce = VoceMateriali(id_scheda, id_materiale, float(quantita), float(materiale['prezzo_unitario_base']))
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO voci_materiali (id_scheda, id_materiale, quantita, prezzo_unitario_snapshot)
                VALUES (?, ?, ?, ?)
                """,
                (voce.id_scheda, voce.id_materiale, voce.quantita, voce.prezzo_unitario_snapshot),
            )
            conn.commit()
            conn.close()
            return voce
        except ValueError:
            raise
        except Exception as e:
            print(f"Errore nell'assegnazione materiale a scheda: {e}")
            return None

    def rimuoviMaterialeDaScheda(self, id_scheda: int, id_materiale: int) -> None:
        """Alias compatibile per rimuovere un materiale da una scheda."""
        self.rimuoviVoceMateriale(id_scheda, id_materiale)

    def rimuoviOperaioDaScheda(self, id_scheda: int, id_operaio: int) -> None:
        """Alias compatibile per rimuovere un operaio da una scheda."""
        self.rimuoviVoceOperaio(id_scheda, id_operaio)

    def listaSchede(self) -> list:
        """Restituisce le schede giornaliere ordinate per data desc."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM schede_giornaliere ORDER BY data DESC, id DESC")
            rows = cur.fetchall()
            conn.close()
            return [SchedaGiornaliera(r['id'], r['data'], r['descrizione'], r['id_progetto']) for r in rows]
        except Exception as e:
            print(f"Errore nel recupero lista schede: {e}")
            return []

    def cercaScheda(self, termine_ricerca: str) -> list:
        """Cerca schede per id, data o descrizione."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            t = f"%{(termine_ricerca or '').strip()}%"
            cur.execute(
                """
                SELECT * FROM schede_giornaliere
                WHERE CAST(id AS TEXT) LIKE ? OR data LIKE ? OR descrizione LIKE ?
                ORDER BY data DESC, id DESC
                """,
                (t, t, t),
            )
            rows = cur.fetchall()
            conn.close()
            return [SchedaGiornaliera(r['id'], r['data'], r['descrizione'], r['id_progetto']) for r in rows]
        except Exception as e:
            print(f"Errore nella ricerca schede: {e}")
            return []

    def costiTotali(self, id_scheda: int) -> float:
        """Ottiene il costo totale di una scheda (operai + materiali)."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()

            cur.execute("""
                SELECT SUM(ore_lavorate * costo_orario_snapshot) as costo
                FROM voci_operai WHERE id_scheda = ?
            """, (id_scheda,))
            c_operai = (cur.fetchone()['costo'] or 0.0)

            cur.execute("""
                SELECT SUM(quantita * prezzo_unitario_snapshot) as costo
                FROM voci_materiali WHERE id_scheda = ?
            """, (id_scheda,))
            c_materiali = (cur.fetchone()['costo'] or 0.0)

            conn.close()
            return float(c_operai + c_materiali)
        except Exception as e:
            print(f"Errore nel calcolo costi totali: {e}")
            return 0.0

    def dettaglioScheda(self, id_scheda: int) -> dict:
        """Restituisce i dettagli completi di una scheda."""
        try:
            scheda = self._trova_scheda(id_scheda)
            if not scheda:
                return {}

            scheda.voci_operai = self._get_voci_operai(id_scheda)
            scheda.voci_materiali = self._get_voci_materiali(id_scheda)
            scheda.allegati = self._get_allegati(id_scheda)

            return {
                "id": scheda.id,
                "data": scheda.data,
                "descrizione": scheda.descrizione,
                "id_progetto": scheda.id_progetto,
                "scheda": scheda,
                "vociOperai": scheda.voci_operai,
                "vociMat": scheda.voci_materiali,
                "allegati": scheda.allegati,
                "totale_ore": scheda.getTotaleOre(),
                "costo_totale": self.costiTotali(id_scheda)
            }
        except Exception as e:
            print(f"Errore recupero dettaglio scheda: {e}")
            return {}

    def eliminaScheda(self, id_scheda: int) -> None:
        """Elimina una scheda."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM schede_giornaliere WHERE id = ?", (id_scheda,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore nell'eliminazione scheda: {e}")

    def modificaScheda(self, data: str, descrizione: str, id_scheda: int = None) -> None:
        """Modifica i dati di una scheda. Parametri UML: String, String."""
        try:
            if id_scheda is None:
                return

            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "UPDATE schede_giornaliere SET data = ?, descrizione = ? WHERE id = ?",
                (data, descrizione, id_scheda)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore nella modifica scheda: {e}")

    def oreOperaioPerScheda(self, id_scheda: int, id_operaio: int) -> float:
        """Restituisce le ore lavorate da un determinato operaio su una singola scheda."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT ore_lavorate FROM voci_operai 
                WHERE id_scheda = ? AND id_operaio = ?
            """, (id_scheda, id_operaio))
            row = cur.fetchone()
            conn.close()
            return float(row['ore_lavorate']) if row else 0.0
        except Exception as e:
            print(f"Errore calcolo ore operaio: {e}")
            return 0.0

    def quantitaTotaleMaterialePerScheda(self, id_scheda: int, id_materiale: int) -> float:
        """Restituisce la quantità di un materiale in una specifica scheda."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT quantita FROM voci_materiali 
                WHERE id_scheda = ? AND id_materiale = ?
            """, (id_scheda, id_materiale))
            row = cur.fetchone()
            conn.close()
            return float(row['quantita']) if row else 0.0
        except Exception as e:
            print(f"Errore calcolo quantità materiale: {e}")
            return 0.0

    def rimuoviAllegato(self, id_allegato: int) -> None:
        """Rimuove un allegato."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id_scheda, path FROM allegati WHERE id = ?", (id_allegato,))
            row = cur.fetchone()
            if row and not self._verificaSchedaModificabile(row['id_scheda']):
                conn.close()
                return
            cur.execute("DELETE FROM allegati WHERE id = ?", (id_allegato,))
            conn.commit()
            conn.close()
            if row and row['path'] and os.path.exists(row['path']):
                try:
                    os.remove(row['path'])
                except OSError:
                    pass
        except Exception as e:
            print(f"Errore rimozione allegato: {e}")

    def rimuoviVoceMateriale(self, id_scheda: int, id_materiale: int) -> None:
        """Rimuove un materiale da una scheda."""
        try:
            if not self._verificaSchedaModificabile(id_scheda):
                return
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM voci_materiali WHERE id_scheda = ? AND id_materiale = ?", (id_scheda, id_materiale))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore rimozione voce materiale: {e}")

    def rimuoviVoceOperaio(self, id_scheda: int, id_operaio: int) -> None:
        """Rimuove un operaio da una scheda."""
        try:
            if not self._verificaSchedaModificabile(id_scheda):
                return
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM voci_operai WHERE id_scheda = ? AND id_operaio = ?", (id_scheda, id_operaio))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore rimozione voce operaio: {e}")

    def _get_voci_operai(self, id_scheda: int) -> list:
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM voci_operai WHERE id_scheda = ? ORDER BY id_operaio", (id_scheda,))
            rows = cur.fetchall()
            conn.close()
            return [VoceOperai(r['id_scheda'], r['id_operaio'], r['ore_lavorate'], r['costo_orario_snapshot']) for r in rows]
        except Exception as e:
            print(f"Errore nel recupero voci operai: {e}")
            return []

    def _get_voci_materiali(self, id_scheda: int) -> list:
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM voci_materiali WHERE id_scheda = ? ORDER BY id_materiale", (id_scheda,))
            rows = cur.fetchall()
            conn.close()
            return [VoceMateriali(r['id_scheda'], r['id_materiale'], r['quantita'], r['prezzo_unitario_snapshot']) for r in rows]
        except Exception as e:
            print(f"Errore nel recupero voci materiali: {e}")
            return []

    def _get_allegati(self, id_scheda: int) -> list:
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM allegati WHERE id_scheda = ? ORDER BY id DESC", (id_scheda,))
            rows = cur.fetchall()
            conn.close()
            return [Allegato(r['id'], r['id_scheda'], r['path']) for r in rows]
        except Exception as e:
            print(f"Errore nel recupero allegati: {e}")
            return []

    def _verificaSchedaModificabile(self, id_scheda: int) -> bool:
        try:
            scheda = self._trova_scheda(id_scheda)
            if not scheda:
                return False
            return self._verificaProgettoModificabile(scheda.id_progetto)
        except Exception:
            return False

    def _trova_scheda_by_allegato(self, id_allegato: int):
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id_scheda FROM allegati WHERE id = ?", (id_allegato,))
            row = cur.fetchone()
            conn.close()
            return row['id_scheda'] if row else None
        except Exception:
            return None

    # ==========================================
    # METODI PRIVATI
    # ==========================================

    def _validaOre(self, ore: float) -> bool:
        """Valida le ore lavorate (devono essere positive e ragionevoli)."""
        return isinstance(ore, (int, float)) and ore >= 0

    def _validaQuantita(self, quantita: float) -> bool:
        """Valida la quantità del materiale (deve essere positiva)."""
        return isinstance(quantita, (int, float)) and quantita > 0

    def _verificaEsistenzaFile(self, path: str) -> bool:
        """Verifica se il file specificato esiste nel filesystem."""
        return os.path.exists(path)

    def _verificaProgettoModificabile(self, id_progetto: int) -> bool:
        """Verifica se il progetto è aperto e quindi modificabile (es. IN_CORSO)."""
        try:
            p = self._trova_progetto(id_progetto)
            if p and p['stato'] == StatoProgetto.IN_CORSO.value:
                return True
            return False
        except Exception:
            return False

    def _trova_materiale(self, id_materiale: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM materiali WHERE id = ?", (id_materiale,))
        row = cur.fetchone()
        conn.close()
        return row

    def _trova_operaio(self, id_operaio: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM operai WHERE id = ?", (id_operaio,))
        row = cur.fetchone()
        conn.close()
        return row

    def _trova_scheda(self, id_scheda: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM schede_giornaliere WHERE id = ?", (id_scheda,))
        row = cur.fetchone()
        conn.close()
        return None if not row else SchedaGiornaliera(row['id'], row['data'], row['descrizione'], row['id_progetto'])

    def _trova_progetto(self, id_progetto: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM progetti WHERE id = ?", (id_progetto,))
        row = cur.fetchone()
        conn.close()
        return row

