import json
import os
import secrets
import uuid
from datetime import datetime, date
from zoneinfo import ZoneInfo
from functools import wraps
from pathlib import Path

from authlib.integrations.flask_client import OAuth
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, or_, text
from werkzeug.middleware.proxy_fix import ProxyFix

BASE_DIR = Path(__file__).resolve().parent
APP_TZ = ZoneInfo(os.getenv("APP_TIMEZONE", "America/Sao_Paulo"))

def _database_uri():
    url = os.getenv("DATABASE_URL", "").strip()
    # SQLAlchemy + psycopg2 entende postgresql:// diretamente.
    # Compatibilidade com URLs antigas que ainda usam postgres://.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if os.getenv("RENDER") == "true" and not url:
        raise RuntimeError(
            "DATABASE_URL não foi configurada no Render. "
            "Conecte o Web Service ao Render Postgres antes de iniciar o CRM."
        )
    return url or f"sqlite:///{BASE_DIR / 'lmtech.db'}"

app = Flask(__name__)
# Render fica atrás de proxy HTTPS. ProxyFix faz o Flask respeitar Host/Proto encaminhados.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
DATABASE_URI = _database_uri()
ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
if DATABASE_URI.startswith("postgresql://"):
    ENGINE_OPTIONS["connect_args"] = {"connect_timeout": 10}

app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY") or secrets.token_hex(32),
    SQLALCHEMY_DATABASE_URI=DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "0") == "1",
    PREFERRED_URL_SCHEME="https" if os.getenv("RENDER") == "true" else "http",
    SQLALCHEMY_ENGINE_OPTIONS=ENGINE_OPTIONS,
)

db = SQLAlchemy(app)
oauth = OAuth(app)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
ALLOWED_GOOGLE_EMAILS = {
    x.strip().lower() for x in os.getenv("ALLOWED_GOOGLE_EMAILS", "").split(",") if x.strip()
}
DEV_BYPASS_AUTH = os.getenv("DEV_BYPASS_AUTH", "0") == "1"

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


def uid(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


def now_iso():
    return datetime.now(APP_TZ).replace(tzinfo=None, microsecond=0).isoformat()

def local_today():
    return datetime.now(APP_TZ).date()


def month_key(value=None):
    if isinstance(value, str) and len(value) >= 7:
        return value[:7]
    d = value or local_today()
    return f"{d.year:04d}-{d.month:02d}"


def cents(value):
    if value is None or value == "":
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value * 100))
    s = str(value).strip().replace("R$", "").replace(" ", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return int(round(float(s) * 100))
    except ValueError:
        return 0


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.String(64), primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, default="Usuário")
    picture = db.Column(db.Text, nullable=False, default="")
    role = db.Column(db.String(32), nullable=False, default="member")
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.String(32), nullable=False, default=now_iso)
    last_login = db.Column(db.String(32), nullable=False, default=now_iso)

    def to_dict(self):
        return {
            "id": self.id, "email": self.email, "name": self.name, "picture": self.picture,
            "role": self.role, "active": self.active, "createdAt": self.created_at, "lastLogin": self.last_login,
        }


