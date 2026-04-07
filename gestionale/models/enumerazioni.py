from enum import Enum

class RuoloUtente(Enum):
    ADMIN = "ADMIN"
    STAFF = "STAFF"

class StatoEntita(Enum):
    ATTIVO = "ATTIVO"
    DISATTIVATO = "DISATTIVATO"

class StatoProgetto(Enum):
    IN_CORSO = "IN_CORSO"
    COMPLETATO = "COMPLETATO"
