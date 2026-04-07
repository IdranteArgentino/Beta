from .enumerazioni import StatoEntita, RuoloUtente
import hashlib

class Utente:
    def __init__(self, id_utente: int, username: str, nome: str, cognome: str, password_hash: str, stato: StatoEntita, ruolo: RuoloUtente):
        self.id = id_utente
        self.username = username
        self.nome = nome
        self.cognome = cognome
        self.password = password_hash # hash SHA-256
        self.stato = stato
        self.ruolo = ruolo

    def verificaPassword(self, password: str) -> bool:
        return self.password == hashlib.sha256(password.encode('utf-8')).hexdigest()

    def isAttivo(self) -> bool:
        return self.stato == StatoEntita.ATTIVO

    def isAdmin(self) -> bool:
        return self.ruolo == RuoloUtente.ADMIN

    def getNomeCompleto(self) -> str:
        return f"{self.nome} {self.cognome}"