class Lead(db.Model):
    __tablename__ = "leads"
    id = db.Column(db.String(80), primary_key=True)
    category = db.Column(db.String(80), default="ADVOCACIA")
    name = db.Column(db.String(255), nullable=False, index=True)
    phone = db.Column(db.String(80), default="")
    address = db.Column(db.Text, default="")
    rating = db.Column(db.String(20), default="")
    reviews = db.Column(db.String(40), default="")
    score = db.Column(db.Integer, default=0)
    grade = db.Column(db.String(8), default="")
    priority = db.Column(db.String(80), default="")
    argument = db.Column(db.Text, default="")
    pitch = db.Column(db.Text, default="")
    status = db.Column(db.String(64), default="Novo", index=True)
    website = db.Column(db.Text, default="")
    instagram = db.Column(db.String(255), default="")
    email = db.Column(db.String(255), default="")
    responsible = db.Column(db.String(255), default="")
    last_contact = db.Column(db.String(16), default="")
    next_date = db.Column(db.String(16), default="")
    next_action = db.Column(db.Text, default="")
    notes = db.Column(db.Text, default="")
    site_status = db.Column(db.String(80), default="Não analisado")
    archived = db.Column(db.Boolean, default=False, nullable=False, index=True)
    imported_at = db.Column(db.String(40), default="")
    source_batch = db.Column(db.String(255), default="Base original")
    owner_id = db.Column(db.String(64), db.ForeignKey("users.id"), nullable=True, index=True)
    created_by = db.Column(db.String(64), db.ForeignKey("users.id"), nullable=True)
    updated_by = db.Column(db.String(64), db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.String(32), default=now_iso, nullable=False)
    updated_at = db.Column(db.String(32), default=now_iso, nullable=False)

    def to_dict(self):
        return {
            "id": self.id, "category": self.category, "name": self.name, "phone": self.phone,
            "address": self.address, "rating": self.rating, "reviews": self.reviews, "score": self.score,
            "grade": self.grade, "priority": self.priority, "argument": self.argument, "pitch": self.pitch,
            "status": self.status, "website": self.website, "instagram": self.instagram, "email": self.email,
            "responsible": self.responsible, "lastContact": self.last_contact, "nextDate": self.next_date,
            "nextAction": self.next_action, "notes": self.notes, "siteStatus": self.site_status,
            "archived": self.archived, "importedAt": self.imported_at, "sourceBatch": self.source_batch,
            "ownerId": self.owner_id, "createdBy": self.created_by, "updatedBy": self.updated_by,
            "createdAt": self.created_at, "updatedAt": self.updated_at,
        }


