from django_celery_beat.models import IntervalSchedule
from django_celery_beat.models import PeriodicTask


def schedule_task(t):

    # Define the interval schedule
    interval_schedule = IntervalSchedule.objects.create(every=t.time_interval,
                                                        period=IntervalSchedule.MINUTES)

    # Define the periodic task
    periodic_task = PeriodicTask.objects.create(interval=interval_schedule,
                                                name=str(t.pk),
                                                task='crawlers.crawler_engine.run_task',
                                                args=[t.pk])


def unschedule_task(t):

    # Get periodic task
    try:
        periodic_task = PeriodicTask.objects.get(name=str(t.pk))
    except PeriodicTask.DoesNotExist:
        return

    # Delete periodic task
    periodic_task.delete()
