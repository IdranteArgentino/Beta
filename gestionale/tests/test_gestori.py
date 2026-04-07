"""
Unit Test per i Gestori (Controller) del Gestionale Commesse PMI
Utilizzano un database SQLite temporaneo in-memory o su file temp.
"""
import unittest
import tempfile
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gestionale.database import inizializza_db
from gestionale.azienda import Azienda
from gestionale.models.enumerazioni import StatoEntita, StatoProgetto, RuoloUtente

from gestionale.gestori.gestore_utenti import GestoreUtenti
from gestionale.gestori.gestore_clienti import GestoreClienti
from gestionale.gestori.gestore_operai import GestoreOperai
from gestionale.gestori.gestore_materiali import GestoreMateriali
from gestionale.gestori.gestore_progetti import GestoreProgetti
from gestionale.gestori.gestore_schede import GestoreSchede


class BaseTestGestori(unittest.TestCase):
    """Classe base che crea un DB temporaneo per ogni test"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        inizializza_db(self.db_path)
        self.azienda = Azienda(self.db_path)

    def tearDown(self):
        try:
            os.remove(self.db_path)
            os.rmdir(self.temp_dir)
        except:
            pass


# ===========================================================
# TEST GESTORE UTENTI
# ===========================================================
class TestGestoreUtenti(BaseTestGestori):

    def setUp(self):
        super().setUp()
        self.gestore = GestoreUtenti(self.azienda)

    def _crea_utente_test(self, username, nome, cognome, ruolo):
        """Inserisce direttamente un utente nel DB con password 'cambiami123' per i test di setup."""
        from gestionale.database import create_connection
        password_hash = self.gestore.hashPassword("cambiami123")
        conn = create_connection(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO utenti (username, nome, cognome, password_hash, stato, ruolo) VALUES (?, ?, ?, ?, ?, ?)",
            (username, nome, cognome, password_hash, "ATTIVO", ruolo.value)
        )
        conn.commit()
        conn.close()

    def test_login_admin_default(self):
        """L'admin di default (admin/admin) deve poter accedere"""
        utente = self.gestore.login("admin", "admin")
        self.assertIsNotNone(utente)
        self.assertTrue(utente.isAdmin())
        self.assertEqual(utente.username, "admin")

    def test_login_password_errata(self):
        with self.assertRaises(ValueError):
            self.gestore.login("admin", "sbagliata")

    def test_login_utente_inesistente(self):
        with self.assertRaises(ValueError):
            self.gestore.login("fantasma", "password")

    def test_revoca_utente(self):
        admin = self.gestore.login("admin", "admin")
        self._crea_utente_test("da_revocare", "Test", "Revoca", RuoloUtente.STAFF)
        self.gestore.revocaUtente("da_revocare", admin)
        # L'utente revocato non può più fare login
        with self.assertRaises(ValueError):
            self.gestore.login("da_revocare", "cambiami123")

    def test_revoca_se_stesso_impossibile(self):
        admin = self.gestore.login("admin", "admin")
        with self.assertRaises(ValueError):
            self.gestore.revocaUtente("admin", admin)

    def test_revoca_senza_permessi(self):
        self._crea_utente_test("staff1", "Staff", "Uno", RuoloUtente.STAFF)
        staff = self.gestore.login("staff1", "cambiami123")
        with self.assertRaises(PermissionError):
            self.gestore.revocaUtente("admin", staff)

    def test_riattiva_utente(self):
        admin = self.gestore.login("admin", "admin")
        self._crea_utente_test("riattiva", "Test", "Ri", RuoloUtente.STAFF)
        self.gestore.revocaUtente("riattiva", admin)
        self.gestore.riattivaUtente("riattiva", admin)
        logged = self.gestore.login("riattiva", "cambiami123")
        self.assertIsNotNone(logged)

    def test_reset_password(self):
        self._crea_utente_test("reset_test", "Test", "Reset", RuoloUtente.STAFF)
        self.gestore.resetPassword("reset_test")
        logged = self.gestore.login("reset_test", "cambiami123")
        self.assertIsNotNone(logged)

    def test_modifica_password(self):
        self._crea_utente_test("cambio_pwd", "Test", "Pwd", RuoloUtente.STAFF)
        utente = self.gestore.login("cambio_pwd", "cambiami123")
        self.gestore.modificaPassword(utente, "cambiami123", "nuova_password_123", "nuova_password_123")
        # La vecchia password non funziona più
        with self.assertRaises(ValueError):
            self.gestore.login("cambio_pwd", "cambiami123")
        # La nuova funziona
        logged = self.gestore.login("cambio_pwd", "nuova_password_123")
        self.assertIsNotNone(logged)

    def test_lista_utenti(self):
        utenti = self.gestore.listaUtenti()
        self.assertGreaterEqual(len(utenti), 1)  # almeno admin


