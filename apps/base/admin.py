from django.contrib import admin


class MoodyBaseAdmin(admin.ModelAdmin):
    list_display = ('created', 'updated')
    primary_key_value = ('pk',)

    def get_list_display(self, request):
        return self.primary_key_value + self.list_display + MoodyBaseAdmin.list_display
