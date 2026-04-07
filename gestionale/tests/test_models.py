"""
Unit Test per i Modelli di Dominio del Gestionale Commesse PMI
Testano il comportamento delle entità e le regole business a livello di modello.
"""
import unittest
import hashlib
import sys
import os

# Aggiunge il path per risolvere gli import gestionale.*
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gestionale.models.enumerazioni import StatoEntita, StatoProgetto, RuoloUtente
from gestionale.models.utente import Utente, Amministratore, Staff
from gestionale.models.cliente import Cliente
from gestionale.models.operaio import Operaio
from gestionale.models.materiale import Materiale
from gestionale.models.progetto import Progetto
from gestionale.models.scheda import SchedaGiornaliera, VoceOperai, VoceMateriali, Allegato


# ===========================================================
# TEST ENUMERAZIONI
# ===========================================================
class TestEnumerazioni(unittest.TestCase):
    """Verifica che le enum abbiano i valori corretti"""

    def test_stati_entita(self):
        self.assertEqual(StatoEntita.ATTIVO.value, "ATTIVO")
        self.assertEqual(StatoEntita.DISATTIVATO.value, "DISATTIVATO")

    def test_stati_progetto(self):
        self.assertEqual(StatoProgetto.IN_CORSO.value, "IN_CORSO")
        self.assertEqual(StatoProgetto.COMPLETATO.value, "COMPLETATO")

    def test_ruoli_utente(self):
        self.assertEqual(RuoloUtente.ADMIN.value, "ADMIN")
        self.assertEqual(RuoloUtente.STAFF.value, "STAFF")


# ===========================================================
# TEST UTENTE
# ===========================================================
class TestUtente(unittest.TestCase):

    def setUp(self):
        pwd_hash = hashlib.sha256("password123".encode('utf-8')).hexdigest()
        self.admin = Amministratore(1, "admin", "Mario", "Rossi", pwd_hash, StatoEntita.ATTIVO)
        self.staff = Staff(2, "staff1", "Luca", "Verdi", pwd_hash, StatoEntita.ATTIVO)
        self.staff_disattivato = Staff(3, "ex_staff", "Anna", "Bianchi", pwd_hash, StatoEntita.DISATTIVATO)

    def test_creazione_amministratore(self):
        self.assertEqual(self.admin.ruolo, RuoloUtente.ADMIN)
        self.assertEqual(self.admin.username, "admin")
        self.assertEqual(self.admin.nome, "Mario")
        self.assertEqual(self.admin.cognome, "Rossi")

    def test_creazione_staff(self):
        self.assertEqual(self.staff.ruolo, RuoloUtente.STAFF)
        self.assertEqual(self.staff.username, "staff1")

    def test_verifica_password_corretta(self):
        self.assertTrue(self.admin.verificaPassword("password123"))

    def test_verifica_password_errata(self):
        self.assertFalse(self.admin.verificaPassword("password_sbagliata"))

    def test_is_attivo(self):
        self.assertTrue(self.admin.isAttivo())
        self.assertTrue(self.staff.isAttivo())
        self.assertFalse(self.staff_disattivato.isAttivo())

    def test_is_admin(self):
        self.assertTrue(self.admin.isAdmin())
        self.assertFalse(self.staff.isAdmin())

    def test_nome_completo(self):
        self.assertEqual(self.admin.getNomeCompleto(), "Mario Rossi")
        self.assertEqual(self.staff.getNomeCompleto(), "Luca Verdi")


# ===========================================================
# TEST CLIENTE
# ===========================================================
class TestCliente(unittest.TestCase):

    def setUp(self):
        self.cliente_attivo = Cliente(1, "Edilizia Moderna s.r.l.", "Torino", "+39 011 88", "Note test", StatoEntita.ATTIVO)
        self.cliente_disattivato = Cliente(2, "Vecchia Ditta", "", "", "", StatoEntita.DISATTIVATO)

    def test_creazione_cliente(self):
        self.assertEqual(self.cliente_attivo.ragione_sociale, "Edilizia Moderna s.r.l.")
        self.assertEqual(self.cliente_attivo.indirizzo, "Torino")
        self.assertEqual(self.cliente_attivo.telefono, "+39 011 88")

    def test_is_attivo(self):
        self.assertTrue(self.cliente_attivo.isAttivo())
        self.assertFalse(self.cliente_disattivato.isAttivo())

    def test_ha_progetti_inizialmente_vuoto(self):
        self.assertFalse(self.cliente_attivo.haProgetti())
        self.assertEqual(self.cliente_attivo.getNumeroProgetti(), 0)

    def test_ha_progetti_dopo_aggiunta(self):
        p = Progetto(1, "Prova", 1, "", "", StatoProgetto.IN_CORSO)
        self.cliente_attivo.progetti.append(p)
        self.assertTrue(self.cliente_attivo.haProgetti())
        self.assertEqual(self.cliente_attivo.getNumeroProgetti(), 1)


