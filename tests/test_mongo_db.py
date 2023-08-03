from datetime import datetime

from mongo.db import convert_fields_to_datetime_in_json


def test_convert_fields_to_datetime_in_json():
    data = {
        'l': [{
            'o': {
                'd': '2023-01-17T12:26:23.000000Z',
                's': '...',
            },
        }],
    }

    convert_fields_to_datetime_in_json(data)

    assert isinstance(data['l'][0]['o']['d'], datetime)
    assert isinstance(data['l'][0]['o']['s'], str)
