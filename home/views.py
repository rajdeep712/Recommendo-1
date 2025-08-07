from django.shortcuts import render,redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
import requests
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Case, When

from .models import Movie,Comment,Cast
from accounts.models import Profile
import pickle
import json
from decouple import config

# Create your views here.

def Home_page(request):
    if request.method == 'POST':
        return redirect('search_movie')
    if request.user.is_authenticated:
        return redirect('auth_home')
    

    filtered_movies = Movie.objects.filter(in_slider=True).order_by("-year")[:10]
    slider_data = []

    for movie in filtered_movies:
        slider_data.append({
            'code':movie.code,
            'year':movie.year,
            'rating':movie.imdb_rating,
            'plot':movie.plot,
            'title': movie.title,
            'backdrop_url': movie.backdrop_url,
        })

    return render(request,"home/index.html", {
        'slider_data':slider_data
    })


##### RECOMMENDATION LOGIC #####

import requests

API_URL = "https://recommenderfastapi-production.up.railway.app/recommend" 

def fetch_recommendations_from_api(fav_codes, top_n=200):
    if hasattr(fav_codes, "values_list"):
        fav_codes = list(fav_codes.values_list("code", flat=True))
    else:
        fav_codes = list(fav_codes)
    payload = {"fav_movies": fav_codes}
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        return response.json()["recommended_movies"]
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return []



def GetSliderMovies(request):
    category = request.GET.get('category')
    page_number = request.GET.get('page',1)

    if request.user.is_authenticated and request.user.profile.favourites.first():
        fav_movie = request.user.profile.favourites.last()
        if category == 'trending':
            # genres = fav_movie.genres.split(',')
            # genre1 = genres[0].strip()
            # genre2 = genres[1].strip()
            # trendings = Movie.objects.filter(Q(genres__icontains=genre1) | Q(genres__icontains=genre2)).distinct().order_by("-imdb_votes")

            fav_movie_code = fav_movie.code
            trendings = fetch_recommendations_from_api([fav_movie_code])

            order = Case(
                *[When(code=code, then=pos) for pos, code in enumerate(trendings)]
            )
            recommendations = Movie.objects.filter(code__in=trendings)

            paginator = Paginator(recommendations,15)

            pag_movies = paginator.page(page_number)

        elif category == 'latest':
            fav_movies = request.user.profile.favourites.values_list('code', flat=True)
            # genres = fav_movie.genres.split(',')
            # casts = fav_movie.casts.all()
            # latests = Movie.objects.filter(Q(casts__in=casts)).distinct().order_by("-vote_count")
            recommended_codes = fetch_recommendations_from_api(fav_movies, top_n=200)
            order = Case(
                *[When(code=code, then=pos) for pos, code in enumerate(recommended_codes)]
            )
            recommendations = Movie.objects.filter(code__in=recommended_codes).order_by(order)

            paginator = Paginator(recommendations,15)

            pag_movies = paginator.page(page_number)

        elif category == 'favcasts':
            fav_casts = request.user.profile.fav_casts.all()
            movies = Movie.objects.filter(casts__in=fav_casts).distinct().order_by("-imdb_rating")
            paginator = Paginator(movies,15)

            pag_movies = paginator.page(page_number)
            
        else:
            top_rated = Movie.objects.filter(Q(imdb_rating__gte=8) & Q(vote_count__gte=1500)).order_by("-popularity")
            paginator = Paginator(top_rated,15)

            pag_movies = paginator.page(page_number)

    elif request.user.is_authenticated:
        if category == 'trending':
            trendings = Movie.objects.filter(Q(vote_count__gte=1000)).order_by('-popularity')
            paginator = Paginator(trendings,15)

            pag_movies = paginator.page(page_number)

        elif category == 'latest': 
            latests = Movie.objects.filter(year__gte=2024).order_by('-popularity')
            paginator = Paginator(latests,15)

            pag_movies = paginator.page(page_number)

        elif category == 'favcasts':
            fav_casts = request.user.profile.fav_casts.all()
            movies = Movie.objects.filter(casts__in=fav_casts).distinct().order_by("-imdb_rating")
            paginator = Paginator(movies,15)

            pag_movies = paginator.page(page_number)
            
        else:
            top_rated = Movie.objects.filter(Q(imdb_rating__gte=8) & Q(vote_count__gte=1500)).order_by("-popularity")
            paginator = Paginator(top_rated,15)

            pag_movies = paginator.page(page_number)

    else:
        if category == 'trending':
            trendings = Movie.objects.filter(Q(vote_count__gte=1000)).order_by('-popularity')
            paginator = Paginator(trendings,15)

            pag_movies = paginator.page(page_number)

        elif category == 'latest':
            latests = Movie.objects.filter(year__gte=2024).order_by('-popularity')
            paginator = Paginator(latests,15)

            pag_movies = paginator.page(page_number)
            
        else:
            top_rated = Movie.objects.filter(Q(imdb_rating__gte=8) & Q(vote_count__gte=1500)).order_by("-popularity")
            paginator = Paginator(top_rated,15)

            pag_movies = paginator.page(page_number)


    mov_data = []
    for movie in pag_movies:
        mov_data.append({
            'code':movie.code,
            'poster':movie.poster,
            'title':movie.title,
            'year':movie.year,
            'rating':movie.imdb_rating,
            'content_type':movie.content_type
        })

    return JsonResponse(data={'movies':mov_data , 'has_next':pag_movies.has_next()})
    

