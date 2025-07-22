from django.utils.translation import get_language


class DataMixin:
    """Mixin to add pagination and customizable context data to views."""
    paginate_by = 12
    title_page = None
    cat_selected = None
    extra_context = {}

    def __init__(self):
        """Initialize extra context data with title and selected category if provided."""
        if self.title_page:
            self.extra_context['title'] = self.title_page

        if self.cat_selected is not None:
            self.extra_context['cat_selected'] = self.cat_selected

    @staticmethod
    def get_mixin_context(context, **kwargs):
        """Update the context with additional data, defaulting cat_selected to None."""
        context['cat_selected'] = None
        context.update(kwargs)
        return context


def generate_cache_key(obj, data):
    """Generate a cache key based on the object type and language."""
    return f'{obj}: {data}_{get_language()}'


def get_ru_suffix(obj, data):
    """Return the correct Russian suffix for words based on quantity."""
    if get_language() == 'ru':
        if data % 10 == 1 and data % 100 != 11:
            if obj == 'comments':
                return 'й'
            elif obj == 'search':
                return ''
        elif 2 <= data % 10 <= 4 and (data % 100 < 10 or data % 100 >= 20):
            if obj == 'comments':
                return 'я'
            elif obj == 'search':
                return 'а'
        else:
            if obj == 'comments':
                return 'ев'
            elif obj == 'search':
                return 'ов'
