"""SQLAlchemy models for the shop database.

Tables:
    - products: Product catalog
    - customers: Customer information
    - orders: Order records
    - order_items: Line items for orders
    - reservations: Stock reservations
"""

import enum
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    UUID,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class OrderStatus(str, enum.Enum):
    """Enumeration of order statuses."""

    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Product(Base):
    """Product catalog table.

    Attributes:
        id: Unique identifier (UUID)
        name: Product name
        category: Product category
        price: Product price (Decimal)
        stock: Current stock quantity
        sku: Stock Keeping Unit (unique)
        description: Product description
        created_at: Timestamp when product was created
        updated_at: Timestamp when product was last updated
    """

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    order_items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="product", lazy="selectin"
    )
    reservations: Mapped[list["Reservation"]] = relationship(
        "Reservation", back_populates="product", lazy="selectin"
    )

    # Indexes
    __table_args__ = (
        Index("idx_product_category", "category"),
        Index("idx_product_sku", "sku"),
    )

    def __repr__(self) -> str:
        """String representation of Product."""
        return f"<Product(id={self.id}, sku={self.sku}, name={self.name})>"


class Customer(Base):
    """Customer information table.

    Attributes:
        id: Unique identifier (UUID)
        name: Customer name
        email: Customer email (unique)
        address: Customer address
        created_at: Timestamp when customer was created
    """

    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    # Relationships
    orders: Mapped[list["Order"]] = relationship(
        "Order", back_populates="customer", lazy="selectin"
    )

    # Indexes
    __table_args__ = (Index("idx_customer_email", "email"),)

    def __repr__(self) -> str:
        """String representation of Customer."""
        return f"<Customer(id={self.id}, email={self.email}, name={self.name})>"


class Order(Base):
    """Order records table.

    Attributes:
        id: Unique identifier (UUID)
        customer_id: Foreign key to customers table
        status: Order status (enum)
        total: Order total amount (Decimal)
        created_at: Timestamp when order was created
        updated_at: Timestamp when order was last updated
    """

    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING
    )
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders", lazy="joined")
    order_items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )
    reservations: Mapped[list["Reservation"]] = relationship(
        "Reservation", back_populates="order", lazy="selectin"
    )

    # Indexes
    __table_args__ = (
        Index("idx_order_customer_id", "customer_id"),
        Index("idx_order_status", "status"),
        Index("idx_order_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation of Order."""
        return f"<Order(id={self.id}, customer_id={self.customer_id}, status={self.status})>"


class OrderItem(Base):
    """Order line items table.

    Attributes:
        id: Unique identifier (UUID)
        order_id: Foreign key to orders table
        product_id: Foreign key to products table
        quantity: Quantity ordered
        price_each: Price per unit at time of order (Decimal)
    """

    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_each: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="order_items", lazy="joined")
    product: Mapped["Product"] = relationship(
        "Product", back_populates="order_items", lazy="joined"
    )

    # Indexes and constraints
    __table_args__ = (
        Index("idx_order_item_order_id", "order_id"),
        Index("idx_order_item_product_id", "product_id"),
        UniqueConstraint("order_id", "product_id", name="uq_order_item_order_product"),
    )

    def __repr__(self) -> str:
        """String representation of OrderItem."""
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id})>"


class Reservation(Base):
    """Stock reservations table.

    Attributes:
        id: Unique identifier (UUID)
        product_id: Foreign key to products table
        quantity: Quantity reserved
        expires_at: Expiration timestamp for reservation
        order_id: Foreign key to orders table (nullable)
        created_at: Timestamp when reservation was created
    """

    __tablename__ = "reservations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    # Relationships
    product: Mapped["Product"] = relationship(
        "Product", back_populates="reservations", lazy="joined"
    )
    order: Mapped["Order | None"] = relationship(
        "Order", back_populates="reservations", lazy="joined"
    )

    # Indexes
    __table_args__ = (
        Index("idx_reservation_product_id", "product_id"),
        Index("idx_reservation_expires_at", "expires_at"),
        Index("idx_reservation_order_id", "order_id"),
    )

    def __repr__(self) -> str:
        """String representation of Reservation."""
        return (
            f"<Reservation(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"
        )
