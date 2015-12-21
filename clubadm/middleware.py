from django.utils import timezone

from clubadm.models import Member


class LastVisitMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if 'pk' in view_kwargs and request.user.is_authenticated():
            if not view_kwargs['pk'].isdigit():
                return
            Member.objects.filter(
                season_id=view_kwargs['pk'],
                user=request.user
            ).update(last_visit=timezone.now())
