from django.conf import settings


def format_module_name_with_project_prefix(name):
    """
    Return name prefixed with 'mtdj'. Useful for using __name__ when
    constructing a logger. Needed because the dotted path inside the modules
    defined in apps/ start with their app name.
    """
    if '.' not in name:
        # Didn't get something that looks like a path, return ''
        return ''

    start_module = name.split('.')[0]

    # If name contains a module defined in apps, prepend 'apps' to the name
    if start_module in settings.INSTALLED_APPS:
        name = '{apps_dir}.{module_name}'.format(
            apps_dir='apps',
            module_name=name,
        )

    return '{prefix}.{module_name}'.format(
        prefix=settings.PROJECT_PREFIX,
        module_name=name,
    )
