import os
import sys
import django
import time
import requests
from django.core.management.base import BaseCommand
from home.models import Movie, Episode  # Change 'home' to your actual app name

# If running outside manage.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")  # Change to your project name
django.setup()

class Command(BaseCommand):
    help = "Fetch and store episodes for series using OMDb API"

    # List of OMDb API keys
    OMDB_KEYS = [
        '5eeb4d2a',
        '57f88196',
        '31a51af6',
        '8e6ad8a0',
        'f34f41a',
        '9f9b4fd5',
        '1eddebb7',
        'cb14d3a4',
        'ea72618d',
        '16e3787',
        'ef3b167',
        '2d423aa1',
        '116311f3',
        'bad8ea95',
        '6491cc6f',
        '84450ae4',
        '452b44a2',
        '701b07fd',
        '515f29e1',
        '1bf06826',
        '5618c29c',
        '4433916'
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--start-id",
            type=int,
            help="Start fetching from a specific series Movie ID",
        )

    def get_response_with_retry(self, url):
        for key in self.OMDB_KEYS:
            try:
                response = requests.get(url.replace("OMDB_KEY", key), timeout=10)
                data = response.json()
                if data.get("Response") == "True":
                    return data
                elif data.get("Error") == "Request limit reached!":
                    self.stderr.write(f"⚠️  OMDb key limit reached for key: {key}, trying next.")
                    continue
                else:
                    return data  # Sometimes returns False but with useful error
            except Exception as e:
                self.stderr.write(f"❌ Error with key {key}: {str(e)}")
                continue
        return None

    def handle(self, *args, **options):
        start_id = options.get("start_id")

        series_queryset = Movie.objects.filter(content_type="series").order_by("id")
        if start_id:
            series_queryset = series_queryset.filter(id__gte=start_id)

        for series in series_queryset:
            if Episode.objects.filter(series=series).exists():
                self.stdout.write(f"⏭️  Skipping {series.title} (ID {series.id}) — Episodes already fetched.")
                continue

            imdb_id = series.code
            total_seasons = series.no_of_seasons or 0

            self.stdout.write(f"\n📺 {series.id}: {series.title} ({total_seasons} seasons)")

            for season_num in range(1, total_seasons + 1):
                season_url = f"http://www.omdbapi.com/?apikey=OMDB_KEY&i={imdb_id}&Season={season_num}"
                season_data = self.get_response_with_retry(season_url)

                if not season_data or 'Episodes' not in season_data:
                    self.stdout.write(f"  ⚠️ Skipping season {season_num} (no data)")
                    continue

                for ep in season_data['Episodes']:
                    episode_id = ep.get("imdbID")
                    if not episode_id:
                        continue

                    episode_url = f"http://www.omdbapi.com/?apikey=OMDB_KEY&i={episode_id}&plot=full"
                    episode_data = self.get_response_with_retry(episode_url)

                    if not episode_data or episode_data.get("Response") != "True":
                        self.stdout.write(f"    ❌ Failed to fetch episode {episode_id}")
                        continue

                    try:
                        episode_obj, created = Episode.objects.update_or_create(
                            imdb_id=episode_id,
                            defaults={
                                'series': series,
                                'season': int(episode_data.get("Season", season_num)),
                                'episode_number': int(episode_data.get("Episode", 0)),
                                'title': episode_data.get("Title", ""),
                                'plot': episode_data.get("Plot", ""),
                                'imdb_rating': float(episode_data.get("imdbRating", 0)) if episode_data.get("imdbRating") != "N/A" else None,
                                'runtime': episode_data.get("Runtime", "")
                            }
                        )

                        status = "✅ Created" if created else "🔁 Updated"
                        self.stdout.write(f"    {status}: S{season_num:02}E{episode_obj.episode_number:02} - {episode_obj.title}")

                    except Exception as e:
                        self.stderr.write(f"    ❌ Error saving episode {episode_id}: {e}")

                    time.sleep(0.2)  # Rate limit safety