class Meeting(db.Model):
    __tablename__ = "meetings"
    id = db.Column(db.String(80), primary_key=True)
    lead_id = db.Column(db.String(80), db.ForeignKey("leads.id"), nullable=True, index=True)
    owner_id = db.Column(db.String(64), db.ForeignKey("users.id"), nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    start_at = db.Column(db.String(32), nullable=False, index=True)
    duration_minutes = db.Column(db.Integer, default=30)
    format = db.Column(db.String(50), default="Online")
    location = db.Column(db.Text, default="")
    meet_link = db.Column(db.Text, default="")
    status = db.Column(db.String(50), default="Marcada", index=True)
    notes = db.Column(db.Text, default="")
    outcome = db.Column(db.Text, default="")
    created_by = db.Column(db.String(64), db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.String(32), default=now_iso, nullable=False)
    updated_at = db.Column(db.String(32), default=now_iso, nullable=False)

    def to_dict(self):
        lead = db.session.get(Lead, self.lead_id) if self.lead_id else None
        owner = db.session.get(User, self.owner_id) if self.owner_id else None
        return {
            "id": self.id, "leadId": self.lead_id, "leadName": lead.name if lead else "",
            "ownerId": self.owner_id, "ownerName": owner.name if owner else "",
            "title": self.title, "startAt": self.start_at, "durationMinutes": self.duration_minutes,
            "format": self.format, "location": self.location, "meetLink": self.meet_link,
            "status": self.status, "notes": self.notes, "outcome": self.outcome,
            "createdBy": self.created_by, "createdAt": self.created_at, "updatedAt": self.updated_at,
        }


class Contract(db.Model):
    __tablename__ = "contracts"
    id = db.Column(db.String(80), primary_key=True)
    lead_id = db.Column(db.String(80), db.ForeignKey("leads.id"), nullable=True, index=True)
    owner_id = db.Column(db.String(64), db.ForeignKey("users.id"), nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    client_name = db.Column(db.String(255), nullable=False, default="")
    value_cents = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(50), nullable=False, default="Fechado", index=True)
    closed_at = db.Column(db.String(16), nullable=False, index=True)
    payment_method = db.Column(db.String(120), default="")
    notes = db.Column(db.Text, default="")
    created_by = db.Column(db.String(64), db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.String(32), default=now_iso, nullable=False)
    updated_at = db.Column(db.String(32), default=now_iso, nullable=False)

    def to_dict(self):
        lead = db.session.get(Lead, self.lead_id) if self.lead_id else None
        owner = db.session.get(User, self.owner_id) if self.owner_id else None
        return {
            "id": self.id, "leadId": self.lead_id, "leadName": lead.name if lead else "",
            "ownerId": self.owner_id, "ownerName": owner.name if owner else "",
            "title": self.title, "clientName": self.client_name, "valueCents": self.value_cents,
            "value": self.value_cents / 100, "status": self.status, "closedAt": self.closed_at,
            "paymentMethod": self.payment_method, "notes": self.notes,
            "createdBy": self.created_by, "createdAt": self.created_at, "updatedAt": self.updated_at,
        }


class Goal(db.Model):
    __tablename__ = "goals"
    id = db.Column(db.String(80), primary_key=True)
    month = db.Column(db.String(7), nullable=False, index=True)
    scope = db.Column(db.String(20), nullable=False, default="team")
    user_id = db.Column(db.String(64), db.ForeignKey("users.id"), nullable=True, index=True)
    revenue_target_cents = db.Column(db.Integer, nullable=False, default=0)
    contracts_target = db.Column(db.Integer, nullable=False, default=0)
    meetings_target = db.Column(db.Integer, nullable=False, default=0)
    created_by = db.Column(db.String(64), db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.String(32), default=now_iso, nullable=False)
    updated_at = db.Column(db.String(32), default=now_iso, nullable=False)

    __table_args__ = (db.UniqueConstraint("month", "scope", "user_id", name="uq_goal_scope_month"),)

    def to_dict(self):
        user = db.session.get(User, self.user_id) if self.user_id else None
        return {
            "id": self.id, "month": self.month, "scope": self.scope, "userId": self.user_id,
            "userName": user.name if user else "Equipe", "revenueTargetCents": self.revenue_target_cents,
            "revenueTarget": self.revenue_target_cents / 100, "contractsTarget": self.contracts_target,
            "meetingsTarget": self.meetings_target, "createdBy": self.created_by,
            "createdAt": self.created_at, "updatedAt": self.updated_at,
        }


class Activity(db.Model):
    __tablename__ = "activities"
    id = db.Column(db.String(80), primary_key=True)
    user_id = db.Column(db.String(64), db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(80), nullable=False)
    entity_type = db.Column(db.String(40), nullable=False)
    entity_id = db.Column(db.String(80), nullable=True, index=True)
    description = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.String(32), default=now_iso, nullable=False, index=True)

    def to_dict(self):
        user = db.session.get(User, self.user_id) if self.user_id else None
        return {
            "id": self.id, "userId": self.user_id, "userName": user.name if user else "Sistema",
            "action": self.action, "entityType": self.entity_type, "entityId": self.entity_id,
            "description": self.description, "createdAt": self.created_at,
        }


class Setting(db.Model):
    __tablename__ = "settings"
    key = db.Column(db.String(80), primary_key=True)
    value_json = db.Column(db.Text, nullable=False, default="{}")
    updated_by = db.Column(db.String(64), db.ForeignKey("users.id"), nullable=True)
    updated_at = db.Column(db.String(32), default=now_iso, nullable=False)


def current_user():
    uid_ = session.get("user_id")
    return db.session.get(User, uid_) if uid_ else None


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u or not u.active:
            if request.path.startswith("/api/"):
                return jsonify({"error": "unauthorized"}), 401
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


def log_activity(action, entity_type, entity_id, description, user_id=None):
    u = current_user()
    db.session.add(Activity(
        id=uid("act"), user_id=user_id or (u.id if u else None), action=action,
        entity_type=entity_type, entity_id=entity_id, description=description,
    ))


