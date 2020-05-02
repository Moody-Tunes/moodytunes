from django.core.exceptions import FieldError
from django.db.models import Avg


def average(collection, *criteria, precision=2):
    """
    Given a QuerySey of records, calculate the average for given attributes of the set to `precision` decimal places

    :param collection: (QuerySet) Queryset of records
    :param criteria: (*args[str]) Desired fields for calculated average
    :param precision: (int) Precision to round values to. Default is 2

    :return: (dict)
    """
    try:
        fields = [Avg(field) for field in criteria]
        ret = collection.aggregate(*fields)

        if not all(ret.values()):
            return dict([(key, None) for key in ret.keys()])

        for key, value in ret.items():
            ret[key] = round(value, precision)

        return ret

    except FieldError:
        raise ValueError('{} does not have an attribute {}'.format(collection.model, criteria))