@login_required(login_url='/accounts/login/')
def Auth_Home_Page(request):
    if(request.method == "POST"):
        selector = request.POST['selector']
        if selector == 'logout':
            logout(request)
            return redirect('login')
        
        else:
            return redirect('search_movie')
    
    name = request.user.first_name
    profile = request.user.profile
    avatar_url = profile.avatar_url
    if (profile.firstTime_login_done == False):
        request.session['login_first'] = True

    filtered_movies = Movie.objects.filter(in_slider=True).order_by("-year")[:10]
    slider_data = []

    for movie in filtered_movies:
        slider_data.append({
            'code':movie.code,
            'year':movie.year,
            'rating':movie.imdb_rating,
            'plot':movie.plot,
            'title': movie.title,
            'backdrop_url': movie.backdrop_url,
        })


    
    if not profile.favourites.exists():
        section1 = 'Trending'
        section2 = 'Latest'
        section3 = 'Top rated'
        section4 = 'Based on Your Favourite Casts'

    else:
        fav_movie = profile.favourites.last()
        title = fav_movie.title
        section1 = f'Because you liked {title}'
        section2 = 'Recommended for you'
        section3 = 'Trending Now'
        section4 = 'Based on your Favourite Casts'

    return render(request,"home/user-home.html", {
        'name':name,
        'section1':section1,
        'section2':section2,
        'section3':section3,
        'section4':section4,
        'avatar_url':avatar_url,
        'slider_data':slider_data
    })

