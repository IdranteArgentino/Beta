# Gestionale Web (Flask)

Questa versione usa Flask e sostituisce le vecchie viste PyQt.

## Avvio rapido

1. Installa dipendenze:

```bash
pip install -r requirements.txt
```

2. Avvia l'app:

```bash
python -m gestionale.main
```

3. Apri il browser su:

- http://127.0.0.1:5000/login

## Credenziali admin di default

- username: `admin`
- password: `admin`

## Sezioni disponibili

- Clienti
- Operai
- Materiali
- Progetti
- Giornaliero
- Utenti (solo ADMIN)

Ogni sezione include:

- barra di ricerca
- ordinamento alfabetico / ultimi inseriti (dove previsto)
- aggiunta elemento
- dettaglio elemento
- modifica ed eliminazione

