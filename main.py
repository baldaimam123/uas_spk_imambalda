from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api
from models import Laptop as LaptopModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session

session = Session(engine)

app = Flask(__name__)
api = Api(app)


class BaseMethod:
    def __init__(self):
        # 1-5
        self.raw_weight = {
            'baterai': 4, 'memori_internal': 3,
            'layar': 3, 'ram': 4, 'processor': 5, 'harga': 5
        }

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v / total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(
            LaptopModel.id, LaptopModel.nama_laptop, LaptopModel.memori_internal, LaptopModel.baterai,
            LaptopModel.layar, LaptopModel.ram, LaptopModel.processor, LaptopModel.harga
        )
        result = session.execute(query).fetchall()
        return [
            {
                'id': laptop.id,
                'nama_laptop': laptop.nama_laptop,
                'memori_internal': laptop.memori_internal,
                'baterai': laptop.baterai,
                'layar': laptop.layar,
                'ram': laptop.ram,
                'processor': laptop.processor,
                'harga': laptop.harga
            } for laptop in result
        ]

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
            baterai_spec = str(data['baterai'])
            baterai_numeric_values = [int(value.split()[0]) for value in baterai_spec.split() if value.split()[0].isdigit()]
            max_baterai_value = max(baterai_numeric_values) if baterai_numeric_values else 1
            baterai_values.append(max_baterai_value)

            # Layar
            layar_spec = str(data['layar'])
            layar_numeric_values = [float(value.split()[0]) for value in layar_spec.split() if value.replace('.', '').isdigit()]
            max_layar_value = max(layar_numeric_values) if layar_numeric_values else 1
            layar_values.append(max_layar_value)

            # RAM
            ram_spec = str(data['ram'])
            ram_numeric_values = [int(value) for value in ram_spec.split() if value.isdigit()]
            max_ram_value = max(ram_numeric_values) if ram_numeric_values else 1
            ram_values.append(max_ram_value)

            # Processor
            processor_spec = str(data['processor'])
            processor_numeric_values = [int(value.split()[0]) for value in processor_spec.split() if value.split()[0].isdigit()]
            max_processor_value = max(processor_numeric_values) if processor_numeric_values else 1
            processor_values.append(max_processor_value)

            # Harga
            harga_cleaned = ''.join(char for char in str(data.get('harga', '')) if char.isdigit())
            harga_values.append(float(harga_cleaned) if harga_cleaned else 0)  # Convert to float

        return [
            {
                'id': data['id'],
                'nama_laptop': data['nama_laptop'],
                'memori_internal': memori_internal_value / max(memori_internal_values),
                'baterai': max_baterai_value / max(baterai_values),
                'layar': max_layar_value / max(layar_values),
                'ram': max_ram_value / max(ram_values),
                'processor': max_processor_value / max(processor_values),
                'harga': min(harga_values) / max(harga_values) if max(harga_values) != 0 else 0
            }
            for data, memori_internal_value, max_baterai_value, max_layar_value, max_ram_value, max_processor_value, harga_value
            in zip(self.data, memori_internal_values, baterai_values, layar_values, ram_values, processor_values, harga_values)
        ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights


class WeightedProduct(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = [
            {
                'id': row['id'],
                'nama_laptop': row['nama_laptop'],
                'produk': row['memori_internal'] ** self.weight['memori_internal'] *
                          row['baterai'] ** self.weight['baterai'] *
                          row['layar'] ** self.weight['layar'] *
                          row['ram'] ** self.weight['ram'] *
                          row['processor'] ** self.weight['processor'] *
                          row['harga'] ** self.weight['harga']
            }
            for row in normalized_data
        ]
        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)
        sorted_data = [
            {
                'ID': product['id'],
                'nama_laptop': product['nama_laptop'],
                'score': round(product['produk'], 3)
            }
            for product in sorted_produk
        ]
        return sorted_data


class WeightedProductResource(Resource):
    def get(self):
        calculator = WeightedProduct()
        result = calculator.calculate
        return sorted(result, key=lambda x: x['score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProduct()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'acer': sorted(result, key=lambda x: x['score'], reverse=True)}, HTTPStatus.OK.value


class SimpleAdditiveWeighting(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = [
            {
                'ID': row['id'],
                'nama_laptop': row.get('nama_laptop'),
                'Score': round(row['memori_internal'] * weight['memori_internal'] +
                                row['baterai'] * weight['baterai'] +
                                row['layar'] * weight['layar'] +
                                row['ram'] * weight['ram'] +
                                row['processor'] * weight['processor'] +
                                row['harga'] * weight['harga'], 3)
            }
            for row in self.normalized_data
        ]        
        sorted_result = sorted(result, key=lambda x: x['Score'], reverse=True)
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class SimpleAdditiveWeightingResource(Resource):
    def get(self):
        calculator = SimpleAdditiveWeighting()
        result = calculator.calculate
        return sorted(result, key=lambda x: x['Score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        calculator = SimpleAdditiveWeighting()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'Acer': sorted(result, key=lambda x: x['Score'], reverse=True)}, HTTPStatus.OK.value



class LaptopResource(Resource):
    def get_paginated_result(self, url, lst, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(lst) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(lst))

        if page < page_count:
            next_page = f'{url}?page={page + 1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page - 1}&page_size={page_size}'
        else:
            prev_page = None

        if page > page_count or page < 1:
            abort(404, description='Data Tidak Ditemukan.')

        return {
            'page': page,
            'page_size': page_size,
            'next': next_page,
            'prev': prev_page,
            'Results': lst[start:end]
        }

    def get(self):
        query = session.query(LaptopModel).order_by(LaptopModel.id)
        result_set = query.all()
        data = [
            {
                'id': row.id, 'nama_laptop': row.nama_laptop, 'memori_internal': row.memori_internal,
                'baterai': row.baterai, 'layar': row.layar, 'ram': row.ram, 'processor': row.processor, 'harga': row.harga
            } for row in result_set
        ]
        return self.get_paginated_result('acer/', data, request.args), 200


api.add_resource(LaptopResource, '/acer')
api.add_resource(WeightedProductResource, '/wp')
api.add_resource(SimpleAdditiveWeightingResource, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)
