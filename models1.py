from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Laptop(Base):
    __tablename__ = "app_laptop"
    id = Column(Integer, primary_key=True)
    nama_laptop = Column(String(255))
    ram = Column(Integer)
    memori_internal = Column(Integer)
    layar = Column(String(255))
    harga = Column(Integer)
    processor = Column(String(255))
    baterai = Column(Integer)

    def __init__(self, id, nama_laptop, baterai, layar, ram, processor, harga):
        self.id = id
        self.nama_laptop = nama_laptop
        self.baterai = baterai
        self.layar = layar
        self.ram = ram
        self.processor = processor
        self.harga = harga

    def calculate_score(self, dev_scale):
        score = 0
        score += self.nama_laptop * dev_scale['nama_laptop']
        score += self.baterai * dev_scale['baterai']
        score += self.layar * dev_scale['layar']
        score += self.ram * dev_scale['ram']
        score += self.processor * dev_scale['processor']
        score -= self.harga * dev_scale['harga']
        return score

    def __repr__(self):
        return f"Laptop(id={self.id!r}, nama_laptop={self.nama_laptop!r}, baterai={self.baterai!r}, layar={self.layar!r}, ram={self.ram!r}, processor={self.processor!r}, harga={self.harga!r})"