# ===========================================================
# TEST OPERAIO
# ===========================================================
class TestOperaio(unittest.TestCase):

    def setUp(self):
        self.op = Operaio(1, "Marco", "Bianchi", "Marchetto", 25.0, StatoEntita.ATTIVO, "Caposquadra")
        self.op_no_alias = Operaio(2, "Luca", "Verdi", "", 20.0, StatoEntita.ATTIVO, "")
        self.op_dis = Operaio(3, "Mario", "Neri", "", 15.0, StatoEntita.DISATTIVATO, "")

    def test_creazione_operaio(self):
        self.assertEqual(self.op.nome, "Marco")
        self.assertEqual(self.op.cognome, "Bianchi")
        self.assertEqual(self.op.costo_orario_base, 25.0)

    def test_is_attivo(self):
        self.assertTrue(self.op.isAttivo())
        self.assertFalse(self.op_dis.isAttivo())

    def test_nome_completo(self):
        self.assertEqual(self.op.getNomeCompleto(), "Marco Bianchi")

    def test_nome_visualizzazione_con_alias(self):
        self.assertEqual(self.op.getNomeVisualizzazione(), "Marco Bianchi (Marchetto)")

    def test_nome_visualizzazione_senza_alias(self):
        self.assertEqual(self.op_no_alias.getNomeVisualizzazione(), "Luca Verdi")


# ===========================================================
# TEST MATERIALE
# ===========================================================
class TestMateriale(unittest.TestCase):

    def setUp(self):
        self.mat = Materiale(1, "Cemento Portland", "kg", 0.15, StatoEntita.ATTIVO, "Tipo 325")
        self.mat_dis = Materiale(2, "Vecchio Prodotto", "pz", 10.0, StatoEntita.DISATTIVATO, "")

    def test_creazione_materiale(self):
        self.assertEqual(self.mat.descrizione, "Cemento Portland")
        self.assertEqual(self.mat.unita_misura, "kg")
        self.assertEqual(self.mat.prezzo_unitario_base, 0.15)

    def test_is_attivo(self):
        self.assertTrue(self.mat.isAttivo())
        self.assertFalse(self.mat_dis.isAttivo())

    def test_prezzo_formattato(self):
        self.assertEqual(self.mat.getPrezzoFormattato(), "€ 0.15/kg")


# ===========================================================
# TEST VOCE OPERAI (Snapshot)
# ===========================================================
class TestVoceOperai(unittest.TestCase):

    def test_costo_totale(self):
        voce = VoceOperai(1, 10, 8.0, 25.0)  # 8h * 25€ = 200€
        self.assertEqual(voce.getCostoTotale(), 200.0)

    def test_costo_totale_mezza_giornata(self):
        voce = VoceOperai(1, 10, 4.5, 30.0)  # 4.5h * 30€ = 135€
        self.assertAlmostEqual(voce.getCostoTotale(), 135.0)

    def test_snapshot_non_cambia(self):
        """Il costo snapshot deve rimanere fisso anche se il costo base dell'operaio cambia"""
        voce = VoceOperai(1, 10, 8.0, 25.0)
        costo_iniziale = voce.getCostoTotale()
        # Simuliamo che l'operaio ha cambiato tariffa, ma la voce è un snapshot
        self.assertEqual(voce.costo_orario_snapshot, 25.0)
        self.assertEqual(costo_iniziale, 200.0)


# ===========================================================
# TEST VOCE MATERIALI (Snapshot)
# ===========================================================
class TestVoceMateriali(unittest.TestCase):

    def test_costo_totale(self):
        voce = VoceMateriali(1, 5, 100.0, 0.15)  # 100kg * 0.15€ = 15€
        self.assertEqual(voce.getCostoTotale(), 15.0)

    def test_costo_totale_decimali(self):
        voce = VoceMateriali(1, 5, 2.5, 12.50)  # 2.5 * 12.50 = 31.25€
        self.assertAlmostEqual(voce.getCostoTotale(), 31.25)


