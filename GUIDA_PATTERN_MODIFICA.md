"""
GUIDA AI GESTORI - PATTERN DI MODIFICA UNICO
=============================================================================

PRINCIPIO FONDAMENTALE
=============================================================================

Ogni gestore ha UN SOLO metodo di modifica principale: modifica()

Questo metodo:
✅ Accetta TUTTI i campi modifcabili come parametri opzionali (default None)
✅ Aggiorna SOLO i campi forniti (non None)
✅ Se un campo è None, NON viene toccato nel database
✅ Se NESSUN campo è fornito, restituisce True (idempotente)
✅ Ritorna True se successo, False se errore


=============================================================================
PATTERN DI UTILIZZO
=============================================================================

# SCENARIO 1: Modificare un solo campo
gestore_clienti.modifica(id_cliente=1, telefono="123456789")
# ➜ Aggiorna SOLO il telefono, gli altri campi rimangono uguali

# SCENARIO 2: Modificare più campi contemporaneamente
gestore_clienti.modifica(
    id_cliente=1, 
    ragione_sociale="Nuova Ragione",
    indirizzo="Via Roma 456",
    telefono="987654321"
)
# ➜ Aggiorna TUTTI e tre i campi in una sola query

# SCENARIO 3: Nessuna modifica (idempotente)
gestore_clienti.modifica(id_cliente=1)
# ➜ Restituisce True senza fare nulla

# SCENARIO 4: Dalla vista (PyQt/Jinja)
# Prendi i valori dai campi input
nuovo_telefono = input_field.text()
nuovo_indirizzo = input_field2.text()

# Se il campo è stato lasciato vuoto, è None
if nuovo_telefono == "":
    nuovo_telefono = None
if nuovo_indirizzo == "":
    nuovo_indirizzo = None

# Chiama modifica una sola volta
if gestore_clienti.modifica(id_cliente=1, telefono=nuovo_telefono, indirizzo=nuovo_indirizzo):
    print("Modifiche salvate!")
else:
    print("Errore nella modifica")


=============================================================================
METODI DI MODIFICA PER GESTORE
=============================================================================

📌 GESTORE UTENTI
-------------------
gestore_utenti.modifica(
    username: str,                    # username ATTUALE (identificatore)
    nome: str = None,
    cognome: str = None,
    password_hash: str = None,
    stato: StatoEntita = None,
    ruolo: RuoloUtente = None,
    nuovo_username: str = None        # per cambiare lo username
) -> bool

Esempio:
    gestore_utenti.modifica("mario.rossi", nome="Mario", cognome="Bianchi")
    # Cambia nome e cognome, lascia il resto invariato


📌 GESTORE CLIENTI
-------------------
gestore_clienti.modifica(
    id_cliente: int,
    ragione_sociale: str = None,
    indirizzo: str = None,
    telefono: str = None,
    note: str = None,
    stato: StatoEntita = None
) -> bool

Esempio:
    gestore_clienti.modifica(1, telefono="123456789", note="Cliente VIP")
    # Aggiorna solo telefono e note


📌 GESTORE OPERAI
-------------------
gestore_operai.modifica(
    id_operaio: int,
    nome: str = None,
    cognome: str = None,
    alias: str = None,
    costo_orario_base: float = None,
    stato: StatoEntita = None,
    note: str = None
) -> bool

Esempio:
    gestore_operai.modifica(1, costo_orario_base=27.50, stato=StatoEntita.ATTIVO)
    # Aumenta il costo orario e attiva l'operaio


📌 GESTORE MATERIALI
-------------------
gestore_materiali.modifica(
    id_materiale: int,
    descrizione: str = None,
    unita_misura: str = None,
    prezzo_unitario_base: float = None,
    stato: StatoEntita = None,
    note: str = None
) -> bool

Esempio:
    gestore_materiali.modifica(5, prezzo_unitario_base=12.50)
    # Aggiorna solo il prezzo


📌 GESTORE PROGETTI
-------------------
gestore_progetti.modifica(
    id_progetto: int,
    nome_progetto: str = None,
    id_cliente: int = None,
    indirizzo_cantiere: str = None,
    stato: StatoProgetto = None,
    note: str = None
) -> bool

Esempio:
    gestore_progetti.modifica(1, stato=StatoProgetto.COMPLETATO)
    # Cambia lo stato a completato


📌 GESTORE SCHEDE
-------------------
gestore_schede.modifica(
    id_scheda: int,
    data: str = None,
    descrizione: str = None
) -> bool

Esempio:
    gestore_schede.modifica(1, descrizione="Lavori sul tetto")
    # Aggiorna la descrizione


gestore_schede.modifica_ore_operaio(
    id_scheda: int,
    id_operaio: int,
    ore_lavorate: float = None,
    costo_orario_snapshot: float = None
) -> bool

Esempio:
    gestore_schede.modifica_ore_operaio(1, 5, ore_lavorate=9.5)
    # Cambia solo le ore dell'operaio 5 sulla scheda 1


gestore_schede.modifica_materiale_a_scheda(
    id_scheda: int,
    id_materiale: int,
    quantita: float = None,
    prezzo_unitario_snapshot: float = None
) -> bool

Esempio:
    gestore_schede.modifica_materiale_a_scheda(1, 3, quantita=50.0)
    # Cambia solo la quantità del materiale 3


=============================================================================
VANTAGGI DI QUESTO PATTERN
=============================================================================

✅ UNA SOLA QUERY SQL PER OGNI MODIFICA
   (non importa quanti campi sono stati modificati)

✅ INTERFACCIA SEMPLICE E INTUITIVA
   - Chiami modifica() e passi quello che vuoi cambiare
   - I parametri non passati rimangono come sono

✅ FACILE DA USARE NELLE VISTE
   - Prendi i valori dai form
   - Se vuoto, lascia None
   - Chiami modifica() con tutti i campi

✅ IDEMPOTENTE
   - Puoi chiamare modifica() senza campi e non succede nulla
   - Perfetto per logica difensiva

✅ MANUTENIBILE
   - Un solo metodo per entità, non 10 metodi diversi
   - Meno codice duplicato
   - Più facile aggiungere/rimuovere campi


=============================================================================
ESEMPIO COMPLETO: VISTA MODIFICA CLIENTE (PyQt)
=============================================================================

class VistaModificaCliente(QDialog):
    def __init__(self, azienda, gestore_clienti, id_cliente):
        super().__init__()
        self.azienda = azienda
        self.gestore = gestore_clienti
        self.cliente = azienda.trova_cliente(id_cliente)
        self.setup_ui()
    
    def setup_ui(self):
        # Crea form con i dati attuali
        self.input_ragione = QLineEdit(self.cliente.ragione_sociale)
        self.input_indirizzo = QLineEdit(self.cliente.indirizzo)
        self.input_telefono = QLineEdit(self.cliente.telefono)
        self.input_note = QTextEdit(self.cliente.note)
        
        btn_conferma = QPushButton("Conferma Modifica")
        btn_conferma.clicked.connect(self.conferma_modifica)
        
        # Layout...
    
    def conferma_modifica(self):
        # Raccogli i valori dai campi
        ragione = self.input_ragione.text()
        indirizzo = self.input_indirizzo.text()
        telefono = self.input_telefono.text()
        note = self.input_note.toPlainText()
        
        # Converti stringhe vuote a None
        ragione = ragione if ragione.strip() else None
        indirizzo = indirizzo if indirizzo.strip() else None
        telefono = telefono if telefono.strip() else None
        note = note if note.strip() else None
        
        # UNA SOLA CHIAMATA, indipendentemente da quanti campi hai modificato
        if self.gestore.modifica(
            self.cliente.id,
            ragione_sociale=ragione,
            indirizzo=indirizzo,
            telefono=telefono,
            note=note
        ):
            QMessageBox.information(self, "Successo", "Cliente modificato!")
            self.accept()
        else:
            QMessageBox.critical(self, "Errore", "Errore nella modifica del cliente")


=============================================================================
ESEMPIO COMPLETO: VISTA MODIFICA CLIENTE (Jinja2)
=============================================================================

<!-- modifica_cliente.html -->
<form method="POST">
    <label>Ragione Sociale:</label>
    <input type="text" name="ragione_sociale" value="{{ cliente.ragione_sociale }}" />
    
    <label>Indirizzo:</label>
    <input type="text" name="indirizzo" value="{{ cliente.indirizzo }}" />
    
    <label>Telefono:</label>
    <input type="text" name="telefono" value="{{ cliente.telefono }}" />
    
    <label>Note:</label>
    <textarea name="note">{{ cliente.note }}</textarea>
    
    <button type="submit">Conferma Modifica</button>
</form>

# Nel backend Flask
@app.route('/clienti/<int:id>/modifica', methods=['POST'])
def modifica_cliente(id):
    # Raccogli solo i campi che sono stati compilati
    dati = {}
    if request.form.get('ragione_sociale', '').strip():
        dati['ragione_sociale'] = request.form['ragione_sociale']
    if request.form.get('indirizzo', '').strip():
        dati['indirizzo'] = request.form['indirizzo']
    if request.form.get('telefono', '').strip():
        dati['telefono'] = request.form['telefono']
    if request.form.get('note', '').strip():
        dati['note'] = request.form['note']
    
    # UNA SOLA CHIAMATA
    if gestore_clienti.modifica(id, **dati):
        return redirect(f'/clienti/{id}')
    else:
        return "Errore nella modifica", 400


=============================================================================
DOMANDE FREQUENTI
=============================================================================

D: Cosa succede se passo None esplicitamente?
R: Viene trattato come "non modificare questo campo", quindi il valore nel DB
   rimane invariato. Perfetto per i form vuoti.

D: E se voglio davvero impostare un campo a NULL nel database?
R: Attualmente il pattern non lo permette (per sicurezza). Se necessario,
   puoi aggiungere un parametro speciale come force_null=True.

D: Posso modificare un campo a stringa vuota?
R: Sì, basta passare "" (stringa vuota), che è diverso da None.
   - None = non modificare
   - "" = impostare a stringa vuota

D: Quante query SQL vengono eseguite?
R: Una sola, indipendentemente da quanti campi modifichi.
   Il metodo costruisce dinamicamente la query UPDATE.

D: E se faccio un errore nella modifica?
R: Il metodo ritorna False e stampa l'errore in console. 
   La transazione non viene committata, quindi il DB rimane coerente.

=============================================================================
"""

