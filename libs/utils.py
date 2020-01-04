from django.core.exceptions import FieldError
from django.db.models import Avg


def average(collection, criteria):
    """
    Given a QuerySey of records, calculate the average for a given attribute of the set
    :param collection: (QuerySet) Queryset of records
    :param criteria: (str) Desired field for calculated average

    :return: (float)
    """
    if not collection.exists():
        return None

    try:
        val = collection.aggregate(Avg(criteria))['{}__avg'.format(criteria)]
        return round(val, 2)

    except FieldError:
        raise ValueError('{} does not have an attribute {}'.format(collection.model, criteria))
