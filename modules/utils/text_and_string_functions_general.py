import re

from modules.third_party_modules.neuron_writer.neuron_general import \
    neuron_get_query,\
    query_id,\
    article,\
    article_terms_not_used_added, \
    article_reduced_terms, \
    article_reduced_terms_2


def get_terms_not_used(article, query_result):
    basic_terms_array = query_result['terms']['content_basic']
    extended_terms_array = query_result['terms']['content_extended']

    basic_and_extended_terms = basic_terms_array + extended_terms_array

    terms_not_used = []

    # Convert the article to lowercase once for more efficient repeated checks
    article_lower = article.lower()

    for term_obj in basic_and_extended_terms:
        term_lower = term_obj['t'].lower()

        # Create a regex pattern that checks for the term as a whole word only
        # using \b (word boundary) and re.escape() to handle special regex characters
        pattern = r"\b" + re.escape(term_lower) + r"\b"

        if not re.search(pattern, article_lower):
            terms_not_used.append(term_obj['t'])

    return terms_not_used


def get_terms_used_excessively(article, query_result):
    """
    Returns a list of objects describing terms that are used excessively in the article.

    Each object contains:
        - term (str): the actual term
        - suggested_usage (list[int, int]): the lower and higher suggested usage
        - current_usage (int): how many times the term currently appears in the article

    Based on the suggested usage (sugg_usage) criteria:

    - If 'sugg_usage' has two numbers [lo, hi]:
        Mark term as 'use_less' if actual_usage >= 5*lo AND actual_usage >= 2.5*hi.
    - If 'sugg_usage' has only one number (or both the same):
        Mark term as 'use_less' if actual_usage >= 5 * that number.

    Note: We're using a leading word boundary (\b) so suffixes like "claims" match "claim".
    """

    # Extract terms
    basic_terms_array = query_result['terms']['content_basic']
    extended_terms_array = query_result['terms']['content_extended']
    basic_and_extended_terms = basic_terms_array + extended_terms_array

    # Convert article to lowercase for case-insensitive matching
    article_lower = article.lower()

    # List of terms to return (those that exceed usage thresholds)
    use_less_objects = []

    # Check each term
    for term_obj in basic_and_extended_terms:
        term_lower = term_obj['t'].lower()

        # Build regex pattern: leading word boundary only
        # This ensures any suffix (e.g., "s" in "claims") is still matched
        pattern = r"\b" + re.escape(term_lower)

        # Count how many times this term actually appears in the article
        actual_usage = len(re.findall(pattern, article_lower))

        # Retrieve the suggested usage array
        sugg_usage = term_obj.get('sugg_usage', [])

        # We'll define lo and hi so that we always have 2 values (lo <= hi)
        if len(sugg_usage) >= 2:
            # Identify the lower and higher suggested usage
            lo = min(sugg_usage)
            hi = max(sugg_usage)

            # Check if actual usage is 5x the lower AND 2.5x the higher
            if (actual_usage >= 5 * lo) and (actual_usage >= 2.5 * hi):
                use_less_objects.append({
                    'term': term_obj['t'],
                    'suggested_usage': [lo, hi],
                    'current_usage': actual_usage
                })

        elif len(sugg_usage) == 1:
            # If there's only one value (or if both values are the same),
            # treat it like a single range
            val = sugg_usage[0]
            if actual_usage >= 5 * val:
                use_less_objects.append({
                    'term': term_obj['t'],
                    'suggested_usage': [val, val],
                    'current_usage': actual_usage
                })

        # If sugg_usage is empty, there's no guidance—skip or handle differently.

    return use_less_objects

def format_use_less_objects(use_less_objects):
    """
    Transforms an array of objects into a string, each line describing:
        term: should be used Xx (currently used Y times)
      or
        term: should be used X-Yx (currently used Z times)
    depending on whether suggested_usage has the same min/max or not.
    """

    lines = []
    for obj in use_less_objects:
        term = obj['term']
        lo, hi = obj['suggested_usage']
        current_usage = obj['current_usage']

        # Decide how to display the suggested usage
        if lo == hi:
            usage_str = f"{lo}x"  # e.g., "1x times"
        else:
            usage_str = f"{lo}-{hi}x"  # e.g., "1-3x times"

        line = f"{term}: should be used {usage_str} times (currently used {current_usage} times)"
        lines.append(line)

    # Join all lines with a newline character
    return "\n".join(lines)


def format_terms_with_usage(terms_objects):
    """
    Transforms an array of objects into a string.
    """

    lines = []
    for obj in terms_objects:
        term = obj['t']
        lo, hi = obj['sugg_usage']

        # Decide how to display the suggested usage
        if lo == hi:
            usage_str = f"{lo}"  # e.g., "1 times"
        else:
            usage_str = f"{lo}-{hi}"  # e.g., "1-3 times"

        line = f"{term}: {usage_str} times"
        lines.append(line)

    # Join all lines with a newline character
    return "\n".join(lines)

# Example usage:
'''
example_use_less_objects = [
    {'term': 'wizz air flight', 'suggested_usage': [1, 2], 'current_usage': 9},
    {'term': 'may', 'suggested_usage': [1, 3], 'current_usage': 12},
    {'term': 'cancellation', 'suggested_usage': [1, 1], 'current_usage': 7}
]

formatted_string = format_use_less_objects(example_use_less_objects)
print(formatted_string)
'''


def sentence_to_multiline(sentence):
    """
    Splits the given sentence into words and returns a string
    with each word on a new line.
    """
    words = sentence.split()          # Split on whitespace
    multiline_string = "\n".join(words)
    return multiline_string


def objects_array_to_multiline(terms_array):

    multiline_string = ''

    for term_object in terms_array:
        term_string = term_object['t']
        multiline_string += f'{term_string}\n'

    return multiline_string


def tests():

    # get query result from neuron API
    #query_result = neuron_get_query(query_id)

    # get terms not used
    '''
    terms_not_used = get_terms_not_used(
        article_terms_not_used_added,
        query_result
    )
    
    print(terms_not_used)
    

    terms_to_use_less = get_terms_used_excessively(
        article_reduced_terms_2,
        query_result
    )

    formatted_string = format_use_less_objects(terms_to_use_less)

    print(formatted_string)
    '''

    # Example usage:
    sentence = "Hello world! This is a sample sentence."
    result = sentence_to_multiline(sentence)
    print(result)


#tests()
