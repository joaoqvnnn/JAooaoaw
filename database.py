import secrets
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey, Numeric, String, Text, func, select,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import DATABASE_URL, SUPER_ADMIN_ID


class Base(DeclarativeBase):
    pass


# ---------- BASE ----------
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128), default="Membro")
    wallet_id: Mapped[str] = mapped_column(String(32), unique=True)
    balance: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class UserState(Base):
    __tablename__ = "user_states"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    screen: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deep_link_arg: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    pending_operation: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    pending_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")


# ---------- CATÁLOGO ----------
class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    promo_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    min_qty: Mapped[int] = mapped_column(default=1)
    max_qty: Mapped[int] = mapped_column(default=10)
    delivery_type: Mapped[str] = mapped_column(String(30), default="credentials")
    activation_link: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    visible: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Credential(Base):
    __tablename__ = "credentials"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    email: Mapped[str] = mapped_column(String(200))
    password: Mapped[str] = mapped_column(String(200))
    extra: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="available", index=True)
    order_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ProductView(Base):
    __tablename__ = "product_views"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_tg_id: Mapped[int] = mapped_column(BigInteger, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    reminded: Mapped[bool] = mapped_column(Boolean, default=False)


# ---------- CARRINHO / PEDIDO ----------
class CartItem(Base):
    __tablename__ = "cart_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_tg_id: Mapped[int] = mapped_column(BigInteger, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(default=1)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_tg_id: Mapped[int] = mapped_column(BigInteger, index=True)
    total: Mapped[float] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product_name: Mapped[str] = mapped_column(String(120))
    quantity: Mapped[int] = mapped_column(default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2))
    total_price: Mapped[float] = mapped_column(Numeric(10, 2))


class OrderCredential(Base):
    __tablename__ = "order_credentials"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"))
    credential_id: Mapped[int] = mapped_column(ForeignKey("credentials.id"))


# ---------- ENGINE / SESSION ----------
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
SessionLocal = (
    async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    if engine else None
)


async def init_db() -> None:
    if not engine:
        raise RuntimeError("DATABASE_URL não configurado.")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def gen_wallet_id() -> str:
    return "W" + secrets.token_hex(6).upper()


# ---------- HELPERS BASE ----------
async def get_or_create_user(tg_user) -> User:
    async with SessionLocal() as session:
        row = (await session.execute(
            select(User).where(User.telegram_id == tg_user.id)
        )).scalar_one_or_none()
        is_root = tg_user.id == SUPER_ADMIN_ID
        if row is None:
            row = User(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name or "Membro",
                wallet_id=gen_wallet_id(),
                is_admin=is_root,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
        else:
            row.username = tg_user.username
            row.first_name = tg_user.first_name or row.first_name
            if is_root and not row.is_admin:
                row.is_admin = True
            row.last_activity = datetime.now(timezone.utc)
            await session.commit()
        return row


async def get_user_by_tg_id(telegram_id: int) -> Optional[User]:
    async with SessionLocal() as session:
        return (await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )).scalar_one_or_none()


async def get_state(user_id: int) -> Optional[UserState]:
    async with SessionLocal() as session:
        return await session.get(UserState, user_id)


async def upsert_state(user_id: int, **fields) -> UserState:
    async with SessionLocal() as session:
        state = await session.get(UserState, user_id)
        if state is None:
            state = UserState(user_id=user_id)
            session.add(state)
        for k, v in fields.items():
            setattr(state, k, v)
        state.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(state)
        return state


async def get_setting(key: str) -> Optional[str]:
    async with SessionLocal() as session:
        row = await session.get(Setting, key)
        return row.value if row else None


async def set_setting(key: str, value: str) -> None:
    async with SessionLocal() as session:
        row = await session.get(Setting, key)
        if row is None:
            session.add(Setting(key=key, value=value))
        else:
            row.value = value
        await session.commit()


# ---------- HELPERS CATÁLOGO ----------
async def list_categories() -> list[Category]:
    async with SessionLocal() as s:
        return list((await s.execute(
            select(Category).where(Category.active == True)
            .order_by(Category.position, Category.id)
        )).scalars().all())


async def get_category(cat_id: int) -> Optional[Category]:
    async with SessionLocal() as s:
        return await s.get(Category, cat_id)


async def list_products_by_category(cat_id: int, limit: int = 15, offset: int = 0) -> list[Product]:
    async with SessionLocal() as s:
        return list((await s.execute(
            select(Product).where(
                Product.category_id == cat_id,
                Product.active == True, Product.visible == True,
            ).order_by(Product.id).limit(limit).offset(offset)
        )).scalars().all())


async def count_products_by_category(cat_id: int) -> int:
    async with SessionLocal() as s:
        return (await s.execute(
            select(func.count()).select_from(Product).where(
                Product.category_id == cat_id,
                Product.active == True, Product.visible == True,
            )
        )).scalar_one()


async def get_product(prod_id: int) -> Optional[Product]:
    async with SessionLocal() as s:
        return await s.get(Product, prod_id)


async def count_stock(prod_id: int) -> int:
    async with SessionLocal() as s:
        return (await s.execute(
            select(func.count()).select_from(Credential).where(
                Credential.product_id == prod_id, Credential.status == "available"
            )
        )).scalar_one()


