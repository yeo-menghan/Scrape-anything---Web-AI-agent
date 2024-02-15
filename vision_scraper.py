from openai import OpenAI
import subprocess
import base64
import os
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
model = OpenAI(api_key=openai_api_key)
model.timeout = 30

def image_b64(image):
    with open(image, "rb") as f:
        return base64.b64encode(f.read()).decode()

def url2screenshot(url):
    print(f"Crawling {url}")

    if os.path.exists("screenshot.jpg"):
        os.remove("screenshot.jpg")

    result = subprocess.run(
        ["node", "screenshot.js", url],
        capture_output=True,
        text=True
    )

    exitcode = result.returncode
    output = result.stdout

    if not os.path.exists("screenshot.jpg"):
        print("ERROR")
        return "Failed to scrape the website"

    b64_image = image_b64("screenshot.jpg")
    return b64_image

def visionExtract(b64_image, prompt):
    response = model.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "system",
                "content": "You are a web scraper, your job is to extract information based on a screenshot of a website & user's instruction",
            }
        ] + [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{b64_image}",
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ]
            }
        ],
        max_tokens=1024,
    )

    message = response.choices[0].message
    message_text = message.content
    # Access the `usage` attribute correctly
    if hasattr(response, 'usage'):
        total_tokens = response.usage.total_tokens
    else:
        total_tokens = 'Unknown'

    if "ANSWER_NOT_FOUND" in message_text:
        print("ERROR: Answer not found")
        return {
            "message": "I was unable to find the answer on that website. Please pick another one",
            "total_tokens": total_tokens
        }
    else:
        print(f"GPT: {message_text}")
        return {
            "message": message_text,
            "total_tokens": total_tokens
        }


def visionCrawl(url, prompt):
    b64_image = url2screenshot(url)

    print("Image captured")

    if b64_image == "Failed to scrape the website":
        return "I was unable to crawl that site. Please pick a different one."
    else:
        extraction_result = visionExtract(b64_image, prompt)
        # Adjust the return value to include token usage information
        return f"Response: {extraction_result['message']}\nTotal Tokens: {extraction_result.get('total_tokens', 'Unknown')}"

response = visionCrawl("https://openai.com/pricing", "Tell me what is the price of gpt3.5-turbo based on this screenshot")
print(response)