def seed_initial_data():
    if Lead.query.first() is not None:
        return
    seed_file = BASE_DIR / "seeds" / "leads.json"
    if not seed_file.exists():
        return
    data = json.loads(seed_file.read_text(encoding="utf-8"))
    for item in data:
        db.session.add(Lead(
            id=item.get("id") or uid("lead"), category=item.get("category", "ADVOCACIA"),
            name=item.get("name", "Lead"), phone=item.get("phone", ""), address=item.get("address", ""),
            rating=item.get("rating", ""), reviews=item.get("reviews", ""), score=int(item.get("score") or 0),
            grade=item.get("grade", ""), priority=item.get("priority", ""), argument=item.get("argument", ""),
            pitch=item.get("pitch", ""), status=item.get("status", "Novo"), website=item.get("website", ""),
            instagram=item.get("instagram", ""), email=item.get("email", ""), responsible=item.get("responsible", ""),
            last_contact=item.get("lastContact", ""), next_date=item.get("nextDate", ""), next_action=item.get("nextAction", ""),
            notes=item.get("notes", ""), site_status=item.get("siteStatus", "Não analisado"),
            archived=bool(item.get("archived", False)), imported_at=item.get("importedAt", ""),
            source_batch=item.get("sourceBatch", "Base original"),
        ))
    db.session.commit()


def initialize_database():
    """Cria as tabelas e popula a base inicial de forma idempotente."""
    with app.app_context():
        db.create_all()
        seed_initial_data()


