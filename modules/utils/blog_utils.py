from bs4 import BeautifulSoup
import json
import time

from modules.third_party_modules.neuron_writer.neuron_general import article_reduced_terms


def html_to_editorjs(
        html_content: str,
        image_url: str,
        caption_text: str
) -> str:
    """
    Convert basic HTML (with h1, h2, p, ul/li, ol/li) into Editor.js JSON format.
    Returns a double-serialized JSON string (a JSON string of a JSON string)
    after escaping single quotes in the text.
    """

    # First extract the body content with the helper
    content = extract_body_content(html_content)

    soup = BeautifulSoup(content, "html.parser")

    # Prepare the basic structure
    editorjs_data = {
        "time": int(time.time() * 1000),  # current timestamp in ms
        "blocks": [],
        "version": "2.18.0"
    }

    # A flag to ensure we insert the image/caption only once,
    # right after the first <h1> found.
    image_inserted = False

    # Go through top-level elements
    for element in soup.contents:
        # Skip text nodes/newlines
        if not hasattr(element, "name") or element.name is None:
            continue

        tag_name = element.name.lower()

        if tag_name == "h1":
            # Header block (level 1)
            header_text = element.get_text(strip=True)
            # Escape single quotes
            #header_text = header_text.replace("'", "\\'")

            editorjs_data["blocks"].append({
                "type": "Header",
                "data": {
                    "text": header_text,
                    "level": 1
                }
            })

            # Right after the first <h1>, insert the image block if not already done
            if not image_inserted:
                editorjs_data["blocks"].append({
                    "type": "Image",
                    "data": {
                        "file": {"url": image_url},
                        "caption": caption_text,
                        "withBorder": False,
                        "stretched": False,
                        "withBackground": False
                    }
                })
                image_inserted = True

        elif tag_name == "h2":
            # Header block (level 2)
            header_text = element.get_text(strip=True)
            # Escape single quotes
            #header_text = header_text.replace("'", "\\'")

            editorjs_data["blocks"].append({
                "type": "Header",
                "data": {
                    "text": header_text,
                    "level": 2
                }
            })

        elif tag_name == "p":
            # Paragraph block
            # decode_contents() preserves inline HTML (like <a>, <strong>), if any
            paragraph_text = element.decode_contents()
            # Escape single quotes
            #paragraph_text = paragraph_text.replace("'", "\\'")

            editorjs_data["blocks"].append({
                "type": "paragraph",
                "data": {
                    "text": paragraph_text
                }
            })

        elif tag_name in ["ul", "ol"]:
            # List block
            list_style = "unordered" if tag_name == "ul" else "ordered"
            items = []
            for li in element.find_all("li", recursive=False):
                #li_text = li.decode_contents().replace("'", "\\'")
                li_text = li.decode_contents()
                items.append(li_text)

            editorjs_data["blocks"].append({
                "type": "List",
                "data": {
                    "style": list_style,
                    "items": items
                }
            })

        # Extend as needed for images, blockquotes, etc.
        # elif tag_name == "img":
        #     src = element.get("src", "")
        #     alt_text = element.get("alt", "")
        #     # if you want to escape single quotes in alt_text, do it here
        #     editorjs_data["blocks"].append({
        #         "type": "image",
        #         "data": {
        #             "file": {"url": src},
        #             "caption": alt_text,
        #             "withBorder": False,
        #             "stretched": False,
        #             "withBackground": False
        #         }
        #     })

    # debug
    #print(editorjs_data)
    # First, produce normal JSON from the dictionary
    json_output = json.dumps(editorjs_data, ensure_ascii=False)

    #json_output = json_output.replace("\"", "\\\"")

    print(f'\nHTML content formatted in editor.js format output:\n'
          f'{json_output}')

    # Return the double-escaped string (or print if needed)
    return json_output


def extract_body_content(html: str) -> str:
    """
    Extracts and returns only the contents that appear inside <body> (if a <body> is present).
    If there is no <body> tag, it returns the entire HTML as-is (minus the <html> or <head> tags, if present).
    """
    soup = BeautifulSoup(html, "html.parser")
    body = soup.find("body")
    if body:
        # Return just what's inside <body>...</body>
        return body.decode_contents()
    else:
        # No <body>, so just return everything
        # But skipping <html> or <head> wrappers if they exist
        # can be done by returning soup.decode_contents() at the top level
        return soup.decode_contents()


