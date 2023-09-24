from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
import translators as ts

from constants import available_languages
from db import *

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Password hashing
password_hasher = CryptContext(schemes=["bcrypt"], deprecated="auto")


@app.get("/", response_model=dict)
@app.post("/", response_model=dict)
async def home(request: Request, user: User = Depends(get_current_user)):
    words = []
    languages = []
    if user:
        words = get_user_translations(user["id"])
        languages = get_user_languages(user["id"])
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user_logged_in": user is not None,
            "username": user["username"] if user else None,
            "words": words if words else None,
            "languages": languages if languages else [],
            "available_languages": available_languages,
        },
    )


# Authentication page (for GET requests)
@app.get("/auth", response_class=HTMLResponse)
async def auth_form(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})


@app.post("/auth", response_class=HTMLResponse)
async def auth(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    register: str = Form(None),
):
    if register:
        # Registration process
        if not get_user_by_username(username):
            # Username does not exist, so create a new user
            hashed_password = password_hasher.hash(password)
            create_user(username, hashed_password)
            redirect_url = request.url_for("home")
            response = RedirectResponse(redirect_url)
            response.set_cookie(key="username", value=username)
            return response
        else:
            response = templates.TemplateResponse(
                "auth.html",
                {
                    "request": request,
                    "user_logged_in": None,
                    "username": None,
                    "error_message": "username already exists.",
                },
            )
            return response
    else:
        # Login process
        user = get_user_by_username(username)
        if user and password_hasher.verify(password, user["password"]):
            redirect_url = request.url_for("home")
            response = RedirectResponse(redirect_url)
            response.set_cookie(key="username", value=username)
            return response
        else:
            response = templates.TemplateResponse(
                "auth.html",
                {
                    "request": request,
                    "user_logged_in": None,
                    "username": None,
                    "error_message": "incorrect username or password.",
                },
            )
            return response


@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    redirect_url = request.url_for("home")
    response = RedirectResponse(redirect_url)
    response.delete_cookie(key="username")
    return response


@app.post("/add_word", response_class=HTMLResponse)
async def add_word(
    request: Request, word: str = Form(...), user: User = Depends(get_current_user)
):
    languages = get_user_languages(user["id"])
    t = {}
    for language in languages:  # TODO: parallelize
        try:
            translation = ts.translate_text(word, to_language=language)
            t.update({language: translation})
        except Exception as e:
            print(e)  # TODO: dev remove
            t.update({language: "not found"})

    print(t)  # TODO: dev remove
    insert_user_word_and_translations(user["id"], word, t)

    redirect_url = request.url_for("home")
    return RedirectResponse(redirect_url)


@app.get("/delete_word", response_class=HTMLResponse)
async def delete_word(
    request: Request, submission_id: str, user: User = Depends(get_current_user)
):
    delete_user_word_and_translations(submission_id)
    redirect_url = request.url_for("home")
    return RedirectResponse(redirect_url)


@app.get("/delete_language", response_class=HTMLResponse)
async def delete_language(
    request: Request, language: str, user: User = Depends(get_current_user)
):
    print(f"... {language}")
    delete_user_language(user["id"], language)
    redirect_url = request.url_for("home")
    return RedirectResponse(redirect_url)


@app.post("/update_languages", response_class=HTMLResponse)
async def update_languages(
    request: Request,
    updated_languages: list = Form([]),
    user: User = Depends(get_current_user),
):
    old_languages = get_user_languages(user["id"])
    update_user_languages(user["id"], old_languages, updated_languages)
    redirect_url = request.url_for("home")
    return RedirectResponse(redirect_url)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, proxy_headers=True, forwarded_allow_ips="*")
