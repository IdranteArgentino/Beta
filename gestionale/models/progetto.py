from .enumerazioni import StatoProgetto

class Progetto:
    def __init__(self, id_progetto: int, nome_progetto: str, id_cliente: int, indirizzo_cantiere: str, note: str, stato: StatoProgetto):
        self.id = id_progetto
        self.nome_progetto = nome_progetto
        self.id_cliente = id_cliente
        self.indirizzo_cantiere = indirizzo_cantiere
        self.note = note
        self.stato = stato
        self.schede_giornaliere = []

    def isInCorso(self) -> bool:
        return self.stato == StatoProgetto.IN_CORSO

    def isAttivo(self) -> bool:
        """Alias di isInCorso() per compatibilità"""
        return self.isInCorso()

    def isCompletato(self) -> bool:
        return self.stato == StatoProgetto.COMPLETATO

    def isModificabile(self) -> bool:
        # Un progetto completato o disattivato non e' modificabile.
        return self.stato in (StatoProgetto.IN_CORSO, StatoProgetto.ATTIVO)

    def haSchede(self) -> bool:
        return len(self.schede_giornaliere) > 0

    def getCostoTotale(self) -> float:
        return sum(scheda.getCostoTotale() for scheda in self.schede_giornaliere)

    def getTotaleOre(self) -> float:
        return sum(scheda.getTotaleOre() for scheda in self.schede_giornaliere)

    def getTotaleMateriali(self) -> int:
        return sum(len(scheda.voci_materiali) for scheda in self.schede_giornaliere)
