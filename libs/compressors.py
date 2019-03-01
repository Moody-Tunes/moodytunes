from compressor.conf import settings
from compressor.filters import CompilerFilter


class UglifyJSFilter(CompilerFilter):
    command = "{binary} {args}"
    options = (
        ('binary', settings.UGLIFY_BINARY),
        ('args', settings.UGLIFY_ARGUMENTS)
    )