# ===========================================================
# TEST GESTORE CLIENTI
# ===========================================================
class TestGestoreClienti(BaseTestGestori):

    def setUp(self):
        super().setUp()
        self.gestore = GestoreClienti(self.azienda)

    def test_aggiungi_cliente(self):
        result = self.gestore.aggiungiCliente("Edilizia Moderna", "Torino", "+39 011 88", "Note")
        self.assertIn("cliente", result)
        self.assertEqual(result["cliente"].ragione_sociale, "Edilizia Moderna")

    def test_normalizzazione_ragione_sociale(self):
        result = self.gestore.aggiungiCliente("  edilizia moderna  ", "", "", "")
        self.assertEqual(result["cliente"].ragione_sociale, "Edilizia Moderna")

    def test_duplicato_warning(self):
        self.gestore.aggiungiCliente("Test Duplicato", "", "", "")
        result = self.gestore.aggiungiCliente("test duplicato", "", "", "")
        self.assertTrue(len(result["warning"]) > 0)

    def test_lista_clienti(self):
        self.gestore.aggiungiCliente("Cliente A", "", "", "")
        self.gestore.aggiungiCliente("Cliente B", "", "", "")
        lista = self.gestore.listaClienti()
        self.assertEqual(len(lista), 2)

    def test_cerca_cliente(self):
        self.gestore.aggiungiCliente("Alfa Costruzioni", "", "", "")
        self.gestore.aggiungiCliente("Beta Engineering", "", "", "")
        risultati = self.gestore.cercaCliente("alfa")
        self.assertEqual(len(risultati), 1)
        self.assertEqual(risultati[0].ragione_sociale, "Alfa Costruzioni")

    def test_modifica_cliente(self):
        res = self.gestore.aggiungiCliente("Da Modificare", "", "", "")
        cid = res["cliente"].id
        self.gestore.modificaCliente(cid, {"ragione_sociale": "Modificato Srl", "telefono": "123"})
        cliente = self.azienda.trova_cliente(cid)
        self.assertEqual(cliente.ragione_sociale, "Modificato Srl")
        self.assertEqual(cliente.telefono, "123")

    def test_elimina_cliente(self):
        res = self.gestore.aggiungiCliente("Da Eliminare", "", "", "")
        cid = res["cliente"].id
        self.gestore.eliminaCliente(cid)
        # Dopo eliminazione, la lista è vuota o il cliente è disattivato
        trovato = self.azienda.trova_cliente(cid)
        self.assertTrue(trovato is None or not trovato.isAttivo())


# ===========================================================
# TEST GESTORE OPERAI
# ===========================================================
class TestGestoreOperai(BaseTestGestori):

    def setUp(self):
        super().setUp()
        self.gestore = GestoreOperai(self.azienda)

    def test_aggiungi_operaio(self):
        res = self.gestore.aggiungiOperaio("Marco", "Bianchi", 25.0, "Marchetto", "Caposquadra")
        self.assertEqual(res["operaio"].nome, "Marco")
        self.assertEqual(res["operaio"].costo_orario_base, 25.0)

    def test_costo_orario_zero_invalido(self):
        with self.assertRaises(ValueError):
            self.gestore.aggiungiOperaio("Test", "Zero", 0.0, "", "")

    def test_costo_orario_negativo_invalido(self):
        with self.assertRaises(ValueError):
            self.gestore.aggiungiOperaio("Test", "Neg", -5.0, "", "")

    def test_omonimia_warning(self):
        self.gestore.aggiungiOperaio("Mario", "Rossi", 20.0, "", "")
        res = self.gestore.aggiungiOperaio("Mario", "Rossi", 22.0, "Mario2", "")
        self.assertTrue(len(res["warning"]) > 0)

    def test_normalizzazione_nome(self):
        res = self.gestore.aggiungiOperaio("  marco  ", "  bianchi  ", 20.0, "", "")
        self.assertEqual(res["operaio"].nome, "Marco")
        self.assertEqual(res["operaio"].cognome, "Bianchi")

    def test_lista_operai(self):
        self.gestore.aggiungiOperaio("A", "B", 20.0, "", "")
        self.gestore.aggiungiOperaio("C", "D", 25.0, "", "")
        self.assertEqual(len(self.gestore.listaOperai()), 2)

    def test_cerca_operaio(self):
        self.gestore.aggiungiOperaio("Marco", "Bianchi", 20.0, "MarcB", "")
        self.gestore.aggiungiOperaio("Luca", "Verdi", 25.0, "", "")
        # Cerca per nome
        self.assertEqual(len(self.gestore.cercaOperaio("marco")), 1)
        # Cerca per alias
        self.assertEqual(len(self.gestore.cercaOperaio("marcb")), 1)

    def test_modifica_operaio(self):
        res = self.gestore.aggiungiOperaio("Test", "Mod", 20.0, "", "")
        oid = res["operaio"].id
        self.gestore.modificaOperaio(oid, {"costo_orario_base": 30.0})
        op = self.azienda.trova_operaio(oid)
        self.assertEqual(op.costo_orario_base, 30.0)


