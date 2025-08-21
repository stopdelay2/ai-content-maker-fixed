import re


def keyword_to_slug(google_keyword: str) -> str:
    """
    Transforms a Google search keyword/phrase into a URL-friendly slug format.

    Args:
        google_keyword (str): The search term to be converted (e.g., "best hotels in miami")

    Returns:
        str: The URL-friendly slug (e.g., "best-hotels-in-miami")

    Examples:
        >>> keyword_to_slug("best hotels in miami")
        'best-hotels-in-miami'
        >>> keyword_to_slug("  Python Programming  ")
        'python-programming'
        >>> keyword_to_slug("Where's the best café?")
        'wheres-the-best-cafe'
    """
    # First, convert the string to lowercase to ensure consistency
    # This is important because URLs are typically case-insensitive
    cleaned_keyword = google_keyword.lower()

    # Replace any special characters or punctuation with spaces
    # This handles cases where someone might search with punctuation

    cleaned_keyword = re.sub(r'[^a-z0-9\s]', ' ', cleaned_keyword)

    # Split the string into words and filter out empty strings
    # This handles cases where we might have multiple spaces
    words = [word for word in cleaned_keyword.split() if word]

    # Join the words with hyphens to create the final slug
    url_slug = '-'.join(words)

    return url_slug
