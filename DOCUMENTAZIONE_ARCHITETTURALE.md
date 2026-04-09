# Documentazione architetturale del gestionale

## 1. Obiettivo iniziale del progetto

Questo progetto nasce per rispondere a un’esigenza molto concreta: **gestire in modo ordinato e centralizzato il lavoro operativo di un’azienda** che lavora con clienti, operai, materiali, progetti e schede giornaliere.

L’obiettivo non è soltanto “salvare dati”, ma costruire un piccolo sistema gestionale capace di:

- mantenere anagrafiche pulite e aggiornabili;
- collegare ogni progetto al relativo cliente;
- registrare le attività svolte giornalmente;
- tenere traccia delle ore degli operai e dei materiali scaricati;
- conservare allegati e documenti collegati alle schede;
- offrire una dashboard iniziale utile per capire subito lo stato del lavoro;
- consentire la gestione degli utenti con ruoli diversi, soprattutto con privilegi amministrativi.

In altre parole, il progetto vuole trasformare una gestione che potrebbe essere dispersiva, manuale o frammentata in una struttura coerente, consultabile e modificabile da interfaccia web.

Il punto importante è che il gestionale non nasce come semplice archivio: nasce come **strumento operativo**, cioè come applicazione che aiuta a lavorare ogni giorno. Per questo motivo il progetto ha una struttura a livelli molto precisa:

1. il database conserva i dati;
2. i modelli rappresentano le entità del dominio;
3. `Azienda` fa da contenitore e punto di accesso al dominio;
4. i gestori applicano le regole e compiono operazioni sui dati;
5. `webapp.py` riceve le richieste HTTP e decide cosa mostrare o cosa salvare;
6. i template mostrano le informazioni all’utente;
7. il CSS definisce l’aspetto grafico e l’esperienza visiva.

Questa separazione è molto importante, perché evita di mescolare le responsabilità e rende il progetto più leggibile, manutenibile e ampliabile.

---

## 2. Visione generale dell’architettura

L’architettura del gestionale è organizzata in modo abbastanza classico per un’app Flask:

- **`main.py`** avvia l’applicazione;
- **`webapp.py`** crea l’app Flask, registra le route e orchestra il flusso;
- **`database.py`** inizializza il database SQLite e crea eventuali tabelle o aggiornamenti minimi;
- **`azienda.py`** rappresenta il contenitore del dominio e il ponte verso i dati;
- **`gestori/`** contiene la logica applicativa per ciascun dominio funzionale;
- **`models/`** contiene le classi che descrivono le entità del sistema;
- **`templates/`** contiene i file Jinja2 che costruiscono la UI;
- **`static/app.css`** contiene tutta la parte estetica e di layout.

L’idea di fondo è semplice ma molto importante:

> il database non deve parlare direttamente con il template, e il template non deve conoscere il database.

Tra i due ci sono i livelli intermedi, che servono proprio a separare i ruoli.

---

## 3. Il ruolo delle classi `models`

La cartella `models` rappresenta il **dominio puro** del progetto. Qui non c’è la parte visiva, non c’è il routing Flask, non c’è il rendering HTML. Qui ci sono solo gli oggetti che descrivono il mondo del gestionale.

L’idea dei modelli è questa: invece di lavorare sempre con righe di database, dizionari sparsi o tuple anonime, il progetto usa oggetti con attributi e metodi propri.

Questo ha diversi vantaggi:

- il codice diventa più leggibile;
- ogni entità ha un significato preciso;
- si possono aggiungere metodi utili al dominio;
- si riduce il rischio di confusione tra campi simili;
- si facilita il passaggio dei dati tra livelli diversi.

### 3.1 Le enumerazioni

Nel file `models/enumerazioni.py` ci sono le enumerazioni fondamentali:

- `RuoloUtente` con i valori `ADMIN` e `STAFF`;
- `StatoEntita` con i valori `ATTIVO` e `DISATTIVATO`;
- `StatoProgetto` con i valori `IN_CORSO` e `COMPLETATO`.

