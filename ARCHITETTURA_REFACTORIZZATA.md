   - aggiorna_* (aggiornamenti di campo)
   - storico_* (statistiche e aggregazioni)
   - operazioni complesse


=============================================================================
RESPONSABILITÀ DEI GESTORI
=============================================================================

Ogni gestore gestisce la logica di modifica e operazioni complesse per una 
categoria di oggetti. I gestori accedono sia ad Azienda che direttamente al DB.


GESTORE UTENTI (gestore_utenti.py):
----------------------------------
Modifiche:
  - modifica_username(username_attuale, nuovo_username)
  - modifica_dati_personali(username, nome, cognome)
  - modifica_password(username, password_hash)
  - modifica_stato(username, stato)
  - modifica_ruolo(username, nuovo_ruolo)

Validazioni:
  - esiste_username(username)


GESTORE CLIENTI (gestore_clienti.py):
-------------------------------------
Modifiche:
  - modifica_ragione_sociale(id_cliente, nuova_ragione)
  - modifica_indirizzo(id_cliente, nuovo_indirizzo)
  - modifica_telefono(id_cliente, nuovo_telefono)
  - modifica_note(id_cliente, nuove_note)
  - modifica_stato(id_cliente, stato)
  - modifica_dati_contatto(id_cliente, indirizzo, telefono, note)

Operazioni complesse:
  - get_progetti_cliente(id_cliente) → lista progetti
  - get_totale_progetti(id_cliente) → numero progetti


GESTORE OPERAI (gestore_operai.py):
-----------------------------------
Modifiche:
  - modifica_nome(id_operaio, nuovo_nome)
  - modifica_cognome(id_operaio, nuovo_cognome)
  - modifica_alias(id_operaio, nuovo_alias)
  - modifica_costo_orario(id_operaio, nuovo_costo)
  - modifica_note(id_operaio, nuove_note)
  - modifica_stato(id_operaio, stato)

Statistiche:
  - get_storico_ore(id_operaio) → ore totali, ricavi, numero schede
  - get_ore_per_progetto(id_operaio) → ore e ricavi divisi per progetto


GESTORE MATERIALI (gestore_materiali.py):
------------------------------------------
Modifiche:
  - modifica_descrizione(id_materiale, nuova_descrizione)
  - modifica_unita_misura(id_materiale, nuova_unita)
  - modifica_prezzo_unitario(id_materiale, nuovo_prezzo)
  - modifica_note(id_materiale, nuove_note)
  - modifica_stato(id_materiale, stato)

Statistiche:
  - get_storico_utilizzo(id_materiale) → quantità, costo, numero schede
  - get_utilizzo_per_progetto(id_materiale) → utilizzo diviso per progetto


GESTORE PROGETTI (gestore_progetti.py):
----------------------------------------
Modifiche:
  - modifica_nome(id_progetto, nuovo_nome)
  - modifica_indirizzo_cantiere(id_progetto, nuovo_indirizzo)
  - modifica_note(id_progetto, nuove_note)
  - modifica_stato(id_progetto, stato)
  - modifica_cliente(id_progetto, id_cliente)

Statistiche e Costi:
  - get_totale_ore(id_progetto) → ore totali
  - get_costo_operai(id_progetto) → costo manodopera
  - get_costo_materiali(id_progetto) → costo materiali
  - get_costo_totale(id_progetto) → riepilogo completo
  - get_numero_schede(id_progetto) → numero schede


GESTORE SCHEDE (gestore_schede.py):
-----------------------------------
Modifiche:
  - modifica_data(id_scheda, nuova_data)
  - modifica_descrizione(id_scheda, nuova_descrizione)
  - aggiungi_operaio_a_scheda(id_scheda, id_operaio, ore, costo)
  - modifica_ore_operaio(id_scheda, id_operaio, nuove_ore)
  - aggiungi_materiale_a_scheda(id_scheda, id_materiale, quantita, prezzo)
  - modifica_quantita_materiale(id_scheda, id_materiale, nuova_quantita)
  - aggiungi_allegato(id_scheda, path)

Statistiche:
  - get_costo_totale_scheda(id_scheda) → costo operai + materiali
  - get_ore_totali_scheda(id_scheda) → ore totali


=============================================================================
ESEMPIO DI USO
=============================================================================

# Inizializzazione
from azienda import Azienda
from gestori import (
    GestoreUtenti, GestoreClienti, GestoreOperai,
    GestoreMateriali, GestoreProgetti, GestoreSchede
)

azienda = Azienda("data/gestionale.db")
gestore_utenti = GestoreUtenti(azienda)
gestore_clienti = GestoreClienti(azienda)
gestore_operai = GestoreOperai(azienda)
gestore_progetti = GestoreProgetti(azienda)
gestore_schede = GestoreSchede(azienda)


