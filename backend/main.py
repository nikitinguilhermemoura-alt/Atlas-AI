import os
from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))
app = FastAPI(title="Atlas AI API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, troque pelo domínio real do frontend.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)

class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, le=20)

class OrderRequest(BaseModel):
    items: List[OrderItem]

PRODUCTS = [
    {"id": "atlas-starter", "name": "Atlas Starter", "description": "Acesso básico de demonstração", "price_cents": 0, "currency": "BRL"},
    {"id": "atlas-pro-demo", "name": "Atlas Pro (demonstração)", "description": "Produto de teste; não ativa cobrança real", "price_cents": 1990, "currency": "BRL"},
]
ORDERS = []

@app.get("/")
def root():
    return {"name": "Atlas AI API", "status": "online"}

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/chat")
def chat(body: ChatRequest):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return {"reply": "O backend do Atlas está funcionando! Para respostas reais de IA, configure OPENAI_API_KEY no arquivo backend/.env e reinicie o servidor."}
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=body.message,
        )
        return {"reply": response.output_text}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao consultar o serviço de IA: {type(exc).__name__}")

@app.get("/api/store/products")
def products():
    return {"products": PRODUCTS}

@app.post("/api/store/orders")
def create_order(body: OrderRequest):
    product_map = {p["id"]: p for p in PRODUCTS}
    items = []
    total = 0
    for item in body.items:
        product = product_map.get(item.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        line_total = product["price_cents"] * item.quantity
        total += line_total
        items.append({"product_id": product["id"], "name": product["name"], "quantity": item.quantity,
                      "unit_price_cents": product["price_cents"], "line_total_cents": line_total})
    order = {"id": f"demo-{len(ORDERS)+1:04d}", "status": "demo_created_not_paid",
             "total_cents": total, "currency": "BRL", "items": items,
             "message": "Pedido de demonstração criado. Nenhum pagamento foi realizado."}
    ORDERS.append(order)
    return {"order": order}

@app.get("/api/store/orders")
def list_orders():
    return {"orders": ORDERS}
