import os

class VoceOperai:
    def __init__(self, id_scheda: int, id_operaio: int, ore_lavorate: float, costo_orario_snapshot: float):
        self.id_scheda = id_scheda
        self.id_operaio = id_operaio
        self.ore_lavorate = ore_lavorate
        self.costo_orario_snapshot = costo_orario_snapshot

    def getCostoTotale(self) -> float:
        return self.ore_lavorate * self.costo_orario_snapshot

class VoceMateriali:
    def __init__(self, id_scheda: int, id_materiale: int, quantita: float, prezzo_unitario_snapshot: float):
        self.id_scheda = id_scheda
        self.id_materiale = id_materiale
        self.quantita = quantita
        self.prezzo_unitario_snapshot = prezzo_unitario_snapshot

    def getCostoTotale(self) -> float:
        return self.quantita * self.prezzo_unitario_snapshot

class Allegato:
    def __init__(self, id_allegato: int, id_scheda: int, path: str):
        self.id = id_allegato
        self.id_scheda = id_scheda
        self.path = path

    def fileEsiste(self) -> bool:
        return os.path.exists(self.path)

    def getNomeFile(self) -> str:
        return os.path.basename(self.path)

class SchedaGiornaliera:
    def __init__(self, id_scheda: int, data: str, descrizione: str, id_progetto: int):
        self.id = id_scheda
        self.data = data # formato YYYY-MM-DD
        self.descrizione = descrizione
        self.id_progetto = id_progetto
        self.voci_operai = []
        self.voci_materiali = []
        self.allegati = []

    def getCostoTotaleOre(self) -> float:
        return sum(voce.getCostoTotale() for voce in self.voci_operai)

    def getCostoTotaleMateriali(self) -> float:
        return sum(voce.getCostoTotale() for voce in self.voci_materiali)

    def getCostoTotale(self) -> float:
        return self.getCostoTotaleOre() + self.getCostoTotaleMateriali()

    def getTotaleOre(self) -> float:
        return sum(voce.ore_lavorate for voce in self.voci_operai)

    def haAllegati(self) -> bool:
        return len(self.allegati) > 0
