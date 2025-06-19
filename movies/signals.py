from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Booking, Seat

@receiver(post_save, sender=Booking)
def update_seat_booking_status(sender, instance, created, **kwargs):
    if created:
        seat = instance.seat
        seat.is_booked = True
        seat.save()