Le enumerazioni servono a evitare errori e a standardizzare i valori.

Ad esempio:

- un utente non dovrebbe avere un ruolo scritto in modo ambiguo;
- uno stato non dovrebbe essere una stringa libera;
- un progetto dovrebbe essere sempre “in corso” oppure “completato”, senza versioni alternative o errori di battitura.

Le enum danno quindi **rigidità utile** al dominio: il sistema diventa più prevedibile.

### 3.2 `Utente`

La classe `Utente` rappresenta un account applicativo.

Campi principali:

- `id`;
- `username`;
- `nome`;
- `cognome`;
- `password` salvata come hash SHA-256;
- `stato`;
- `ruolo`.

Metodi importanti:

- `verificaPassword()` per controllare la password inserita;
- `isAttivo()` per sapere se l’utente può accedere;
- `isAdmin()` per capire se ha privilegi amministrativi;
- `getNomeCompleto()` per costruire una rappresentazione leggibile.

Questa classe non gestisce login HTTP, sessioni o pagine: si limita a rappresentare l’utente come entità di dominio.

### 3.3 `Cliente`

La classe `Cliente` rappresenta il committente o soggetto associato a uno o più progetti.

Campi principali:

- `id`;
- `ragione_sociale`;
- `nome` e `cognome`;
- `indirizzo`;
- `telefono`;
- `note`;
- `stato`;
- `progetti`, popolata dal repository o dal livello dati.

Metodi utili:

- `isAttivo()`;
- `haProgetti()`;
- `getNumeroProgetti()`.

Qui si vede già una caratteristica importante del dominio: il cliente non è solo un record anagrafico, ma può avere relazioni con progetti collegati.

### 3.4 `Operaio`

La classe `Operaio` rappresenta la risorsa umana che può essere assegnata alle schede giornaliere.

Campi principali:

- `id`;
- `nome`;
- `cognome`;
- `alias`;
- `costo_orario_base`;
- `stato`;
- `note`.

Metodi:

- `isAttivo()`;
- `getNomeCompleto()`;
- `getNomeVisualizzazione()`.

Il metodo di visualizzazione è importante perché il sistema può mostrare un nome più leggibile all’utente, ad esempio includendo un alias se presente.

### 3.5 `Materiale`

La classe `Materiale` rappresenta un bene o una risorsa consumabile.

Campi principali:

- `id`;
- `descrizione`;
- `unita_misura`;
- `prezzo_unitario_base`;
- `stato`;
- `note`.

Metodi:

- `isAttivo()`;
- `getPrezzoFormattato()`.

Anche qui il modello non fa UI, ma fornisce un metodo utile alla rappresentazione del dato in forma leggibile.

### 3.6 `Progetto`

La classe `Progetto` è una delle entità centrali del sistema.

Campi principali:

- `id`;
- `nome_progetto`;
- `id_cliente`;
- `indirizzo_cantiere`;
- `note`;
- `stato`;
- `schede_giornaliere`.

Metodi significativi:

- `isInCorso()`;
- `isAttivo()` come alias;
- `isCompletato()`;
- `isModificabile()`;
- `haSchede()`;
- `getCostoTotale()`;
- `getTotaleOre()`;
- `getTotaleMateriali()`.

Il progetto non è solo un nome: è il contenitore logico di attività, costi e schede. È quindi un nodo fondamentale dell’applicazione.

### 3.7 `SchedaGiornaliera`, `VoceOperai`, `VoceMateriali`, `Allegato`

Questi sono i modelli operativi più dinamici.

#### `VoceOperai`
Rappresenta le ore di un operaio su una scheda giornaliera.

- `id_scheda`;
- `id_operaio`;
- `ore_lavorate`;
- `costo_orario_snapshot`.

Il concetto di snapshot è fondamentale: il costo salvato nella voce non dipende più da un eventuale cambio futuro del prezzo base dell’operaio.

Metodi:

- `getCostoTotale()`.

#### `VoceMateriali`
Rappresenta il consumo di materiale su una scheda.

