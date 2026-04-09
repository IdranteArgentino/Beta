# Gestionale Web

Applicazione web Flask per la gestione operativa di:

- clienti
- operai
- materiali
- progetti
- schede giornaliere (con voci ore/materiali e allegati)
- utenti (solo admin)

## Requisiti

- Python 3.11+ (consigliato 3.12)
- Sistema operativo: Windows, Linux, macOS

## Installazione

### 1) Crea e attiva ambiente virtuale (consigliato)

```powershell
cd C:\Users\nikol\Downloads\gestionale
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Installa dipendenze

```powershell
pip install -r requirements.txt
```

## Avvio applicazione

```powershell
cd C:\Users\nikol\Downloads\gestionale
python -m gestionale.main
```

Poi apri nel browser:

- http://127.0.0.1:5000/login

## Credenziali iniziali

Alla prima inizializzazione DB viene creato automaticamente l'utente admin:

- username: `admin`
- password: `password`

## Struttura progetto

```text
gestionale/
  gestionale/
    main.py                # entrypoint
    webapp.py              # route Flask e wiring app
    database.py            # inizializzazione schema DB
    azienda.py             # accesso dati principale
    gestori/               # logica applicativa per dominio
    models/                # modelli dominio
    templates/             # template Jinja2
    static/                # css/js statici
    data/
      gestionale.db        # database SQLite
      allegati/            # file allegati schede
    tests/                 # test unitari
  requirements.txt
  README.md
```

## Sezioni funzionali

- **Home**: dashboard con riepilogo economico e attività recenti
- **Clienti**: anagrafica, dettaglio, modifica, cancellazione
- **Operai**: anagrafica, storico voci lavoro, costi/ore
- **Materiali**: anagrafica e prezzi unitari
- **Progetti**: creazione, stato (in corso/completato), schede collegate
- **Giornaliero**: schede giornaliere con:
  - voci operai (ore e costo snapshot)
  - voci materiali (quantità e prezzo snapshot)
  - allegati (upload, mostra, sostituisci, rimuovi)
- **Utenti (admin)**: gestione utenti, reset password, stato/ruolo

## Dati e allegati

- Il DB è SQLite in: `gestionale/data/gestionale.db`
- Gli allegati sono file reali in: `gestionale/data/allegati/`
- Se elimini un file allegato dal filesystem, la riga DB può restare ma il file non sarà più apribile da UI

## Test

Esecuzione test `unittest`:

```powershell
cd C:\Users\nikol\Downloads\gestionale
python -m unittest discover -s gestionale\tests
```

Se vuoi usare `pytest` (opzionale), installalo manualmente:

```powershell
pip install pytest
python -m pytest gestionale\tests -q
```

## Note operative

- L'app crea automaticamente la cartella `gestionale/data/` se assente.
- Le migrazioni leggere sono gestite in `database.py` (es. colonne aggiunte se mancanti).
- In sviluppo l'app parte con `debug=True` da `gestionale/main.py`.

