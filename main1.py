import sys
from colorama import Fore, Style
from models import Base, Laptop
from engine import engine
from tabulate import tabulate

from sqlalchemy import select
from sqlalchemy.orm import Session
from settings import DEV_SCALE

session = Session(engine)


def create_table():
    Base.metadata.create_all(engine)
    print(f'{Fore.GREEN}[Success]: {Style.RESET_ALL}Database has created!')


def review_data():
    query = select(Laptop)
    for laptop in session.scalars(query):
        print(laptop)


class BaseMethod():

    def __init__(self):
        # 1-5
        self.raw_weight = {'baterai': 4, 'memori_internal':3,
                           'layar': 3, 'ram': 4, 'processor': 5, 'harga': 5}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(Laptop.id, Laptop.nama_laptop, Laptop.memori_internal, Laptop.baterai, Laptop.layar,
                       Laptop.ram, Laptop.processor, Laptop.harga)
        result = session.execute(query).fetchall()
        return [{'id': laptop.id, 'nama_laptop': laptop.nama_laptop, 'memori_internal': laptop.memori_internal, 'baterai': laptop.baterai,
                'layar': laptop.layar, 'ram': laptop.ram, 'processor': laptop.processor, 'harga': laptop.harga} for laptop in result]

    @property
    def normalized_data(self):
        # x/max [benefit]
        # min/x [cost]
        memori_internal_values = []  # max
        baterai_values = []  # max
        layar_values = []  # max
        ram_values = []  # max
        processor_values = []  # max
        harga_values = []  # min

        for data in self.data:
            # Memori Internal
            memori_internal_spec = str(data['memori_internal'])  # Konversi ke string
            memori_internal_numeric_values = [int(value) for value in memori_internal_spec.split() if value.isdigit()]
            memori_internal_value = max(memori_internal_numeric_values) if memori_internal_numeric_values else 1
            memori_internal_values.append(memori_internal_value)

            # Baterai
            baterai_spec =  str(data['baterai'])
            baterai_numeric_values = [int(value.split()[0]) for value in baterai_spec.split() if value.split()[0].isdigit()]
            max_baterai_value = max(baterai_numeric_values) if baterai_numeric_values else 1
            baterai_values.append(max_baterai_value)

            # Layar
            layar_spec =  str(data['layar'])
            layar_numeric_values = [float(value.split()[0]) for value in layar_spec.split() if value.replace('.', '').isdigit()]
            max_layar_value = max(layar_numeric_values) if layar_numeric_values else 1
            layar_values.append(max_layar_value)

            # RAM
            ram_spec =  str(data['ram'])
            ram_numeric_values = [int(value) for value in ram_spec.split() if value.isdigit()]
            max_ram_value = max(ram_numeric_values) if ram_numeric_values else 1
            ram_values.append(max_ram_value)

            # Processor
            processor_value = DEV_SCALE.get('processor', {}).get(data.get('processor'), 1)
            processor_values.append(processor_value)

            # Harga
            harga_cleaned = ''.join(char for char in str(data.get('harga', '')) if char.isdigit())
            harga_values.append(float(harga_cleaned) if harga_cleaned else 0)  # Convert to float

        return [
            {
                'id': data['id'],
                'memori_internal': memori_internal_value / max(memori_internal_values),
                'baterai': max_baterai_value / max(baterai_values),
                'layar': max_layar_value / max(layar_values),
                'ram': max_ram_value / max(ram_values),
                'processor': processor_value / max(processor_values),
                'harga': min(harga_values) / max(harga_values) if max(harga_values) != 0 else 0
            }
            for data, memori_internal_value, max_baterai_value, max_layar_value, max_ram_value, processor_value, harga_value
            in zip(self.data, memori_internal_values, baterai_values, layar_values, ram_values, processor_values, harga_values)
        ]



class WeightedProduct(BaseMethod):
    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = [
            {
                'id': row['id'],
                'produk': row['memori_internal']**self.weight['memori_internal'] *
                row['baterai']**self.weight['baterai'] *
                row['layar']**self.weight['layar'] *
                row['ram']**self.weight['ram'] *
                row['processor']**self.weight['processor'] *
                row['harga']**self.weight['harga']
            }
            for row in normalized_data
        ]
        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)
        sorted_data = [
            {
                'id': product['id'],
                'memori_internal': product['produk'] / self.weight['memori_internal'],
                'baterai': product['produk'] / self.weight['baterai'],
                'layar': product['produk'] / self.weight['layar'],
                'ram': product['produk'] / self.weight['ram'],
                'processor': product['produk'] / self.weight['processor'],
                'harga': product['produk'] / self.weight['harga'],
                'score': product['produk']  # Nilai skor akhir
            }
            for product in sorted_produk
        ]
        return sorted_data


class SimpleAdditiveWeighting(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = {row['id']:
                  round(row['memori_internal'] * weight['memori_internal'] +
                        row['baterai'] * weight['baterai'] +
                        row['layar'] * weight['layar'] +
                        row['ram'] * weight['ram'] +
                        row['processor'] * weight['processor'] +
                        row['harga'] * weight['harga'], 2)
                  for row in self.normalized_data
                  }
        
        sorted_result = dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
        return sorted_result


def run_saw():
    saw = SimpleAdditiveWeighting()
    result = saw.calculate
    print(tabulate(result.items(), headers=['Id', 'Score'], tablefmt='pretty'))


def run_wp():
    wp = WeightedProduct()
    result = wp.calculate
    headers = result[0].keys()
    rows = [
        {k: round(v, 4) if isinstance(v, float) else v for k, v in val.items()}
        for val in result
    ]
    print(tabulate(rows, headers="keys", tablefmt="grid"))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == 'create_table':
            create_table()
        elif arg == 'saw':
            run_saw()
        elif arg == 'wp':
            run_wp()
        else:
            print('command not found')
