import pytest
import os
import json
import base64
from datetime import datetime
from app import gen_file_name, allowed_file

FILE_NAMES = [
    'photo.jpg',
    'photo_1.jpg',
]


def test_get_images_info(test_client, images_dir):
    response = test_client.get('/image')
    assert response.status_code == 200
    files = response.json['files']
    assert len(files) == len(FILE_NAMES)

    for file in files:
        file_name = file['file_name']
        file_path = os.path.join(images_dir, file_name)
        assert file['size'] == os.path.getsize(file_path)
        last_mod_time = os.path.getmtime(file_path)
        time = datetime.fromtimestamp(last_mod_time).strftime('%Y-%m-%d %H:%M:%S')
        assert file['last_modification_time'] == time


@pytest.mark.parametrize('file', FILE_NAMES)
def test_get_jpg_file(test_client, images_dir, file):
    response = test_client.get(f'/images/{file}')
    assert response.status_code == 200

    with open(os.path.join(images_dir, file), 'rb') as img_file:
        img_data = img_file.read()
        assert img_data == response.data


def test_gen_file_name(images_dir):
    name = gen_file_name(images_dir, 'photo.jpg')
    assert name == 'photo_2.jpg'


def test_allowed_file():
    assert allowed_file('photo.jpg')
    assert allowed_file('photo.JPG')
    assert allowed_file('photo.Jpg')

    assert not allowed_file('photo')
    assert not allowed_file('photo.doc')
    assert not allowed_file('photo.')


def test_post_get_delete(test_client, images_dir):
    file_name = 'photo_1.jpg'
    future_img_name = gen_file_name(images_dir, file_name)

    with open(os.path.join(images_dir, file_name), 'rb') as img_file:
        img_data = img_file.read()
    img_data_base64 = base64.b64encode(img_data)
    data = {'filename': file_name, 'data': img_data_base64}

    post_resp = test_client.post('/image', data=data)
    posted_img = post_resp.json['file_name']
    assert post_resp.status_code == 200
    assert posted_img == future_img_name

    imgs_info = test_client.get('/image')
    assert len(imgs_info.json['files']) == len(FILE_NAMES) + 1

    get_resp = test_client.get(f'/images/{posted_img}')
    assert get_resp.status_code == 200
    assert get_resp.data == img_data

    payload = {'file': posted_img}
    delete_resp = test_client.delete('/image', json=payload)
    assert delete_resp.status_code == 200
    assert delete_resp.json[posted_img] == 'True'


def test_image_not_found_error(test_client):
    response = test_client.get('/images/foo')
    assert response.status_code == 500
    assert response.json['description'] == "Image file not found"


def test_error_post_response(test_client):
    response = test_client.post('/image')
    assert response.status_code == 400
    assert response.json['description'] == "Missing file in data payload"


def test_error_post_response2(test_client):
    data = {'filename': 'foo', 'data': '111'}
    response = test_client.post('/image', data=data)
    assert response.status_code == 400
    assert response.json['description'] == "File type not allowed"


def test_error_post_response3(test_client):
    data = {'filename': 'foo.jpg', 'data': '111'}
    response = test_client.post('/image', data=data)
    assert response.status_code == 400
    assert "invalid data in base64" in response.json['description']


def test_error_delete_response(test_client):
    payload = {'foo': 'bar'}
    delete_resp = test_client.delete('/image', json=payload)
    assert delete_resp.status_code == 400
    assert delete_resp.json['description'] == "Missing required key 'file'"


def test_error_delete_response2(test_client):
    payload = {'file': 'foo'}
    delete_resp = test_client.delete('/image', json=payload)
    assert delete_resp.status_code == 500
    assert "No such file or directory: 'images/foo'" in delete_resp.json['description']