# ===========================================================
# TEST GESTORE MATERIALI
# ===========================================================
class TestGestoreMateriali(BaseTestGestori):

    def setUp(self):
        super().setUp()
        self.gestore = GestoreMateriali(self.azienda)

    def test_aggiungi_materiale(self):
        mat = self.gestore.aggiungiMateriale("Cemento", "kg", 0.15, "Portland")
        self.assertEqual(mat.descrizione, "Cemento")
        self.assertEqual(mat.prezzo_unitario_base, 0.15)

    def test_duplicato_descrizione(self):
        self.gestore.aggiungiMateriale("Cemento", "kg", 0.15, "")
        with self.assertRaises(ValueError):
            self.gestore.aggiungiMateriale("cemento", "kg", 0.20, "")

    def test_prezzo_negativo_invalido(self):
        with self.assertRaises(ValueError):
            self.gestore.aggiungiMateriale("Test", "pz", -1.0, "")

    def test_normalizzazione_descrizione(self):
        mat = self.gestore.aggiungiMateriale("  tavole abete  ", "m", 8.0, "")
        self.assertEqual(mat.descrizione, "Tavole Abete")

    def test_lista_materiali(self):
        self.gestore.aggiungiMateriale("Mat A", "kg", 1.0, "")
        self.gestore.aggiungiMateriale("Mat B", "pz", 2.0, "")
        self.assertEqual(len(self.gestore.listaMateriali()), 2)

    def test_cerca_materiale(self):
        self.gestore.aggiungiMateriale("Cemento", "kg", 0.15, "")
        self.gestore.aggiungiMateriale("Ferro", "kg", 0.80, "")
        self.assertEqual(len(self.gestore.cercaMateriale("cem")), 1)

    def test_modifica_prezzo(self):
        mat = self.gestore.aggiungiMateriale("Test Mod", "pz", 10.0, "")
        self.gestore.modificaMateriale(mat.id, {"prezzo_unitario_base": 15.0})
        aggiornato = self.azienda.trova_materiale(mat.id)
        self.assertEqual(aggiornato.prezzo_unitario_base, 15.0)


