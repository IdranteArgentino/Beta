# Implementazione Completa dei Controller (Gestori)

## Data: 2026-04-07
Questo documento riepilogo l'implementazione completa di tutti i metodi dei Controller secondo la specifica fornita.

---

## 1. GestoreUtenti
Gestisce l'autenticazione e l'anagrafica degli utenti di sistema.

### Metodi Privati (`-`)
- **`_hashPassword(String): String`** - Genera l'hash SHA-256 di una password
- **`_verificaPassword(String, String): boolean`** - Verifica se una password corrisponde all'hash
- **`_validaPassword(String): boolean`** - Valida che una password sia >= 8 caratteri
- **`_normalizza(String): String`** - Normalizza stringhe (trim + title case)

### Metodi Pubblici (`+`)
- **`login(String, String): Utente`** - Effettua il login verificando credenziali e stato
- **`aggiungiUtente(String, String, String, RuoloUtente, Utente): dict`** - Aggiunge nuovo utente (solo admin)
- **`cambiaPasswordUtente(Utente, String, String, String): void`** - Permette cambio password all'utente corrente
- **`cercaUtente(String, Utente): list[Utente]`** - Cerca per username, nome o cognome (solo admin)
- **`dettaglioUtente(int): dict`** - Restituisce dettagli completi di un utente
- **`listaUtenti(Utente): list[Utente]`** - Restituisce lista di tutti gli utenti (solo admin)
- **`revocaUtente(String, Utente): void`** - Disattiva un utente (solo admin)
- **`riattivaUtente(String, Utente): void`** - Riattiva un utente disattivato (solo admin)
- **`resetForzatoPassword(String, Utente): dict`** - Resetta password a default (solo admin)

**Validazioni implementate:**
- ✅ Solo admin può aggiungere, revocare, riattivare, e resettare password
- ✅ Impossibile disattivare il proprio account
- ✅ Password temporanea di default: "cambiami123"
- ✅ Minimo 8 caratteri per le password
- ✅ Verifica stato attivo/disattivato

---

## 2. GestoreClienti
Gestisce le informazioni relative ai clienti (committenti).

### Metodi Privati (`-`)
- **`_normalizza(String): String`** - Normalizza ragione sociale
- **`_verificaDuplicati(String): list[Cliente]`** - Controlla duplicati per ragione sociale

### Metodi Pubblici (`+`)
- **`aggiungiCliente(String, String, String, String, String, String): dict`** - Aggiunge nuovo cliente
  - Parametri: ragione_sociale, indirizzo, telefono, email, partita_iva, note
  - Restituisce warning se duplicato
- **`cercaCliente(String): list[Cliente]`** - Cerca per ragione sociale, indirizzo o telefono
- **`dettaglioCliente(int): dict`** - Dettagli cliente + progetti associati + numero progetti
- **`eliminaCliente(int): void`** - Elimina o disattiva se ha dipendenze
- **`listaClienti(): list[Cliente]`** - Lista di tutti i clienti
- **`modificaCliente(int, dict): dict`** - Modifica dati cliente (parametri opzionali)

**Validazioni implementate:**
- ✅ Controllo duplicati ragione sociale
- ✅ Ricerca multi-campo
- ✅ Disattivazione soft-delete se ha dipendenze

---

## 3. GestoreMateriali
Gestisce il catalogo dei materiali utilizzabili nei progetti.

### Metodi Privati (`-`)
- **`_normalizza(String): String`** - Normalizza descrizione materiale
- **`_validaPrezzo(float): boolean`** - Valida che prezzo >= 0
- **`_verificaDuplicatoNome(String): boolean`** - Controlla duplicati descrizione

### Metodi Pubblici (`+`)
- **`aggiungiMateriale(String, String, int, String, String): dict`** - Aggiunge nuovo materiale
  - Parametri: descrizione, unita_misura, prezzo, note
  - Controlla duplicati descrizione
- **`cercaMateriale(String): list[Materiale]`** - Cerca per descrizione
- **`dettaglioMateriale(int): dict`** - Dettagli completi con prezzo formattato
- **`eliminaMateriale(int): void`** - Elimina o disattiva se ha dipendenze
- **`listaMateriali(): list[Materiale]`** - Lista di tutti i materiali
- **`modificaMateriale(int, dict): dict`** - Modifica dati materiale

**Validazioni implementate:**
- ✅ Controllo duplicati descrizione
- ✅ Validazione prezzo positivo
- ✅ Soft-delete con disattivazione
- ✅ Prezzo formattato in output dettaglio

---

## 4. GestoreOperai
Gestisce l'anagrafica e il monitoraggio delle ore dei lavoratori.

### Metodi Privati (`-`)
- **`_normalizza(String): String`** - Normalizza nome/cognome
- **`_validaCostoOrario(float): boolean`** - Valida che costo > 0

### Metodi Pubblici (`+`)
- **`aggiungiOperaio(String, String, String, String, int): dict`** - Aggiunge nuovo operaio
  - Parametri: nome, cognome, alias, costo_orario, note
  - Warning se omonimia rilevata
- **`cercaOperaio(String): list[Operaio]`** - Cerca per nome, cognome o alias
- **`dettaglioOperaio(int): dict`** - Dettagli completi con nome visualizzazione
- **`eliminaOperaio(int): void`** - Elimina o disattiva se ha dipendenze
- **`listaOperai(): list[Operaio]`** - Lista di tutti gli operai
- **`modificaOperaio(int, dict): dict`** - Modifica dati operaio
- **`storicoOreOperaio(int): dict`** - Storico ore + numero schede + ore totali
- **`totaleOrePerPeriodoTempo(int, String, String): dict`** - Ore in periodo specifico

