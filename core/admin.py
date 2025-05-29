from django.contrib import admin
from .models import Board, Memo, User, Neighbor, NeighborRequest

admin.site.register(Board)
admin.site.register(Memo) 
admin.site.register(User)
admin.site.register(Neighbor)
admin.site.register(NeighborRequest)