# ===========================================================
# TEST GESTORE PROGETTI
# ===========================================================
class TestGestoreProgetti(BaseTestGestori):

    def setUp(self):
        super().setUp()
        self.g_clienti = GestoreClienti(self.azienda)
        self.g_progetti = GestoreProgetti(self.azienda)
        # Crea un cliente per associare progetti
        res = self.g_clienti.aggiungiCliente("Cliente Test", "", "", "")
        self.id_cliente = res["cliente"].id

    def test_crea_progetto(self):
        prog = self.g_progetti.creaProgetto("Cantiere A", self.id_cliente, "Via Test 1", "Note")
        self.assertEqual(prog.nome_progetto, "Cantiere A")
        self.assertTrue(prog.isInCorso())

    def test_crea_progetto_senza_nome(self):
        with self.assertRaises(ValueError):
            self.g_progetti.creaProgetto("", self.id_cliente, "", "")

    def test_lista_progetti(self):
        self.g_progetti.creaProgetto("Prog A", self.id_cliente, "", "")
        self.g_progetti.creaProgetto("Prog B", self.id_cliente, "", "")
        self.assertEqual(len(self.g_progetti.listaProgetti()), 2)

    def test_cerca_progetto(self):
        self.g_progetti.creaProgetto("Residenziale Lotto A", self.id_cliente, "Milano", "")
        self.g_progetti.creaProgetto("Commerciale Centro", self.id_cliente, "Roma", "")
        self.assertEqual(len(self.g_progetti.cercaProgetto("residenziale")), 1)
        self.assertEqual(len(self.g_progetti.cercaProgetto("roma")), 1)

    def test_cambia_stato_completato(self):
        prog = self.g_progetti.creaProgetto("Da completare", self.id_cliente, "", "")
        self.g_progetti.cambiaStato(prog.id, StatoProgetto.COMPLETATO)
        aggiornato = self.azienda.trova_progetto(prog.id)
        self.assertTrue(aggiornato.isCompletato())
        self.assertFalse(aggiornato.isModificabile())

    def test_dettaglio_progetto(self):
        prog = self.g_progetti.creaProgetto("Dettaglio", self.id_cliente, "", "")
        dettaglio = self.g_progetti.dettaglioProgetto(prog.id)
        self.assertIn("progetto", dettaglio)
        self.assertIn("cliente", dettaglio)
        self.assertIn("costoTot", dettaglio)

    def test_elimina_progetto(self):
        prog = self.g_progetti.creaProgetto("Da eliminare", self.id_cliente, "", "")
        self.g_progetti.eliminaProgetto(prog.id)
        self.assertIsNone(self.azienda.trova_progetto(prog.id))