- `id_scheda`;
- `id_materiale`;
- `quantita`;
- `prezzo_unitario_snapshot`.

Anche qui lo snapshot serve a congelare il valore usato al momento della registrazione.

Metodi:

- `getCostoTotale()`.

#### `Allegato`
Rappresenta un file collegato a una scheda.

- `id`;
- `id_scheda`;
- `path`;
- `nome_file`.

Metodi:

- `fileEsiste()`;
- `getNomeFile()`.

Questa classe collega il mondo del database al filesystem.

#### `SchedaGiornaliera`
È il centro operativo della gestione quotidiana.

Campi:

- `id`;
- `data`;
- `descrizione`;
- `id_progetto`;
- `voci_operai`;
- `voci_materiali`;
- `allegati`.

Metodi:

- `getCostoTotaleOre()`;
- `getCostoTotaleMateriali()`;
- `getCostoTotale()`;
- `getTotaleOre()`;
- `haAllegati()`.

La scheda è il punto in cui convergono lavoro, materiali e documenti. Per questo è uno degli oggetti più importanti dell’intero sistema.

---

## 4. A cosa serve `Azienda`

La classe `Azienda` è un elemento di raccordo nel progetto.

Dal punto di vista concettuale, è un **contenitore del dominio**. Dal punto di vista pratico, oggi funge anche da **facciata verso il database** per alcune operazioni di lookup.

Nel file `azienda.py` si vede che la classe:

- conserva il `db_path`;
- mantiene alcune liste interne di oggetti di dominio;
- espone metodi come `trova_cliente`, `trova_operaio`, `trova_materiale`, `trova_progetto`, `trova_scheda`;
- carica oggetti completi dal database;
- popola relazioni come le schede di un progetto e le relative voci.

Quindi il suo ruolo è importante perché rappresenta una specie di **nodo centrale del dominio applicativo**.

### 4.1 Perché esiste

Serve a dare una base unica agli altri livelli. In pratica, i gestori ricevono una istanza di `Azienda` e la usano come riferimento comune per accedere ai dati.

### 4.2 Cosa fa concretamente

`Azienda` si occupa di:

- recuperare entità dal database quando serve una visione completa;
- costruire oggetti di modello a partire dalle righe SQL;
- offrire accessi coerenti al dominio;
- raccogliere relazioni tra entità correlate.

Per esempio, `trova_progetto()` non si limita a leggere la riga del progetto, ma carica anche le schede giornaliere collegate e le relative voci di operai e materiali.

### 4.3 Un’osservazione architetturale importante

Nel progetto attuale `Azienda` è una classe di dominio con una natura un po’ ibrida: da un lato è un contenitore, dall’altro contiene ancora logica di accesso ai dati per compatibilità con i gestori esistenti.

Questo non è per forza un problema, ma è bene capirlo chiaramente:

- **non è la UI**;
- **non è la route HTTP**;
- **non è il template**;
- **non è il gestore**;
- è piuttosto una base centrale che aiuta i livelli superiori a parlare con il dominio e con i dati.

---

## 5. A cosa servono i gestori

I gestori sono il vero livello di **logica applicativa**.

Ogni dominio principale ha il suo gestore:

- `GestoreClienti`
- `GestoreOperai`
- `GestoreMateriali`
- `GestoreProgetti`
- `GestoreSchede`
- `GestoreUtenti`

La loro funzione non è mostrare dati, ma **gestire operazioni**.

### 5.1 Responsabilità dei gestori

Un gestore si occupa di:

- creare, modificare ed eliminare record;
- applicare regole di validazione;
- controllare duplicati o condizioni particolari;
- comporre dati complessi;
- restituire oggetti o liste utili alla `webapp`;
- proteggere il dominio da operazioni incoerenti.

### 5.2 Perché sono utili

Se ogni route Flask dovesse parlare direttamente con SQL, il progetto diventerebbe presto disordinato. I gestori evitano questo problema perché centralizzano la logica del dominio.

Questo porta a diversi benefici:

- il codice è più riusabile;
- la `webapp` resta più pulita;
- le regole non si duplicano in tante route;
- è più facile fare test;
- è più semplice cambiare l’implementazione interna.

### 5.3 Esempi pratici

#### `GestoreClienti`
Gestisce:

- aggiunta cliente;
- modifica cliente;
- cancellazione;
- ricerca;
- dettaglio;
- eventuale controllo su entità collegate.

#### `GestoreOperai`
Gestisce:

- anagrafica operaio;
- modifica dati;
- ricerca;
- controllo costo orario;
- dettaglio.

#### `GestoreMateriali`
Gestisce:

- descrizione;
- unità di misura;
- prezzo unitario;
- stati;
- ricerca.

#### `GestoreProgetti`
Gestisce:

- creazione progetto;
- stato progetto;
- ricerca;
- dettaglio aggregato;
- costo totale;
- modifiche;
- eliminazione.

È uno dei gestori più importanti perché lavora su un’entità centrale del flusso operativo.

#### `GestoreSchede`
Gestisce:

- schede giornaliere;
- assegnazione ore operai;
- scarico materiali;
- allegati;
- rimozioni;
- sostituzioni;
- dashboard;
- liste e dettagli operativi.

È probabilmente il gestore più complesso, perché concentra la logica delle attività quotidiane e il collegamento con il filesystem.

#### `GestoreUtenti`
Gestisce:

- login;
- creazione utenti;
- modifica utenti;
- stato attivo/disattivo;
- reset password;
- cambio password;
- permessi amministrativi.

Questo gestore è fondamentale anche per la sicurezza applicativa.

---

## 6. Cosa fa `webapp.py`

`webapp.py` è il cuore della parte HTTP del progetto.

Qui non si definisce il dominio, ma si decide come il dominio viene esposto al browser.

### 6.1 `create_app`

La funzione `create_app()` crea l’istanza Flask e inizializza tutto il necessario:

- prepara la cartella `data`;
- definisce il path del database;
- richiama `inizializza_db()`;
- crea un’istanza di `Azienda`;
- istanzia tutti i gestori;
- registra le route;
- configura la chiave segreta dell’app.

Questa è una scelta molto buona perché rende l’applicazione più flessibile e più testabile.

### 6.2 Autenticazione e autorizzazione

Nel file ci sono due decoratori importanti:

- `login_required`
- `admin_required`

Il primo impedisce l’accesso alle sezioni private se l’utente non è autenticato.
Il secondo restringe l’accesso alle funzioni amministrative.

Questa logica non appartiene ai gestori, perché riguarda la richiesta HTTP e la sessione, quindi è giusto che stia nella `webapp`.

### 6.3 Context processor

La funzione `inject_globals()` rende disponibili ai template vari dati comuni:

- `current_user`;
- `is_admin`;
- `active_section`.

Questo evita di ripetere la stessa logica in ogni template e rende possibile evidenziare il menu attivo.

### 6.4 Flusso delle route

Ogni route segue uno schema molto chiaro:

1. riceve la richiesta;
2. legge i parametri;
3. chiede i dati al gestore;
4. prepara eventuali variabili per la pagina;
5. richiama `render_template(...)` oppure `redirect(...)`;
6. usa `flash(...)` per comunicare esiti o errori.

Questo è esattamente il comportamento corretto di uno strato web ben separato.

### 6.5 Esempi di responsabilità della `webapp`

#### Home
La route `/` recupera la dashboard tramite `gestori["schede"].dashboardData()` e la passa al template `home.html`.

La `webapp` non calcola direttamente i dati contabili: li chiede al gestore.

#### Login e logout
La route `/login` verifica le credenziali e imposta la sessione.
La route `/logout` svuota la sessione.

#### CRUD delle sezioni
Per clienti, operai, materiali, progetti e utenti la `webapp`:

- riceve i parametri del form;
- controlla il metodo GET/POST;
- chiama il gestore giusto;
- decide se mostrare il dettaglio o tornare alla lista.

#### Giornaliero
La sezione giornaliera è una delle più ricche perché:

- filtra le schede;
- costruisce la paginazione;
- prepara il calendario;
- organizza la mappa delle celle;
- gestisce aggiunta e rimozione di operai e materiali;
- gestisce upload, sostituzione e visualizzazione allegati.

Tutta questa parte è giustamente orchestrata nella `webapp`, perché è molto legata alla pagina e alla sua interazione.

### 6.6 Perché qui non va la presentazione

La `webapp` non deve diventare un posto dove si impasta tutto. Deve solo orchestrare.

Quindi:

- se qualcosa riguarda il DB o il dominio, la delega al gestore;
- se qualcosa riguarda sessione, redirect, flash o rendering, la gestisce lei;
- se qualcosa riguarda la forma visiva, la demandano ai template e al CSS.

---

## 7. Estetica e linea visiva del progetto

L’estetica del gestionale è chiaramente ispirata a uno stile moderno, pulito e “Apple-like”.

Lo si vede già da `static/app.css`, dove compaiono:

- variabili colore ben definite;
- sfondi chiari;
- trasparenze leggere;
- blur e glassmorphism;
- ombre morbide;
- bordi sottili;
- layout responsive;
- pulsanti con gerarchia visiva netta.

### 7.1 Cosa richiama lo stile

Lo stile visivo si ispira a:

- interfacce minimaliste;
- macOS / iOS;
- dashboard moderne SaaS;
- pannelli chiari e leggibili;
- navigazione semplice ma elegante.

Non è uno stile rumoroso o aggressivo. L’obiettivo è dare un’impressione di ordine, pulizia e affidabilità.

### 7.2 Gli elementi principali del CSS

Tra i più importanti ci sono:

- la `topbar` sticky con blur;
- il logo/brand a sinistra;
- il menu di navigazione con stato attivo;
- il menu profilo;
- card e pannelli con ombre leggere;
- pulsanti coerenti;
- tabelle e liste leggibili;
- badge di stato;
- modali di conferma;
- loader per operazioni asincrone o attese.

La presenza di questi elementi fa capire che l’interfaccia non è pensata solo per “funzionare”, ma anche per risultare gradevole e professionale.

### 7.3 Riferimento concreto ai template

L’estetica si riflette nei template in modo molto chiaro.

#### `base.html`
È il layout comune a tutte le pagine.
Contiene:

- struttura HTML base;
- topbar;
- navigazione;
- profilo utente;
- modali;
- area messaggi flash;
- script JS di supporto.

È il template più importante dal punto di vista della coerenza grafica.

#### `home.html`
Mostra la dashboard iniziale con:

- saluto personalizzato;
- collegamenti rapidi;
- riepilogo economico;
- schede recenti;
- ultimi progetti.

È la pagina che meglio rappresenta il progetto come sistema operativo di lavoro.

#### Template di lista
I template di lista, come:

- `clienti_list.html`
- `operai_list.html`
- `materiali_list.html`
- `progetti_list.html`
- `giornaliero_list.html`
- `utenti_list.html`

servono a consultare dati, filtrare, ordinare e accedere ai dettagli.

Sono pagine pensate per la navigazione quotidiana.

#### Template di dettaglio
I template di dettaglio, come:

- `clienti_detail.html`
- `operai_detail.html`
- `materiali_detail.html`
- `progetti_detail.html`
- `giornaliero_detail.html`
- `utenti_detail.html`

servono a visualizzare la scheda completa di una singola entità.

#### Template di modifica e creazione
I template come:

- `clienti_new.html`
- `clienti_edit.html`
- `operaio_new.html`
- `operai_edit.html`
- `materiale_new.html`
- `materiali_edit.html`
- `progetto_new.html`
- `progetti_edit.html`
- `giornaliero_edit.html`
- `utenti_edit.html`

servono a inserire o aggiornare dati.

Sono pagine form-based, quindi la loro struttura è orientata ai campi, non alla logica di business.

### 7.4 Il ruolo della UI nel progetto

La UI non deve prendere decisioni di dominio. Deve solo:

