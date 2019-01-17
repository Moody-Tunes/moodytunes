def average(collection):
    """
    Given a list of numbers, calculate the average of the set
    :param collection: (list) List of values to calculate average of
    :return: (float) Average of list elements to two decimal points
    :raises: `ValueError` if non-number values are passed in the `collection`
    """
    if not collection:
        return None

    all_nums = [type(ele) == int or type(ele) == float for ele in collection]

    if not all(all_nums):
        raise ValueError('Received a non numeric type, the only types accepted are `float` and `int`')

    return round(sum(collection) / len(collection), 2)