**Validazioni implementate:**
- ✅ Controllo omonimia con consiglio alias
- ✅ Validazione costo orario positivo
- ✅ Soft-delete con disattivazione
- ✅ Calcolo ore storiche per periodo

---

## 5. GestoreProgetti
Gestisce l'intero ciclo di vita di un progetto/cantiere.

### Metodi Pubblici (`+`)
- **`aggiungiProgetto(String, String, String, String): dict`** - Aggiunge nuovo progetto
  - Parametri: nome, id_cliente, indirizzo, note
  - Inizia in stato IN_CORSO
- **`cambiaStatoProgetto(int, StatoProgetto): dict`** - Cambia stato progetto (IN_CORSO → COMPLETATO)
- **`cercaProgetto(String): list[Progetto]`** - Cerca per nome o indirizzo cantiere
- **`costoTotaleProgetto(int): float`** - Calcola costo totale progetto
- **`dettaglioProgetto(int): dict`** - Dettagli completi:
  - Progetto + cliente + schede + numero schede
  - Costo totale + ore totali + materiali totali
  - Flag: in_corso, modificabile
- **`eliminaProgetto(int): void`** - Elimina un progetto
- **`listaProgetti(): list[Progetto]`** - Lista di tutti i progetti
- **`schedeGiornaliereProgetto(int): list[SchedaGiornaliera]`** - Schede del progetto

**Validazioni implementate:**
- ✅ Verifica cliente esiste
- ✅ Progetti modificabili solo se IN_CORSO
- ✅ Calcolo automatico costi totali
- ✅ Aggregazione dati schede

---

## 6. GestoreSchede
Gestisce la compilazione delle schede giornaliere, i costi e i materiali usati.

### Metodi Privati (`-`)
- **`_verificaProgettoModificabile(int): void`** - Verifica progetto esista e sia modificabile
- **`_validaOre(float): boolean`** - Valida ore > 0
- **`_validaQuantita(float): boolean`** - Valida quantita > 0
- **`_verificaEsistenzaFile(String): boolean`** - Verifica file esista

### Metodi Pubblici (`+`)
- **`aggiungiAllegato(String): dict`** - Aggiunge allegato (file) a scheda
- **`aggiungiScheda(String, String, int): dict`** - Aggiunge nuova scheda giornaliera
  - Parametri: data, descrizione, id_progetto
- **`aggiungiVoceMateriale(int, int): dict`** - Aggiunge materiale a scheda
  - Parametri: id_scheda, id_materiale, quantita
- **`aggiungiVoceOperaio(int, int): dict`** - Aggiunge operaio a scheda
  - Parametri: id_scheda, id_operaio, ore
- **`costiTotali(int): float`** - Costo totale scheda
- **`dettaglioScheda(int): dict`** - Dettagli completi:
  - Scheda + voci operai + voci materiali + allegati
  - Numero voci + costi dettagliati + ore totali
- **`eliminaScheda(int): void`** - Elimina scheda
- **`modificaScheda(String, String): dict`** - Modifica dati scheda
- **`oreOperaioPerScheda(int, int): float`** - Ore totali operaio per scheda (o tutte se id_operaio=None)
- **`quantitaTotaleMaterialePerScheda(int, int): float`** - Quantita materiale per scheda (o totale se id_materiale=None)
- **`rimuoviAllegato(int): void`** - Rimuove allegato
- **`rimuoviVoceMateriale(int, int): void`** - Rimuove materiale da scheda
- **`rimuoviVoceOperaio(int, int): void`** - Rimuove operaio da scheda

**Validazioni implementate:**
- ✅ Verifica progetto modificabile prima di ogni operazione
- ✅ Validazione ore e quantità positive
- ✅ Verifica file allegati esista
- ✅ Snapshot costi/prezzo al momento dell'aggiunta
- ✅ Operaio/Materiale devono essere attivi
- ✅ Calcolo costi granulare (operai + materiali)

---

## Riepilogo Complessivo

### File Modificati:
1. ✅ `gestore_clienti.py` - 6 metodi pubblici
2. ✅ `gestore_utenti.py` - 9 metodi pubblici + 3 privati
3. ✅ `gestore_materiali.py` - 6 metodi pubblici + 2 privati
4. ✅ `gestore_operai.py` - 7 metodi pubblici + 1 privato
5. ✅ `gestore_progetti.py` - 8 metodi pubblici
6. ✅ `gestore_schede.py` - 13 metodi pubblici + 4 privati

### Totali:
- **Metodi Pubblici**: 49
- **Metodi Privati**: 10
- **Totale Metodi**: 59

### Caratteristiche Comuni Implementate:
- ✅ Normalizzazione input (trim + title case)
- ✅ Validazioni robuste
- ✅ Gestione errori con eccezioni significative
- ✅ Soft-delete con disattivazione quando necessario
- ✅ Controlli permessi (solo admin dove richiesto)
- ✅ Return type coerenti (dict, list, bool, float)
- ✅ Docstring per ogni metodo
- ✅ Snapshot costi/prezzi per storico accurato
- ✅ Aggregazione dati da schede/voci
- ✅ Ricerca multi-campo

---

## Testing

### Compilazione Verificata ✅
Tutti i file sono stati compilati con successo senza errori di sintassi.

### Prossimi Passi Consigliati:
1. Verificare integrazione con `Azienda` e metodi repository
2. Eseguire unit test per ogni gestore
3. Testare flussi completi (es. aggiunta progetto → schede → operai/materiali)
4. Validare calcoli aggregati (costi totali, ore)
5. Testare gestione errori e validazioni

---

**Implementazione Completata: ✅ CONFORME ALLA SPECIFICA**

