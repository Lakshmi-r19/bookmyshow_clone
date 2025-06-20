from django.shortcuts import render, redirect ,get_object_or_404
from .models import Movie,Theater,Seat,Booking,ShowTiming
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta

def movie_timing(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    show_timing = ShowTiming.objects.filter(movie=movie)
    return render(request, 'movies/movie_timing.html', {
        'movie': movie,
        'show_timing': show_timing,
        'trailer_id': movie.trailer_id,
    })

def reservation_payment_page(request, show_id):
    show = get_object_or_404(ShowTiming, id=show_id)
    # Example: Pretend user selects first 2 available seats for demo
    seats = Seat.objects.filter(show=show, is_reserved=False)[:2]
    
    if request.method == 'POST':
        # Mark seats reserved and redirect to success page
        for seat in seats:
            seat.is_reserved = True
            seat.save()
        return redirect('successfully_booked')
    
    return render(request, 'movies/reservation_payment_page.html', {
        'seats': seats,
    })

def payment_timeout(request):
    return render(request, 'movies/payment_timeout.html', {
        'seats_expired': ['A1', 'A2'],  # Example expired seats
        'theater': None,  # Optional, use if going back to seat selection
    })

def successfully_booked(request):
    return render(request, 'movies/successfully_booked.html', {
        'seats': ['A1', 'A2'],  # Example, should come dynamically
    })

def movie_list(request):
    search_query=request.GET.get('search')
    if search_query:
        movies=Movie.objects.filter(name__icontains=search_query)
    else:
        movies=Movie.objects.all()
    return render(request,'movies/movie_list.html',{'movies':movies})

'''def theater_list(request,movie_id):
    movie = get_object_or_404(Movie,id=movie_id)
    theater=Theater.objects.filter(movie=movie)
    return render(request,'movies/theater_list.html',{'movie':movie,'theaters':theater})'''

def theater_list(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    theaters = Theater.objects.filter(movie=movie)

    showtimes = []
    for theater in theaters:
        total_seats = Seat.objects.filter(theater=theater).count()
        available_seats = Seat.objects.filter(theater=theater, is_booked=False).count()
        is_fully_booked = available_seats == 0

        showtimes.append({
            'theater': theater,
            'available_seats': available_seats,
            'is_fully_booked': is_fully_booked,
        })

    return render(request, 'movies/theater_list.html', {
        'movie': movie,
        'showtimes': showtimes,
    })


@login_required(login_url='/login/')
def book_seats(request,theater_id):
    theaters=get_object_or_404(Theater,id=theater_id)
    seats=Seat.objects.filter(theater=theaters)
    if request.method == 'POST':
        selected_seats = request.POST.getlist('seats')
        error_seats = []

        if not selected_seats:
            return render(request, "movies/seat_selection.html", {
                'theater': theaters,
                "seats": seats,
                'error': "No seat selected"
            })
        reserved_ids=[]
        for seat_id in selected_seats:
            seat = get_object_or_404(Seat, id=seat_id, theater=theaters)


            if seat.is_booked or (seat.is_seat_reserved and seat.seat_reserved_by != request.user):
                error_seats.append(seat.seat_number)
                continue
            seat.is_seat_reserved = True
            seat.seat_reserved_by = request.user
            seat.seat_reserved_at = timezone.now()
            seat.save()
            reserved_ids.append(seat.id)
        if error_seats:
             error_message = f"The following seats are already booked or reserved: {', '.join(error_seats)}"
             return render(request, 'movies/seat_selection.html', {
                'theater': theaters,
                "seats": seats,
                'error': error_message
            })
        if reserved_ids:
            return redirect('reservation_payment_page', seat_ids=",".join(map(str, reserved_ids)))
        else:
            return render(request, 'movies/seat_selection.html', {
                 'theater': theaters,
                 'seats': seats,
                 'error': "No valid seats could be reserved."
    })    
       

  

    return render(request, 'movies/seat_selection.html', {
        'theater': theaters,
        "seats": seats
    })
       

  

    
@login_required(login_url='/login/')
def reservation_payment_page(request, seat_ids):
    seat_ids = seat_ids.split(',')
    seats = Seat.objects.filter(id__in=seat_ids, seat_reserved_by=request.user)
    if not seats.exists():
       return redirect('home')  # or show error
    theater = seats.first().theater
   

    
    seats_expired = []
    for seat in seats:
        if seat.seat_reserved_at and timezone.now() > seat.seat_reserved_at + timedelta(minutes=5):
            seat.is_seat_reserved = False
            seat.seat_reserved_by = None
            seat.seat_reserved_at = None
            seat.save()
            seats_expired.append(seat.seat_number)

    
    if seats_expired:
        return render(request, 'movies/payment_timeout.html', {
            'seats_expired': seats_expired,
            'theater': theater
        })

    
    if request.method == 'POST':
        for seat in seats:
            seat.is_booked = True
            seat.is_seat_reserved = False
            seat.seat_reserved_by = None
            seat.seat_reserved_at = None
            seat.save()
        return render(request, 'movies/successfully_booked.html', {
            'seats': seats
        })

    
    return render(request, 'movies/reservation_payment_page.html', {
        'seats': seats
        
    })
def timeout_page(request):
    return render(request, 'movies/payment_timeout.html')

                