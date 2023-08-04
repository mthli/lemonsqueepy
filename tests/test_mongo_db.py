from datetime import datetime

from mongo.db import convert_id_to_str_in_json, \
    convert_fields_to_datetime_in_json


def test_convert_id_to_str_in_json():
    data = {
        'id': 1,
        'l': [{
            'd': {
                '_id': 1,
                'uid': 2,
                'user_id': '...',
            },
        }],
    }

    convert_id_to_str_in_json(data)

    assert data['id'] == '1'
    assert data['l'][0]['d']['_id'] == '1'
    assert isinstance(data['l'][0]['d']['uid'], int)
    assert isinstance(data['l'][0]['d']['user_id'], str)


def test_convert_fields_to_datetime_in_json():
    data = {
        'l': [{
            'd': {
                't': '2023-01-17T12:26:23.000000Z',
                's': '...',
            },
        }],
    }

    convert_fields_to_datetime_in_json(data)

    assert isinstance(data['l'][0]['d']['t'], datetime)
    assert isinstance(data['l'][0]['d']['s'], str)
