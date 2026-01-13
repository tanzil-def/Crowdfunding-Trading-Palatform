from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class for API responses.
    Default: 10 items per page
    Can be customized via ?page_size query parameter
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100