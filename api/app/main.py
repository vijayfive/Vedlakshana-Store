"""
Vedlakshana Store API — replaces Code.gs / the Google Sheet backend.

Two endpoints, matching exactly what index.html already calls today:
  GET  /state   -> full store state as JSON (same shape loadState() expects)
  POST /sync    -> {"token": "...", "state": {...}}  (same shape persist() sends)

The only real behavior change from Code.gs: this does proper upserts
(INSERT ... ON CONFLICT equivalent via SQLAlchemy merge) instead of
clearing and rewriting everything on every save — which is what let
duplicate sales pile up silently on the old Sheets backend. A sale with
an id that's sent again updates in place; it can never be duplicated.
"""
import os
import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select

from .db import get_db, engine, Base
from . import models
from .schemas import SyncRequest, SyncResponse, StateOut

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vedlakshana-api")

WRITE_TOKEN = os.environ["WRITE_TOKEN"]
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "https://vijayfive.github.io")
ENV = os.environ.get("ENV", "production")

app = FastAPI(
    title="Vedlakshana Store API",
    docs_url="/docs" if ENV != "production" else None,   # hide Swagger UI in prod
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.on_event("startup")
def on_startup():
    # creates tables if they don't exist yet — safe to run every time,
    # it's a no-op once the schema is already there
    Base.metadata.create_all(bind=engine)
    logger.info("Startup complete, tables ensured.")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/state", response_model=StateOut)
def get_state(db: Session = Depends(get_db)):
    settings = {s.key: s.value for s in db.scalars(select(models.Setting)).all()}

    products = db.scalars(select(models.Product).order_by(models.Product.name)).all()
    sales = db.scalars(select(models.Sale).order_by(models.Sale.ts.desc())).all()
    purchases = db.scalars(select(models.Purchase).order_by(models.Purchase.ts.desc())).all()
    expenses = db.scalars(select(models.Expense).order_by(models.Expense.ts.desc())).all()

    return StateOut(
        storeName=settings.get("storeName", "Vedlakshana Store"),
        pin=settings.get("pin", "1234"),
        lowStockThreshold=int(settings.get("lowStockThreshold", 5)),
        products=[
            {"id": p.id, "name": p.name, "price": float(p.price),
             "costPrice": float(p.cost_price), "stock": p.stock}
            for p in products
        ],
        sales=[
            {
                "id": s.id, "ts": s.ts, "total": float(s.total),
                "paymentMethod": s.payment_method,
                "customerName": s.customer_name or "", "customerPhone": s.customer_phone or "",
                "items": [
                    {"productId": it.product_id, "name": it.name, "price": float(it.price),
                     "costPrice": float(it.cost_price), "qty": it.qty}
                    for it in s.items
                ],
            }
            for s in sales
        ],
        purchases=[
            {"id": x.id, "ts": x.ts, "productId": x.product_id, "productName": x.product_name,
             "qty": x.qty, "costPrice": float(x.cost_price), "total": float(x.total)}
            for x in purchases
        ],
        expenses=[
            {"id": x.id, "ts": x.ts, "description": x.description,
             "amount": float(x.amount), "category": x.category}
            for x in expenses
        ],
    )


@app.post("/sync", response_model=SyncResponse)
def sync_state(body: SyncRequest, db: Session = Depends(get_db)):
    if body.token != WRITE_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")

    state = body.state
    try:
        # settings
        for key, value in (
            ("storeName", state.storeName),
            ("pin", state.pin),
            ("lowStockThreshold", str(state.lowStockThreshold)),
        ):
            row = db.get(models.Setting, key)
            if row:
                row.value = value
            else:
                db.add(models.Setting(key=key, value=value))

        # products: upsert everything sent, then delete anything not sent
        # (mirrors the old full-overwrite behavior so deleteProduct() still works)
        incoming_ids = {p.id for p in state.products}
        for p in state.products:
            row = db.get(models.Product, p.id)
            if row:
                row.name, row.price, row.cost_price, row.stock = p.name, p.price, p.costPrice, p.stock
            else:
                db.add(models.Product(id=p.id, name=p.name, price=p.price,
                                       cost_price=p.costPrice, stock=p.stock))
        for row in db.scalars(select(models.Product)).all():
            if row.id not in incoming_ids:
                db.delete(row)

        # sales: upsert, never duplicated — this is the core fix
        for s in state.sales:
            row = db.get(models.Sale, s.id)
            if row:
                row.ts, row.total = s.ts, s.total
                row.payment_method = s.paymentMethod
                row.customer_name, row.customer_phone = s.customerName, s.customerPhone
                row.items.clear()
            else:
                row = models.Sale(
                    id=s.id, ts=s.ts, total=s.total, payment_method=s.paymentMethod,
                    customer_name=s.customerName, customer_phone=s.customerPhone,
                )
                db.add(row)
            for it in s.items:
                row.items.append(models.SaleItem(
                    product_id=it.productId, name=it.name, price=it.price,
                    cost_price=it.costPrice, qty=it.qty,
                ))

        # purchases: upsert
        for x in state.purchases:
            row = db.get(models.Purchase, x.id)
            if row:
                row.ts, row.product_id, row.product_name = x.ts, x.productId, x.productName
                row.qty, row.cost_price, row.total = x.qty, x.costPrice, x.total
            else:
                db.add(models.Purchase(
                    id=x.id, ts=x.ts, product_id=x.productId, product_name=x.productName,
                    qty=x.qty, cost_price=x.costPrice, total=x.total,
                ))

        # expenses: upsert
        for x in state.expenses:
            row = db.get(models.Expense, x.id)
            if row:
                row.ts, row.description = x.ts, x.description
                row.amount, row.category = x.amount, x.category
            else:
                db.add(models.Expense(
                    id=x.id, ts=x.ts, description=x.description,
                    amount=x.amount, category=x.category,
                ))

        db.commit()
        return SyncResponse(ok=True)

    except Exception as e:
        db.rollback()
        logger.exception("sync_state failed")
        return SyncResponse(ok=False, error=str(e))
