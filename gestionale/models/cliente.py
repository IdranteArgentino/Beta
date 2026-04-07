from .enumerazioni import StatoEntita

class Cliente:
    def __init__(self, id_cliente: int, ragione_sociale: str, nome: str, cognome: str, indirizzo: str, telefono: str, note: str, stato: StatoEntita):
        self.id = id_cliente
        self.ragione_sociale = ragione_sociale
        self.nome = nome
        self.cognome = cognome
        self.indirizzo = indirizzo
        self.telefono = telefono
        self.note = note
        self.stato = stato
        self.progetti = [] # Viene popolato dal repository

    def isAttivo(self) -> bool:
        return self.stato == StatoEntita.ATTIVO

    def haProgetti(self) -> bool:
        return len(self.progetti) > 0

    def getNumeroProgetti(self) -> int:
        return len(self.progetti)
