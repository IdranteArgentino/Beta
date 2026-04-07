from .database import create_connection
from .models import Cliente, Materiale, Operaio, Progetto, Utente


class Azienda:
    """Classe contenitore dominio (UML): gestisce collezioni in memoria."""

    def __init__(self, db_path="data/gestionale.db"):
        self.db_path = db_path
        self._lista_clienti: list[Cliente] = []
        self._lista_materiali: list[Materiale] = []
        self._lista_operai: list[Operaio] = []
        self._lista_progetti: list[Progetto] = []
        self._lista_utenti: list[Utente] = []

    def _get_conn(self):
        """Compatibilità con i gestori attuali che lavorano su DB."""
        return create_connection(self.db_path)

    # --- Accesso liste (se ti serve esporle in sola lettura) ---
    @property
    def listaClienti(self) -> list[Cliente]:
        return list(self._lista_clienti)

    @property
    def listaMateriali(self) -> list[Materiale]:
        return list(self._lista_materiali)

    @property
    def listaOperai(self) -> list[Operaio]:
        return list(self._lista_operai)

    @property
    def listaProgetti(self) -> list[Progetto]:
        return list(self._lista_progetti)

    @property
    def listaUtenti(self) -> list[Utente]:
        return list(self._lista_utenti)

    # --- Operazioni di aggiunta ---
    def aggiungiCliente(self, cliente: Cliente) -> None:
        self._lista_clienti.append(cliente)

    def aggiungiMateriale(self, materiale: Materiale) -> None:
        self._lista_materiali.append(materiale)

    def aggiungiOperaio(self, operaio: Operaio) -> None:
        self._lista_operai.append(operaio)

    def aggiungiProgetto(self, progetto: Progetto) -> None:
        self._lista_progetti.append(progetto)

    def aggiungiUtente(self, utente: Utente) -> None:
        self._lista_utenti.append(utente)

    # --- Operazioni di ricerca ---
    def cercaCliente(self, termine: str):
        t = termine.lower()
        for c in self._lista_clienti:
            if t in c.ragione_sociale.lower():
                return c
        return None

    def cercaMateriale(self, termine: str):
        t = termine.lower()
        for m in self._lista_materiali:
            if t in m.descrizione.lower():
                return m
        return None

    def cercaOperaio(self, termine: str):
        t = termine.lower()
        for o in self._lista_operai:
            if t in o.nome.lower() or t in o.cognome.lower() or t in (o.alias or "").lower():
                return o
        return None

    def cercaProgetti(self, termine: str):
        t = termine.lower()
        for p in self._lista_progetti:
            if t in p.nome_progetto.lower() or t in p.indirizzo_cantiere.lower():
                return p
        return None

    def cercaUtenti(self, username: str, password_hash: str):
        for u in self._lista_utenti:
            if u.username == username and u.password == password_hash:
                return u
        return None

    # --- Operazioni di eliminazione ---
    def eliminaCliente(self, id_cliente: int) -> None:
        self._lista_clienti = [c for c in self._lista_clienti if c.id != id_cliente]

    def eliminaMateriale(self, id_materiale: int) -> None:
        self._lista_materiali = [m for m in self._lista_materiali if m.id != id_materiale]

    def eliminaOperaio(self, id_operaio: int) -> None:
        self._lista_operai = [o for o in self._lista_operai if o.id != id_operaio]

    def eliminaProgetto(self, id_progetto: int) -> None:
        self._lista_progetti = [p for p in self._lista_progetti if p.id != id_progetto]

    def eliminaUtente(self, username: str, password_hash: str) -> None:
        self._lista_utenti = [
            u for u in self._lista_utenti
            if not (u.username == username and u.password == password_hash)
        ]
