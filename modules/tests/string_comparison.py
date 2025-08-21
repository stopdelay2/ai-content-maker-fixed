def compare_string_arrays(array1, array2):
    """
    Compares two arrays of strings of equal length.
    Returns True if all elements match; otherwise returns False and
    prints the indices where the elements differ.
    """

    # First, check if both arrays have the same length
    if len(array1) != len(array2):
        print("Error: Arrays must have the same length.")
        return False

    # Track indices where the arrays differ
    different_indices = []

    # Compare elements at the same index
    for i in range(len(array1)):
        if array1[i] != array2[i]:
            different_indices.append(i)

    # If we found differences, print them out and return False
    if different_indices:
        print("Differences found at indices:", different_indices)
        return False

    # If no differences, return True
    return True


# --------------------
# Example usage:
# --------------------

def mini_tests():

    arr1 = ["apple", "banana", "cherry"]
    arr2 = ["apple", "banana", "cherry"] # "berry"

    result = compare_string_arrays(arr1, arr2)

    if result:
        print("All strings match at every index.")
    else:
        print("There are differences in one or more indices.")


#mini_tests()

def tests():
        array1 = [
            "<h1>Flight Delay on Wizz Air Flight 1030 (W61030)? Your Guide to Compensation and Claims</h1>",
            "<h2>What Is Wizz Air Flight 1030 (W61030)?</h2>",
            "<h2>How to Check the Flight Status of W6 1030 Flight?</h2>",
            "<h2>Understanding Your Passenger Rights Under Regulation 261</h2>",
            "<h2>Am I Entitled to Compensation for Wizz Air Flight W61030 Delay or Cancellation?</h2>",
            "<h2>How to Claim Compensation from Wizz Air</h2>",
            "<h2>Tips to Avoid Future Flight Disruptions</h2>",
            "<h2>Tracking Your Flight: Real-Time Data and Flight Map</h2>",
            "<h2>What Happens If Your Flight Was Cancelled?</h2>",
            "<h2>Refunds, Compensation, and Next Steps for Affected Passengers</h2>",
            "<h2>Conclusion</h2>"
        ]

        array2 = [
            "<h1>Flight Delay on Wizz Air Flight 1030 (W61030)? Your Guide to Compensation and Claims</h1>",
            "<h2>What Is Wizz Air Flight 1030 (W61030)?</h2>",
            "<h2>How to Check the Flight Status of W6 1030 Flight?</h2>",
            "<h2>Understanding Your Passenger Rights Under Regulation 261</h2>",
            "<h2>Am I Entitled to Compensation for Wizz Air Flight W61030 Delay or Cancellation?</h2>",
            "<h2>How to Claim Compensation from Wizz Air</h2>",
            "<h2>Tips to Avoid Future Flight Disruptions</h2>",
            "<h2>Tracking Your Flight: Real-Time Data and Flight Map</h2>",
            "<h2>What Happens If Your Flight Was Cancelled?</h2>",
            "<h2>Refunds, Compensation, and Next Steps for Affected Passengers</h2>",
            "<h2>Conclusion</h2>"
        ]

        result = compare_string_arrays(array1, array2)

        if result:
            print("All strings match at every index.")
        else:
            print("There are differences in one or more indices.")

#tests()