# ===========================================================
# TEST ALLEGATO
# ===========================================================
class TestAllegato(unittest.TestCase):

    def test_nome_file(self):
        a = Allegato(1, 1, "/path/to/foto_cantiere.jpg")
        self.assertEqual(a.getNomeFile(), "foto_cantiere.jpg")

    def test_file_non_esiste(self):
        a = Allegato(1, 1, "/path/inesistente/file.pdf")
        self.assertFalse(a.fileEsiste())


# ===========================================================
# TEST SCHEDA GIORNALIERA
# ===========================================================
class TestSchedaGiornaliera(unittest.TestCase):

    def setUp(self):
        self.scheda = SchedaGiornaliera(1, "2023-10-24", "Posa pavimenti", 1)
        # Aggiungi voci operai
        self.scheda.voci_operai = [
            VoceOperai(1, 10, 8.0, 25.0),   # 200€
            VoceOperai(1, 11, 6.5, 30.0),   # 195€
        ]
        # Aggiungi voci materiali
        self.scheda.voci_materiali = [
            VoceMateriali(1, 5, 100.0, 0.15),  # 15€
            VoceMateriali(1, 6, 10.0, 8.50),   # 85€
        ]

    def test_costo_totale_ore(self):
        self.assertAlmostEqual(self.scheda.getCostoTotaleOre(), 395.0)

    def test_costo_totale_materiali(self):
        self.assertAlmostEqual(self.scheda.getCostoTotaleMateriali(), 100.0)

    def test_costo_totale_complessivo(self):
        self.assertAlmostEqual(self.scheda.getCostoTotale(), 495.0)

    def test_totale_ore(self):
        self.assertAlmostEqual(self.scheda.getTotaleOre(), 14.5)

    def test_scheda_vuota(self):
        vuota = SchedaGiornaliera(2, "2023-10-25", "Vuota", 1)
        self.assertEqual(vuota.getCostoTotale(), 0.0)
        self.assertEqual(vuota.getTotaleOre(), 0.0)
        self.assertFalse(vuota.haAllegati())

    def test_ha_allegati(self):
        self.assertFalse(self.scheda.haAllegati())
        self.scheda.allegati.append(Allegato(1, 1, "/foto.jpg"))
        self.assertTrue(self.scheda.haAllegati())


# ===========================================================
# TEST PROGETTO
# ===========================================================
class TestProgetto(unittest.TestCase):

    def setUp(self):
        self.prog = Progetto(1, "Residenziale Le Vele", 1, "Via Roma 1", "Note progetto", StatoProgetto.IN_CORSO)
        # Scheda con dati
        s1 = SchedaGiornaliera(1, "2023-10-24", "Giorno 1", 1)
        s1.voci_operai = [VoceOperai(1, 10, 8.0, 25.0)]  # 200€
        s1.voci_materiali = [VoceMateriali(1, 5, 50.0, 0.20)]  # 10€
        s2 = SchedaGiornaliera(2, "2023-10-25", "Giorno 2", 1)
        s2.voci_operai = [VoceOperai(2, 10, 4.0, 25.0)]  # 100€
        self.prog.schede_giornaliere = [s1, s2]

    def test_is_in_corso(self):
        self.assertTrue(self.prog.isInCorso())
        self.assertFalse(self.prog.isCompletato())

    def test_is_modificabile(self):
        self.assertTrue(self.prog.isModificabile())

    def test_progetto_completato_non_modificabile(self):
        compl = Progetto(2, "Finito", 1, "", "", StatoProgetto.COMPLETATO)
        self.assertFalse(compl.isModificabile())

    def test_ha_schede(self):
        self.assertTrue(self.prog.haSchede())

    def test_costo_totale_cumulativo(self):
        # Giorno1: 200 + 10 = 210€,  Giorno2: 100€  → Totale: 310€
        self.assertAlmostEqual(self.prog.getCostoTotale(), 310.0)

    def test_totale_ore_cumulativo(self):
        # Giorno1: 8h, Giorno2: 4h → 12h
        self.assertAlmostEqual(self.prog.getTotaleOre(), 12.0)

    def test_totale_materiali(self):
        # Giorno1: 1 voce, Giorno2: 0 voci → 1
        self.assertEqual(self.prog.getTotaleMateriali(), 1)

    def test_progetto_senza_schede(self):
        vuoto = Progetto(3, "Vuoto", 1, "", "", StatoProgetto.IN_CORSO)
        self.assertFalse(vuoto.haSchede())
        self.assertEqual(vuoto.getCostoTotale(), 0.0)
        self.assertEqual(vuoto.getTotaleOre(), 0.0)


if __name__ == '__main__':
    unittest.main()