# Aggiungere un nuovo cliente (AZIENDA)
from models import Cliente, StatoEntita
cliente = Cliente(None, "Ditta XYZ", "Via Roma 123", "123456789", "Cliente importante", StatoEntita.ATTIVO)
azienda.aggiungi_cliente(cliente)
print(f"Cliente aggiunto con ID: {cliente.id}")


# Modificare il cliente (GESTORE)
gestore_clienti.modifica_telefono(cliente.id, "987654321")
gestore_clienti.modifica_note(cliente.id, "Cliente VIP - sempre prioritario")


# Ottenere informazioni sui progetti del cliente (GESTORE)
progetti = gestore_clienti.get_progetti_cliente(cliente.id)
print(f"Progetti del cliente: {len(progetti)}")


# Aggiungere un nuovo operaio (AZIENDA)
from models import Operaio
operaio = Operaio(None, "Mario", "Rossi", "Mario", 25.50, StatoEntita.ATTIVO, "Esperto")
azienda.aggiungi_operaio(operaio)


# Modificare il costo orario dell'operaio (GESTORE)
gestore_operai.modifica_costo_orario(operaio.id, 27.00)


# Ottenere statistiche sull'operaio (GESTORE)
storico = gestore_operai.get_storico_ore(operaio.id)
print(f"Ore totali: {storico['ore_totali']}, Ricavo: {storico['ricavo_totale']}")


# Aggiungere una scheda giornaliera (AZIENDA)
from models import SchedaGiornaliera
scheda = SchedaGiornaliera(None, "2024-04-07", "Lavori in cantiere", 1)
azienda.aggiungi_scheda(scheda)


# Aggiungere operaio alla scheda (GESTORE)
gestore_schede.aggiungi_operaio_a_scheda(scheda.id, operaio.id, 8.0, 25.50)


# Ottenere costo della scheda (GESTORE)
costo_scheda = gestore_schede.get_costo_totale_scheda(scheda.id)
print(f"Costo scheda: {costo_scheda['costo_totale']}")


# Ottenere costo totale del progetto (GESTORE)
costo_progetto = gestore_progetti.get_costo_totale(1)
print(f"Costo totale progetto: {costo_progetto['costo_totale']}")


=============================================================================
VANTAGGI DI QUESTA ARCHITETTURA
=============================================================================

✅ Separazione delle responsabilità (SRP - Single Responsibility Principle)
✅ Azienda rimane semplice e manutenibile
✅ Gestori concentrano tutta la logica di modifica e business logic
✅ Facile da testare (AZIENDA = DB access, GESTORI = business logic)
✅ Estendibile: aggiungere nuovi gestori non modifica Azienda
✅ Riusabile: ogni gestore può essere usato indipendentemente
✅ Facile da documentare: ogni gestore ha responsabilità chiare
✅ Errori gestiti a livello gestore, non a livello di accesso DB


=============================================================================
PER LE VISTE
=============================================================================

Le viste (PyQt o Jinja2) dovrebbero:

1. Usare AZIENDA per letture semplici (trova, lista)
2. Usare GESTORI per modifiche
3. Usare GESTORI per operazioni complesse (statistiche, costi)

Esempio vista cliente in PyQt:

class VistaDettaglioCliente:
    def __init__(self, azienda, gestore_clienti, id_cliente):
        self.azienda = azienda
        self.gestore = gestore_clienti
        self.cliente = azienda.trova_cliente(id_cliente)
        self.progetti = gestore_clienti.get_progetti_cliente(id_cliente)
    
    def aggiorna_telefono(self, nuovo_telefono):
        if self.gestore.modifica_telefono(self.cliente.id, nuovo_telefono):
            # refresh UI
            self.cliente = self.azienda.trova_cliente(self.cliente.id)
        else:
            # mostri errore
            pass


=============================================================================
"""
"""
ARCHITETTURA REFACTORIZZATA - GUIDA ALL'USO

=============================================================================
RESPONSABILITÀ DELLA CLASSE AZIENDA
=============================================================================

La classe Azienda è ora un REPOSITORY PURO con SOLE operazioni base:

✅ OPERAZIONI PERMESSE IN AZIENDA:
   - aggiungi_* (aggiungere nuovi oggetti)
   - trova_* (leggere singoli oggetti)
   - lista_* (leggere liste di oggetti)
   - elimina_* (eliminare oggetti)
   - schede_per_progetto, progetti_per_cliente (query semplici di relazione)
   - voci_operai_per_scheda, voci_materiali_per_scheda (getter di dati correlati)

❌ OPERAZIONI NON PERMESSE IN AZIENDA (SPOSTATE NEI GESTORI):
   - modifica_* (tutte le modifiche)

