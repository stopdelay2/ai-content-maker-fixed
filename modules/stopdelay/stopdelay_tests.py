import base64


def image_convert_base64(picture_path):
    # Read the image file as binary and encode it to base64 for JSON transmission
    with open(picture_path, 'rb') as img_file:
        image_data = base64.b64encode(img_file.read()).decode('utf-8')
        print(image_data)


def image_convert_raw_bytes(file_path):

    with open(file_path, "rb") as f:
        # Read the entire file as bytes
        file_bytes = f.read()
        print(file_bytes)


def tests():
    picture_path = f'C:/Users/User/PycharmProjects/1k-content-articles-maker/modules/stopdelay/test_pictures/test_picture_1.png'

    #image_convert_base64(picture_path)

    image_convert_raw_bytes(picture_path)


#tests()
