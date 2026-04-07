import os
from datetime import date, timedelta
from functools import wraps
from uuid import uuid4

from flask import Flask, redirect, render_template, request, session, url_for, abort
from werkzeug.utils import secure_filename

from .azienda import Azienda
from .database import inizializza_db
from .gestori.gestore_clienti import GestoreClienti
from .gestori.gestore_materiali import GestoreMateriali
from .gestori.gestore_operai import GestoreOperai
from .gestori.gestore_progetti import GestoreProgetti
from .gestori.gestore_schede import GestoreSchede
from .gestori.gestore_utenti import GestoreUtenti
from .models import RuoloUtente, StatoEntita


def create_app(db_path=None):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    final_db_path = db_path or os.path.join(data_dir, "gestionale.db")

    inizializza_db(final_db_path)
    azienda = Azienda(final_db_path)

    gestori = {
        "utenti": GestoreUtenti(azienda),
        "clienti": GestoreClienti(azienda),
        "operai": GestoreOperai(azienda),
        "materiali": GestoreMateriali(azienda),
        "progetti": GestoreProgetti(azienda),
        "schede": GestoreSchede(azienda),
    }

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = "gestionale-dev-secret-key"

    def get_current_user():
        username = session.get("username")
        if not username:
            return None
        return gestori["utenti"]._trova_utente(username)

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("username"):
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    def admin_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if not user or user.ruolo != RuoloUtente.ADMIN:
                abort(403)
            return view(*args, **kwargs)
        return wrapped

    @app.context_processor
    def inject_globals():
        u = get_current_user()
        return {
            "current_user": u,
            "is_admin": bool(u and u.ruolo == RuoloUtente.ADMIN),
        }

    @app.route("/")
    @login_required
    def home():
        dashboard = gestori["schede"].dashboardData()
        return render_template("home.html", dashboard=dashboard)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            try:
                utente = gestori["utenti"].login(username, password)
                if utente and utente.stato == StatoEntita.ATTIVO:
                    session["username"] = utente.username
                    return redirect(url_for("home"))
                return render_template("login.html", error="Credenziali non valide o utente disattivato")
            except ValueError:
                return render_template("login.html", error="Credenziali non valide o utente disattivato")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/clienti")
    @login_required
    def clienti():
        q = request.args.get("q", "").strip()
        sort = request.args.get("sort", "alpha")
        items = gestori["clienti"].cercaCliente(q) if q else gestori["clienti"].listaClienti()
        if sort == "latest":
            items = sorted(items, key=lambda c: c.id or 0, reverse=True)
        return render_template("clienti_list.html", items=items, q=q, sort=sort)

    @app.route("/clienti/new", methods=["GET", "POST"])
    @login_required
    def clienti_new():
        if request.method == "POST":
            gestori["clienti"].aggiungiCliente(
                request.form.get("ragione_sociale", ""),
                indirizzo=request.form.get("indirizzo", ""),
                telefono=request.form.get("telefono", ""),
                note=request.form.get("note", ""),
                nome=request.form.get("nome", ""),
                cognome=request.form.get("cognome", ""),
            )
            return redirect(url_for("clienti"))
        return render_template("clienti_new.html")

    @app.route("/clienti/<int:item_id>")
    @login_required
    def clienti_detail(item_id):
        item = gestori["clienti"].dettaglioCliente(item_id)
        if not item:
            abort(404)
        return render_template("clienti_detail.html", item=item)

    @app.route("/clienti/<int:item_id>/edit", methods=["GET", "POST"])
    @login_required
    def clienti_edit(item_id):
        item = gestori["clienti"].dettaglioCliente(item_id)
        if not item:
            abort(404)
        if request.method == "GET":
            return render_template("clienti_edit.html", item=item)
        gestori["clienti"].modificaCliente(
            item_id,
            ragione_sociale=request.form.get("ragione_sociale"),
            nome=request.form.get("nome"),
            cognome=request.form.get("cognome"),
            indirizzo=request.form.get("indirizzo"),
            telefono=request.form.get("telefono"),
            note=request.form.get("note"),
        )
        return redirect(url_for("clienti_detail", item_id=item_id))

    @app.route("/clienti/<int:item_id>/delete", methods=["POST"])
    @login_required
    def clienti_delete(item_id):
        gestori["clienti"].eliminaCliente(item_id)
        return redirect(url_for("clienti"))

    @app.route("/operai")
    @login_required
    def operai():
        q = request.args.get("q", "").strip()
        sort = request.args.get("sort", "alpha")
        items = gestori["operai"].cercaOperaio(q) if q else gestori["operai"].listaOperai()
        if sort == "latest":
            items = sorted(items, key=lambda o: o.id or 0, reverse=True)
        return render_template("operai_list.html", items=items, q=q, sort=sort)

    @app.route("/operai/new", methods=["GET", "POST"])
    @login_required
    def operai_new():
        if request.method == "POST":
            try:
                gestori["operai"].aggiungiOperaio(
                    request.form.get("nome", ""),
                    request.form.get("cognome", ""),
                    float(request.form.get("costo_orario_base", "0") or 0),
                    alias=request.form.get("alias", ""),
                    note=request.form.get("note", ""),
                )
            except ValueError:
                pass
            return redirect(url_for("operai"))
        return render_template("operaio_new.html")

    @app.route("/operai/<int:item_id>")
    @login_required
    def operai_detail(item_id):
        item = gestori["operai"].dettaglioOperaio(item_id)
        if not item:
            abort(404)
        return render_template("operai_detail.html", item=item)

    @app.route("/operai/<int:item_id>/edit", methods=["GET", "POST"])
    @login_required
    def operai_edit(item_id):
        item = gestori["operai"].dettaglioOperaio(item_id)
        if not item:
            abort(404)
        if request.method == "GET":
            return render_template("operai_edit.html", item=item)
        cost = request.form.get("costo_orario_base")
        gestori["operai"].modificaOperaio(
            item_id,
            nome=request.form.get("nome"),
            cognome=request.form.get("cognome"),
            alias=request.form.get("alias"),
            costo_orario_base=float(cost) if cost else None,
            note=request.form.get("note"),
        )
        return redirect(url_for("operai_detail", item_id=item_id))

    @app.route("/operai/<int:item_id>/delete", methods=["POST"])
    @login_required
    def operai_delete(item_id):
        gestori["operai"].eliminaOperaio(item_id)
        return redirect(url_for("operai"))

    @app.route("/materiali")
    @login_required
    def materiali():
        q = request.args.get("q", "").strip()
        sort = request.args.get("sort", "alpha")
        items = gestori["materiali"].cercaMateriale(q) if q else gestori["materiali"].listaMateriali()
        if sort == "latest":
            items = sorted(items, key=lambda m: m.id or 0, reverse=True)
        return render_template("materiali_list.html", items=items, q=q, sort=sort)

    @app.route("/materiali/new", methods=["GET", "POST"])
    @login_required
    def materiali_new():
        if request.method == "POST":
            try:
                gestori["materiali"].aggiungiMateriale(
                    request.form.get("descrizione", ""),
                    request.form.get("unita_misura", "pz"),
                    float(request.form.get("prezzo_unitario", "0") or 0),
                    request.form.get("note", ""),
                )
            except ValueError:
                pass
            return redirect(url_for("materiali"))
        return render_template("materiale_new.html")

    @app.route("/materiali/<int:item_id>")
    @login_required
    def materiali_detail(item_id):
        item = gestori["materiali"].dettaglioMateriale(item_id)
        if not item:
            abort(404)
        return render_template("materiali_detail.html", item=item)

    @app.route("/materiali/<int:item_id>/edit", methods=["GET", "POST"])
    @login_required
    def materiali_edit(item_id):
        item = gestori["materiali"].dettaglioMateriale(item_id)
        if not item:
            abort(404)
        if request.method == "GET":
            return render_template("materiali_edit.html", item=item)
        prezzo = request.form.get("prezzo_unitario_base")
        gestori["materiali"].modificaMateriale(
            item_id,
            descrizione=request.form.get("descrizione"),
            unita_misura=request.form.get("unita_misura"),
            prezzo_unitario_base=float(prezzo) if prezzo else None,
            note=request.form.get("note"),
        )
        return redirect(url_for("materiali_detail", item_id=item_id))

    @app.route("/materiali/<int:item_id>/delete", methods=["POST"])
    @login_required
    def materiali_delete(item_id):
        gestori["materiali"].eliminaMateriale(item_id)
        return redirect(url_for("materiali"))

    @app.route("/progetti")
    @login_required
    def progetti():
        q = request.args.get("q", "").strip()
        sort = request.args.get("sort", "alpha")
        items = gestori["progetti"].cercaProgetto(q) if q else gestori["progetti"].listaProgetti()
        if sort == "latest":
            items = sorted(items, key=lambda p: p.id or 0, reverse=True)
        clienti = gestori["clienti"].listaClienti()
        return render_template("progetti_list.html", items=items, clienti=clienti, q=q, sort=sort)

    @app.route("/progetti/new", methods=["GET", "POST"])
    @login_required
    def progetti_new():
        if request.method == "POST":
            id_cliente_raw = request.form.get("id_cliente", "0")
            try:
                gestori["progetti"].creaProgetto(
                    request.form.get("nome_progetto", ""),
                    int(id_cliente_raw) if id_cliente_raw else 0,
                    request.form.get("indirizzo_cantiere", ""),
                    request.form.get("note", ""),
                )
            except ValueError:
                pass
            # Redirect al cliente se pre-selezionato
            from_cliente = request.form.get("from_cliente")
            if from_cliente:
                return redirect(url_for("clienti_detail", item_id=from_cliente))
            return redirect(url_for("progetti"))
        clienti = gestori["clienti"].listaClienti()
        preselect_cliente = request.args.get("id_cliente")
        return render_template("progetto_new.html", clienti=clienti, preselect_cliente=preselect_cliente)

    @app.route("/progetti/<int:item_id>")
    @login_required
    def progetti_detail(item_id):
        item = gestori["progetti"].dettaglioProgetto(item_id)
        if not item:
            abort(404)
        clienti = gestori["clienti"].listaClienti()
        clienti_by_id = {c.id: c for c in clienti}
        cliente = clienti_by_id.get(item.get("id_cliente"))
        return render_template("progetti_detail.html", item=item, clienti=clienti, cliente=cliente)

    @app.route("/progetti/<int:item_id>/edit", methods=["GET", "POST"])
    @login_required
    def progetti_edit(item_id):
        item = gestori["progetti"].dettaglioProgetto(item_id)
        if not item:
            abort(404)
        clienti = gestori["clienti"].listaClienti()
        if request.method == "GET":
            return render_template("progetti_edit.html", item=item, clienti=clienti)
        id_cliente = request.form.get("id_cliente")
        gestori["progetti"].modificaProgetto(
            item_id,
            nome_progetto=request.form.get("nome_progetto"),
            id_cliente=int(id_cliente) if id_cliente else None,
            indirizzo_cantiere=request.form.get("indirizzo_cantiere"),
            note=request.form.get("note"),
        )
        return redirect(url_for("progetti_detail", item_id=item_id))

    @app.route("/progetti/<int:item_id>/delete", methods=["POST"])
    @login_required
    def progetti_delete(item_id):
        gestori["progetti"].eliminaProgetto(item_id)
        return redirect(url_for("progetti"))

    @app.route("/giornaliero")
    @login_required
    def giornaliero():
        items = gestori["schede"].listaSchede()
        all_progetti = gestori["progetti"].listaProgetti()

        today = date.today()
        default_start = date(today.year, 1, 1)
        default_end = date(today.year, 12, 31)

        def _parse_filter_date(param_name: str, default_date: date) -> date:
            raw_value = (request.args.get(param_name) or "").strip()
            if not raw_value:
                return default_date
            try:
                return date.fromisoformat(raw_value)
            except ValueError:
                return default_date

        start_day = _parse_filter_date("start_date", default_start)
        end_day = _parse_filter_date("end_date", default_end)

        if start_day > end_day:
            start_day, end_day = end_day, start_day

        selected_project_ids_raw = request.args.getlist("project_ids")
        selected_project_ids = set()
        for value in selected_project_ids_raw:
            try:
                selected_project_ids.add(int(value))
            except (TypeError, ValueError):
                continue

        if selected_project_ids:
            progetti = [p for p in all_progetti if p.id in selected_project_ids]
        else:
            progetti = all_progetti

        days = []
        cursor_day = start_day
        while cursor_day <= end_day:
            days.append({
                "key": cursor_day.isoformat(),
                "label": cursor_day.strftime("%d/%m/%Y"),
            })
            cursor_day += timedelta(days=1)

        # Mappa cella (giorno, progetto) -> scheda (o conteggio schede se multiple)
        cell_map = {}
        for scheda in items:
            day_key = getattr(scheda, "data", None)
            project_id = getattr(scheda, "id_progetto", None)
            if not day_key or project_id is None:
                continue

            day_cells = cell_map.setdefault(day_key, {})
            if project_id in day_cells:
                day_cells[project_id]["count"] += 1
                day_cells[project_id]["id"] = scheda.id
            else:
                day_cells[project_id] = {"id": scheda.id, "count": 1}

        return render_template(
            "giornaliero_list.html",
            all_progetti=all_progetti,
            progetti=progetti,
            days=days,
            cell_map=cell_map,
            start_date_value=start_day.isoformat(),
            end_date_value=end_day.isoformat(),
            selected_project_ids=sorted(selected_project_ids),
        )

    def _prepare_giornaliero_detail(item_id: int):
        item = gestori["schede"].dettaglioScheda(item_id)
        if not item:
            return None

        all_operai = gestori["operai"].listaOperai()
        all_materiali = gestori["materiali"].listaMateriali()
        all_progetti = gestori["progetti"].listaProgetti()

        return item, all_operai, all_materiali, all_progetti

    @app.route("/giornaliero/new", methods=["POST"])
    @login_required
    def giornaliero_new():
        id_progetto = int(request.form.get("id_progetto", "0") or 0)
        gestori["schede"].aggiungiScheda(
            request.form.get("data", ""),
            request.form.get("descrizione", ""),
            id_progetto,
        )
        return redirect(url_for("giornaliero"))

    @app.route("/giornaliero/<int:item_id>")
    @login_required
    def giornaliero_detail(item_id):
        prepared = _prepare_giornaliero_detail(item_id)
        if not prepared:
            abort(404)
        item, all_operai, all_materiali, all_progetti = prepared
        return render_template(
            "giornaliero_detail.html",
            item=item,
            all_operai=all_operai,
            all_materiali=all_materiali,
            all_progetti=all_progetti,
        )

    @app.route("/giornaliero/<int:item_id>/operai/add", methods=["POST"])
    @login_required
    def giornaliero_add_operaio(item_id):
        if not gestori["schede"].dettaglioScheda(item_id):
            abort(404)
        id_operaio = int(request.form.get("id_operaio", "0") or 0)
        ore = float(request.form.get("ore_lavorate", "0") or 0)
        gestori["schede"].assegnaOreOperaio(item_id, id_operaio, ore)
        return redirect(url_for("giornaliero_detail", item_id=item_id))

    @app.route("/giornaliero/<int:item_id>/operai/<int:id_operaio>/delete", methods=["POST"])
    @login_required
    def giornaliero_remove_operaio(item_id, id_operaio):
        gestori["schede"].rimuoviOperaioDaScheda(item_id, id_operaio)
        return redirect(url_for("giornaliero_detail", item_id=item_id))

    @app.route("/giornaliero/<int:item_id>/materiali/add", methods=["POST"])
    @login_required
    def giornaliero_add_materiale(item_id):
        if not gestori["schede"].dettaglioScheda(item_id):
            abort(404)
        id_materiale = int(request.form.get("id_materiale", "0") or 0)
        quantita = float(request.form.get("quantita", "0") or 0)
        gestori["schede"].scaricaMateriale(item_id, id_materiale, quantita)
        return redirect(url_for("giornaliero_detail", item_id=item_id))

    @app.route("/giornaliero/<int:item_id>/materiali/<int:id_materiale>/delete", methods=["POST"])
    @login_required
    def giornaliero_remove_materiale(item_id, id_materiale):
        gestori["schede"].rimuoviMaterialeDaScheda(item_id, id_materiale)
        return redirect(url_for("giornaliero_detail", item_id=item_id))

    @app.route("/giornaliero/<int:item_id>/allegati/add", methods=["POST"])
    @login_required
    def giornaliero_add_allegato(item_id):
        if not gestori["schede"].dettaglioScheda(item_id):
            abort(404)

        uploaded = request.files.get("file")
        if not uploaded or not uploaded.filename:
            return redirect(url_for("giornaliero_detail", item_id=item_id))

        uploads_dir = os.path.join(data_dir, "allegati")
        os.makedirs(uploads_dir, exist_ok=True)

        original_name = secure_filename(uploaded.filename)
        unique_name = f"scheda_{item_id}_{uuid4().hex}_{original_name}"
        save_path = os.path.join(uploads_dir, unique_name)
        uploaded.save(save_path)
        gestori["schede"].aggiungiAllegato(save_path, item_id)
        return redirect(url_for("giornaliero_detail", item_id=item_id))

    @app.route("/giornaliero/<int:item_id>/allegati/<int:id_allegato>/delete", methods=["POST"])
    @login_required
    def giornaliero_remove_allegato(item_id, id_allegato):
        gestori["schede"].rimuoviAllegato(id_allegato)
        return redirect(url_for("giornaliero_detail", item_id=item_id))

    @app.route("/giornaliero/<int:item_id>/edit", methods=["GET", "POST"])
    @login_required
    def giornaliero_edit(item_id):
        item = gestori["schede"].dettaglioScheda(item_id)
        if not item:
            abort(404)
        if request.method == "GET":
            progetti = gestori["progetti"].listaProgetti()
            return render_template("giornaliero_edit.html", item=item, progetti=progetti)
        gestori["schede"].modificaScheda(
            request.form.get("data", ""),
            request.form.get("descrizione", ""),
            item_id,
        )
        return redirect(url_for("giornaliero_detail", item_id=item_id))

    @app.route("/giornaliero/<int:item_id>/delete", methods=["POST"])
    @login_required
    def giornaliero_delete(item_id):
        gestori["schede"].eliminaScheda(item_id)
        return redirect(url_for("giornaliero"))

    @app.route("/utenti")
    @login_required
    @admin_required
    def utenti():
        admin = get_current_user()
        q = request.args.get("q", "").strip()
        items = gestori["utenti"].cercaUtente(q, admin) if q else gestori["utenti"].listaUtenti(admin)
        return render_template("utenti_list.html", items=items, q=q)

    @app.route("/utenti/new", methods=["POST"])
    @login_required
    @admin_required
    def utenti_new():
        admin = get_current_user()
        ruolo = RuoloUtente(request.form.get("ruolo", "STAFF"))
        gestori["utenti"].aggiungiUtente(
            request.form.get("username", ""),
            request.form.get("nome", ""),
            request.form.get("cognome", ""),
            ruolo,
            admin,
        )
        return redirect(url_for("utenti"))

    @app.route("/utenti/<int:item_id>")
    @login_required
    @admin_required
    def utenti_detail(item_id):
        item = gestori["utenti"].dettaglioUtente(item_id)
        if not item:
            abort(404)
        current = get_current_user()
        is_self = bool(current and current.username == item.get("username"))
        return render_template("utenti_detail.html", item=item, is_self=is_self)

    @app.route("/utenti/<int:item_id>/edit", methods=["GET", "POST"])
    @login_required
    @admin_required
    def utenti_edit(item_id):
        detail = gestori["utenti"].dettaglioUtente(item_id)
        if not detail:
            abort(404)
        if request.method == "GET":
            return render_template("utenti_edit.html", item=detail)
        gestori["utenti"].modificaUtente(
            detail["username"],
            nome=request.form.get("nome"),
            cognome=request.form.get("cognome"),
            ruolo=RuoloUtente(request.form.get("ruolo")) if request.form.get("ruolo") else None,
            stato=StatoEntita(request.form.get("stato")) if request.form.get("stato") else None,
        )
        return redirect(url_for("utenti_detail", item_id=item_id))

    @app.route("/utenti/<int:item_id>/reset-password", methods=["POST"])
    @login_required
    @admin_required
    def utenti_reset_password(item_id):
        detail = gestori["utenti"].dettaglioUtente(item_id)
        if not detail:
            abort(404)
        admin = get_current_user()
        gestori["utenti"].resetForzatoPassword(detail["username"], admin)
        return redirect(url_for("utenti_edit", item_id=item_id))


    @app.route("/utenti/<int:item_id>/delete", methods=["POST"])
    @login_required
    @admin_required
    def utenti_delete(item_id):
        detail = gestori["utenti"].dettaglioUtente(item_id)
        current = get_current_user()
        if detail and current and detail.get("username") == current.username:
            return redirect(url_for("utenti_detail", item_id=item_id))
        if detail:
            gestori["utenti"].eliminaUtente(detail["username"])
        return redirect(url_for("utenti"))

    return app

