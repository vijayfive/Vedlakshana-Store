"""
Pydantic schemas — define the exact JSON shape the app sends and receives.
FastAPI uses these to validate incoming requests automatically (a malformed
request gets rejected with a clear error before any of our code runs) and
to document the API at /docs.
"""
from pydantic import BaseModel, Field
from typing import List


class SaleItemIn(BaseModel):
    productId: str
    name: str
    price: float
    costPrice: float = 0
    qty: int


class SaleIn(BaseModel):
    id: str
    ts: int
    items: List[SaleItemIn]
    total: float
    paymentMethod: str = "Cash"
    customerName: str = ""
    customerPhone: str = ""


class ProductIn(BaseModel):
    id: str
    name: str
    price: float
    costPrice: float = 0
    stock: int = 0


class PurchaseIn(BaseModel):
    id: str
    ts: int
    productId: str
    productName: str
    qty: int
    costPrice: float
    total: float


class ExpenseIn(BaseModel):
    id: str
    ts: int
    description: str
    amount: float
    category: str = "Misc"


class StateIn(BaseModel):
    """The full payload shape persist() sends — mirrors state in index.html."""
    storeName: str = "Vedlakshana Store"
    pin: str = "1234"
    lowStockThreshold: int = 5
    products: List[ProductIn] = Field(default_factory=list)
    sales: List[SaleIn] = Field(default_factory=list)
    purchases: List[PurchaseIn] = Field(default_factory=list)
    expenses: List[ExpenseIn] = Field(default_factory=list)


class SyncRequest(BaseModel):
    """The full POST body shape: {"token": "...", "state": {...}}."""
    token: str
    state: StateIn


class SyncResponse(BaseModel):
    ok: bool
    error: str | None = None


class StateOut(BaseModel):
    """What GET /state returns — same fields as StateIn, just the output side."""
    storeName: str
    pin: str
    lowStockThreshold: int
    products: List[ProductIn]
    sales: List[SaleIn]
    purchases: List[PurchaseIn]
    expenses: List[ExpenseIn]
