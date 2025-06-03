from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class DefaultPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'size'

    def get_paginated_response(self, data):
        return Response({
            'items': data,
            'page': self.page.number,
            'count': len(data),
            'total': self.page.paginator.count,
            'size': self.page.paginator.per_page
        })