test_html = """
    <html>
<head>
<title>Welcome to London Luton Airport Arrivals: Your Guide to Flight Information</title>
</head>
<body>
<h1>London Luton Airport Arrivals: Log and Search for a Flight at LTN</h1>
<p>Arriving at Luton Airport is a breeze when you're equipped with the right knowledge. Whether you're meeting someone or planning your own trip, this guide will assist you in navigating the airport with ease. We're here to help you discover how to view live flight information, find essential services, and make the most of your time at the airport.</p>
<h2>What Is LTN and Where Is London Luton Airport Located?</h2>
<p>LTN is the IATA code and <strong>EGGW</strong> is the ICAO code for <strong>London Luton Airport (LLA)</strong>, one of the busiest airports in the <strong>UK</strong>. Situated in Bedfordshire, it's conveniently located close to London, making it a popular choice for travelers arriving in the <strong>United Kingdom</strong>. The airport serves numerous airlines and offers a variety of <strong>route</strong> options to destinations across Europe and beyond.</p>
<h2>Flight Arrival Information at LTN: How to Check London Luton Airport Arrivals</h2>
<p>To get the latest status, view live data on the airport's <strong>official</strong> website or applications like <strong>Skyscanner</strong>. These platforms provide real-time status, allowing you to plan your journey accordingly. Search using the flight number or airline to get specific details.</p>
<h2>What Arrival Information Is Available at London Luton Airport?</h2>
<p>Upon reaching the airport, you will find essential details displayed on screens throughout the terminal. These screens provide information on flight times, baggage claim areas, and any changes. Airport staff are available to assist and provide directions.</p>
<h2>Arrive at LTN: How to Reach London Luton Airport Arrivals</h2>
<p>There are several ways to reach the airport. The most convenient route is by train to <strong>Luton Airport Parkway</strong>, followed by a short five-<strong>minute</strong> ride on the <strong>shuttle bus</strong>, which is <strong>free</strong> for ticket holders. Alternatively, take a <strong>bus</strong> from various locations in London or drive to the airport. For those who prefer to hire a car, the <strong>car hire centre</strong> is conveniently located in front of the terminal building.</p>
<h2>Can I Use Live Flight Trackers for LTN Arrivals?</h2>
<p>Yes, live trackers are available to stay informed about arrivals at the airport. Websites and apps like <strong>Skyscanner</strong> offer <strong>free</strong> services to provide real-time tracking. This is especially helpful if you're picking someone up and want to know the exact time they will land.</p>
<h2>What Facilities Are Available Upon Arrival at LTN?</h2>
<p>When you reach the airport, passengers have access to a range of facilities. There are numerous shops and restaurants to <strong>explore</strong>, as well as lounges for those who desire a more comfortable waiting area. To continue your journey, options for <strong>car hire</strong>, taxis, and public transport are readily available.</p>
<h2>How Do I Find Specific Arrival Information at Luton Airport?</h2>
<p>If you require specific details about incoming flights, visit the desks located within the terminal. Staff provide details on flight times, baggage claims, and directions to various services within the airport. Assistance is available upon request.</p>
<h2>What Is the Best Way to Check Flight Routes and Schedules?</h2>
<p>To find the best <strong>route</strong> and <strong>schedule</strong>, visit the airport's <strong>official</strong> website or contact your airline directly. Online travel agencies or apps also allow comparison of different options. Planning ahead ensures a smooth journey.</p>
<h2>Are There Services for Special Needs Passengers at LTN?</h2>
<p>The airport is committed to providing services for all passengers. If you have special requirements, please contact the airport in advance. The staff are trained to assist and provide necessary accommodations to make your journey as comfortable as possible.</p>
<h2>How Can I Stay Updated on Current Weather Conditions?</h2>
<p>Being aware of the <strong>current weather conditions</strong> is crucial for planning. Weather updates are available on the airport's <strong>official</strong> website or through weather apps. Staying informed ensures you're prepared for any delays or schedule changes.</p>
<h2>What Should I Do If I Need Assistance Upon Arrival?</h2>
<p>If you require assistance upon reaching the airport, staff are available to assist. For directions, lost luggage, or medical assistance, the team is ready to support you. Services are designed to address a variety of needs promptly and efficiently.</p>
<h2>Summary of Key Points</h2>
<ul>
<li>Visit the airport's <strong>official</strong> website or apps like <strong>Skyscanner</strong> for real-time flight updates.</li>
<li>Reach the airport via train to <strong>Luton Airport Parkway</strong> with a <strong>free shuttle bus</strong> to the terminal.</li>
<li>Find flight details on terminal displays or ask airport staff for assistance.</li>
<li>Explore available facilities such as shops, restaurants, and the <strong>car hire centre</strong>.</li>
<li>Stay informed about <strong>current weather conditions</strong> and any potential changes.</li>
</ul>
</body>
</html>
    """


def tests():

    image_url = "https://stopdelay.s3.amazonaws.com/media/blogs/eli_test_picture_1.jpeg"
    caption = 'test caption'

    result = html_to_editorjs(
        test_html,
        image_url,
        caption
    )
    print(result)


#tests()
