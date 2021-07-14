from .import models

def menu_links(request):
    links = models.category.objects.all()
    return dict(links = links)