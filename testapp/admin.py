from django.contrib import admin
from testapp.models import *
# Register your models here.
class ContactAdmin(admin.ModelAdmin):
    list_display=['name','email','msg']
admin.site.register(Contact,ContactAdmin)


admin.site.register(ChatMessage)
admin.site.register(Experience)