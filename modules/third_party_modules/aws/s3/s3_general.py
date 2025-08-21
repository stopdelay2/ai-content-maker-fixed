import boto3

from modules.third_party_modules.midjourney.imagine_api_dev import *
# Create an S3 client
s3_client = boto3.client('s3')


def upload_image_bytesio(image_in_memory, bucket_name, object_key):
    try:

        image_in_memory.seek(0)  # reset the pointer

        s3_client.upload_fileobj(
            image_in_memory,
            bucket_name,
            object_key,
            ExtraArgs={
                "ContentType": "image/jpeg",
                "ACL": "public-read"
            }
        )
        print(f"Upload successful!\n"
              f"for object key - {object_key}\n"
              f"bucket name - {bucket_name}\n")
    except Exception as e:
        print(f"Something went wrong: {e}")


def tests():
    prompt = 'create a picture of a flight delay'
    image_in_memory = generate_image_from_prompt(prompt)

    bucket_name = 'stopdelay'
    path = 'media/blogs/'
    picture_name = 'eli_test_picture_2'
    object_key_test = f'{path}{picture_name}.jpeg'

    upload_image_bytesio(
        image_in_memory,
        bucket_name,
        object_key_test)

    ########################################
    # upload picture to aws s3 bucket of stopdelay, and return it's URL
    ########################################

    picture_name = picture_name.replace('-', '_')

    object_key = f'{picture_name}.jpeg'

    picture_url = s3_bucket_domain + s3_bucket_path + object_key
    print(f'The picture URL that have been constructed - \n'
          f'{picture_url}')


#tests()
