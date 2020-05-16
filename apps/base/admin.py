from django.contrib import admin


class MoodyBaseAdmin(admin.ModelAdmin):
    list_display = ('created', 'updated')