# ===========================================================
# TEST GESTORE SCHEDE (+ Snapshot prezzi)
# ===========================================================
class TestGestoreSchede(BaseTestGestori):

    def setUp(self):
        super().setUp()
        self.g_clienti = GestoreClienti(self.azienda)
        self.g_operai = GestoreOperai(self.azienda)
        self.g_materiali = GestoreMateriali(self.azienda)
        self.g_progetti = GestoreProgetti(self.azienda)
        self.g_schede = GestoreSchede(self.azienda)

        # Setup dati di test
        res_c = self.g_clienti.aggiungiCliente("Cliente Schede", "", "", "")
        self.id_cliente = res_c["cliente"].id

        self.prog = self.g_progetti.creaProgetto("Progetto Schede", self.id_cliente, "", "")

        res_o = self.g_operai.aggiungiOperaio("Mario", "Test", 25.0, "", "")
        self.id_operaio = res_o["operaio"].id

        self.mat = self.g_materiali.aggiungiMateriale("Cemento Test", "kg", 0.15, "")

    def test_crea_scheda(self):
        scheda = self.g_schede.creaScheda(self.prog.id, "2023-10-24", "Posa pavimenti")
        self.assertIsNotNone(scheda)
        self.assertGreater(scheda.id, 0)

    def test_crea_scheda_progetto_completato(self):
        """Non si possono creare schede su progetti completati"""
        self.g_progetti.cambiaStato(self.prog.id, StatoProgetto.COMPLETATO)
        with self.assertRaises(PermissionError):
            self.g_schede.creaScheda(self.prog.id, "2023-10-25", "Tentativo")

    def test_assegna_ore_operaio(self):
        scheda = self.g_schede.creaScheda(self.prog.id, "2023-10-24", "Test ore")
        voce = self.g_schede.assegnaOreOperaio(scheda.id, self.id_operaio, 8.0)
        self.assertEqual(voce.ore_lavorate, 8.0)
        self.assertEqual(voce.costo_orario_snapshot, 25.0)  # Snapshot del costo attuale

    def test_snapshot_prezzo_congelato(self):
        """Il prezzo snapshot deve essere congelato al momento dell'assegnazione"""
        scheda = self.g_schede.creaScheda(self.prog.id, "2023-10-24", "Test snapshot")
        voce = self.g_schede.assegnaOreOperaio(scheda.id, self.id_operaio, 8.0)
        costo_snapshot = voce.costo_orario_snapshot

        # Ora modifichiamo il costo dell'operaio
        self.g_operai.modificaOperaio(self.id_operaio, {"costo_orario_base": 50.0})

        # La voce nella scheda deve mantenere il vecchio prezzo
        dettaglio = self.g_schede.dettaglioScheda(scheda.id)
        voce_db = dettaglio["vociOperai"][0]
        self.assertEqual(voce_db.costo_orario_snapshot, costo_snapshot)
        self.assertEqual(voce_db.costo_orario_snapshot, 25.0)  # NON 50!

    def test_scarica_materiale(self):
        scheda = self.g_schede.creaScheda(self.prog.id, "2023-10-24", "Test mat")
        voce = self.g_schede.scaricaMateriale(scheda.id, self.mat.id, 100.0)
        self.assertEqual(voce.quantita, 100.0)
        self.assertEqual(voce.prezzo_unitario_snapshot, 0.15)

    def test_snapshot_materiale_congelato(self):
        """Il prezzo materiale snapshot deve essere congelato"""
        scheda = self.g_schede.creaScheda(self.prog.id, "2023-10-24", "Mat snapshot")
        self.g_schede.scaricaMateriale(scheda.id, self.mat.id, 50.0)

        # Modifichiamo il prezzo base
        self.g_materiali.modificaMateriale(self.mat.id, {"prezzo_unitario_base": 1.00})

        dettaglio = self.g_schede.dettaglioScheda(scheda.id)
        voce_db = dettaglio["vociMat"][0]
        self.assertEqual(voce_db.prezzo_unitario_snapshot, 0.15)  # NON 1.00!

    def test_ore_non_valide(self):
        scheda = self.g_schede.creaScheda(self.prog.id, "2023-10-24", "Ore invalide")
        with self.assertRaises(ValueError):
            self.g_schede.assegnaOreOperaio(scheda.id, self.id_operaio, 0)
        with self.assertRaises(ValueError):
            self.g_schede.assegnaOreOperaio(scheda.id, self.id_operaio, -5)

    def test_quantita_non_valida(self):
        scheda = self.g_schede.creaScheda(self.prog.id, "2023-10-24", "Qty invalida")
        with self.assertRaises(ValueError):
            self.g_schede.scaricaMateriale(scheda.id, self.mat.id, 0)

    def test_rimuovi_operaio_da_scheda(self):
        scheda = self.g_schede.creaScheda(self.prog.id, "2023-10-24", "Rimuovi")
        self.g_schede.assegnaOreOperaio(scheda.id, self.id_operaio, 8.0)
        self.g_schede.rimuoviOperaioDaScheda(scheda.id, self.id_operaio)
        dettaglio = self.g_schede.dettaglioScheda(scheda.id)
        self.assertEqual(len(dettaglio["vociOperai"]), 0)

    def test_rimuovi_materiale_da_scheda(self):
        scheda = self.g_schede.creaScheda(self.prog.id, "2023-10-24", "Rimuovi mat")
        self.g_schede.scaricaMateriale(scheda.id, self.mat.id, 10.0)
        self.g_schede.rimuoviMaterialeDaScheda(scheda.id, self.mat.id)
        dettaglio = self.g_schede.dettaglioScheda(scheda.id)
        self.assertEqual(len(dettaglio["vociMat"]), 0)

    def test_elimina_scheda(self):
        scheda = self.g_schede.creaScheda(self.prog.id, "2023-10-24", "Da eliminare")
        self.g_schede.eliminaScheda(scheda.id)
        trovata = self.azienda.trova_scheda(scheda.id)
        self.assertIsNone(trovata)

    def test_costo_cumulativo_progetto(self):
        """Verifica il calcolo cumulativo dei costi a livello di progetto"""
        s1 = self.g_schede.creaScheda(self.prog.id, "2023-10-24", "Giorno 1")
        self.g_schede.assegnaOreOperaio(s1.id, self.id_operaio, 8.0)      # 8 * 25 = 200
        self.g_schede.scaricaMateriale(s1.id, self.mat.id, 100.0)          # 100 * 0.15 = 15

        s2 = self.g_schede.creaScheda(self.prog.id, "2023-10-25", "Giorno 2")
        self.g_schede.assegnaOreOperaio(s2.id, self.id_operaio, 4.0)      # 4 * 25 = 100

        progetto = self.azienda.trova_progetto(self.prog.id)
        # Totale atteso: 200 + 15 + 100 = 315€
        self.assertAlmostEqual(progetto.getCostoTotale(), 315.0)


if __name__ == '__main__':
    unittest.main()
