import requests
import time
import json
from typing import Optional, Dict, Any
from datetime import datetime
import os
from PIL import Image
import io


class MidjourneyAPI:
    def __init__(self, api_key: str):
        """
        Initialize the Midjourney API client.

        The api_key is your Midjourney API token that you receive after subscribing
        to their API service. This is different from a Discord token.

        Args:
            api_key (str): Your Midjourney API authentication token
        """
        self.api_key = api_key
        self.base_url = "https://api.midjourney.com/v1"  # Example URL
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def generate_blog_image(
            self,
            prompt: str,
            max_wait_time: int = 300,
            image_quality: str = "HD"
    ) -> Dict[Any, Any]:
        """
        Generates a blog image using Midjourney's latest model with the provided prompt.

        This function sends the initial request and then polls for results until
        the image is ready. It automatically selects the highest-rated variation
        based on Midjourney's internal scoring.

        Args:
            prompt (str): The image generation prompt
            max_wait_time (int): Maximum time to wait for image generation in seconds
            image_quality (str): Quality setting for the image ("HD" or "STANDARD")

        Returns:
            Dict containing:
                - 'image_url': URL to download the final image
                - 'prompt': The original prompt used
                - 'generation_time': Time taken to generate
                - 'model_version': Version of Midjourney model used

        Raises:
            TimeoutError: If image generation exceeds max_wait_time
            RequestError: If there's an API communication error
        """
        # Prepare the generation request
        payload = {
            "prompt": prompt,
            "model": "midjourney-v6",  # Using latest model
            "quality": image_quality,
            "aspect_ratio": "1:1",  # Square format good for blog posts
            "num_variations": 4,  # Generate 4 to pick the best one
        }

        try:
            # Submit the initial generation request
            response = requests.post(
                f"{self.base_url}/generations",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()

            # Get the generation job ID
            job_id = response.json()['job_id']

            # Poll for results
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                status_response = requests.get(
                    f"{self.base_url}/generations/{job_id}",
                    headers=self.headers
                )
                status_response.raise_for_status()

                generation_status = status_response.json()

                if generation_status['status'] == 'completed':
                    # Find the highest-rated variation
                    variations = generation_status['variations']
                    best_variation = max(
                        variations,
                        key=lambda x: x.get('rating', 0)
                    )

                    return {
                        'image_url': best_variation['image_url'],
                        'prompt': prompt,
                        'generation_time': time.time() - start_time,
                        'model_version': generation_status['model_version']
                    }

                elif generation_status['status'] == 'failed':
                    raise Exception(f"Generation failed: {generation_status.get('error')}")

                time.sleep(5)  # Wait 5 seconds before polling again

            raise TimeoutError("Image generation exceeded maximum wait time")

        except requests.exceptions.RequestException as e:
            raise Exception(f"API communication error: {str(e)}")

    def download_image(self, image_url: str, save_path: str) -> str:
        """
        Downloads and saves the generated image.

        Args:
            image_url (str): URL of the generated image
            save_path (str): Path where the image should be saved

        Returns:
            str: Path to the saved image
        """
        try:
            response = requests.get(image_url)
            response.raise_for_status()

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # Save the image
            with open(save_path, 'wb') as f:
                f.write(response.content)

            return save_path

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to download image: {str(e)}")


# Example usage of the class
def generate_blog_image_with_retry(prompt: str, max_retries: int = 3) -> str:
    """
    Generates a blog image with retry logic for reliability.

    Args:
        prompt (str): The image generation prompt
        max_retries (int): Maximum number of retry attempts

    Returns:
        str: Path to the downloaded image
    """
    api = MidjourneyAPI(api_key="your_api_key_here")

    for attempt in range(max_retries):
        try:
            # Generate the image
            generation_result = api.generate_blog_image(
                prompt=prompt,
                image_quality="HD"
            )

            # Create a timestamp for unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Download the image
            save_path = f"blog_images/{timestamp}_blog_image.jpg"
            final_path = api.download_image(
                generation_result['image_url'],
                save_path
            )

            print(f"Successfully generated image for prompt: {prompt}")
            print(f"Generation time: {generation_result['generation_time']:.2f} seconds")
            print(f"Model version: {generation_result['model_version']}")

            return final_path

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                raise Exception("Max retries exceeded for image generation")
            time.sleep(10)  # Wait before retrying


# Example of how to use the function
if __name__ == "__main__":
    try:
        blog_prompt = """
        A cozy modern cafe interior with warm lighting, 
        people working on laptops, and coffee cups on wooden tables. 
        Professional photography style, soft depth of field
        """

        image_path = generate_blog_image_with_retry(blog_prompt)
        print(f"Image saved to: {image_path}")

    except Exception as e:
        print(f"Failed to generate image: {str(e)}")