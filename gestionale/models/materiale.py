from .enumerazioni import StatoEntita

class Materiale:
    def __init__(self, id_materiale: int, descrizione: str, unita_misura: str, prezzo_unitario_base: float, stato: StatoEntita, note: str):
        self.id = id_materiale
        self.descrizione = descrizione
        self.unita_misura = unita_misura
        self.prezzo_unitario_base = prezzo_unitario_base
        self.stato = stato
        self.note = note

    def isAttivo(self) -> bool:
        return self.stato == StatoEntita.ATTIVO

    def getPrezzoFormattato(self) -> str:
        return f"€ {self.prezzo_unitario_base:.2f}/{self.unita_misura}"
