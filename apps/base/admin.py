from django.contrib import admin


class MoodyBaseAdmin(admin.ModelAdmin):
    list_display = ('created', 'updated', 'pk')

    def get_list_display(self, request):
        return self.list_display + MoodyBaseAdmin.list_display
