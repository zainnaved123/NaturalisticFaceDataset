import requests
from dotenv import load_dotenv

load_dotenv()
import os

# API keys
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")


def get_movie_id(movie_name):
    url = f"http://www.omdbapi.com/?t={movie_name}&apikey={OMDB_API_KEY}"
    response = requests.get(url)
    data = response.json()
    if "imdbID" in data:
        return data["imdbID"]
    else:
        return None


def get_tmdb_id(imdb_id):
    url = f"https://api.themoviedb.org/3/find/{imdb_id}?api_key={TMDB_API_KEY}&external_source=imdb_id"
    response = requests.get(url)
    data = response.json()
    if "movie_results" in data and data["movie_results"]:
        return data["movie_results"][0]["id"]
    else:
        return None


def get_actors_details(tmdb_id):
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    data = response.json()
    if "cast" in data:
        actors = []
        for actor in data["cast"]:
            actors.append(
                {
                    "name": actor["name"],
                    "profile_image": (
                        f"https://image.tmdb.org/t/p/w500{actor['profile_path']}"
                        if actor["profile_path"]
                        else None
                    ),
                }
            )
        print(actors)
        return actors
    else:
        return None


def fetch_actors_from_movie(movie_name):
    imdb_id = get_movie_id(movie_name)
    if imdb_id:
        tmdb_id = get_tmdb_id(imdb_id)
        if tmdb_id:
            actors = get_actors_details(tmdb_id)
            if actors:
                return actors
    return None


# def main():
#     movie_name = input("Enter the movie name: ")
#     imdb_id = get_movie_id(movie_name)
#     if imdb_id:
#         print(f"IMDb ID for {movie_name}: {imdb_id}")
#         tmdb_id = get_tmdb_id(imdb_id)
#         if tmdb_id:
#             actors = get_actors_details(tmdb_id)
#             if actors:
#                 print(f"Actors in {movie_name}:")
#                 for actor in actors:
#                     print(f"Name: {actor['name']}")
#                     print(f"Profile Image: {actor['profile_image']}\n")
#             else:
#                 print("No actor details found.")
#         else:
#             print("TMDb ID not found.")
#     else:
#         print("Movie not found.")


# if __name__ == "__main__":
#     main()