async def register_view(user_tg_id: int, prod_id: int) -> None:
    async with SessionLocal() as s:
        s.add(ProductView(user_tg_id=user_tg_id, product_id=prod_id))
        await s.commit()


async def count_viewers(prod_id: int) -> int:
    async with SessionLocal() as s:
        return (await s.execute(
            select(func.count(func.distinct(ProductView.user_tg_id)))
            .where(ProductView.product_id == prod_id)
        )).scalar_one()


# ---------- HELPERS CARRINHO ----------
async def get_cart(user_tg_id: int) -> list[CartItem]:
    async with SessionLocal() as s:
        return list((await s.execute(
            select(CartItem).where(CartItem.user_tg_id == user_tg_id)
            .order_by(CartItem.added_at)
        )).scalars().all())


async def cart_total_qty(user_tg_id: int) -> int:
    async with SessionLocal() as s:
        rows = (await s.execute(
            select(CartItem.quantity).where(CartItem.user_tg_id == user_tg_id)
        )).scalars().all()
        return int(sum(rows or [0]))


async def add_to_cart(user_tg_id: int, prod_id: int, qty: int = 1) -> None:
    async with SessionLocal() as s:
        existing = (await s.execute(
            select(CartItem).where(
                CartItem.user_tg_id == user_tg_id, CartItem.product_id == prod_id
            )
        )).scalar_one_or_none()
        if existing:
            existing.quantity += qty
        else:
            s.add(CartItem(user_tg_id=user_tg_id, product_id=prod_id, quantity=qty))
        await s.commit()


async def remove_cart_item(cart_item_id: int, user_tg_id: int) -> None:
    async with SessionLocal() as s:
        item = await s.get(CartItem, cart_item_id)
        if item and item.user_tg_id == user_tg_id:
            await s.delete(item)
            await s.commit()


async def clear_cart(user_tg_id: int) -> None:
    async with SessionLocal() as s:
        items = (await s.execute(
            select(CartItem).where(CartItem.user_tg_id == user_tg_id)
        )).scalars().all()
        for i in items:
            await s.delete(i)
        await s.commit()


# ---------- COMPRA (TRANSACIONAL) ----------
async def execute_purchase(user_tg_id: int, items: list[dict]) -> dict:
    """items = [{'product_id': int, 'quantity': int}]"""
    async with SessionLocal() as s:
        async with s.begin():
            user = (await s.execute(
                select(User).where(User.telegram_id == user_tg_id).with_for_update()
            )).scalar_one()

            plans = []
            total = 0.0
            for it in items:
                prod = (await s.execute(
                    select(Product).where(Product.id == it["product_id"]).with_for_update()
                )).scalar_one_or_none()
                if not prod or not prod.active or not prod.visible:
                    return {"ok": False, "error": "produto_indisponivel",
                            "product": it["product_id"]}

                creds = (await s.execute(
                    select(Credential).where(
                        Credential.product_id == prod.id,
                        Credential.status == "available",
                    ).with_for_update().limit(it["quantity"])
                )).scalars().all()

                if len(creds) < it["quantity"]:
                    return {"ok": False, "error": "estoque",
                            "product": prod.name, "available": len(creds)}

                price = float(prod.promo_price or prod.price)
                sub = price * it["quantity"]
                total += sub
                plans.append({"prod": prod, "creds": creds,
                              "price": price, "sub": sub, "qty": it["quantity"]})

            if float(user.balance) < total:
                return {
                    "ok": False, "error": "saldo",
                    "saldo": float(user.balance), "total": total,
                    "faltante": round(total - float(user.balance), 2),
                }

            user.balance = float(user.balance) - total
            order = Order(user_tg_id=user_tg_id, total=total,
                          status="paid", paid_at=datetime.now(timezone.utc))
            s.add(order)
            await s.flush()

            for p in plans:
                oi = OrderItem(
                    order_id=order.id, product_id=p["prod"].id,
                    product_name=p["prod"].name, quantity=p["qty"],
                    unit_price=p["price"], total_price=p["sub"],
                )
                s.add(oi)
                await s.flush()
                for cred in p["creds"]:
                    cred.status = "sold"
                    cred.order_id = order.id
                    cred.delivered_at = datetime.now(timezone.utc)
                    s.add(OrderCredential(order_id=order.id,
                                          order_item_id=oi.id,
                                          credential_id=cred.id))

            await s.flush()
            return {
                "ok": True, "order_id": order.id, "total": total,
                "new_balance": float(user.balance),
            }


async def get_order_with_credentials(order_id: int, user_tg_id: int) -> Optional[dict]:
    async with SessionLocal() as s:
        order = await s.get(Order, order_id)
        if not order or order.user_tg_id != user_tg_id:
            return None
        items = (await s.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        )).scalars().all()
        result = []
        for oi in items:
            creds = (await s.execute(
                select(Credential).join(OrderCredential,
                    OrderCredential.credential_id == Credential.id)
                .where(OrderCredential.order_item_id == oi.id)
            )).scalars().all()
            result.append({
                "item": oi,
                "credentials": [
                    {"email": c.email, "password": c.password, "extra": c.extra}
                    for c in creds
                ],
            })
        return {"order": order, "items": result}
