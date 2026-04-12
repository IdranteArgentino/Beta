from enum import Enum

class RuoloUtente(Enum):
    ADMIN = "ADMIN"
    STAFF = "STAFF"

class StatoEntita(Enum):
    ATTIVO = "ATTIVO"
    DISATTIVO = "DISATTIVATO"
    # Alias legacy gia' usato nel codice esistente
    DISATTIVATO = "DISATTIVATO"

class StatoProgetto(Enum):
    IN_CORSO = "IN_CORSO"
    COMPLETATO = "COMPLETATO"
    ATTIVO = "ATTIVO"
    DISATTIVO = "DISATTIVO"