def SingleMoviePage(request,code):
    

    if(request.method == "GET"):
        movie = Movie.objects.get(code=code)

        YOUTUBE_API_KEY = config('YOUTUBE_API_KEY')
        def get_youtube_trailer_id(title):
            search_query = f"{title} official trailer"
            url = "https://www.googleapis.com/youtube/v3/search"

            params = {
                "part": "snippet",
                "q": search_query,
                "key": YOUTUBE_API_KEY,
                "type": "video",
                "maxResults": 1
            }

            response = requests.get(url, params=params)
            data = response.json()

            items = data.get("items", [])
            if items:
                video_id = items[0]["id"]["videoId"]
                return video_id

            return None

        movie_title = movie.title
        video_id = get_youtube_trailer_id(movie_title)


        genres = movie.genres.split(',')
        casts = movie.casts.all()

        is_box_office_hit = movie.revenue and movie.budget and movie.revenue >= 2*movie.budget
        is_blockbuster = movie.revenue and movie.budget and movie.revenue >= 5*movie.budget and movie.imdb_rating and movie.imdb_rating >= 8.0 

        is_comments = False
        if movie.comments.all() is not None:
            is_comments = True
            comments = movie.comments.all().order_by("-created_at")

        if request.user.is_authenticated:
            profile = request.user.profile
            username = request.user.username
            is_favourite = False
            if profile.favourites.filter(code=code).first():
                is_favourite = True

            eps_per_season = {}
            raw = movie.episodes_per_season
            if isinstance(raw, str):
                try:
                    eps_per_season = json.loads(raw)
                except Exception:
                    eps_per_season = {}
            elif isinstance(raw, dict):
                eps_per_season = raw

            if movie.content_type == 'series':
                seasons = list(range(1, movie.no_of_seasons + 1))
                episodes_per_season = {
                    s: list(range(1, int(eps_per_season.get(str(s), 0)) + 1))
                    for s in seasons
                }
                
            else:
                seasons = []
                episodes_per_season = {}


            watched_set = set()
            watched_episodes = profile.watched_episodes or {}

            for mcode, seasons_dict in watched_episodes.items():
                for season, episodes in seasons_dict.items():
                    for episode in episodes:
                        key = f"{str(mcode)}-{str(season)}-{str(episode)}"
                        watched_set.add(key)
            
            return render(request, "home/singleMovie.html", {
                'movie':movie,
                'genres':genres,
                'casts':casts,
                'is_favourite':is_favourite,
                'is_comments':is_comments,
                'comments':comments,
                'username':username,
                'video_url':f"https://www.youtube.com/embed/{video_id}?enablejspi=1",
                'box_office_hit':is_box_office_hit,
                'blockbuster':is_blockbuster,
                'seasons':seasons,
                'episodes_per_season':episodes_per_season,
                'watched_set':watched_set
            })
        else:
            return render(request, "home/normalSingleMovie.html", {
                'movie':movie,
                'genres':genres,
                'casts':casts,
                'is_comments':is_comments,
                'comments':comments,
                'video_url':f"https://www.youtube.com/embed/{video_id}?enablejspi=1",
                'box_office_hit':is_box_office_hit,
                'blockbuster':is_blockbuster
            })
        

def SearchMovie(request):
    movies = Movie.objects.filter(Q(imdb_rating__gt=8) & Q(vote_count__gte=1500))[:16]
    return render(request,"home/search.html" , {
        'movies':movies
    })

def FilterMovie(request):
    category = str(request.GET.get('category'))

    page_num = int(request.GET.get('page',1))

    if category == 'All':
        movies = Movie.objects.filter(Q(imdb_rating__gt=7.5) & Q(vote_count__gte=1000)).order_by("-popularity")

        paginator = Paginator(movies , 20)
        pag_movies = paginator.page(page_num)

    else:
        movies = Movie.objects.filter(Q(genres__icontains=category) & Q(vote_count__gt=1000)).order_by('-popularity')

        paginator = Paginator(movies , 20)
        pag_movies = paginator.page(page_num)

    mov_data = []
    for movie in pag_movies:
        mov_data.append({
            'title':movie.title,
            'poster':movie.poster,
            'rating':movie.imdb_rating,
            'year':movie.year,
            'code':movie.code,
            'content_type':movie.content_type
        })

    return JsonResponse(data={'movies':mov_data , 'has_next':pag_movies.has_next()})


def SearchResult(request):
    mov_name = request.GET.get('mov_name').strip()
    is_found = 'True'

    movies = Movie.objects.filter(title__icontains=mov_name).order_by('-imdb_votes')[:600]

    if not movies:
        is_found = 'False'

        data = {'is_found':is_found}

    else:
        rel_movies = Movie.objects.filter(vote_count__gt=1000).order_by('-popularity')[:20]
        mov_data = []
        rel_mov_data = []
        for movie in movies:
            mov_data.append({
            'title':movie.title,
            'poster':movie.poster,
            'rating':movie.imdb_rating,
            'year':movie.year,
            'code':movie.code,
            'content_type':movie.content_type
        })
            
        for rel_mov in rel_movies:
            rel_mov_data.append({
            'title':rel_mov.title,
            'poster':rel_mov.poster,
            'rating':rel_mov.imdb_rating,
            'year':rel_mov.year,
            'code':rel_mov.code,
            'content_type':rel_mov.content_type
        })
            
        data = {'is_found':is_found , 'movies':mov_data , 'rel_movies':rel_mov_data}

    return JsonResponse(data)


def AddToFavourites(request):
    mov_code = request.GET.get('mov_code')
    profile = request.user.profile
    fav_movie = Movie.objects.get(code=mov_code)

    if profile.favourites.filter(code=mov_code).exists():
        profile.favourites.remove(fav_movie)
    else:
        profile.favourites.add(fav_movie)

    return JsonResponse(data={"status":"success"})


