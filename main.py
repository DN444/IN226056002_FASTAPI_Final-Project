from fastapi import FastAPI, Query, HTTPException, status
from pydantic import BaseModel, Field
from typing import List
app = FastAPI()
products = [
    {"id": 1, "name": "Slim Fit Shirt", "brand": "Zara", "category": "Shirt", "price": 1200, "sizes_available": ["S", "M", "L"], "in_stock": True},
    {"id": 2, "name": "Denim Jeans", "brand": "Levis", "category": "Jeans", "price": 2200, "sizes_available": ["M", "L"], "in_stock": True},
    {"id": 3, "name": "Running Shoes", "brand": "Nike", "category": "Shoes", "price": 3500, "sizes_available": ["8", "9", "10"], "in_stock": False},
    {"id": 4, "name": "Summer Dress", "brand": "H&M", "category": "Dress", "price": 1800, "sizes_available": ["S", "M"], "in_stock": True},
    {"id": 5, "name": "Leather Jacket", "brand": "Zara", "category": "Jacket", "price": 5000, "sizes_available": ["M", "L"], "in_stock": True},
    {"id": 6, "name": "Casual Shirt", "brand": "H&M", "category": "Shirt", "price": 1000, "sizes_available": ["S", "M", "L"], "in_stock": False},
]
orders = []
wishlist = []
order_counter = 1
class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    size: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0, le=10)
    delivery_address: str = Field(..., min_length=10)
    gift_wrap: bool = False
    season_sale: bool = False
class NewProduct(BaseModel):
    name: str = Field(..., min_length=2)
    brand: str = Field(..., min_length=2)
    category: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    sizes_available: List[str]
    in_stock: bool = True
def find_product(product_id: int):
    return next((p for p in products if p["id"] == product_id), None)
def calculate_order_total(price, quantity, gift_wrap, season_sale):
    base = price * quantity
    sale_discount = 0
    bulk_discount = 0
    gift_cost = 0
    if season_sale:
        sale_discount = base * 0.15
        base -= sale_discount
    if quantity >= 5:
        bulk_discount = base * 0.05
        base -= bulk_discount
    if gift_wrap:
        gift_cost = 50 * quantity
        base += gift_cost
    return {
        "final_total": int(base),
        "season_discount": int(sale_discount),
        "bulk_discount": int(bulk_discount),
        "gift_wrap_cost": gift_cost
    }
def filter_products_logic(category=None, brand=None, max_price=None, in_stock=None):
    result = products
    if category is not None:
        result = [p for p in result if p["category"] == category]
    if brand is not None:
        result = [p for p in result if p["brand"] == brand]
    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]
    if in_stock is not None:
        result = [p for p in result if p["in_stock"] == in_stock]
    return result
@app.get("/")
def home():
    return {"message": "Welcome to TrendZone Fashion Store"}
@app.get("/products")
def get_products():
    in_stock_count = sum(p["in_stock"] for p in products)
    return {"products": products, "total": len(products), "in_stock_count": in_stock_count}
@app.get("/products/summary")
def summary():
    brands = list(set(p["brand"] for p in products))
    category_count = {}
    for p in products:
        category_count[p["category"]] = category_count.get(p["category"], 0) + 1
    return {
        "total_products": len(products),
        "in_stock": sum(p["in_stock"] for p in products),
        "out_of_stock": sum(not p["in_stock"] for p in products),
        "brands": brands,
        "category_count": category_count
    }
@app.get("/products/filter")
def filter_products(category: str = None, brand: str = None,
                    max_price: int = None, in_stock: bool = None):
    result = filter_products_logic(category, brand, max_price, in_stock)
    return {"results": result, "count": len(result)}
@app.get("/products/search")
def search_products(keyword: str):
    result = [
        p for p in products
        if keyword.lower() in p["name"].lower()
        or keyword.lower() in p["brand"].lower()
        or keyword.lower() in p["category"].lower()
    ]
    if not result:
        return {"message": "No results found"}

    return {"results": result, "total_found": len(result)}