def public_origin():
    """Origem pública usada pelo OAuth, priorizando a URL HTTPS do Render."""
    configured = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if configured:
        return configured
    render_url = os.getenv("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
    if render_url:
        return render_url
    return request.url_root.rstrip("/")


@app.get("/login")
def login():
    if current_user():
        return redirect(url_for("index"))
    return render_template(
        "login.html", google_ready=bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        dev_bypass=DEV_BYPASS_AUTH, allowed_count=len(ALLOWED_GOOGLE_EMAILS),
        error=request.args.get("error", "")
    )


@app.get("/auth/google")
def google_login():
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
        return redirect(url_for("login", error="google_not_configured"))
    redirect_uri = f"{public_origin()}{url_for('google_callback')}"
    return oauth.google.authorize_redirect(redirect_uri)


@app.get("/auth/google/callback")
def google_callback():
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
        return redirect(url_for("login", error="google_not_configured"))
    try:
        token = oauth.google.authorize_access_token()
        info = token.get("userinfo") or oauth.google.userinfo(token=token)
    except Exception:
        return redirect(url_for("login", error="oauth_failed"))
    email = str(info.get("email", "")).strip().lower()
    if not info.get("email_verified") or not email:
        return redirect(url_for("login", error="email_unverified"))
    if not ALLOWED_GOOGLE_EMAILS or email not in ALLOWED_GOOGLE_EMAILS:
        return redirect(url_for("login", error="not_allowed"))
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(id=uid("usr"), email=email, name=info.get("name") or email.split("@")[0], picture=info.get("picture") or "")
        db.session.add(user)
    user.name = info.get("name") or user.name
    user.picture = info.get("picture") or user.picture
    user.last_login = now_iso()
    db.session.commit()
    session.clear()
    session["user_id"] = user.id
    session.permanent = True
    with app.app_context():
        log_activity("login", "user", user.id, f"{user.name} entrou no CRM", user.id)
        db.session.commit()
    return redirect(url_for("index"))


@app.get("/dev-login")
def dev_login():
    if not DEV_BYPASS_AUTH:
        return "Not found", 404
    email = request.args.get("email", "dev@lmtech.local").strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(id=uid("usr"), email=email, name=request.args.get("name", "Usuário Dev"), role="admin")
        db.session.add(user)
        db.session.commit()
    session["user_id"] = user.id
    return redirect(url_for("index"))


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
@login_required
def index():
    return render_template("index.html")


def user_stats_for(user_id, month):
    revenue = db.session.query(func.coalesce(func.sum(Contract.value_cents), 0)).filter(
        Contract.owner_id == user_id, Contract.status == "Fechado", Contract.closed_at.like(f"{month}%")
    ).scalar() or 0
    contracts_count = Contract.query.filter(
        Contract.owner_id == user_id, Contract.status == "Fechado", Contract.closed_at.like(f"{month}%")
    ).count()
    meetings = Meeting.query.filter(Meeting.owner_id == user_id, Meeting.start_at.like(f"{month}%")).count()
    completed_meetings = Meeting.query.filter(
        Meeting.owner_id == user_id, Meeting.start_at.like(f"{month}%"), Meeting.status == "Realizada"
    ).count()
    lead_updates = Activity.query.filter(
        Activity.user_id == user_id, Activity.entity_type == "lead", Activity.created_at.like(f"{month}%")
    ).count()
    return {
        "revenueCents": int(revenue), "revenue": int(revenue) / 100,
        "contracts": contracts_count, "meetings": meetings, "completedMeetings": completed_meetings,
        "leadActions": lead_updates,
    }


def team_stats(month):
    revenue = db.session.query(func.coalesce(func.sum(Contract.value_cents), 0)).filter(
        Contract.status == "Fechado", Contract.closed_at.like(f"{month}%")
    ).scalar() or 0
    contracts_count = Contract.query.filter(Contract.status == "Fechado", Contract.closed_at.like(f"{month}%")).count()
    meetings = Meeting.query.filter(Meeting.start_at.like(f"{month}%")).count()
    completed = Meeting.query.filter(Meeting.start_at.like(f"{month}%"), Meeting.status == "Realizada").count()
    return {"revenueCents": int(revenue), "revenue": int(revenue)/100, "contracts": contracts_count, "meetings": meetings, "completedMeetings": completed}


def goal_progress(goal, actual):
    if not goal:
        return None
    d = goal.to_dict()
    d["actual"] = actual
    d["revenueProgress"] = round((actual["revenueCents"] / goal.revenue_target_cents * 100), 1) if goal.revenue_target_cents else 0
    d["contractsProgress"] = round((actual["contracts"] / goal.contracts_target * 100), 1) if goal.contracts_target else 0
    d["meetingsProgress"] = round((actual["meetings"] / goal.meetings_target * 100), 1) if goal.meetings_target else 0
    return d


@app.get("/api/bootstrap")
@login_required
def api_bootstrap():
    m = month_key(request.args.get("month"))
    users = User.query.filter_by(active=True).order_by(User.name.asc()).all()
    leads = Lead.query.order_by(Lead.score.desc(), Lead.name.asc()).all()
    meetings = Meeting.query.order_by(Meeting.start_at.asc()).all()
    contracts = Contract.query.order_by(Contract.closed_at.desc(), Contract.created_at.desc()).all()
    goals = Goal.query.filter_by(month=m).all()
    team_goal = next((g for g in goals if g.scope == "team" and not g.user_id), None)
    summaries = []
    for u in users:
        st = user_stats_for(u.id, m)
        ug = next((g for g in goals if g.scope == "user" and g.user_id == u.id), None)
        recent = Activity.query.filter_by(user_id=u.id).order_by(Activity.created_at.desc()).limit(12).all()
        summaries.append({**u.to_dict(), "stats": st, "goal": goal_progress(ug, st), "recentActivities": [a.to_dict() for a in recent]})
    default_scripts = {
        "ADVOCACIA": {
            "dependency": "Google + reputação + indicação + confiança. A decisão costuma passar pela clareza das áreas de atuação, autoridade percebida, conteúdo informativo e facilidade de contato. Comunicação deve respeitar as regras da OAB e evitar promessas de resultado.",
            "script": "Oi, tudo bem? Aqui é o Miguel, da LM TECH. Eu estava analisando a presença digital da [EMPRESA] e encontrei alguns pontos que podem elevar bastante a percepção institucional sem mudar o posicionamento jurídico do escritório. A ideia é organizar melhor especialidades, autoridade, conteúdo e contato, com uma experiência mais premium e adequada às regras de publicidade da advocacia. Eu já separei um diagnóstico rápido do que melhoraria. Posso te mostrar em 1 minuto?"
        }
    }
    setting = db.session.get(Setting, "scripts")
    scripts = default_scripts
    if setting:
        try: scripts = {**default_scripts, **json.loads(setting.value_json)}
        except Exception: pass
    return jsonify({
        "user": current_user().to_dict(), "month": m,
        "leads": [l.to_dict() for l in leads], "meetings": [x.to_dict() for x in meetings],
        "contracts": [x.to_dict() for x in contracts], "goals": [g.to_dict() for g in goals],
        "team": {"stats": team_stats(m), "goal": goal_progress(team_goal, team_stats(m))},
        "users": summaries, "scripts": scripts,
    })


def apply_lead_payload(lead, data):
    mapping = {
        "category": "category", "name": "name", "phone": "phone", "address": "address", "rating": "rating",
        "reviews": "reviews", "score": "score", "grade": "grade", "priority": "priority", "argument": "argument",
        "pitch": "pitch", "status": "status", "website": "website", "instagram": "instagram", "email": "email",
        "responsible": "responsible", "lastContact": "last_contact", "nextDate": "next_date", "nextAction": "next_action",
        "notes": "notes", "siteStatus": "site_status", "archived": "archived", "importedAt": "imported_at",
        "sourceBatch": "source_batch", "ownerId": "owner_id",
    }
    for key, attr in mapping.items():
        if key in data:
            val = data[key]
            if key == "score":
                try: val = int(val or 0)
                except (TypeError, ValueError): val = 0
            if key == "archived": val = bool(val)
            setattr(lead, attr, val if val is not None else "")
    lead.category = lead.category or "ADVOCACIA"
    lead.updated_at = now_iso()
    lead.updated_by = current_user().id


@app.post("/api/leads")
@login_required
def create_lead():
    data = request.get_json(silent=True) or {}
    if not str(data.get("name", "")).strip():
        return jsonify({"error": "name_required"}), 400
    lead = Lead(id=data.get("id") or uid("lead"), name=str(data["name"]).strip(), created_by=current_user().id, updated_by=current_user().id)
    apply_lead_payload(lead, data)
    db.session.add(lead)
    log_activity("create", "lead", lead.id, f"Criou o lead {lead.name}")
    db.session.commit()
    return jsonify(lead.to_dict()), 201


@app.post("/api/leads/bulk")
@login_required
def create_leads_bulk():
    items = (request.get_json(silent=True) or {}).get("leads") or []
    existing_names = {x[0].lower().strip() for x in db.session.query(Lead.name).all()}
    created = []
    for data in items[:500]:
        name = str(data.get("name", "")).strip()
        if not name or name.lower() in existing_names:
            continue
        lead = Lead(id=data.get("id") or uid("lead"), name=name, created_by=current_user().id, updated_by=current_user().id)
        apply_lead_payload(lead, data)
        db.session.add(lead); created.append(lead); existing_names.add(name.lower())
    log_activity("bulk_import", "lead", None, f"Importou {len(created)} leads")
    db.session.commit()
    return jsonify({"created": len(created), "leads": [x.to_dict() for x in created]})


@app.patch("/api/leads/<lead_id>")
@login_required
def update_lead(lead_id):
    lead = db.session.get(Lead, lead_id)
    if not lead: return jsonify({"error": "not_found"}), 404
    data = request.get_json(silent=True) or {}
    apply_lead_payload(lead, data)
    log_activity("update", "lead", lead.id, f"Atualizou o lead {lead.name}")
    db.session.commit()
    return jsonify(lead.to_dict())


@app.delete("/api/leads/<lead_id>")
@login_required
def delete_lead(lead_id):
    lead = db.session.get(Lead, lead_id)
    if not lead: return jsonify({"error": "not_found"}), 404
    name = lead.name
    Meeting.query.filter_by(lead_id=lead_id).update({"lead_id": None})
    Contract.query.filter_by(lead_id=lead_id).update({"lead_id": None})
    db.session.delete(lead)
    log_activity("delete", "lead", lead_id, f"Excluiu permanentemente o lead {name}")
    db.session.commit()
    return jsonify({"ok": True})


@app.post("/api/meetings")
@login_required
def create_meeting():
    data = request.get_json(silent=True) or {}
    if not data.get("startAt"): return jsonify({"error": "start_required"}), 400
    lead = db.session.get(Lead, data.get("leadId")) if data.get("leadId") else None
    title = str(data.get("title") or (f"Reunião — {lead.name}" if lead else "Reunião")).strip()
    meeting = Meeting(
        id=uid("meet"), lead_id=lead.id if lead else None, owner_id=data.get("ownerId") or current_user().id,
        title=title, start_at=str(data["startAt"]), duration_minutes=int(data.get("durationMinutes") or 30),
        format=data.get("format") or "Online", location=data.get("location") or "", meet_link=data.get("meetLink") or "",
        status=data.get("status") or "Marcada", notes=data.get("notes") or "", outcome=data.get("outcome") or "",
        created_by=current_user().id,
    )
    db.session.add(meeting)
    if lead:
        lead.status = "Reunião marcada"; lead.next_action = "Participar da reunião"; lead.next_date = meeting.start_at[:10]
        lead.updated_by = current_user().id; lead.updated_at = now_iso()
    log_activity("create", "meeting", meeting.id, f"Marcou {title}" + (f" com {lead.name}" if lead else ""))
    db.session.commit()
    return jsonify(meeting.to_dict()), 201


@app.patch("/api/meetings/<meeting_id>")
@login_required
def update_meeting(meeting_id):
    m = db.session.get(Meeting, meeting_id)
    if not m: return jsonify({"error": "not_found"}), 404
    data = request.get_json(silent=True) or {}
    mp = {"leadId":"lead_id","ownerId":"owner_id","title":"title","startAt":"start_at","durationMinutes":"duration_minutes","format":"format","location":"location","meetLink":"meet_link","status":"status","notes":"notes","outcome":"outcome"}
    for k,a in mp.items():
        if k in data: setattr(m,a,data[k])
    m.updated_at = now_iso()
    log_activity("update", "meeting", m.id, f"Atualizou a reunião {m.title}")
    db.session.commit()
    return jsonify(m.to_dict())


@app.delete("/api/meetings/<meeting_id>")
@login_required
def delete_meeting(meeting_id):
    m = db.session.get(Meeting, meeting_id)
    if not m: return jsonify({"error":"not_found"}), 404
    title = m.title; db.session.delete(m); log_activity("delete", "meeting", meeting_id, f"Excluiu a reunião {title}")
    db.session.commit(); return jsonify({"ok":True})


@app.post("/api/contracts")
@login_required
def create_contract():
    data = request.get_json(silent=True) or {}
    lead = db.session.get(Lead, data.get("leadId")) if data.get("leadId") else None
    client_name = str(data.get("clientName") or (lead.name if lead else "")).strip()
    if not client_name: return jsonify({"error":"client_required"}), 400
    closed_at = str(data.get("closedAt") or local_today().isoformat())[:10]
    contract = Contract(
        id=uid("contract"), lead_id=lead.id if lead else None, owner_id=data.get("ownerId") or current_user().id,
        title=str(data.get("title") or f"Contrato — {client_name}"), client_name=client_name,
        value_cents=cents(data.get("value")) if "value" in data else int(data.get("valueCents") or 0),
        status=data.get("status") or "Fechado", closed_at=closed_at, payment_method=data.get("paymentMethod") or "",
        notes=data.get("notes") or "", created_by=current_user().id,
    )
    db.session.add(contract)
    if lead and contract.status == "Fechado":
        lead.status = "Fechado"; lead.archived = False; lead.next_action = "Contrato fechado"; lead.updated_by=current_user().id; lead.updated_at=now_iso()
    log_activity("create", "contract", contract.id, f"Registrou contrato fechado de {client_name} por R$ {contract.value_cents/100:,.2f}")
    db.session.commit()
    return jsonify(contract.to_dict()), 201


@app.patch("/api/contracts/<contract_id>")
@login_required
def update_contract(contract_id):
    c = db.session.get(Contract, contract_id)
    if not c: return jsonify({"error":"not_found"}), 404
    data = request.get_json(silent=True) or {}
    mp = {"leadId":"lead_id","ownerId":"owner_id","title":"title","clientName":"client_name","status":"status","closedAt":"closed_at","paymentMethod":"payment_method","notes":"notes"}
    for k,a in mp.items():
        if k in data: setattr(c,a,data[k])
    if "value" in data: c.value_cents = cents(data["value"])
    if "valueCents" in data: c.value_cents = int(data["valueCents"] or 0)
    c.updated_at=now_iso(); log_activity("update","contract",c.id,f"Atualizou contrato de {c.client_name}")
    db.session.commit(); return jsonify(c.to_dict())


@app.delete("/api/contracts/<contract_id>")
@login_required
def delete_contract(contract_id):
    c=db.session.get(Contract,contract_id)
    if not c:return jsonify({"error":"not_found"}),404
    client=c.client_name;db.session.delete(c);log_activity("delete","contract",contract_id,f"Excluiu contrato de {client}")
    db.session.commit();return jsonify({"ok":True})


@app.post("/api/goals")
@login_required
def upsert_goal():
    data = request.get_json(silent=True) or {}
    m = month_key(data.get("month"))
    scope = data.get("scope") or "team"
    user_id = data.get("userId") if scope == "user" else None
    if scope == "user" and not user_id: return jsonify({"error":"user_required"}), 400
    q = Goal.query.filter_by(month=m, scope=scope, user_id=user_id).first()
    if not q:
        q = Goal(id=uid("goal"), month=m, scope=scope, user_id=user_id, created_by=current_user().id)
        db.session.add(q)
    q.revenue_target_cents = cents(data.get("revenueTarget")) if "revenueTarget" in data else int(data.get("revenueTargetCents") or 0)
    q.contracts_target = int(data.get("contractsTarget") or 0)
    q.meetings_target = int(data.get("meetingsTarget") or 0)
    q.updated_at = now_iso()
    target_name = db.session.get(User,user_id).name if user_id and db.session.get(User,user_id) else "Equipe"
    log_activity("upsert", "goal", q.id, f"Atualizou meta de {target_name} para {m}")
    db.session.commit(); return jsonify(q.to_dict())


@app.delete("/api/goals/<goal_id>")
@login_required
def delete_goal(goal_id):
    g=db.session.get(Goal,goal_id)
    if not g:return jsonify({"error":"not_found"}),404
    db.session.delete(g);log_activity("delete","goal",goal_id,f"Excluiu meta de {g.month}");db.session.commit();return jsonify({"ok":True})


@app.put("/api/settings/scripts")
@login_required
def save_scripts():
    data = request.get_json(silent=True) or {}
    setting = db.session.get(Setting, "scripts")
    if not setting:
        setting = Setting(key="scripts"); db.session.add(setting)
    setting.value_json=json.dumps(data,ensure_ascii=False);setting.updated_by=current_user().id;setting.updated_at=now_iso()
    log_activity("update","settings","scripts","Atualizou os scripts comerciais")
    db.session.commit();return jsonify({"ok":True})


@app.get("/api/activities")
@login_required
def activities():
    user_id=request.args.get("userId");limit=min(int(request.args.get("limit",50)),200)
    q=Activity.query
    if user_id:q=q.filter_by(user_id=user_id)
    return jsonify([a.to_dict() for a in q.order_by(Activity.created_at.desc()).limit(limit).all()])


@app.get("/healthz")
def healthz():
    # Liveness simples para o Render. A conexão com o banco já é validada no startup.
    return jsonify({"ok": True, "service": "LM TECH CRM"})


@app.get("/api/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"ok": True, "service": "LM TECH CRM", "database": "ok"})
    except Exception:
        db.session.rollback()
        return jsonify({"ok": False, "service": "LM TECH CRM", "database": "unavailable"}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "0") == "1")