def ForgetPassword(request):
    return render(request,"home/forgetpass.html")


@login_required(login_url="/accounts/login/")
def AuthFavourites(request):
    if request.user.profile.favourites.first():
        movies = request.user.profile.favourites.all()
        return render(request, "home/favs.html" , {
            'is_fav':True,
            'movies':movies,
            'is_cast':False
        })
    
    else:
        return render(request, "home/favs.html", {
            "is_fav":False,
            'movies':None,
            'is_cast':False
        })
    

def CastMoviesPage(request,name):
    return render(request,"home/favs.html" , {
        'is_fav':True,
        'movies':None,
        'is_cast':True,
        'cast_name':name
    })

def GetCastMovies(request):
    cast_name = request.GET.get('name')
    page_number = request.GET.get('page',1)

    movies = Movie.objects.filter(casts__name__icontains=cast_name).order_by("-imdb_votes")

    paginator = Paginator(movies,16)
    pag_movies = paginator.page(page_number)
    movie_data = []

    for movie in pag_movies:
        movie_data.append({
            'poster':movie.poster,
            'title':movie.title,
            'year':movie.year,
            'rating':movie.imdb_rating,
            'code':movie.code,
            'content_type':movie.content_type
        })

    return JsonResponse(data={'movies':movie_data,'has_next':pag_movies.has_next()})



def ToggleComment(request):
    user = request.user
    category = request.GET.get('category')

    profile = user.profile

    if category == "comment":
        fname = request.user.first_name[0]
        lname = request.user.last_name[0]
        avatar = fname+lname
        mov_code = request.GET.get('code')
        comment = request.GET.get('comment').strip()
        if not comment:
            return redirect('single_movie', code=mov_code)
        username = request.user.username
        name = request.user.get_full_name()
        movie = Movie.objects.get(code=mov_code)
        comment_obj = Comment.objects.create(name=name,username=username,comment=comment,movies=movie,avatar=avatar)

        return JsonResponse(data={
            'avatar':avatar,
            'name':name,
            'comment':comment,
            'code':mov_code,
            'comment_id':comment_obj.id
        })
    
    else:
        comment_id = int(request.GET.get('commentId'))
        my_comment = Comment.objects.get(id=comment_id)
        my_comment.delete()
        return JsonResponse(data={
            'status':"SUCCESS"
        })


@login_required
def getCasts(request):
    casts = Cast.objects.filter(in_option=True)
    cast_data = []
    for cast in casts:
        cast_data.append({
            'name':cast.name,
            'id':cast.id,
            'image_url':cast.image_url
        })

    return JsonResponse(data={'casts':cast_data})

@login_required
def clearFirstLogin(request):
    selected_casts = request.GET.get('selectedCasts')
    selected_casts_ids = [int(cast_id) for cast_id in selected_casts.split(',')]

    request.session.pop('login_first')
    profile = request.user.profile
    for id in selected_casts_ids:
        cast = Cast.objects.get(pk=id)
        profile.fav_casts.add(cast)
    profile.firstTime_login_done = True
    profile.save()

    return JsonResponse(data={'status':'SUCCESS'})




@csrf_exempt
def mark_watched(request):
    if request.method == 'POST' and request.user.is_authenticated:
        data = json.loads(request.body)
        movie = data['movie']
        season = str(data['season'])
        episode = str(data['episode'])
        profile = request.user.profile

        watched = profile.watched_episodes or {}
        watched.setdefault(movie, {}).setdefault(season, [])
        if episode not in watched[movie][season]:
            watched[movie][season].append(episode)
        profile.watched_episodes = watched
        profile.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@csrf_exempt
def unmark_watched(request):
    if request.method == 'POST' and request.user.is_authenticated:
        data = json.loads(request.body)
        movie = data['movie']
        season = str(data['season'])
        episode = str(data['episode'])
        profile = request.user.profile

        watched = profile.watched_episodes or {}
        if movie in watched and season in watched[movie]:
            if episode in watched[movie][season]:
                watched[movie][season].remove(episode)
                # Clean up empty lists/dicts
                if not watched[movie][season]:
                    del watched[movie][season]
                if not watched[movie]:
                    del watched[movie]
                profile.watched_episodes = watched
                profile.save()
                return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)