from sqlalchemy import String, Integer, Column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Laptop(Base):
    __tablename__ = "app_laptop"
    id = Column(Integer, primary_key=True)
    nama_laptop = Column(String)
    ram = Column(Integer)
    memori_internal = Column(Integer)
    layar = Column(String)
    harga = Column(Integer)
    processor = Column(String)
    baterai = Column(Integer)

    def __repr__(self):
        return f"Laptop(id={self.id!r}, nama_laptop={self.nama_laptop!r}, ram={self.ram!r}, memori_internal={self.memori_internal!r}, layar={self.layar!r}, harga={self.harga!r}, processor={self.processor!r},  baterai={self.baterai!r})"