@app.get("/products/sort")
def sort_products(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price", "name", "brand", "category"]:
        raise HTTPException(400, "Invalid sort field")
    return sorted(products, key=lambda x: x[sort_by], reverse=(order == "desc"))
@app.get("/products/page")
def paginate_products(page: int = 1, limit: int = 3):
    total = len(products)
    start = (page - 1) * limit
    return {
        "page": page,
        "total_pages": (total + limit - 1) // limit,
        "data": products[start:start + limit]
    }
@app.get("/products/browse")
def browse(keyword: str = None, category: str = None, brand: str = None,
           in_stock: bool = None, max_price: int = None,
           sort_by: str = "price", order: str = "asc",
           page: int = 1, limit: int = 3):
    result = filter_products_logic(category, brand, max_price, in_stock)
    if keyword:
        result = [p for p in result if keyword.lower() in p["name"].lower()]
    result = sorted(result, key=lambda x: x[sort_by], reverse=(order == "desc"))
    total = len(result)
    start = (page - 1) * limit
    return {
        "total": total,
        "page": page,
        "total_pages": (total + limit - 1) // limit,
        "data": result[start:start + limit]
    }
@app.post("/products", status_code=201)
def add_product(product: NewProduct):
    for p in products:
        if p["name"] == product.name and p["brand"] == product.brand:
            raise HTTPException(400, "Duplicate product")
    new_product = product.dict()
    new_product["id"] = max(p["id"] for p in products) + 1
    products.append(new_product)
    return new_product
@app.put("/products/{product_id}")
def update_product(product_id: int, price: int = None, in_stock: bool = None):
    product = find_product(product_id)
    if not product:
        raise HTTPException(404, "Not found")
    if price is not None:
        product["price"] = price
    if in_stock is not None:
        product["in_stock"] = in_stock
    return product
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    product = find_product(product_id)
    if not product:
        raise HTTPException(404, "Not found")
    for o in orders:
        if o["product"] == product["name"]:
            raise HTTPException(400, "Product has order history")
    products.remove(product)
    return {"message": "Deleted"}
@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = find_product(product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return product
@app.get("/orders")
def get_orders():
    return {
        "orders": orders,
        "total": len(orders),
        "total_revenue": sum(o["total"] for o in orders)
    }
@app.get("/orders/search")
def search_orders(customer_name: str):
    result = [o for o in orders if customer_name.lower() in o["customer"].lower()]
    if not result:
        return {"message": "No orders found"}
    return {"results": result, "total_found": len(result)}
@app.get("/orders/sort")
def sort_orders(sort_by: str = "total", order: str = "asc"):
    if sort_by not in ["total", "quantity"]:
        raise HTTPException(400, "sort_by must be 'total' or 'quantity'")
    if order not in ["asc", "desc"]:
        raise HTTPException(400, "order must be 'asc' or 'desc'")
    reverse = (order == "desc")
    sorted_orders = sorted(
        orders,
        key=lambda o: o.get(sort_by, 0),
        reverse=reverse
    )
    return {
        "sort_by": sort_by,
        "order": order,
        "total_orders": len(sorted_orders),
        "orders": sorted_orders
    }
@app.get("/orders/page")
def paginate_orders(page: int = 1, limit: int = 3):
    total = len(orders)
    start = (page - 1) * limit
    return {
        "page": page,
        "total_pages": (total + limit - 1) // limit,
        "data": orders[start:start + limit]
    }
@app.post("/orders")
def create_order(order: OrderRequest):
    global order_counter
    product = find_product(order.product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    if not product["in_stock"]:
        raise HTTPException(400, "Out of stock")
    if order.size not in product["sizes_available"]:
        raise HTTPException(400, f"Available sizes: {product['sizes_available']}")
    pricing = calculate_order_total(
        product["price"], order.quantity, order.gift_wrap, order.season_sale
    )
    new_order = {
        "order_id": order_counter,
        "customer": order.customer_name,
        "product": product["name"],
        "brand": product["brand"],
        "size": order.size,
        "quantity": order.quantity,
        "gift_wrap": order.gift_wrap,
        "total": pricing["final_total"],
        "breakdown": pricing
    }
    orders.append(new_order)
    order_counter += 1
    return new_order
@app.get("/wishlist")
def view_wishlist():
    return {
        "wishlist": wishlist,
        "total_value": sum(item["price"] for item in wishlist)
    }
@app.post("/wishlist/add")
def add_wishlist(customer_name: str, product_id: int, size: str):
    product = find_product(product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    if size not in product["sizes_available"]:
        raise HTTPException(400, "Invalid size")
    for item in wishlist:
        if item["customer"] == customer_name and item["product_id"] == product_id and item["size"] == size:
            raise HTTPException(400, "Already exists")
    wishlist.append({
        "customer": customer_name,
        "product_id": product_id,
        "size": size,
        "price": product["price"]
    })
    return {"message": "Added"}
@app.delete("/wishlist/remove")
def remove_wishlist(customer_name: str, product_id: int):
    for item in wishlist:
        if item["customer"] == customer_name and item["product_id"] == product_id:
            wishlist.remove(item)
            return {"message": "Removed"}
    raise HTTPException(404, "Not found")
@app.post("/wishlist/order-all", status_code=201)
def order_all(customer_name: str, delivery_address: str):
    global order_counter
    items = [w for w in wishlist if w["customer"] == customer_name]
    if not items:
        raise HTTPException(400, "Wishlist empty")
    created_orders = []
    total = 0
    for item in items:
        product = find_product(item["product_id"])
        order = {
            "order_id": order_counter,
            "customer": customer_name,
            "product": product["name"],
            "quantity": 1,
            "total": product["price"]
        }
        orders.append(order)
        created_orders.append(order)
        total += product["price"]
        order_counter += 1
    wishlist[:] = [w for w in wishlist if w["customer"] != customer_name]
    return {"orders": created_orders, "grand_total": total}