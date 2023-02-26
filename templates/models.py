from sqlalchemy import String
from sqlalchemy.orm import declarative_base, Mapped, mapped_column

Base = declarative_base()


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))

    def __init__(self, name):
        self.name = name

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r})"
