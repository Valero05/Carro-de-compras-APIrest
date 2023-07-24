from rest_framework.permissions import BasePermission

class IsManager(BasePermission):
    def has_permission(self, request, view):
        if request.user.groups.filter(name='manager').exists():
            return True
        
class IsDeliveryCrew(BasePermission):
    def has_permission(self, request, view):
        if request.user.groups.filter(name='delivery crew').exists():
            return True