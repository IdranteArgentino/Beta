from .enumerazioni import StatoEntita

class Operaio:
    def __init__(self, id_operaio: int, nome: str, cognome: str, alias: str, costo_orario_base: float, stato: StatoEntita, note: str):
        self.id = id_operaio
        self.nome = nome
        self.cognome = cognome
        self.alias = alias
        self.costo_orario_base = costo_orario_base
        self.stato = stato
        self.note = note

    def isAttivo(self) -> bool:
        return self.stato == StatoEntita.ATTIVO

    def getNomeCompleto(self) -> str:
        return f"{self.nome} {self.cognome}"

    def getNomeVisualizzazione(self) -> str:
        if self.alias:
            return f"{self.getNomeCompleto()} ({self.alias})"
        return self.getNomeCompleto()
