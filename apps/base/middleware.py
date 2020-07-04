from django.utils.deprecation import MiddlewareMixin


class ShortCircuitMiddleware(MiddlewareMixin):
    def process_view(self, request, view, view_args, view_kwargs):
        # Skip further middleware processing if view is in list of views
        # to short circuit.
        # TODO: Move to settings
        if view.__name__ in ['BrowseView']:
            return view(request, *view_args, **view_kwargs)
        return None