- presentare il dato;
- raccogliere input;
- guidare l’utente;
- rendere chiara la navigazione;
- usare colori e spaziatura per migliorare la leggibilità.

Questo è perfettamente coerente con la tua idea: **i template non devono passare dai gestori**. La richiesta arriva alla `webapp`, che interroga i gestori, e poi passa il risultato al template.

---

## 8. Il flusso dati completo, passo per passo

Questo è il processo più importante da capire.

### Caso tipo: apertura di una pagina di dettaglio

1. L’utente clicca su un elemento della lista.
2. Il browser invia una richiesta a una route della `webapp`.
3. La route recupera l’ID dalla URL.
4. La route chiama il gestore relativo.
5. Il gestore legge il database, costruisce gli oggetti e applica le regole.
6. La route riceve il risultato.
7. La route può preparare dati aggiuntivi utili alla pagina.
8. La route chiama `render_template(...)`.
9. Il template mostra le informazioni.

### Caso tipo: creazione di un elemento

1. L’utente compila un form.
2. Il browser invia una `POST`.
3. La `webapp` legge i campi dal `request.form`.
4. La `webapp` passa i dati al gestore.
5. Il gestore valida e salva.
6. La `webapp` decide se mostrare un messaggio flash o fare redirect.
7. Il template successivo mostra il risultato.

### Caso tipo: operazione complessa con allegati

1. L’utente carica un file da una scheda.
2. La `webapp` verifica la presenza del file.
3. La `webapp` normalizza il nome e salva il file nel filesystem.
4. La `webapp` chiede al gestore di registrare l’allegato nel dominio.
5. Se tutto va bene, la pagina mostra conferma.
6. Se qualcosa fallisce, il file fisico viene eventualmente rimosso per coerenza.

Questo esempio mostra bene la differenza fra livelli:

- filesystem e request handling: `webapp`;
- coerenza dell’allegato come entità: gestore e modello.

---

## 9. Perché questa separazione è utile davvero

Questa architettura è utile perché mantiene il progetto pulito nel tempo.

Se in futuro vuoi cambiare:

- il database;
- l’aspetto grafico;
- la struttura delle pagine;
- il livello di dettaglio della dashboard;
- la logica delle schede;
- il modo in cui si gestiscono gli utenti;

puoi intervenire nel punto giusto senza dover riscrivere tutto.

In particolare:

- i **modelli** descrivono il dominio;
- `Azienda` collega e supporta il dominio;
- i **gestori** proteggono la logica e il CRUD;
- `webapp.py` organizza il flusso HTTP;
- i **template** mostrano i dati;
- il **CSS** definisce la qualità visiva.

Questa divisione è esattamente quella che rende un gestionale leggibile anche dopo mesi o anni.

---

## 10. Riassunto finale

Se devo sintetizzare tutto il progetto in una frase, direi questo:

> il gestionale è costruito per separare chiaramente dati, logica applicativa, orchestrazione web e presentazione visiva.

In modo ancora più semplice:

- **`models`** = cosa sono le cose;
- **`Azienda`** = contenitore e punto di accesso al dominio;
- **`gestori`** = cosa fare con le cose;
- **`webapp.py`** = come ricevere e coordinare le richieste;
- **`templates`** = come mostrare le cose;
- **`static/app.css`** = come farle apparire bene.

Questa è la struttura mentale corretta per leggere, mantenere e far evolvere il progetto.

---

## 11. Nota conclusiva sulla tua osservazione architetturale

La tua osservazione iniziale è sostanzialmente giusta: **la logica di visibilità non deve stare nei gestori**.

I gestori servono soprattutto per:

- CRUD;
- validazioni;
- regole di dominio;
- operazioni complesse sui dati.

La `webapp` invece serve per:

- ricevere la request;
- orchestrare la risposta;
- preparare i dati per la vista;
- fare redirect e flash;
- decidere quale template mostrare.

I template, infine, devono solo essere la parte visibile dell’applicazione.

Questa separazione è sana, scalabile e molto adatta a un gestionale come questo.

